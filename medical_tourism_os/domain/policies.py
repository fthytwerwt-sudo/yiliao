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
        redacted = {}
        for key, value in payload.items():
            if is_sensitive_key(str(key), markers):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive_payload(value, markers)
        return redacted
    if isinstance(payload, list):
        return [redact_sensitive_payload(item, markers) for item in payload]
    if isinstance(payload, tuple):
        return tuple(redact_sensitive_payload(item, markers) for item in payload)
    return payload
