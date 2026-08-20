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


class BusinessConfigRegistry:
    """配置版本的持久化访问层；所有读取均必须带明确 business/version。"""

    def __init__(self, store: StoragePort) -> None:
        self._store = store

    def exists(self, business_id: str, config_version: str) -> bool:
        """检查版本是否已经存在，用于防止 import 覆盖已有审核轨迹。"""

        return self._store.get_record(self._record_id(business_id, config_version)) is not None

    def save(self, package: BusinessConfigPackage) -> None:
        """保存 pending 或 approved package；状态升级只能由 Pipeline 的审核门生成。"""

        self._store.save_record(
            StoredRecord.new(
                record_id=package.record_id,
                kind=_RECORD_KIND,
                payload=package.to_dict(),
            )
        )

    def get(self, business_id: str, config_version: str) -> BusinessConfigPackage:
        """回读任意已导入版本；调用者若需要 Agent 输入必须使用 get_confirmed。"""

        record = self._store.get_record(self._record_id(business_id, config_version))
        if record is None or record.kind != _RECORD_KIND:
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
        return package

    @staticmethod
    def _record_id(business_id: str, config_version: str) -> str:
        """生成与 BusinessConfigPackage 一致的存储 ID；输入已在 Validator 处校验。"""

        return f"config:{business_id}:{config_version}"

    @staticmethod
    def _from_payload(payload: Mapping[str, Any]) -> BusinessConfigPackage:
        """从 Storage 快照恢复领域对象，避免 Registry 依赖 SQLite row 或 JSON 字段细节。"""

        manifest_payload = payload.get("manifest")
        documents = payload.get("documents")
        if not isinstance(manifest_payload, Mapping) or not isinstance(documents, Mapping):
            raise ConfigNotFoundError("config_record_payload_invalid")
        try:
            manifest = BusinessConfigManifest(
                schema_version=int(manifest_payload["schema_version"]),
                business_id=str(manifest_payload["business_id"]),
                config_version=str(manifest_payload["config_version"]),
                source_refs=tuple(str(item) for item in manifest_payload["source_refs"]),
                classification=ConfigClassification(str(manifest_payload["classification"])),
                review_status=ConfigReviewStatus(str(manifest_payload["review_status"])),
                reviewed_by=manifest_payload.get("reviewed_by"),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ConfigNotFoundError("config_record_manifest_invalid") from error
        return BusinessConfigPackage(manifest=manifest, documents=documents)
