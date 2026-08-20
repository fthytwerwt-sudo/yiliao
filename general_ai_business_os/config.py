"""
用途：
集中定义通用运营系统的本地运行配置。

上游：
CLI、本地 API 和服务工厂读取这里的安全默认值。

下游：
权限策略、SQLite Storage 与 Adapter 依据该配置决定是否允许执行。

边界：
该文件只保存技术运行参数；不保存任何市场、客户、产品、价格或平台业务事实。
"""

from __future__ import annotations

from dataclasses import dataclass
import tempfile
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class SystemConfig:
    """
    作用：
    表达系统运行所需的最小技术配置。

    输入：
    可选的本地状态目录、API host/port 与外部动作总开关。

    输出：
    供基础设施安全共享的不可变配置对象。

    关键边界：
    `external_actions_allowed` 默认且推荐为 false。即使未来某个 Adapter 已实现，
    也不能仅靠 Adapter 自身配置绕过这里的默认拒绝。
    """

    state_root: Optional[Path] = None
    api_host: str = "127.0.0.1"
    api_port: int = 0
    external_actions_allowed: bool = False

    def __post_init__(self) -> None:
        """拒绝 truthy 非布尔开关，防止配置反序列化把字符串误解释为外部执行授权。"""

        if not isinstance(self.external_actions_allowed, bool):
            raise ValueError("external_actions_allowed_must_be_bool")

    def resolved_state_root(self) -> Path:
        """返回明确的本地状态目录，避免接口层各自使用不一致的临时位置。"""

        if self.state_root is not None:
            return self.state_root
        return Path(tempfile.gettempdir()) / "general-ai-business-os-state"

    def sqlite_path(self) -> Path:
        """返回开发期 SQLite 文件路径；领域层不会依赖该具体数据库。"""

        return self.resolved_state_root() / "general-ai-business-os.sqlite3"
