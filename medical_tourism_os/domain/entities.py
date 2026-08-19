"""
用途：
定义系统基础领域对象、状态枚举与共享记录结构。

上游：
repository、permission、adapter、audit 与未来服务层把这里当作唯一领域事实模型。

下游：
SQLite port、审计日志、Mock adapter 等基础设施通过这些 dataclass 交换数据。

边界：
这里只表达结构和状态，不包含 SQL、HTTP、外部平台、真实国家或价格等业务事实。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


def _utc_now_isoformat() -> str:
    """返回统一的 UTC ISO 时间字符串，避免各模块自行发明时间格式。"""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class FactClassification(str, Enum):
    """
    作用：
    标记事实当前所处的治理级别。

    输入：
    枚举值由领域工厂或人工复核流程设置。

    输出：
    一个稳定、可序列化的字符串枚举。

    关键边界：
    Phase 1 只依赖候选与已确认两级，不允许跳过人工复核直接提升。
    """

    FACT_CANDIDATE = "FACT_CANDIDATE"
    CANONICAL_FACT = "CANONICAL_FACT"


class ReviewStatus(str, Enum):
    """
    作用：
    表示人工复核队列中的当前状态。

    输入：
    由创建候选、人工批准或拒绝动作更新。

    输出：
    稳定的字符串枚举，便于 SQLite 与 JSON 存储。

    关键边界：
    新候选默认必须进入 `PENDING`，避免把未审事实误当已确认事实。
    """

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class FactRecord:
    """
    作用：
    承载一条待审或已确认的结构化事实记录。

    输入：
    事实文本、来源、来源日期、作用域与 provenance 等基础字段。

    输出：
    可被仓库保存、读取与序列化的领域对象。

    关键边界：
    该对象只保存结构化治理字段，不携带平台专属字段，避免把战略细节写死到核心模型。
    """

    id: str
    claim: str
    source: str
    source_date: str
    scope: str
    classification: FactClassification
    confidence: str
    freshness: str
    conflict_status: str
    review_status: ReviewStatus
    reviewed_by: Optional[str]
    created_at: str
    updated_at: str
    provenance: str

    @classmethod
    def new_candidate(
        cls,
        claim: str,
        source: str,
        source_date: str,
        scope: str,
        provenance: str,
    ) -> "FactRecord":
        """
        作用：
        为导入或研究输入创建一条待人工复核的事实候选。

        输入：
        `claim`、`source`、`source_date`、`scope`、`provenance`。

        输出：
        `FactRecord`，固定为 `FACT_CANDIDATE + PENDING`。

        关键边界：
        这里强制写死候选态，是为了阻止未来调用者绕过人工复核直接生成 canonical fact。
        """

        timestamp = _utc_now_isoformat()
        return cls(
            id=f"fact_{uuid4().hex}",
            claim=claim,
            source=source,
            source_date=source_date,
            scope=scope,
            classification=FactClassification.FACT_CANDIDATE,
            confidence="unreviewed",
            freshness="unknown",
            conflict_status="unchecked",
            review_status=ReviewStatus.PENDING,
            reviewed_by=None,
            created_at=timestamp,
            updated_at=timestamp,
            provenance=provenance,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        作用：
        把领域对象转成可持久化、可 JSON 编码的字典。

        输入：
        无。

        输出：
        `dict[str, Any]`，枚举被转换为字符串。

        关键边界：
        明确输出的字段集合有助于避免未来意外混入平台专属列。
        """

        payload = asdict(self)
        payload["classification"] = self.classification.value
        payload["review_status"] = self.review_status.value
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "FactRecord":
        """
        作用：
        从存储层字典恢复 `FactRecord`。

        输入：
        SQLite port 或 JSON 载入后的字段映射。

        输出：
        领域对象 `FactRecord`。

        关键边界：
        所有状态字段都回转为枚举，避免上层逻辑混用自由字符串。
        """

        return cls(
            id=str(payload["id"]),
            claim=str(payload["claim"]),
            source=str(payload["source"]),
            source_date=str(payload["source_date"]),
            scope=str(payload["scope"]),
            classification=FactClassification(str(payload["classification"])),
            confidence=str(payload["confidence"]),
            freshness=str(payload["freshness"]),
            conflict_status=str(payload["conflict_status"]),
            review_status=ReviewStatus(str(payload["review_status"])),
            reviewed_by=payload.get("reviewed_by"),
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
            provenance=str(payload["provenance"]),
        )


@dataclass(frozen=True)
class RiskResult:
    """表示风险检查的最小结果，供后续风险路由扩展。"""

    blocked: bool
    reason: str


@dataclass(frozen=True)
class PermissionDecision:
    """表示权限策略对某个动作的允许或拒绝结果。"""

    allowed: bool
    reason: str


@dataclass(frozen=True)
class AuditEvent:
    """表示一条已脱敏的审计事件。"""

    action: str
    outcome: str
    details: Dict[str, Any]
    recorded_at: str


@dataclass(frozen=True)
class AdapterResult:
    """表示适配器执行结果；dry-run 和 executed 必须可同时表达。"""

    dry_run: bool
    executed: bool
    reason: str
    payload: Dict[str, Any]
