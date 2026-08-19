"""
用途：
提供默认关闭的 Mock adapter，用于 dry-run 验证与接口占位。

上游：
测试和未来发布/同步流程可先调用这个 adapter 验证权限链路。

下游：
返回统一的 `AdapterResult`，不产生任何现实外部副作用。

边界：
即使 payload 看起来像真实数据，这里也不连接网络、不发消息、不发布内容。
"""

from __future__ import annotations

from typing import Any, Dict

from medical_tourism_os.adapters.base import BaseAdapter
from medical_tourism_os.domain.entities import AdapterResult


class MockAdapter(BaseAdapter):
    """
    作用：
    在 adapter 默认关闭的条件下提供可测试的 dry-run 行为。

    输入：
    `enabled` 决定当前调用是纯 dry-run 还是本地 mock 执行。

    输出：
    `AdapterResult`，明确说明是否执行以及原因。

    关键边界：
    关闭状态必须显式返回 `adapter_disabled`，避免调用方误判为成功发布。
    """

    def publish(self, payload: Dict[str, Any]) -> AdapterResult:
        """
        作用：
        处理一次 mock publish 调用。

        输入：
        任意结构的发布载荷。

        输出：
        `AdapterResult`。

        关键边界：
        关闭时返回 dry-run；启用时也只做本地 mock 完成态，不产生真实外部动作。
        """

        if not self.enabled:
            return AdapterResult(
                dry_run=True,
                executed=False,
                reason="adapter_disabled",
                payload={"requested_payload": payload},
            )
        return AdapterResult(
            dry_run=False,
            executed=True,
            reason="mock_executed",
            payload={
                "requested_payload": payload,
                "mock_reference": "mock-publication-001",
            },
        )
