"""
用途：
校验 Business Config manifest 的 closed schema、来源引用、初始审核状态与稳定标识格式。

上游：
Loader 输出的原始 mapping 进入此模块。

下游：
Pipeline 获得可安全持久化的 BusinessConfigPackage。

边界：
Validator 只确认结构和治理前提；它不裁决 Research 真伪，也不将配置升级成商业 Decision。
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from general_ai_business_os.business_config.contracts import (
    BusinessConfigManifest,
    BusinessConfigPackage,
    ConfigClassification,
    ConfigReviewStatus,
    ConfigValidationError,
)


_MANIFEST_FIELDS = {
    "schema_version",
    "business_id",
    "config_version",
    "source_refs",
    "classification",
    "review_status",
    "reviewed_by",
}
_SAFE_IDENTIFIER = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")


class BusinessConfigValidator:
    """将安全 mapping 转换为不可变 package，并拒绝导入端伪造的批准状态。"""

    def validate(
        self,
        manifest_payload: Mapping[str, Any],
        documents: Mapping[str, Mapping[str, Any]],
    ) -> BusinessConfigPackage:
        """校验 closed manifest 后返回 pending package；审核状态由 Pipeline 而非输入文件控制。"""

        if set(manifest_payload) != _MANIFEST_FIELDS:
            raise ConfigValidationError("config_manifest_fields_invalid")
        schema_version = manifest_payload["schema_version"]
        if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version != 1:
            raise ConfigValidationError("config_schema_version_invalid")
        business_id = self._require_identifier(manifest_payload["business_id"], "business_id")
        config_version = self._require_identifier(manifest_payload["config_version"], "config_version")
        source_refs = manifest_payload["source_refs"]
        if not isinstance(source_refs, list) or not source_refs:
            raise ConfigValidationError("config_source_refs_required")
        normalized_refs = tuple(self._require_identifier(value, "source_ref") for value in source_refs)
        if len(set(normalized_refs)) != len(normalized_refs):
            raise ConfigValidationError("config_source_refs_duplicate")
        try:
            classification = ConfigClassification(manifest_payload["classification"])
        except (TypeError, ValueError) as error:
            raise ConfigValidationError("config_classification_invalid") from error
        if manifest_payload["review_status"] != ConfigReviewStatus.PENDING.value:
            raise ConfigValidationError("config_initial_review_status_must_be_pending")
        if manifest_payload["reviewed_by"] is not None:
            raise ConfigValidationError("config_initial_reviewer_must_be_null")
        for name, payload in documents.items():
            if not isinstance(name, str) or not isinstance(payload, Mapping):
                raise ConfigValidationError("config_document_mapping_required")
        manifest = BusinessConfigManifest(
            schema_version=schema_version,
            business_id=business_id,
            config_version=config_version,
            source_refs=normalized_refs,
            classification=classification,
            review_status=ConfigReviewStatus.PENDING,
            reviewed_by=None,
        )
        return BusinessConfigPackage(manifest=manifest, documents=dict(documents))

    @staticmethod
    def _require_identifier(value: Any, field_name: str) -> str:
        """只接受 stable source/business/version code，防止自由文本隐式成为配置身份或 provenance。"""

        if not isinstance(value, str) or not _SAFE_IDENTIFIER.fullmatch(value):
            raise ConfigValidationError(f"config_{field_name}_invalid")
        return value
