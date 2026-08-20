"""
用途：
将经过 Validator 的配置版本保存到中性 Storage Port，并只向 Agent 暴露 confirmed+approved 版本。

上游：
Pipeline 调用 Registry 持久化 pending/approved 配置包。

下游：
未来 Agent 使用 `get_confirmed` 明确请求一个 business_id/config_version。

边界：
Registry 不会选择默认业务配置，也不会在版本缺失时回退；缺少审核必须 fail-closed。
"""

from __future__ import annotations

from typing import Any, Mapping

from general_ai_business_os.business_config.contracts import (
    BusinessConfigManifest,
    BusinessConfigPackage,
    ConfigClassification,
    ConfigNotConfirmedError,
    ConfigNotFoundError,
    ConfigReviewStatus,
)
from general_ai_business_os.domain.entities import StoredRecord
from general_ai_business_os.storage.contracts import StoragePort


_RECORD_KIND = "business_config_package"
_EVENT_KIND = "business_config_event"


class BusinessConfigRegistry:
    """配置版本的持久化访问层；所有读取均必须带明确 business/version。"""

    def __init__(self, store: StoragePort) -> None:
        self._store = store

    def exists(self, business_id: str, config_version: str) -> bool:
        """检查版本是否已经存在，用于防止 import 覆盖已有审核轨迹。"""

        return self._store.get_record(self._record_id(business_id, config_version)) is not None

    def stage_import(self, package: BusinessConfigPackage) -> None:
        """保存首次 pending 版本并写入 append-only import event；同 ID 不允许覆盖。"""

        if self.exists(package.manifest.business_id, package.manifest.config_version):
            raise ConfigNotConfirmedError("config_version_already_exists")
        self._store.save_record(
            StoredRecord.new(
                record_id=package.record_id,
                kind=_RECORD_KIND,
                payload=package.to_dict(),
            )
        )
        self._store.save_record(
            StoredRecord.new(
                record_id=self._event_id(package, sequence=1, action="import"),
                kind=_EVENT_KIND,
                payload=self._event_payload(package, sequence=1, action="import", reviewer=None),
            )
        )

    def record_decision(self, package: BusinessConfigPackage, *, action: str, reviewer: str) -> BusinessConfigPackage:
        """写入 review/reject event 后更新当前快照，使批准版本拥有可回读证据。"""

        current = self.get(package.manifest.business_id, package.manifest.config_version)
        if current.manifest.review_status != ConfigReviewStatus.PENDING:
            raise ConfigNotConfirmedError("config_review_not_pending")
        event_id = self._event_id(package, sequence=2, action=action)
        decision = (
            package.approved(reviewer, event_id)
            if action == "review"
            else package.rejected(reviewer, event_id)
        )
        self._store.save_record(
            StoredRecord.new(record_id=decision.record_id, kind=_RECORD_KIND, payload=decision.to_dict())
        )
        self._store.save_record(
            StoredRecord.new(
                record_id=event_id,
                kind=_EVENT_KIND,
                payload=self._event_payload(decision, sequence=2, action=action, reviewer=reviewer),
            )
        )
        return decision

    def save(self, _package: BusinessConfigPackage) -> None:
        """拒绝绕过 Pipeline 的公开保存；配置状态只能由 stage_import/record_decision 写入。"""

        raise ConfigNotConfirmedError("config_registry_save_not_public")

    def get(self, business_id: str, config_version: str) -> BusinessConfigPackage:
        """回读任意已导入版本；调用者若需要 Agent 输入必须使用 get_confirmed。"""

        record = self._store.get_record(self._record_id(business_id, config_version))
        if record is None or record.kind != _RECORD_KIND or record.id != self._record_id(business_id, config_version):
            raise ConfigNotFoundError("config_version_not_found")
        return self._from_payload(record.payload)

    def get_confirmed(self, business_id: str, config_version: str) -> BusinessConfigPackage:
        """只返回 confirmed fact 且具有具名人工批准的版本，其他状态一律阻断。"""

        package = self.get(business_id, config_version)
        manifest = package.manifest
        if (
            manifest.classification != ConfigClassification.CONFIRMED_FACT
            or manifest.review_status != ConfigReviewStatus.APPROVED
            or manifest.reviewed_by is None
        ):
            raise ConfigNotConfirmedError("config_version_not_confirmed")
        approval = self._store.get_record(manifest.approval_event_id)
        if approval is None or approval.kind != _EVENT_KIND:
            raise ConfigNotConfirmedError("config_approval_event_missing")
        expected_action = "review" if manifest.review_status == ConfigReviewStatus.APPROVED else "reject"
        if approval.payload != self._event_payload(package, sequence=2, action=expected_action, reviewer=manifest.reviewed_by):
            raise ConfigNotConfirmedError("config_approval_event_invalid")
        return package

    @staticmethod
    def _record_id(business_id: str, config_version: str) -> str:
        """生成与 BusinessConfigPackage 一致的存储 ID；输入已在 Validator 处校验。"""

        return f"config:{business_id}:{config_version}"

    @staticmethod
    def _from_payload(payload: Mapping[str, Any]) -> BusinessConfigPackage:
        """从 Storage 快照恢复领域对象，避免 Registry 依赖 SQLite row 或 JSON 字段细节。"""

        if set(payload) != {"manifest", "documents"}:
            raise ConfigNotFoundError("config_record_payload_fields_invalid")
        manifest_payload = payload.get("manifest")
        documents = payload.get("documents")
        if not isinstance(manifest_payload, Mapping) or not isinstance(documents, Mapping):
            raise ConfigNotFoundError("config_record_payload_invalid")
        if set(manifest_payload) != {
            "schema_version",
            "business_id",
            "config_version",
            "source_refs",
            "classification",
            "review_status",
            "reviewed_by",
            "approval_event_id",
        }:
            raise ConfigNotFoundError("config_record_manifest_fields_invalid")
        try:
            manifest = BusinessConfigManifest(
                schema_version=manifest_payload["schema_version"],
                business_id=manifest_payload["business_id"],
                config_version=manifest_payload["config_version"],
                source_refs=tuple(manifest_payload["source_refs"]),
                classification=ConfigClassification(manifest_payload["classification"]),
                review_status=ConfigReviewStatus(manifest_payload["review_status"]),
                reviewed_by=manifest_payload.get("reviewed_by"),
                approval_event_id=manifest_payload.get("approval_event_id"),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ConfigNotFoundError("config_record_manifest_invalid") from error
        return BusinessConfigPackage(manifest=manifest, documents=documents)

    @staticmethod
    def _event_id(package: BusinessConfigPackage, *, sequence: int, action: str) -> str:
        """事件 ID 与版本、顺序和动作绑定，便于 get_confirmed 回读审核因果。"""

        return f"config-event:{package.manifest.business_id}:{package.manifest.config_version}:{sequence}:{action}"

    @staticmethod
    def _event_payload(
        package: BusinessConfigPackage,
        *,
        sequence: int,
        action: str,
        reviewer: str | None,
    ) -> Mapping[str, Any]:
        """事件只保存受限 identity/status/reviewer code，不保存业务内容或自由文本。"""

        return {
            "business_id": package.manifest.business_id,
            "config_version": package.manifest.config_version,
            "sequence": sequence,
            "action": action,
            "reviewer": reviewer,
            "classification": package.manifest.classification.value,
            "review_status": package.manifest.review_status.value,
        }
