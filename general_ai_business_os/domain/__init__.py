"""通用领域对象入口；只暴露跨 Agent 可复用的技术合同。"""

from general_ai_business_os.domain.entities import (
    AdapterResult,
    AdapterStatus,
    AuditEvent,
    OperationResult,
    PermissionDecision,
    StoredRecord,
)

__all__ = (
    "AdapterResult",
    "AdapterStatus",
    "AuditEvent",
    "OperationResult",
    "PermissionDecision",
    "StoredRecord",
)
