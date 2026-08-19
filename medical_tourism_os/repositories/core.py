"""
用途：
封装领域仓库，隔离服务层与具体存储实现。

上游：
未来服务层和测试通过仓库接口处理事实记录。

下游：
storage.contracts 中定义的 port 与具体 SQLite 实现。

边界：
仓库负责对象重建与接口稳定，不直接处理权限、风险或外部动作。
"""

from __future__ import annotations

from typing import List, Optional

from medical_tourism_os.domain.entities import FactRecord, LifecycleEvent
from medical_tourism_os.storage.contracts import FactStoragePort


class FactRepository:
    """
    作用：
    提供 `FactRecord` 的最小保存与读取接口。

    输入：
    一个满足 `FactStoragePort` 的存储实现。

    输出：
    可供应用层复用的仓库对象。

    关键边界：
    应用层不应感知 SQL 或 sqlite3 row；一旦未来替换后端，只要 port 不变即可保持上层稳定。
    """

    def __init__(self, store: FactStoragePort) -> None:
        self.store = store

    def save(self, record: FactRecord) -> None:
        """
        作用：
        保存一条事实记录。

        输入：
        `FactRecord`。

        输出：
        无。

        关键边界：
        仓库不在这里做状态晋升校验；Phase 1 只保证持久化合同成立。
        """

        self.store.save_fact(record)

    def get(self, record_id: str) -> Optional[FactRecord]:
        """
        作用：
        读取并重建一条事实记录。

        输入：
        事实 ID。

        输出：
        找到时返回 `FactRecord`，否则返回 `None`。

        关键边界：
        统一在这里完成反序列化，避免上层在多处重复枚举转换逻辑。
        """

        payload = self.store.get_fact(record_id)
        if payload is None:
            return None
        return FactRecord.from_dict(payload)

    def list(self) -> List[FactRecord]:
        """
        作用：
        列出当前事实库中的全部记录。

        输入：
        无。

        输出：
        `FactRecord` 列表。

        关键边界：
        复核队列、去重和导出都需要稳定回读；统一在仓库完成对象重建。
        """

        return [FactRecord.from_dict(payload) for payload in self.store.list_facts()]

    def list_pending_review(self) -> List[FactRecord]:
        """
        作用：
        提供最小的事实复核队列。

        输入：
        无。

        输出：
        所有仍处于 `PENDING` 的事实候选列表。

        关键边界：
        这里不做业务裁决，只暴露人工必须处理的待办集合。
        """

        return [
            record
            for record in self.list()
            if record.review_status.value == "PENDING"
        ]

    def save_lifecycle_event(self, event: LifecycleEvent) -> None:
        """
        作用：
        保存事实生命周期事件。

        输入：
        `LifecycleEvent`。

        输出：
        无。

        关键边界：
        服务层通过仓库记录治理轨迹，而不是直接接触 SQL 表结构。
        """

        self.store.save_lifecycle_event(event)

    def list_lifecycle_events(self, record_id: Optional[str] = None) -> List[LifecycleEvent]:
        """
        作用：
        读取事实生命周期事件。

        输入：
        可选 `record_id`。

        输出：
        `LifecycleEvent` 列表。

        关键边界：
        统一在仓库层完成事件对象重建，保持上层接口一致。
        """

        return [
            LifecycleEvent.from_dict(payload)
            for payload in self.store.list_lifecycle_events(record_id=record_id)
        ]
