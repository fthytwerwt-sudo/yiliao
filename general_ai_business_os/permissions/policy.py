"""
用途：
在所有 Adapter 前统一判断一个动作是否得到执行许可。

上游：
Agent 和 workflow 在请求本地或外部能力前调用本策略。

下游：
Adapter 只接收已产生的 `PermissionDecision`，并据此报告真实状态。

边界：
策略不决定业务是否合理，也不保存业务配置；它只落实默认关闭的执行权限。
"""

from __future__ import annotations

from general_ai_business_os.config import SystemConfig
from general_ai_business_os.domain.entities import PermissionDecision


class PermissionPolicy:
    """
    作用：
    对潜在外部动作应用统一的 default-deny（默认拒绝）规则。

    关键边界：
    调用者传入的 payload、Adapter 状态或业务配置都不能绕过 `external_actions_allowed`。
    """

    def __init__(self, config: SystemConfig) -> None:
        self._config = config

    def authorize(self, action: str) -> PermissionDecision:
        """返回动作许可；空动作也拒绝，防止未知调用借默认路径逃逸。"""

        if not action.strip():
            return PermissionDecision(allowed=False, reason="action_required")
        if not self._config.external_actions_allowed:
            return PermissionDecision(allowed=False, reason="external_actions_disabled")
        return PermissionDecision(allowed=True, reason="explicitly_enabled")
