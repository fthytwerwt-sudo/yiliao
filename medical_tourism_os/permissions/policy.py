"""
用途：
定义外部动作权限策略，确保系统默认 deny-by-default。

上游：
CLI、服务层或适配器协调器在尝试 publish / sync 等动作前调用这里。

下游：
返回纯决策对象，不直接操作 adapter 或数据库。

边界：
这里只做权限裁决，不决定内容业务逻辑，不替代风险模块。
"""

from __future__ import annotations

from medical_tourism_os.config import SystemConfig
from medical_tourism_os.domain.entities import PermissionDecision


class PermissionPolicy:
    """
    作用：
    根据本地配置和调用上下文判断外部动作是否允许。

    输入：
    `SystemConfig` 以及动作名、adapter 状态和风险阻断标记。

    输出：
    `PermissionDecision`，说明允许与否及原因。

    关键边界：
    权限逻辑必须 fail-closed；即使调用者漏传某些上下文，也不能默认放行。
    """

    def __init__(self, config: SystemConfig) -> None:
        self.config = config

    def check_external_action(
        self,
        action: str,
        *,
        adapter_enabled: bool = False,
        risk_blocked: bool = False,
    ) -> PermissionDecision:
        """
        作用：
        对单个外部动作做权限判定。

        输入：
        `action` 为逻辑动作名；`adapter_enabled` 表示具体适配器是否启用；
        `risk_blocked` 表示上游风险路由是否已经阻断。

        输出：
        `PermissionDecision`。

        关键边界：
        先检查全局外部执行开关，再检查 adapter 与风险状态；
        这样即使未来某个调用者误把 adapter 打开，也仍受全局治理约束。
        """

        if not action.strip():
            return PermissionDecision(allowed=False, reason="action_required")
        if not self.config.external_execution_allowed:
            return PermissionDecision(allowed=False, reason="external_execution_disabled")
        if risk_blocked:
            return PermissionDecision(allowed=False, reason="risk_blocked")
        if not self.config.adapters_enabled:
            return PermissionDecision(allowed=False, reason="adapters_disabled")
        if not adapter_enabled:
            return PermissionDecision(allowed=False, reason="adapter_disabled")
        return PermissionDecision(allowed=True, reason="allowed")
