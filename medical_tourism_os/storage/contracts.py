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

from typing import Any, Dict, List, Optional, Protocol

from medical_tourism_os.domain.entities import FactRecord, LifecycleEvent


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

    def list_facts(self) -> List[Dict[str, Any]]:
        """列出当前事实表中的全部记录，供去重、复核队列和导出使用。"""

    def save_lifecycle_event(self, event: LifecycleEvent) -> None:
        """保存一条生命周期事件，形成 Raw/Staging/Adjudicated/Canonical 的真实轨迹。"""

    def list_lifecycle_events(self, record_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """按可选 record_id 回读生命周期事件。"""

    def next_lifecycle_sequence(self, record_id: str) -> int:
        """为指定事实分配下一条单调递增的生命周期 sequence。"""
