"""
用途：
记录最小审计事件，并在持久化前完成敏感字段脱敏。

上游：
导入、权限、风险与未来服务层把这里作为统一审计出口。

下游：
本地 JSONL 文件；每一行代表一条已脱敏的审计事件。

边界：
这里只负责最小安全日志，不保存患者、健康、token、payment 等原始敏感内容。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from medical_tourism_os.config import SystemConfig
from medical_tourism_os.domain.entities import AuditEvent, _utc_now_isoformat
from medical_tourism_os.domain.policies import sanitize_audit_details


class AuditLogger:
    """
    作用：
    追加写入 JSONL 审计事件。

    输入：
    `path` 为审计文件路径；可选 `config` 提供脱敏关键词集合。

    输出：
    `record()` 返回一条已脱敏的 `AuditEvent`。

    关键边界：
    先脱敏再落盘，避免“为了审计而泄露敏感数据”的反向事故。
    """

    def __init__(self, path: Path, config: Optional[SystemConfig] = None) -> None:
        self.path = Path(path)
        self.config = config or SystemConfig.default()

    def record(self, action: str, outcome: str, details: Dict[str, Any]) -> AuditEvent:
        """
        作用：
        生成并持久化一条审计事件。

        输入：
        `action`、`outcome` 与任意字典形态的 `details`。

        输出：
        `AuditEvent`；其中 `details` 已经过脱敏。

        关键边界：
        这里把敏感字段统一替换为 `[REDACTED]`，因为审计只需要知道“发生了什么”，不需要持有原文秘密。
        """

        safe_details = sanitize_audit_details(
            details, self.config.audit_redaction_markers
        )
        event = AuditEvent(
            action=action,
            outcome=outcome,
            details=safe_details,
            recorded_at=_utc_now_isoformat(),
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "action": event.action,
                        "outcome": event.outcome,
                        "details": event.details,
                        "recorded_at": event.recorded_at,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            handle.write("\n")
        return event
