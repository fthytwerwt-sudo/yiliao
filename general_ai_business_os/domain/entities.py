"""
用途：
定义 General AI Business Operating System 的通用结果、权限、审计和存储领域对象。

上游：
Adapter、权限策略、审计、Storage 与未来各 Agent 使用这些对象交换结构化状态。

下游：
CLI、Local API 和 workflow 将对象转换为可审查的本地输出。

边界：
对象只表达系统能力和安全状态；不携带任何业务战略、个人资料或平台专属字段。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict


def utc_now_isoformat() -> str:
    """生成无微秒 UTC 时间，确保审计和 SQLite 记录的时间格式可稳定比较。"""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class AdapterStatus(str, Enum):
    """外部能力的真实可执行状态，不把 Mock 或代码存在误报为真实连接。"""

    IMPLEMENTED = "IMPLEMENTED"
    MOCK = "MOCK"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"


@dataclass(frozen=True)
class PermissionDecision:
    """权限层针对单项动作给出的显式允许或拒绝结果。"""

    allowed: bool
    reason: str


@dataclass(frozen=True)
class AdapterResult:
    """
    作用：
    统一描述 Adapter 是否实际执行、以何种状态结束及其安全原因。

    关键边界：
    `executed=False` 时不得由调用者解释为已经发生外部动作；Mock 的成功只代表合同已走通。
    """

    adapter: str
    operation: str
    status: AdapterStatus
    executed: bool
    reason: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class OperationResult:
    """供本地服务返回的通用操作结果，避免接口层拼装不一致的自由文本。"""

    status: str
    reason: str
    data: Dict[str, Any]


@dataclass(frozen=True)
class AuditEvent:
    """已经过安全字段清洗的审计事件；原始敏感输入不能进入该对象。"""

    action: str
    outcome: str
    details: Dict[str, Any]
    recorded_at: str

    def to_dict(self) -> Dict[str, Any]:
        """将 dataclass 转为 JSON 可写入的字典，保持审计字段稳定。"""

        return asdict(self)


@dataclass(frozen=True)
class StoredRecord:
    """
    作用：
    提供基础阶段的通用持久化记录。

    输入：
    调用者显式提供 record_id、kind 和已校验 payload。

    输出：
    可由任意 Storage Port 保存和回读的不可变对象。

    关键边界：
    `kind` 是能力分类，不是具体业务类别；业务特有的解释必须留在经审核的配置或领域模块。
    """

    id: str
    kind: str
    payload: Dict[str, Any]
    created_at: str
    updated_at: str

    @classmethod
    def new(cls, *, record_id: str, kind: str, payload: Dict[str, Any]) -> "StoredRecord":
        """创建带统一时间戳的新通用记录，拒绝由基础设施私自生成业务标识。"""

        if not record_id.strip():
            raise ValueError("record_id_required")
        if not kind.strip():
            raise ValueError("record_kind_required")
        timestamp = utc_now_isoformat()
        return cls(
            id=record_id,
            kind=kind,
            payload=dict(payload),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def to_dict(self) -> Dict[str, Any]:
        """将记录安全转换成 Storage Port 需要的结构化字典。"""

        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "StoredRecord":
        """从 Storage Port 回读结果恢复领域对象，避免泄漏数据库行结构。"""

        return cls(
            id=str(payload["id"]),
            kind=str(payload["kind"]),
            payload=dict(payload["payload"]),
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
        )
