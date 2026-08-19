"""
用途：
实现 Research 导入治理的可组合小组件。

上游：
services.data_governance 把 dict / JSON / CSV 输入送进这里，完成解析、清洗、校验、
去重、冲突与时效判断。

下游：
返回标准化字典、领域对象或更新后的事实记录，供仓库与审计层持久化。

边界：
这里只做纯 Python 数据治理，不直接写 SQLite、不写审计文件，也不决定任何业务战略。
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from io import StringIO
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from medical_tourism_os.domain.entities import FactRecord, ReviewStatus
from medical_tourism_os.domain.policies import is_sensitive_key


class ValidationError(ValueError):
    """表示输入不满足治理合同，必须在写库前 fail-closed。"""


class Importer:
    """
    作用：
    提供 dict、JSON 和 CSV 的统一导入入口。

    输入：
    `payload` 可以是 dict、list[dict] 或文本；`format_name` 声明导入格式。

    输出：
    标准化前的记录字典列表。

    关键边界：
    这里只负责“把输入拆成记录”，不做字段语义判断；校验和清洗由后续组件处理。
    """

    def load(self, payload: Any, format_name: str = "dict") -> List[Dict[str, Any]]:
        normalized_format = format_name.strip().lower()
        if normalized_format == "dict":
            return self._from_dict_payload(payload)
        if normalized_format == "json":
            return self._from_json_text(str(payload))
        if normalized_format == "csv":
            return self._from_csv_text(str(payload))
        raise ValidationError(f"unsupported_import_format:{format_name}")

    def _from_dict_payload(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, Mapping):
            return [dict(payload)]
        if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
            records = []
            for item in payload:
                if not isinstance(item, Mapping):
                    raise ValidationError("dict_import_requires_mapping_items")
                records.append(dict(item))
            return records
        raise ValidationError("dict_import_requires_mapping_payload")

    def _from_json_text(self, payload: str) -> List[Dict[str, Any]]:
        try:
            loaded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValidationError("invalid_json_payload") from exc
        return self._from_dict_payload(loaded)

    def _from_csv_text(self, payload: str) -> List[Dict[str, Any]]:
        reader = csv.DictReader(StringIO(payload))
        if reader.fieldnames is None:
            raise ValidationError("csv_requires_header")
        return [dict(row) for row in reader]


class Normalizer:
    """
    作用：
    把 Research 输入整理为服务层和仓库都能稳定处理的字段集合。

    输入：
    原始记录字典、来源字符串与导入格式名。

    输出：
    只包含治理链必需字段的新字典。

    关键边界：
    不信任调用者传入的 classification/review_status，因为 Research 输入不能自带“已批准”语义。
    """

    def normalize(
        self,
        payload: Mapping[str, Any],
        source: str,
        import_format: str,
    ) -> Dict[str, Any]:
        claim = " ".join(str(payload.get("claim", "")).split())
        scope = " ".join(str(payload.get("scope", "unspecified_scope")).split())
        source_date = str(payload.get("source_date", "")).strip()
        provenance = str(payload.get("provenance", "")).strip() or (
            f"import:{import_format}|source:{source.strip()}"
        )
        normalized = {
            "claim": claim,
            "source": source.strip(),
            "source_date": source_date,
            "scope": scope or "unspecified_scope",
            "provenance": provenance,
            "import_format": import_format.strip().lower(),
        }
        return normalized


class Validator:
    """
    作用：
    在任何持久化之前执行 fail-closed 校验。

    输入：
    原始记录与标准化后的记录。

    输出：
    无；若不合法则抛 `ValidationError`。

    关键边界：
    这里优先阻止敏感键名、空 claim、无 provenance 和伪造审批状态，
    因为这些问题一旦入库，后面再补救已经太晚。
    """

    def validate(
        self,
        original_payload: Mapping[str, Any],
        normalized_payload: Mapping[str, Any],
    ) -> None:
        for key in original_payload.keys():
            if is_sensitive_key(str(key)):
                raise ValidationError("sensitive_input_detected")

        if not str(normalized_payload.get("source", "")).strip():
            raise ValidationError("source_is_required")

        claim = str(normalized_payload.get("claim", "")).strip()
        if not claim:
            raise ValidationError("claim_is_required")

        scope = str(normalized_payload.get("scope", "")).strip()
        if not scope:
            raise ValidationError("scope_is_required")

        provenance = str(normalized_payload.get("provenance", "")).strip()
        if not provenance:
            raise ValidationError("provenance_is_required")

        source_date_value = str(normalized_payload.get("source_date", "")).strip()
        if not source_date_value:
            raise ValidationError("source_date_is_required")
        try:
            date.fromisoformat(source_date_value)
        except ValueError as exc:
            raise ValidationError("invalid_source_date") from exc

        requested_classification = str(original_payload.get("classification", "")).strip().upper()
        requested_review_status = str(original_payload.get("review_status", "")).strip().upper()
        forbidden = {"CANONICAL_FACT", "DECISION", "APPROVED"}
        if requested_classification in forbidden or requested_review_status in forbidden:
            raise ValidationError("research_input_cannot_preapprove_fact")


class Deduplicator:
    """
    作用：
    基于稳定签名识别重复候选，避免静默写出第二条相同事实。

    输入：
    标准化载荷与现有事实记录列表。

    输出：
    命中时返回已存在记录，否则返回 `None`。

    关键边界：
    签名只依赖已清洗后的 claim/source/source_date/scope，确保不同空白或输入格式
    不会生成“看起来不同、语义相同”的重复候选。
    """

    def build_signature(self, payload: Mapping[str, Any]) -> str:
        raw = "|".join(
            [
                str(payload.get("claim", "")),
                str(payload.get("source", "")),
                str(payload.get("source_date", "")),
                str(payload.get("scope", "")),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def find_duplicate(
        self,
        normalized_payload: Mapping[str, Any],
        existing_records: Iterable[FactRecord],
    ) -> Optional[FactRecord]:
        signature = self.build_signature(normalized_payload)
        for record in existing_records:
            record_signature = self.build_signature(
                {
                    "claim": record.claim,
                    "source": record.source,
                    "source_date": record.source_date,
                    "scope": record.scope,
                }
            )
            if record_signature == signature:
                return record
        return None


class ConflictDetector:
    """
    作用：
    把冲突显式标记为人工复核信号，而不是自动裁决谁真谁假。

    输入：
    两条已存在的事实记录。

    输出：
    两条新的冲突态事实记录。

    关键边界：
    系统只标记冲突，不负责决定哪条结论正确。
    """

    def mark(self, left: FactRecord, right: FactRecord) -> tuple[FactRecord, FactRecord]:
        updated_left = left.with_updates(conflict_status="conflicted", review_status=ReviewStatus.PENDING)
        updated_right = right.with_updates(conflict_status="conflicted", review_status=ReviewStatus.PENDING)
        return updated_left, updated_right


class FreshnessChecker:
    """
    作用：
    根据来源日期判断记录是否过期。

    输入：
    一条事实记录、比较日期与允许的最大天数。

    输出：
    带 freshness 更新的新 `FactRecord`。

    关键边界：
    过期只意味着“需要人再看一次”，不是自动判假。
    """

    def check(self, record: FactRecord, as_of: date, max_age_days: int) -> FactRecord:
        record_date = date.fromisoformat(record.source_date)
        age_days = (as_of - record_date).days
        freshness = "stale" if age_days > max_age_days else "fresh"
        return record.with_updates(freshness=freshness)


class FactReviewQueue:
    """
    作用：
    提供待人工复核事实的最小队列视图。

    输入：
    一组事实记录。

    输出：
    所有待复核的候选列表。

    关键边界：
    只暴露 `PENDING` 的候选；已批准或已拒绝记录不再进入当前待办。
    """

    def pending(self, records: Iterable[FactRecord]) -> List[FactRecord]:
        return [
            record
            for record in records
            if record.review_status == ReviewStatus.PENDING
        ]
