"""
用途：
定义 Business Config（业务配置）包的中性数据合同、状态枚举与领域错误。

上游：
Loader 和 Validator 将 JSON/YAML 原始输入转换成这些不可变对象。

下游：
Registry、未来 Agent、CLI 和 Local API 只能读取经过本合同校验的配置版本。

边界：
合同描述配置治理，不决定业务事实；Research、Hypothesis 或未审核数据不能被本对象自动变成 confirmed config。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import re
from typing import Any, Mapping, Tuple

from general_ai_business_os.domain.immutability import freeze_mapping, to_mutable_json


class BusinessConfigError(ValueError):
    """Business Config 流程的基础异常，便于 CLI/API 返回可审查的阻断原因。"""


class ConfigLoadError(BusinessConfigError):
    """配置文件不存在、格式错误或根结构不符合要求。"""


class ConfigValidationError(BusinessConfigError):
    """配置字段、版本、来源或初始审核状态违反 closed contract。"""


class ConfigDuplicateVersionError(BusinessConfigError):
    """相同 business_id/config_version 已存在，不能通过导入静默覆盖。"""


class ConfigNotFoundError(BusinessConfigError):
    """请求的配置版本尚未导入本地 Registry。"""


class ConfigNotConfirmedError(BusinessConfigError):
    """配置尚未同时满足 confirmed classification 与 named approval，不能供 Agent 消费。"""


class ConfigClassificationError(BusinessConfigError):
    """试图将不属于 confirmed fact 的输入通过审核流程提升为可消费配置。"""


_SAFE_IDENTIFIER = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_SAFE_EVENT_IDENTIFIER = re.compile(r"^config-event:[A-Z][A-Z0-9_]{2,63}:[A-Z][A-Z0-9_]{2,63}:2:(?:review|reject)$")
_DOCUMENT_SCHEMAS = {
    "market": {"market_code": "code", "segment_codes": "code_list"},
    "customer": {"persona_code": "code", "need_codes": "code_list"},
    "product": {"product_code": "code", "fact_refs": "code_list"},
    "channel": {"channel_code": "code", "allowed_action_codes": "code_list"},
    "content_rules": {"template_codes": "code_list", "quality_rule_codes": "code_list"},
    "sales_rules": {"intent_codes": "code_list", "blocked_term_codes": "code_list"},
    "lead_rules": {"required_profile_fields": "code_list", "score_rule_codes": "code_list"},
}


def _require_identifier(value: Any, field_name: str) -> str:
    """所有长期可引用的配置标识使用受限 code，禁止自由文本伪装 provenance 或审批身份。"""

    if not isinstance(value, str) or not _SAFE_IDENTIFIER.fullmatch(value):
        raise ConfigValidationError(f"config_{field_name}_invalid")
    return value


def _validate_documents(documents: Mapping[str, Any]) -> Mapping[str, Any]:
    """对每个可选领域文件执行 closed field schema，防止未知数据直接成为 Agent 输入。"""

    if not isinstance(documents, Mapping):
        raise ConfigValidationError("config_documents_mapping_required")
    normalized = {}
    for name, payload in documents.items():
        schema = _DOCUMENT_SCHEMAS.get(name)
        if schema is None or not isinstance(payload, Mapping) or set(payload) != set(schema):
            raise ConfigValidationError("config_document_schema_invalid")
        normalized_document = {}
        for field, field_type in schema.items():
            value = payload[field]
            if field_type == "code":
                normalized_document[field] = _require_identifier(value, field)
            else:
                if not isinstance(value, (list, tuple)) or not value:
                    raise ConfigValidationError(f"config_{field}_required")
                normalized_document[field] = [_require_identifier(item, field) for item in value]
        normalized[name] = normalized_document
    return normalized


class ConfigClassification(str, Enum):
    """配置来源当前的事实治理级别；值只表达状态，不表达任何具体商业选择。"""

    RESEARCH = "RESEARCH"
    FACT_CANDIDATE = "FACT_CANDIDATE"
    CONFIRMED_FACT = "CONFIRMED_FACT"
    HYPOTHESIS = "HYPOTHESIS"
    DECISION = "DECISION"
    UNKNOWN = "UNKNOWN"


class ConfigReviewStatus(str, Enum):
    """人工审核队列状态；导入时只能为 PENDING。"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class BusinessConfigManifest:
    """
    作用：
    保存一个配置版本的技术身份、来源引用和审核状态。

    关键边界：
    `review_status` 在导入时必须是 PENDING；只有 Pipeline 的具名人工审核动作可生成 APPROVED。
    """

    schema_version: int
    business_id: str
    config_version: str
    source_refs: Tuple[str, ...]
    classification: ConfigClassification
    review_status: ConfigReviewStatus
    reviewed_by: str | None
    approval_event_id: str | None = None

    def __post_init__(self) -> None:
        """公开构造也必须执行 schema、identity、provenance 和状态组合验证。"""

        if isinstance(self.schema_version, bool) or self.schema_version != 1:
            raise ConfigValidationError("config_schema_version_invalid")
        object.__setattr__(self, "business_id", _require_identifier(self.business_id, "business_id"))
        object.__setattr__(self, "config_version", _require_identifier(self.config_version, "config_version"))
        if not self.source_refs:
            raise ConfigValidationError("config_source_refs_required")
        refs = tuple(_require_identifier(value, "source_ref") for value in self.source_refs)
        if len(set(refs)) != len(refs):
            raise ConfigValidationError("config_source_refs_duplicate")
        object.__setattr__(self, "source_refs", refs)
        if self.review_status == ConfigReviewStatus.PENDING:
            if self.reviewed_by is not None or self.approval_event_id is not None:
                raise ConfigValidationError("config_pending_must_not_have_decision_evidence")
        elif self.review_status in (ConfigReviewStatus.APPROVED, ConfigReviewStatus.REJECTED):
            object.__setattr__(self, "reviewed_by", _require_identifier(self.reviewed_by, "reviewer"))
            if not isinstance(self.approval_event_id, str) or not _SAFE_EVENT_IDENTIFIER.fullmatch(self.approval_event_id):
                raise ConfigValidationError("config_approval_event_invalid")
        else:
            raise ConfigValidationError("config_review_status_invalid")

    def approved(self, reviewer: str, approval_event_id: str) -> "BusinessConfigManifest":
        """生成有具名 reviewer 的批准副本；调用方仍须先经过 classification gate。"""

        return replace(
            self,
            review_status=ConfigReviewStatus.APPROVED,
            reviewed_by=reviewer,
            approval_event_id=approval_event_id,
        )

    def rejected(self, reviewer: str, decision_event_id: str) -> "BusinessConfigManifest":
        """生成带可回读拒绝事件的版本，拒绝状态仍不可被 Agent 消费。"""

        return replace(
            self,
            review_status=ConfigReviewStatus.REJECTED,
            reviewed_by=reviewer,
            approval_event_id=decision_event_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """输出新的可 JSON 编码 manifest 快照，不暴露内部 tuple 引用。"""

        return {
            "schema_version": self.schema_version,
            "business_id": self.business_id,
            "config_version": self.config_version,
            "source_refs": list(self.source_refs),
            "classification": self.classification.value,
            "review_status": self.review_status.value,
            "reviewed_by": self.reviewed_by,
            "approval_event_id": self.approval_event_id,
        }


@dataclass(frozen=True)
class BusinessConfigPackage:
    """
    作用：
    把经过校验的 manifest 与各能力域文档组合为一个不可变配置版本。

    关键边界：
    文档值只来自输入包；通用系统不填充国家、客户、产品、价格或平台默认值。
    """

    manifest: BusinessConfigManifest
    documents: Mapping[str, Any]

    def __post_init__(self) -> None:
        """深层冻结文档，避免导入后调用者通过容器别名改写已审核版本。"""

        object.__setattr__(self, "documents", freeze_mapping(_validate_documents(self.documents)))

    @property
    def record_id(self) -> str:
        """生成稳定的本地 record ID；业务代码与版本均经 Validator 的安全格式校验。"""

        return f"config:{self.manifest.business_id}:{self.manifest.config_version}"

    def approved(self, reviewer: str, approval_event_id: str) -> "BusinessConfigPackage":
        """返回批准后的不可变版本；不修改原 pending 版本。"""

        return BusinessConfigPackage(
            manifest=self.manifest.approved(reviewer, approval_event_id),
            documents=self.documents,
        )

    def rejected(self, reviewer: str, decision_event_id: str) -> "BusinessConfigPackage":
        """返回不可消费的拒绝版本，保留与 lifecycle event 的绑定。"""

        return BusinessConfigPackage(
            manifest=self.manifest.rejected(reviewer, decision_event_id),
            documents=self.documents,
        )

    def to_dict(self) -> dict[str, Any]:
        """导出新的 JSON-compatible 快照，供 Storage Port 持久化。"""

        return {"manifest": self.manifest.to_dict(), "documents": to_mutable_json(self.documents)}
