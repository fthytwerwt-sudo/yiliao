"""
用途：
把系统动作写为脱敏 JSONL 审计事件。

上游：
权限、Adapter、导入与未来 Agent 在发生状态变化时调用审计器。

下游：
本地复核和测试读取该日志确认系统为何阻断或降级。

边界：
审计只允许安全结构字段；密钥、Token、密码和授权头的原文必须在落盘前删除。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from general_ai_business_os.domain.entities import AuditEvent, utc_now_isoformat


_ALLOWED_DETAIL_FIELDS = {
    "adapter",
    "count",
    "operation",
    "reason",
    "status",
}
_ALLOWED_ACTIONS = frozenset(
    {
        "adapter.request",
        "config.import",
        "config.review",
        "storage.record",
        "system.initialize",
    }
)
_ALLOWED_OUTCOMES = frozenset({"blocked", "completed", "initialized", "mock", "rejected"})
_ALLOWED_DETAIL_CODES = {
    "adapter": frozenset({"content", "crm", "knowledge", "messaging", "search", "storage"}),
    "operation": frozenset(
        {"analyze", "create", "generate", "import", "initialize", "read", "retrieve", "review", "score", "update", "write"}
    ),
    "reason": frozenset(
        {"action_required", "external_actions_disabled", "mock_dry_run", "permission_denied", "validation_rejected"}
    ),
    "status": frozenset({"BLOCKED", "DISABLED", "IMPLEMENTED", "MOCK"}),
}


def _require_allowed_code(value: Any, *, field_name: str, allowed_values: frozenset[str]) -> str:
    """
    验证允许写入审计日志的字段级 closed code（闭集代码）。

    关键逻辑：
    仅限制字符形状无法证明语义安全：没有空格的患者标识或 Token 仍然可能符合正则。
    因此每个字段只接受维护者明确定义的有限系统值，未知值一律在落盘前拒绝。
    """

    if not isinstance(value, str) or value not in allowed_values:
        raise ValueError(f"audit_{field_name}_invalid")
    return value


def _validate_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """
    构造允许落盘的最小审计详情。

    关键逻辑：
    这里使用 allowlist（允许字段清单）而不是敏感字段 denylist。未知字段、嵌套对象和自由文本
    都会被拒绝，因为无法安全证明它们不包含患者、联系人或凭据数据。
    """

    safe_details: Dict[str, Any] = {}
    for key, value in details.items():
        if key not in _ALLOWED_DETAIL_FIELDS:
            raise ValueError("audit_details_field_not_allowed")
        if key == "count":
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("audit_details_count_invalid")
            safe_details[key] = value
            continue
        allowed_values = _ALLOWED_DETAIL_CODES.get(key)
        if allowed_values is None:
            raise ValueError("audit_details_field_not_allowed")
        safe_details[key] = _require_allowed_code(
            value,
            field_name=f"details_{key}",
            allowed_values=allowed_values,
        )
    return safe_details


class AuditLogger:
    """将安全审计事件 append-only 写入本地 JSONL 文件。"""

    def __init__(self, path: Path) -> None:
        self._path = path

    def record(self, *, action: str, outcome: str, details: Dict[str, Any]) -> AuditEvent:
        """验证 allowlist 后写入一行 JSON；任一不安全字段会在落盘前直接拒绝。"""

        event = AuditEvent(
            action=_require_allowed_code(action, field_name="action", allowed_values=_ALLOWED_ACTIONS),
            outcome=_require_allowed_code(outcome, field_name="outcome", allowed_values=_ALLOWED_OUTCOMES),
            details=_validate_details(details),
            recorded_at=utc_now_isoformat(),
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return event
