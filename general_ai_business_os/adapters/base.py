"""
用途：
定义所有外部能力适配器共享的最小执行合同。

上游：
Media、Lead、Sales、CRM 等 Agent 通过该 Port 请求可能的外部能力。

下游：
具体 Mock 或未来 Provider Adapter 以统一 `AdapterResult` 回报状态。

边界：
接口不持有第三方 SDK，不调用网络；真实执行许可必须由上游权限策略显式传入。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from general_ai_business_os.domain.entities import AdapterResult, PermissionDecision


class BaseAdapter(ABC):
    """Provider 无关的 Adapter 抽象；子类必须明确是否真的执行了请求。"""

    @property
    @abstractmethod
    def capability(self) -> str:
        """返回此 Adapter 的通用能力代码，例如 `content.image`。"""

    @abstractmethod
    def execute(
        self,
        *,
        operation: str,
        payload: Dict[str, Any],
        permission: PermissionDecision,
    ) -> AdapterResult:
        """执行或阻断请求；不允许用异常掩盖 Adapter 状态。"""
