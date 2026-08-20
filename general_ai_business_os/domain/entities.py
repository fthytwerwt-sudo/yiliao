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

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, Mapping

from general_ai_business_os.domain.immutability import freeze_mapping, to_mutable_json


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


_ALLOWED_AUDIT_ACTIONS = frozenset(
    {
        "adapter.request",
        "config.import",
        "config.review",
        "storage.record",
        "system.initialize",
    }
)
_ALLOWED_AUDIT_OUTCOMES = frozenset({"blocked", "completed", "initialized", "mock", "rejected"})
_ALLOWED_AUDIT_DETAIL_CODES = {
    "adapter": frozenset({"content", "crm", "knowledge", "messaging", "search", "storage"}),
    "operation": frozenset(
        {"analyze", "create", "generate", "import", "initialize", "read", "retrieve", "review", "score", "update", "write"}
    ),
    "reason": frozenset(
        {"action_required", "external_actions_disabled", "mock_dry_run", "permission_denied", "validation_rejected"}
    ),
    "status": frozenset({"BLOCKED", "DISABLED", "IMPLEMENTED", "MOCK"}),
}
_RFC3339_TIMESTAMP_PATTERN = re.compile(
    r"^(?P<base>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?P<fraction>\.\d{1,6})?(?P<timezone>Z|[+-]\d{2}:\d{2})$"
)


def _require_audit_code(value: Any, *, field_name: str, allowed_values: frozenset[str]) -> str:
    """验证字段级闭集代码，避免无空格的敏感值伪装成任意系统字符串。"""

    if not isinstance(value, str) or value not in allowed_values:
        raise ValueError(f"audit_{field_name}_invalid")
    return value


def _validate_audit_details(details: Mapping[str, Any]) -> Dict[str, Any]:
    """验证最小审计详情；未知/嵌套/自由文本在构造 AuditEvent 前拒绝。"""

    if not isinstance(details, Mapping):
        raise ValueError("audit_details_invalid")
    safe_details: Dict[str, Any] = {}
    for key, value in details.items():
        if key == "count":
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("audit_details_count_invalid")
            safe_details[key] = value
            continue
        allowed_values = _ALLOWED_AUDIT_DETAIL_CODES.get(key)
        if allowed_values is None:
            raise ValueError("audit_details_field_not_allowed")
        safe_details[key] = _require_audit_code(
            value,
            field_name=f"details_{key}",
            allowed_values=allowed_values,
        )
    return safe_details


def _normalize_audit_recorded_at(value: Any) -> str:
    """
    验证并标准化审计时间。

    关键边界：
    时间字段同样会被返回、序列化和持久化；只依赖类型注解会让自由文本或容器绕过审计安全边界。
    因此只接受带时区的 ISO-8601 字符串，并固定导出为秒级 UTC 格式。
    """

    if not isinstance(value, str):
        raise ValueError("audit_recorded_at_invalid")
    match = _RFC3339_TIMESTAMP_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError("audit_recorded_at_invalid")
    fraction = match.group("fraction")
    # Python 3.9's fromisoformat only accepts 3 or 6 fractional digits. The public contract
    # accepts the full RFC3339 subset of 1-6 digits, so pad the verified fraction before parsing.
    normalized_fraction = f".{fraction[1:].ljust(6, '0')}" if fraction else ""
    timezone_value = match.group("timezone")
    parser_timestamp = f"{match.group('base')}{normalized_fraction}{'+00:00' if timezone_value == 'Z' else timezone_value}"
    try:
        parsed = datetime.fromisoformat(parser_timestamp)
    except ValueError as error:
        raise ValueError("audit_recorded_at_invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("audit_recorded_at_invalid")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class AuditEvent:
    """
    已经过安全字段清洗且传递性不可变的审计事件。

    关键边界：
    `frozen=True` 只能阻止属性重新赋值，不能阻止嵌套容器被原地改写。这里同时验证字段级闭集，
    并使用统一递归冻结合同，使公开构造、AuditLogger 返回和后续 Storage 都共享同一安全边界。
    """

    action: str
    outcome: str
    details: Mapping[str, Any]
    recorded_at: str

    def __post_init__(self) -> None:
        """在公开构造入口验证审计合同并深层冻结详情，避免绕过 Logger。"""

        object.__setattr__(
            self,
            "action",
            _require_audit_code(
                self.action,
                field_name="action",
                allowed_values=_ALLOWED_AUDIT_ACTIONS,
            ),
        )
        object.__setattr__(
            self,
            "outcome",
            _require_audit_code(
                self.outcome,
                field_name="outcome",
                allowed_values=_ALLOWED_AUDIT_OUTCOMES,
            ),
        )
        object.__setattr__(self, "details", freeze_mapping(_validate_audit_details(self.details)))
        object.__setattr__(self, "recorded_at", _normalize_audit_recorded_at(self.recorded_at))

    def to_dict(self) -> Dict[str, Any]:
        """导出新的普通字典供 JSON/Storage 使用，不暴露事件内部的可变引用。"""

        return {
            "action": self.action,
            "outcome": self.outcome,
            "details": to_mutable_json(self.details),
            "recorded_at": self.recorded_at,
        }


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
    payload: Mapping[str, Any]
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        """深层冻结 payload，防止输入/导出容器别名在创建后污染持久化记录。"""

        object.__setattr__(self, "payload", freeze_mapping(self.payload))

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
            payload=payload,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def to_dict(self) -> Dict[str, Any]:
        """将记录安全转换成 Storage Port 需要的结构化字典。"""

        return {
            "id": self.id,
            "kind": self.kind,
            "payload": to_mutable_json(self.payload),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "StoredRecord":
        """从 Storage Port 回读结果恢复领域对象，避免泄漏数据库行结构。"""

        return cls(
            id=str(payload["id"]),
            kind=str(payload["kind"]),
            payload=payload["payload"],
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
        )
