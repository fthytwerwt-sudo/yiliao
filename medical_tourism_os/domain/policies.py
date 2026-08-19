"""
用途：
定义不依赖基础设施的纯领域策略，例如敏感字段识别与脱敏。

上游：
audit.logger、权限层与未来导入治理服务调用这里的纯规则。

下游：
返回纯 Python 值，不直接写文件、不访问数据库、不发起网络请求。

边界：
这里只提供规则函数，不决定业务战略，也不保存任何原始敏感数据。
"""

from __future__ import annotations

import re
from typing import Any, Iterable


DEFAULT_SENSITIVE_MARKERS = (
    "patient",
    "health",
    "token",
    "secret",
    "payment",
    "phi",
    "clinical",
    "medical",
)

SAFE_AUDIT_DETAIL_KEYS = (
    "record_id",
    "stage",
    "reason",
    "count",
)

_SAFE_AUDIT_STRING = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


def is_sensitive_key(key: str, markers: Iterable[str] = DEFAULT_SENSITIVE_MARKERS) -> bool:
    """
    作用：
    判断字段名是否落入需要脱敏的敏感范围。

    输入：
    `key` 为待判断字段名；`markers` 为敏感关键词集合。

    输出：
    `True` 表示该字段值不得原文持久化。

    关键边界：
    这里采用 deny-first 的关键字匹配，是因为 Phase 1 更看重“不泄露”而非“尽量少误杀”。
    """

    normalized_key = key.strip().lower()
    return any(marker in normalized_key for marker in markers)


def redact_sensitive_payload(
    payload: Any,
    markers: Iterable[str] = DEFAULT_SENSITIVE_MARKERS,
) -> Any:
    """
    作用：
    递归脱敏审计或导入载荷中的敏感字段值。

    输入：
    `payload` 可以是字典、列表或标量；`markers` 为敏感关键字。

    输出：
    与原结构等形的安全副本；敏感字段值被替换为 `[REDACTED]`。

    关键边界：
    只返回新对象，不在原地修改输入，避免上游代码误以为自己还持有未脱敏版本。
    """

    if isinstance(payload, dict):
        return sanitize_audit_details(payload, markers)
    if isinstance(payload, (list, tuple)):
        return "[REDACTED]"
    return "[REDACTED]"


def sanitize_audit_details(
    details: Any,
    markers: Iterable[str] = DEFAULT_SENSITIVE_MARKERS,
) -> Any:
    """
    作用：
    只保留精确 allowlist 中的安全审计元数据，其余字段一律脱敏。

    输入：
    `details` 为审计详情对象；`markers` 为敏感关键词集合。

    输出：
    与原字典同 key 结构的安全副本；仅 allowlist 安全元数据保留原值。

    关键边界：
    审计不是原始数据备份。任何自由文本、嵌套对象、列表或未列入 allowlist 的字段都不能原文落盘。
    """

    if not isinstance(details, dict):
        return "[REDACTED]"

    sanitized = {}
    for key, value in details.items():
        normalized_key = str(key).strip().lower()
        if is_sensitive_key(normalized_key, markers):
            sanitized[key] = "[REDACTED]"
            continue
        if normalized_key not in SAFE_AUDIT_DETAIL_KEYS:
            sanitized[key] = "[REDACTED]"
            continue
        sanitized[key] = _sanitize_allowed_audit_value(normalized_key, value)
    return sanitized


def _sanitize_allowed_audit_value(key: str, value: Any) -> Any:
    """
    作用：
    校验 allowlist 审计字段的值是否仍属于安全元数据。

    输入：
    `key` 为 allowlist 字段名；`value` 为其候选值。

    输出：
    安全值本身或 `[REDACTED]`。

    关键边界：
    即使字段名安全，也不能接受任意自由文本；否则调用方可借 allowlist 把敏感内容伪装成 reason 或 stage。
    """

    if key == "count":
        if isinstance(value, bool):
            return "[REDACTED]"
        if isinstance(value, int):
            return value
        return "[REDACTED]"
    if isinstance(value, str) and _SAFE_AUDIT_STRING.fullmatch(value):
        return value
    return "[REDACTED]"
