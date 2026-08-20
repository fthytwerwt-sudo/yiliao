"""
用途：
定义领域服务依赖的存储端口，而不是让业务能力直接绑定 SQLite。

上游：
业务配置、Agent 与 workflow 通过这个 Port 保存和读取结构化记录。

下游：
SQLite 是开发实现；未来 PostgreSQL 可实现相同接口。

边界：
本合同只定义通用记录操作，不包含 SQL、连接字符串或业务专属字段。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from general_ai_business_os.domain.entities import StoredRecord


class StoragePort(ABC):
    """可替换的通用存储接口。"""

    @abstractmethod
    def migrate(self) -> None:
        """初始化实现所需的技术 schema，不做任何业务数据注入。"""

    @abstractmethod
    def save_record(self, record: StoredRecord) -> None:
        """保存一条已由领域层校验的通用记录。"""

    @abstractmethod
    def get_record(self, record_id: str) -> Optional[StoredRecord]:
        """按明确 ID 回读记录；缺失时返回 None 而非隐式创建默认值。"""
