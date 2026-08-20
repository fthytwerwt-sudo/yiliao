"""
用途：
实现 V1 开发环境所需的本地 SQLite Storage Port。

上游：
CLI、Local API 与领域服务通过 `StoragePort` 依赖该实现。

下游：
SQLite 文件保存通用 JSON payload；未来可用同一 Port 替换为 PostgreSQL。

边界：
这里不解释 payload 的业务含义，不连接网络，也不承担事实审核或权限判断。
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Optional

from general_ai_business_os.domain.entities import StoredRecord
from general_ai_business_os.storage.contracts import StoragePort


class SqliteStore(StoragePort):
    """每次短连接访问 SQLite，避免测试和本地命令共享隐式全局连接。"""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _connect(self) -> sqlite3.Connection:
        """打开带 Row 映射的本地连接；父目录由这里显式创建。"""

        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def migrate(self) -> None:
        """创建基础 records 表；列保持中性，后续领域表可独立迁移。"""

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS system_records (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def save_record(self, record: StoredRecord) -> None:
        """显式 upsert 通用记录；调用者负责决定何时应更新已有 ID。"""

        self.migrate()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO system_records (id, kind, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kind = excluded.kind,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    record.id,
                    record.kind,
                    json.dumps(record.payload, ensure_ascii=False, sort_keys=True),
                    record.created_at,
                    record.updated_at,
                ),
            )

    def get_record(self, record_id: str) -> Optional[StoredRecord]:
        """读取一条记录，避免将数据库 row 结构泄漏到上层。"""

        self.migrate()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, kind, payload_json, created_at, updated_at FROM system_records WHERE id = ?",
                (record_id,),
            ).fetchone()
        if row is None:
            return None
        return StoredRecord.from_dict(
            {
                "id": row["id"],
                "kind": row["kind"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )
