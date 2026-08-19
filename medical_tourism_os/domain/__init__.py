"""
用途：
统一导出 Phase 1 的领域对象与规则。

上游：
repositories、permissions、audit 与测试从这里读取稳定领域接口。

下游：
entities.py 与 policies.py 提供具体对象和纯领域规则。

边界：
领域层保持纯 Python，不依赖 SQLite、HTTP、网络或平台 SDK。
"""

from medical_tourism_os.domain.entities import (
    AdapterResult,
    AnonymousLead,
    AuditEvent,
    DemandCluster,
    DemandSignal,
    FactClassification,
    FactRecord,
    LeadScoreCard,
    LifecycleEvent,
    LifecycleStage,
    PermissionDecision,
    ProductCandidate,
    ProductMatch,
    ReviewStatus,
    RiskRouteDecision,
    RiskResult,
    WorkflowResult,
)

__all__ = [
    "AdapterResult",
    "AnonymousLead",
    "AuditEvent",
    "DemandCluster",
    "DemandSignal",
    "FactClassification",
    "FactRecord",
    "LeadScoreCard",
    "LifecycleEvent",
    "LifecycleStage",
    "PermissionDecision",
    "ProductCandidate",
    "ProductMatch",
    "ReviewStatus",
    "RiskRouteDecision",
    "RiskResult",
    "WorkflowResult",
]
