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


class AuditLogger:
    """将安全审计事件 append-only 写入本地 JSONL 文件。"""

    def __init__(self, path: Path) -> None:
        self._path = path

    def record(self, *, action: str, outcome: str, details: Dict[str, Any]) -> AuditEvent:
        """验证 allowlist 后写入一行 JSON；任一不安全字段会在落盘前直接拒绝。"""

        event = AuditEvent(action=action, outcome=outcome, details=details, recorded_at=utc_now_isoformat())
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return event
