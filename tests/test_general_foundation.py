"""验证通用商业运营系统基础层的最小公共入口。"""

from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest


class GeneralFoundationTests(unittest.TestCase):
    """Phase 1 先锁定中性新包必须存在，后续再逐项扩展行为合同。"""

    def test_general_operating_system_package_exists(self) -> None:
        """新能力必须从中性包进入，不能继续扩展旧医疗包作为核心。"""

        self.assertIsNotNone(importlib.util.find_spec("general_ai_business_os"))

    def test_default_permission_policy_denies_external_actions(self) -> None:
        """没有显式授权时，任何 Adapter 都不能取得外部执行许可。"""

        from general_ai_business_os.config import SystemConfig
        from general_ai_business_os.permissions.policy import PermissionPolicy

        decision = PermissionPolicy(SystemConfig()).authorize("content.generate")

        self.assertFalse(decision.allowed)
        self.assertEqual("external_actions_disabled", decision.reason)

    def test_audit_logger_redacts_sensitive_values_before_writing(self) -> None:
        """审计要保留判断证据，但不得把密钥原文写进日志。"""

        from general_ai_business_os.audit.logger import AuditLogger

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "audit.jsonl"
            event = AuditLogger(log_path).record(
                action="adapter.request",
                outcome="blocked",
                details={"api_key": "secret-value", "safe_code": "TEST_VALUE"},
            )

            persisted = log_path.read_text(encoding="utf-8")

        self.assertEqual("[REDACTED]", event.details["api_key"])
        self.assertIn("TEST_VALUE", persisted)
        self.assertNotIn("secret-value", persisted)

    def test_mock_adapter_reports_dry_run_without_external_execution(self) -> None:
        """Mock 可以验证调用合同，但必须明确它没有触发外部副作用。"""

        from general_ai_business_os.adapters.mock import MockAdapter
        from general_ai_business_os.config import SystemConfig
        from general_ai_business_os.permissions.policy import PermissionPolicy

        adapter = MockAdapter(capability="content.image")
        result = adapter.execute(
            operation="generate",
            payload={"request_id": "TEST_REQUEST"},
            permission=PermissionPolicy(SystemConfig()).authorize("content.generate"),
        )

        self.assertEqual("BLOCKED", result.status.value)
        self.assertFalse(result.executed)
        self.assertEqual("external_actions_disabled", result.reason)

    def test_sqlite_store_round_trips_generic_record_through_neutral_port(self) -> None:
        """领域存储只使用通用 record 合同，不含任何业务或平台专属列。"""

        from general_ai_business_os.domain.entities import StoredRecord
        from general_ai_business_os.storage.sqlite_store import SqliteStore

        with tempfile.TemporaryDirectory() as directory:
            store = SqliteStore(Path(directory) / "state.sqlite3")
            store.migrate()
            expected = StoredRecord.new(
                record_id="TEST_RECORD",
                kind="test_kind",
                payload={"value": "TEST_VALUE"},
            )
            store.save_record(expected)
            actual = store.get_record("TEST_RECORD")

        self.assertEqual(expected, actual)

    def test_local_api_is_loopback_only_and_advertises_operating_system_routes(self) -> None:
        """本地接口只能创建 loopback server，路由清单提前暴露但不会自动启动。"""

        from general_ai_business_os.interfaces.local_api import LocalApiApplication

        application = LocalApiApplication()
        server = application.create_server()
        try:
            self.assertEqual("127.0.0.1", server.server_address[0])
            self.assertFalse(application.is_running)
            self.assertEqual(
                {
                    "/config",
                    "/content",
                    "/leads",
                    "/messages",
                    "/crm",
                    "/knowledge",
                    "/experiments",
                    "/metrics",
                },
                set(application.route_inventory()),
            )
        finally:
            server.server_close()

    def test_cli_system_init_creates_local_state_without_enabling_external_actions(self) -> None:
        """CLI 初始化本地状态，但输出必须证明外部动作仍然关闭。"""

        from general_ai_business_os.interfaces.cli import run_cli

        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = run_cli(["system", "init", "--state-root", directory])
            payload = json.loads(output.getvalue())

        self.assertEqual(0, exit_code)
        self.assertEqual("initialized", payload["status"])
        self.assertFalse(payload["external_actions_allowed"])

    def test_legacy_medical_package_import_remains_available(self) -> None:
        """迁移的第一条回归线：新包不得破坏现有兼容入口。"""

        from medical_tourism_os.interfaces.cli import run_cli

        self.assertTrue(callable(run_cli))


if __name__ == "__main__":
    unittest.main()
