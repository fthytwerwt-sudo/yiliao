"""
用途：
定义系统基础配置与默认安全开关。

上游：
CLI、权限策略、适配器和服务层读取这里的默认行为。

下游：
permissions.policy、adapters.mock 与未来应用服务据此判断是否允许外部动作。

边界：
这里只描述本地配置，不加载真实凭据，不决定任何市场、医院、平台或价格策略。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class SystemConfig:
    """
    作用：
    承载 Phase 1 所需的最小系统配置。

    输入：
    构造参数全部为显式配置值；`default()` 生成安全默认值。

    输出：
    一个不可变配置对象，供权限、适配器和存储层读取。

    关键边界：
    默认必须 fail-closed，不能因为缺配置而开启任何现实外部执行。
    """

    storage_backend: str = "sqlite"
    storage_path: str = "medical-tourism-os.sqlite3"
    external_execution_allowed: bool = False
    adapters_enabled: bool = False
    audit_redaction_markers: Tuple[str, ...] = field(
        default_factory=lambda: (
            "patient",
            "health",
            "token",
            "secret",
            "payment",
            "phi",
            "clinical",
            "medical",
        )
    )

    @classmethod
    def default(cls) -> "SystemConfig":
        """
        作用：
        返回本地离线模式的安全默认配置。

        输入：
        无。

        输出：
        `SystemConfig`，其中所有外部执行能力保持关闭。

        关键边界：
        该默认值是权限系统的第一道闸门；未来只有显式本地变更才能放开。
        """

        return cls()
