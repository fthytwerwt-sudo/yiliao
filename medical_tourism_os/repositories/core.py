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

from typing import Optional

from medical_tourism_os.domain.entities import FactRecord
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
