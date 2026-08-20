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
import re
from typing import Any, Dict

from general_ai_business_os.domain.entities import AuditEvent, utc_now_isoformat


_ALLOWED_DETAIL_FIELDS = {
    "adapter",
    "config_version",
    "count",
    "operation",
    "reason",
    "record_id",
    "request_id",
    "safe_code",
    "status",
}
_SAFE_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


def _require_safe_code(value: Any, *, field_name: str) -> str:
    """
    验证允许写入审计日志的代码型字符串。

    关键逻辑：
    审计 action、outcome 和 details 若可承载任意自然语言，仍可成为个人资料、健康信息或
    Token 的旁路。因此基础层只接收有限字符集的系统代码，而不是尝试猜测所有敏感内容。
    """

    if not isinstance(value, str) or not _SAFE_CODE_PATTERN.fullmatch(value):
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
        safe_details[key] = _require_safe_code(value, field_name=f"details_{key}")
    return safe_details


class AuditLogger:
    """将安全审计事件 append-only 写入本地 JSONL 文件。"""

    def __init__(self, path: Path) -> None:
        self._path = path

    def record(self, *, action: str, outcome: str, details: Dict[str, Any]) -> AuditEvent:
        """验证 allowlist 后写入一行 JSON；任一不安全字段会在落盘前直接拒绝。"""

        event = AuditEvent(
            action=_require_safe_code(action, field_name="action"),
            outcome=_require_safe_code(outcome, field_name="outcome"),
            details=_validate_details(details),
            recorded_at=utc_now_isoformat(),
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return event
