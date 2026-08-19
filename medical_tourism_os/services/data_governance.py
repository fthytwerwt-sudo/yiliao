"""
用途：
编排 Research → Raw → Staging → Adjudicated → Canonical 的数据治理流程。

上游：
测试、CLI 和未来本地 API 把 Research 输入交给这里；人工复核也通过这里推进正式事实。

下游：
repository 保存 `FactRecord` 与生命周期事件，audit_logger 只记录已脱敏的安全审计元数据。

边界：
这里不写 SQL、不自动形成业务 Decision，也不允许 Research/AI 输入绕过人工 gate 直接变成 canonical。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Optional, Sequence, Tuple

from medical_tourism_os.audit.logger import AuditLogger
from medical_tourism_os.domain.entities import (
    FactClassification,
    FactRecord,
    LifecycleEvent,
    LifecycleStage,
    ReviewStatus,
)
from medical_tourism_os.imports.pipeline import (
    ConflictDetector,
    Deduplicator,
    FactReviewQueue,
    FreshnessChecker,
    Importer,
    Normalizer,
    ValidationError,
    Validator,
)
from medical_tourism_os.repositories.core import FactRepository


class ReviewGateError(ValueError):
    """表示人工复核 gate 未满足，系统必须拒绝状态晋升。"""


@dataclass(frozen=True)
class IngestionResult:
    """
    作用：
    返回一次导入治理后的核心结果给调用方。

    输入：
    最终候选记录、经历的生命周期、是否重复及重复目标。

    输出：
    稳定 dataclass，便于测试与未来接口层序列化。

    关键边界：
    `record` 永远表示当前治理后的候选事实，不代表它已经是 canonical 或 decision。
    """

    record: FactRecord
    lifecycle: Tuple[str, ...]
    duplicate_of: Optional[str]
    is_duplicate: bool


class DataGovernanceService:
    """
    作用：
    把导入管线、审计、人工复核和 canonical promotion 组合成可验证工作流。

    输入：
    `FactRepository`、`AuditLogger` 与可替换的纯 Python 组件。

    输出：
    导入结果、更新后的事实记录、待复核队列与生命周期事件。

    关键边界：
    服务只负责治理，不决定市场/医院/产品等业务策略，也不会自动创建正式 Decision。
    """

    def __init__(
        self,
        repository: FactRepository,
        audit_logger: AuditLogger,
        importer: Optional[Importer] = None,
        normalizer: Optional[Normalizer] = None,
        deduplicator: Optional[Deduplicator] = None,
        validator: Optional[Validator] = None,
        conflict_detector: Optional[ConflictDetector] = None,
        freshness_checker: Optional[FreshnessChecker] = None,
        review_queue: Optional[FactReviewQueue] = None,
    ) -> None:
        self.repository = repository
        self.audit_logger = audit_logger
        self.importer = importer or Importer()
        self.normalizer = normalizer or Normalizer()
        self.deduplicator = deduplicator or Deduplicator()
        self.validator = validator or Validator()
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.freshness_checker = freshness_checker or FreshnessChecker()
        self.review_queue = review_queue or FactReviewQueue()

    def ingest_research(self, payload: Any, source: str) -> IngestionResult:
        """以默认 dict 入口导入一条 Research 记录。"""

        return self.ingest_research_input(payload=payload, source=source, format_name="dict")

    def ingest_research_json(self, payload: str, source: str) -> IngestionResult:
        """通过 JSON 文本入口导入一条或一组 Research 记录。"""

        return self.ingest_research_input(payload=payload, source=source, format_name="json")

    def ingest_research_csv(self, payload: str, source: str) -> IngestionResult:
        """通过 CSV 文本入口导入一条或一组 Research 记录。"""

        return self.ingest_research_input(payload=payload, source=source, format_name="csv")

    def ingest_research_input(
        self,
        payload: Any,
        source: str,
        format_name: str = "dict",
    ) -> IngestionResult:
        """
        作用：
        执行一次完整的 Research 导入治理。

        输入：
        原始载荷、来源与导入格式。

        输出：
        `IngestionResult`，其中生命周期固定包含 `RAW/STAGING/ADJUDICATED`。

        关键边界：
        Research 在这里最多只能到 `FACT_CANDIDATE + PENDING`，不能借导入参数直接变成 canonical。
        """

        records = self.importer.load(payload, format_name=format_name)
        if len(records) != 1:
            raise ValidationError("research_ingest_requires_single_record")

        original_payload = records[0]
        try:
            normalized = self.normalizer.normalize(
                original_payload,
                source=source,
                import_format=format_name,
            )
            self.validator.validate(original_payload, normalized)
        except ValidationError as exc:
            self._record_rejection(reason=str(exc), stage=LifecycleStage.STAGING)
            raise

        duplicate = self.deduplicator.find_duplicate(normalized, self.repository.list())
        lifecycle = (
            LifecycleStage.RAW.value,
            LifecycleStage.STAGING.value,
            LifecycleStage.ADJUDICATED.value,
        )
        if duplicate is not None:
            self.audit_logger.record(
                action="research_duplicate_detected",
                outcome="accepted",
                details={
                    "record_id": duplicate.id,
                    "stage": LifecycleStage.ADJUDICATED.value,
                    "reason": "duplicate_of_existing_fact",
                    "count": 1,
                },
            )
            return IngestionResult(
                record=duplicate,
                lifecycle=lifecycle,
                duplicate_of=duplicate.id,
                is_duplicate=True,
            )

        candidate = FactRecord.new_candidate(
            claim=normalized["claim"],
            source=normalized["source"],
            source_date=normalized["source_date"],
            scope=normalized["scope"],
            provenance=normalized["provenance"],
        )
        self.repository.save(candidate)

        # Raw 和 Staging 不能只存在于返回值里；这里显式落生命周期事件，后续可审计回读。
        self._record_lifecycle(
            record=candidate,
            stage=LifecycleStage.RAW,
            action="research_received",
            details={
                "import_format": normalized["import_format"],
                "source": candidate.source,
                "scope": candidate.scope,
            },
        )
        # Staging 只保存清洗后的 claim，而不是潜在敏感的原始自由文本。
        self._record_lifecycle(
            record=candidate,
            stage=LifecycleStage.STAGING,
            action="research_normalized",
            details={
                "claim": candidate.claim,
                "provenance": candidate.provenance,
            },
        )
        self._record_lifecycle(
            record=candidate,
            stage=LifecycleStage.ADJUDICATED,
            action="fact_candidate_created",
            details={
                "classification": candidate.classification.value,
                "review_status": candidate.review_status.value,
            },
        )
        self.audit_logger.record(
            action="research_ingested",
            outcome="accepted",
            details={
                "record_id": candidate.id,
                "stage": LifecycleStage.ADJUDICATED.value,
                "reason": "fact_candidate_created",
                "count": 1,
            },
        )
        return IngestionResult(
            record=candidate,
            lifecycle=lifecycle,
            duplicate_of=None,
            is_duplicate=False,
        )

    def check_freshness(self, record_id: str, as_of: date, max_age_days: int) -> FactRecord:
        """
        作用：
        标记一条事实记录的时效状态。

        输入：
        事实 ID、参考日期与允许最大天数。

        输出：
        更新后的 `FactRecord`。

        关键边界：
        过期只提示人工复核，不自动删除或判错。
        """

        record = self._require_record(record_id)
        updated = self.freshness_checker.check(record, as_of=as_of, max_age_days=max_age_days)
        self.repository.save(updated)
        self._record_lifecycle(
            record=updated,
            stage=LifecycleStage.ADJUDICATED,
            action="freshness_checked",
            details={
                "freshness": updated.freshness,
                "max_age_days": max_age_days,
            },
        )
        self.audit_logger.record(
            action="freshness_checked",
            outcome="accepted",
            details={
                "record_id": updated.id,
                "stage": LifecycleStage.ADJUDICATED.value,
                "reason": updated.freshness,
                "count": 1,
            },
        )
        return updated

    def mark_conflict(self, left_record_id: str, right_record_id: str) -> tuple[FactRecord, FactRecord]:
        """
        作用：
        显式标记两条记录存在冲突。

        输入：
        两个事实 ID。

        输出：
        冲突态的两条 `FactRecord`。

        关键边界：
        冲突是人工处理信号，不是系统自动裁决。
        """

        left = self._require_record(left_record_id)
        right = self._require_record(right_record_id)
        updated_left, updated_right = self.conflict_detector.mark(left, right)
        self.repository.save(updated_left)
        self.repository.save(updated_right)
        for record in (updated_left, updated_right):
            self._record_lifecycle(
                record=record,
                stage=LifecycleStage.ADJUDICATED,
                action="conflict_marked",
                details={
                    "conflict_status": record.conflict_status,
                    "review_status": record.review_status.value,
                },
            )
            self.audit_logger.record(
                action="conflict_marked",
                outcome="accepted",
                details={
                    "record_id": record.id,
                    "stage": LifecycleStage.ADJUDICATED.value,
                    "reason": "conflict_requires_review",
                    "count": 1,
                },
            )
        return updated_left, updated_right

    def approve_fact(self, record_id: str, reviewed_by: str) -> FactRecord:
        """
        作用：
        通过有名字的人类 reviewer 把待审候选提升为 canonical fact。

        输入：
        候选事实 ID 与 reviewer 名称。

        输出：
        已批准的 canonical fact。

        关键边界：
        reviewer 为空、记录不是候选、记录已被审批过，或调用者试图从其他状态反向操作时，
        都必须 fail-closed。
        """

        reviewer_name = reviewed_by.strip()
        if not reviewer_name:
            raise ReviewGateError("named_human_reviewer_required")

        record = self._require_record(record_id)
        if record.classification != FactClassification.FACT_CANDIDATE:
            raise ReviewGateError("only_fact_candidate_can_be_promoted")
        if record.review_status != ReviewStatus.PENDING:
            raise ReviewGateError("only_pending_candidate_can_be_promoted")

        canonical = record.with_updates(
            classification=FactClassification.CANONICAL_FACT,
            review_status=ReviewStatus.APPROVED,
            reviewed_by=reviewer_name,
            confidence="human_approved",
        )
        self.repository.save(canonical)
        self._record_lifecycle(
            record=canonical,
            stage=LifecycleStage.CANONICAL,
            action="fact_approved",
            details={
                "reviewed_by": reviewer_name,
                "classification": canonical.classification.value,
            },
        )
        self.audit_logger.record(
            action="fact_approved",
            outcome="accepted",
            details={
                "record_id": canonical.id,
                "stage": LifecycleStage.CANONICAL.value,
                "reason": "human_review_approved",
                "count": 1,
            },
        )
        return canonical

    def list_review_queue(self) -> Sequence[FactRecord]:
        """返回当前仍待人工复核的事实候选。"""

        return self.review_queue.pending(self.repository.list())

    def _record_lifecycle(
        self,
        record: FactRecord,
        stage: LifecycleStage,
        action: str,
        details: dict[str, Any],
    ) -> None:
        event = LifecycleEvent.new(
            record_id=record.id,
            stage=stage,
            action=action,
            details=details,
        )
        self.repository.save_lifecycle_event(event)

    def _record_rejection(self, reason: str, stage: LifecycleStage) -> None:
        """
        作用：
        记录一次被拒绝的导入尝试。

        输入：
        拒绝原因与被阻断阶段。

        输出：
        无。

        关键边界：
        敏感输入被拒绝时这里只保存最小安全审计元数据，绝不回写原始 payload。
        """

        self.audit_logger.record(
            action="research_rejected",
            outcome="blocked",
            details={
                "record_id": "pending",
                "stage": stage.value,
                "reason": reason,
                "count": 1,
            },
        )

    def _require_record(self, record_id: str) -> FactRecord:
        record = self.repository.get(record_id)
        if record is None:
            raise ValidationError("fact_record_not_found")
        return record
