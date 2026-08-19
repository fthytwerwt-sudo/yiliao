"""
用途：
定义存储层 port 合同，隔离领域与 SQLite 细节。

上游：
repositories.core 通过这里约束存储实现的最小接口。

下游：
sqlite_store.py 与未来其他后端实现遵守同一协议。

边界：
这里只声明协议，不实现 SQL、不持有连接、不引入外部依赖。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol

from medical_tourism_os.domain.entities import FactRecord


class FactStoragePort(Protocol):
    """
    作用：
    描述事实记录存储后端必须提供的最小能力。

    输入：
    `FactRecord` 与事实 ID。

    输出：
    保存成功时无返回值；读取时返回字典或 `None`。

    关键边界：
    协议只约束事实相关操作，让未来替换后端时不必改动领域仓库接口。
    """

    def migrate(self) -> None:
        """执行当前已知 migration。"""

    def save_fact(self, record: FactRecord) -> None:
        """保存或更新一条事实记录。"""

    def get_fact(self, record_id: str) -> Optional[Dict[str, Any]]:
        """按 ID 读取一条事实记录。"""
