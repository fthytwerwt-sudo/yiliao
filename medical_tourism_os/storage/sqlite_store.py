"""
用途：
提供 SQLite 存储实现，承接事实记录的最小持久化能力。

上游：
repositories.core 调用这里保存与读取 `FactRecord`。

下游：
SQLite 文件与 migration 脚本。

边界：
这里只实现 port，不夹带业务规则；SQL 细节被限制在该基础设施模块内部。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from medical_tourism_os.domain.entities import FactRecord


class SqliteStore:
    """
    作用：
    以 SQLite 文件实现 `FactStoragePort`。

    输入：
    `database_path` 指向本地 SQLite 文件。

    输出：
    提供 migration、保存和读取事实的能力。

    关键边界：
    所有 SQL 都集中在这里，避免仓库或领域层散落数据库知识。
    """

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)

    def _connect(self) -> sqlite3.Connection:
        """
        作用：
        打开一个带 `Row` 工厂的 SQLite 连接。

        输入：
        无。

        输出：
        `sqlite3.Connection`。

        关键边界：
        目录若不存在会先创建，保证测试与本地运行在空目录也能启动。
        """

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def migrate(self) -> None:
        """
        作用：
        执行当前基础 schema migration。

        输入：
        无。

        输出：
        无；数据库 schema 被更新到至少包含 facts 表。

        关键边界：
        migration 必须可重复执行，因为测试、本地初始化和未来幂等启动都会多次调用。
        """

        migration_path = (
            Path(__file__).resolve().parents[1] / "migrations" / "001_initial_schema.sql"
        )
        script = migration_path.read_text(encoding="utf-8")
        with self._connect() as connection:
            connection.executescript(script)

    def save_fact(self, record: FactRecord) -> None:
        """
        作用：
        把 `FactRecord` 写入 SQLite。

        输入：
        一条完整领域事实记录。

        输出：
        无。

        关键边界：
        使用 `INSERT OR REPLACE` 维持最小实现，后续 phase 再根据审计需求细化更新策略。
        """

        payload = record.to_dict()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO facts (
                    id, claim, source, source_date, scope, classification,
                    confidence, freshness, conflict_status, review_status,
                    reviewed_by, created_at, updated_at, provenance
                ) VALUES (
                    :id, :claim, :source, :source_date, :scope, :classification,
                    :confidence, :freshness, :conflict_status, :review_status,
                    :reviewed_by, :created_at, :updated_at, :provenance
                )
                """,
                payload,
            )

    def get_fact(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        作用：
        按 ID 读取一条事实记录。

        输入：
        `record_id` 为事实唯一标识。

        输出：
        成功时返回字段字典，找不到时返回 `None`。

        关键边界：
        这里返回原始字段映射而不是直接组装领域对象，让仓库继续承担对象重建职责。
        """

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id, claim, source, source_date, scope, classification,
                    confidence, freshness, conflict_status, review_status,
                    reviewed_by, created_at, updated_at, provenance
                FROM facts
                WHERE id = ?
                """,
                (record_id,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)
