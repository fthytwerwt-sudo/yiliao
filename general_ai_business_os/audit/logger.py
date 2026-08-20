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
from typing import Any, Dict, Optional

from general_ai_business_os.domain.entities import AuditEvent, utc_now_isoformat


_SENSITIVE_KEYS = {"api_key", "authorization", "password", "secret", "token"}


def _sanitize(value: Any, key: Optional[str] = None) -> Any:
    """
    递归清洗审计值。

    关键逻辑：
    密钥往往嵌套在请求字典中；只过滤顶层字段会让审计日志变成新的泄漏路径，
    因此每一层 mapping 都按字段名重复判断。
    """

    if key is not None and key.lower() in _SENSITIVE_KEYS:
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(item_key): _sanitize(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    return value


class AuditLogger:
    """将安全审计事件 append-only 写入本地 JSONL 文件。"""

    def __init__(self, path: Path) -> None:
        self._path = path

    def record(self, *, action: str, outcome: str, details: Dict[str, Any]) -> AuditEvent:
        """清洗 details 后写入一行 JSON，返回同一份已清洗事件供调用者检查。"""

        event = AuditEvent(
            action=action,
            outcome=outcome,
            details=dict(_sanitize(details)),
            recorded_at=utc_now_isoformat(),
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return event
