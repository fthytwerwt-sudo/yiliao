"""
用途：
定义 Acquisition Plugin 的 Business Entity、Prospect、Contact Point 与 Outreach Draft。

上游：
目录 Provider、分类/评分服务和人工审核 Workflow 创建这些 immutable（不可变）对象。

下游：
schemas、Mock Adapter 与 Workflow 只通过这些对象交换 B2B 获客状态。

边界：
本文件不包含 Consumer Lead、患者、consent、intent、SQL、HTTP 或真实平台逻辑；
联系方式只保存公开信息的 opaque reference（不透明引用），不保存原始邮箱或电话。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import re
from typing import Any, Dict, Optional


_PUBLIC_CONTACT_REFERENCE = re.compile(r"^public_contact_ref_[0-9a-f]{32}$")


def _require_text(field_name: str, value: str) -> str:
    """校验跨层必填文本，避免空值进入评分、审核和 Adapter。"""

    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{field_name}_required")
    return normalized


def _normalize_refs(field_name: str, values: tuple[str, ...], *, required: bool) -> tuple[str, ...]:
    """稳定去重 evidence/contact refs；缺必需证据时 fail-closed。"""

    normalized = tuple(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))
    if required and not normalized:
        raise ValueError(f"{field_name}_required")
    return normalized


class BusinessCategory(str, Enum):
    """企业候选分类；UNKNOWN 表示尚未得到可审计的分类结果。"""

    TRAVEL_AGENCY = "travel_agency"
    COMMUNITY = "community"
    INSURANCE = "insurance"
    HEALTH_SERVICE = "health_service"
    UNKNOWN = "unknown"


class BusinessEntityStatus(str, Enum):
    """企业实体生命周期，不表达已合作或真实签约。"""

    DISCOVERED = "discovered"
    CLASSIFIED = "classified"
    HELD = "held"


class ProspectPriority(str, Enum):
    """合作潜客优先级，与 Consumer Lead 的 intent/score band 无关。"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProspectStatus(str, Enum):
    """评分后的候选队列；OUTREACH_QUEUE 仍不等于获准或已经发送。"""

    HUMAN_REVIEW_QUEUE = "human_review_queue"
    OUTREACH_QUEUE = "outreach_queue"
    HOLD_FOR_MORE_EVIDENCE = "hold_for_more_evidence"


class ContactType(str, Enum):
    """当前只允许公开商业邮箱/电话的引用。"""

    PUBLIC_EMAIL = "public_email"
    PUBLIC_PHONE = "public_phone"


class OutreachReviewStatus(str, Enum):
    """触达草稿的人工审核状态。"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class BusinessEntity:
    """
    作用：表达从公开企业目录候选中发现的一家企业。

    关键边界：source/evidence 只证明“这条候选从何而来”，不证明企业真实、有效或愿意合作。
    """

    id: str
    company_name: str
    category: BusinessCategory
    location: str
    website: str
    description: str
    source_url: str
    evidence_refs: tuple[str, ...]
    status: BusinessEntityStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_text("business_entity_id", self.id))
        object.__setattr__(self, "company_name", _require_text("company_name", self.company_name))
        object.__setattr__(self, "location", _require_text("location", self.location))
        object.__setattr__(self, "website", str(self.website).strip())
        object.__setattr__(self, "description", str(self.description).strip())
        object.__setattr__(self, "source_url", _require_text("source_url", self.source_url))
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs("evidence_refs", self.evidence_refs, required=True),
        )

    def to_dict(self) -> Dict[str, Any]:
        """返回可序列化企业候选视图。"""

        return asdict(self)


@dataclass(frozen=True)
class Prospect:
    """表达独立 B2B 合作潜客评分结果，不携带 Consumer Lead 字段。"""

    id: str
    business_entity_id: str
    fit_score: int
    priority: ProspectPriority
    reason_codes: tuple[str, ...]
    status: ProspectStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_text("prospect_id", self.id))
        object.__setattr__(
            self,
            "business_entity_id",
            _require_text("business_entity_id", self.business_entity_id),
        )
        if not 0 <= int(self.fit_score) <= 100:
            raise ValueError("fit_score_out_of_range")
        object.__setattr__(self, "fit_score", int(self.fit_score))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_refs("reason_codes", self.reason_codes, required=True),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContactPoint:
    """
    作用：保存公开商业联系方式的引用与来源。

    关键边界：value_reference 不是邮箱/电话号码本身；`@`、`+` 等原始联系人形式会被拒绝。
    """

    type: ContactType
    value_reference: str
    source: str
    verified_at: Optional[str]

    def __post_init__(self) -> None:
        reference = _require_text("value_reference", self.value_reference)
        # 固定长度 hex token 让 reference 无法通过“加前缀”夹带邮箱或电话号码原文。
        if _PUBLIC_CONTACT_REFERENCE.fullmatch(reference) is None:
            raise ValueError("public_contact_reference_required")
        object.__setattr__(self, "value_reference", reference)
        object.__setattr__(self, "source", _require_text("contact_source", self.source))
        if self.verified_at is not None:
            object.__setattr__(self, "verified_at", _require_text("verified_at", self.verified_at))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OutreachDraft:
    """表达只供人工审核的触达草稿；创建草稿永远不代表已发送。"""

    prospect_id: str
    subject: str
    body: str
    personalization_reason: str
    review_status: OutreachReviewStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "prospect_id", _require_text("prospect_id", self.prospect_id))
        object.__setattr__(self, "subject", _require_text("outreach_subject", self.subject))
        object.__setattr__(self, "body", _require_text("outreach_body", self.body))
        object.__setattr__(
            self,
            "personalization_reason",
            _require_text("personalization_reason", self.personalization_reason),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
