"""
用途：
提供确定性的本地 Mock Adapter，用于验证各 Agent 的 Provider 无关调用合同。

上游：
测试和本地 dry-run workflow 注入该 Adapter。

下游：
调用者获得包含 `MOCK`/`BLOCKED` 状态的 `AdapterResult`。

边界：
Mock 永远不连接第三方；即使权限打开，也只返回 dry-run 结果。
"""

from __future__ import annotations

from typing import Any, Dict

from general_ai_business_os.adapters.base import BaseAdapter
from general_ai_business_os.domain.entities import AdapterResult, AdapterStatus, PermissionDecision


class MockAdapter(BaseAdapter):
    """可重复的 Mock，明确区分权限阻断与允许后的本地 dry-run。"""

    def __init__(self, *, capability: str) -> None:
        self._capability = capability

    @property
    def capability(self) -> str:
        """返回注入时声明的通用能力，不推断任何具体平台。"""

        return self._capability

    def execute(
        self,
        *,
        operation: str,
        payload: Dict[str, Any],
        permission: PermissionDecision,
    ) -> AdapterResult:
        """权限拒绝时阻断；获准时仍只返回 Mock dry-run，绝不制造外部副作用。"""

        if not permission.allowed:
            return AdapterResult(
                adapter=self.capability,
                operation=operation,
                status=AdapterStatus.BLOCKED,
                executed=False,
                reason=permission.reason,
                payload={},
            )
        return AdapterResult(
            adapter=self.capability,
            operation=operation,
            status=AdapterStatus.MOCK,
            executed=False,
            reason="mock_dry_run",
            payload=dict(payload),
        )
