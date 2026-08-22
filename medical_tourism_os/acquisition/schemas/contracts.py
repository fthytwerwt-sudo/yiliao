"""
用途：
定义 Acquisition 各层之间的显式 DTO 与 Adapter 执行状态。

上游：
Provider、评分器和 Workflow 生成这些结果。

下游：
本地测试、未来持久化/接口层和人工审查工具读取这些合同。

边界：
Adapter 结果必须同时表达 dry_run 与 executed；reply/feedback 只保存引用，不保存通信正文。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

from medical_tourism_os.acquisition.domain import BusinessEntity, ContactPoint, Prospect


def _utc_now_isoformat() -> str:
    """生成 Python 3.9 可用的 UTC ISO 时间。"""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ProspectScoreDimensions:
    """五个 0–100 的显式 B2B 评分维度及其证据引用。"""

    category_fit: int
    market_fit: int
    audience_overlap: int
    contact_quality: int
    partnership_probability: int
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "category_fit",
            "market_fit",
            "audience_overlap",
            "contact_quality",
            "partnership_probability",
        ):
            value = int(getattr(self, field_name))
            if not 0 <= value <= 100:
                raise ValueError(f"{field_name}_out_of_range")
            object.__setattr__(self, field_name, value)
        refs = tuple(dict.fromkeys(str(item).strip() for item in self.evidence_refs if str(item).strip()))
        object.__setattr__(self, "evidence_refs", refs)

    @classmethod
    def empty(cls) -> "ProspectScoreDimensions":
        """缺证据时返回全零输入，由 scorer 明确路由到 hold。"""

        return cls(0, 0, 0, 0, 0, ())


@dataclass(frozen=True)
class DirectorySearchResult:
    """目录查询结果；entities 是 BusinessEntity，状态说明是否发生现实调用。"""

    entities: tuple[BusinessEntity, ...]
    dry_run: bool
    executed: bool
    status: str


@dataclass(frozen=True)
class ContactExtractionResult:
    """联系方式提取端口结果；V1 仅定义合同，不提供真实实现。"""

    contacts: tuple[ContactPoint, ...]
    dry_run: bool
    executed: bool
    status: str

    def __post_init__(self) -> None:
        contacts = tuple(self.contacts)
        if any(not isinstance(contact, ContactPoint) for contact in contacts):
            raise ValueError("contact_point_required")
        object.__setattr__(self, "contacts", contacts)


@dataclass(frozen=True)
class EmailSendResult:
    """邮件 Provider 结果；Mock 永远不会产生 provider_message_id。"""

    prospect_id: str
    dry_run: bool
    executed: bool
    status: str
    provider_message_id: str | None


@dataclass(frozen=True)
class ProspectDiscoveryResult:
    """汇总一次目录发现、分类、可选联系人提取和评分结果。"""

    directory_result: DirectorySearchResult
    entities: tuple[BusinessEntity, ...]
    prospects: tuple[Prospect, ...]
    contact_results_by_entity: Dict[str, ContactExtractionResult]


class FeedbackOutcome(str, Enum):
    """回复后的最小结构化学习结果，不推断业务成功。"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    MORE_EVIDENCE_REQUIRED = "more_evidence_required"
    NO_RESPONSE_OBSERVED = "no_response_observed"


@dataclass(frozen=True)
class ReplyIntakeRecord:
    """只保存回复引用，不保存原始回复正文。"""

    prospect_id: str
    reply_reference: str
    received_at: str

    @classmethod
    def create(cls, *, prospect_id: str, reply_reference: str) -> "ReplyIntakeRecord":
        normalized_prospect_id = prospect_id.strip()
        if not normalized_prospect_id:
            raise ValueError("prospect_id_required")
        normalized = reply_reference.strip()
        if not normalized.startswith("reply_ref_"):
            raise ValueError("reply_reference_required")
        return cls(
            prospect_id=normalized_prospect_id,
            reply_reference=normalized,
            received_at=_utc_now_isoformat(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FeedbackRecord:
    """把回复结果变成带证据引用的学习信号，不直接修改评分规则。"""

    prospect_id: str
    outcome: FeedbackOutcome
    evidence_refs: tuple[str, ...]
    created_at: str

    @classmethod
    def create(
        cls,
        *,
        prospect_id: str,
        outcome: FeedbackOutcome,
        evidence_refs: tuple[str, ...],
    ) -> "FeedbackRecord":
        normalized_prospect_id = prospect_id.strip()
        if not normalized_prospect_id:
            raise ValueError("prospect_id_required")
        refs = tuple(dict.fromkeys(str(item).strip() for item in evidence_refs if str(item).strip()))
        if not refs:
            raise ValueError("feedback_evidence_required")
        return cls(
            prospect_id=normalized_prospect_id,
            outcome=FeedbackOutcome(outcome),
            evidence_refs=refs,
            created_at=_utc_now_isoformat(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
