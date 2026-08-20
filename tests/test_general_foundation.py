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
        """审计只保存 allowlist 内的安全字段，未知字段不能借日志落盘。"""

        from general_ai_business_os.audit.logger import AuditLogger

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "audit.jsonl"
            event = AuditLogger(log_path).record(
                action="adapter.request",
                outcome="blocked",
                details={"adapter": "content", "operation": "generate", "reason": "external_actions_disabled"},
            )

            persisted = log_path.read_text(encoding="utf-8")

        self.assertIn("content", persisted)
        self.assertEqual(
            {"adapter": "content", "operation": "generate", "reason": "external_actions_disabled"},
            event.details,
        )

    def test_audit_logger_rejects_unknown_and_sensitive_free_text_before_persistence(self) -> None:
        """患者、健康、Token 或嵌套自由文本都不能变成审计日志的旁路。"""

        from general_ai_business_os.audit.logger import AuditLogger

        unsafe_details = (
            {"patient_name": "TEST_PERSON"},
            {"notes": "TEST_HEALTH_DETAIL"},
            {"access_token": "TEST_ACCESS_TOKEN"},
            {"adapter": {"nested": "TEST_UNTRUSTED"}},
        )
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "audit.jsonl"
            logger = AuditLogger(log_path)
            for details in unsafe_details:
                with self.assertRaisesRegex(ValueError, "audit_details"):
                    logger.record(action="adapter.request", outcome="blocked", details=details)

            persisted = log_path.read_text(encoding="utf-8") if log_path.exists() else ""

        self.assertNotIn("TEST_PERSON", persisted)
        self.assertNotIn("TEST_HEALTH_DETAIL", persisted)
        self.assertNotIn("TEST_ACCESS_TOKEN", persisted)
        self.assertNotIn("TEST_UNTRUSTED", persisted)

    def test_audit_logger_rejects_free_text_action_and_outcome_before_persistence(self) -> None:
        """action/outcome 也是日志字段，不能接收调用方注入的任意自由文本。"""

        from general_ai_business_os.audit.logger import AuditLogger

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "audit.jsonl"
            logger = AuditLogger(log_path)
            with self.assertRaisesRegex(ValueError, "audit_action_invalid"):
                logger.record(
                    action="unsafe free text",
                    outcome="blocked",
                    details={"adapter": "content"},
                )
            with self.assertRaisesRegex(ValueError, "audit_outcome_invalid"):
                logger.record(
                    action="adapter.request",
                    outcome="unsafe free text",
                    details={"adapter": "content"},
                )

            persisted = log_path.read_text(encoding="utf-8") if log_path.exists() else ""

        self.assertEqual("", persisted)

    def test_audit_logger_rejects_code_shaped_sensitive_values_in_every_audit_surface(self) -> None:
        """没有空格的敏感字符串也不能伪装成系统 code 并绕过审计 allowlist。"""

        from general_ai_business_os.audit.logger import AuditLogger

        safe_details = {"adapter": "content", "operation": "generate", "reason": "external_actions_disabled"}
        unsafe_detail_attempts = (
            {"adapter": "PATIENT_NOTE"},
            {"operation": "TEST_PERSON"},
            {"status": "ghp_ABC123SECRET"},
            {"reason": "TEST_HEALTH_DETAIL"},
            {"safe_code": "TEST_PERSON"},
            {"request_id": "ghp_ABC123SECRET"},
            {"record_id": "PATIENT_NOTE"},
            {"config_version": "TEST_HEALTH_DETAIL"},
        )
        unsafe_values = ("PATIENT_NOTE", "TEST_PERSON", "ghp_ABC123SECRET", "TEST_HEALTH_DETAIL")

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "audit.jsonl"
            logger = AuditLogger(log_path)
            for details in unsafe_detail_attempts:
                with self.assertRaisesRegex(ValueError, "audit_details"):
                    logger.record(action="adapter.request", outcome="blocked", details=details)
            for unsafe_value in unsafe_values:
                with self.assertRaisesRegex(ValueError, "audit_action_invalid"):
                    logger.record(action=unsafe_value, outcome="blocked", details=safe_details)
                with self.assertRaisesRegex(ValueError, "audit_outcome_invalid"):
                    logger.record(action="adapter.request", outcome=unsafe_value, details=safe_details)

            persisted = log_path.read_text(encoding="utf-8") if log_path.exists() else ""

        for unsafe_value in unsafe_values:
            self.assertNotIn(unsafe_value, persisted)

    def test_audit_event_return_is_immutable_and_stays_safe_when_serialized_for_storage(self) -> None:
        """审计写盘后返回的事件也必须保持安全，不能被调用方改写成存储旁路。"""

        from general_ai_business_os.audit.logger import AuditLogger
        from general_ai_business_os.domain.entities import StoredRecord
        from general_ai_business_os.storage.sqlite_store import SqliteStore

        original_details = {"adapter": "content", "operation": "generate", "reason": "external_actions_disabled"}
        unsafe_values = ("PATIENT_NOTE", "TEST_PERSON", "ghp_ABC123SECRET", "TEST_HEALTH_DETAIL")
        with tempfile.TemporaryDirectory() as directory:
            event = AuditLogger(Path(directory) / "audit.jsonl").record(
                action="adapter.request",
                outcome="blocked",
                details=original_details,
            )
            original_details["adapter"] = "PATIENT_NOTE"
            self.assertEqual("content", event.details["adapter"])
            for unsafe_value in unsafe_values:
                with self.assertRaises(TypeError):
                    event.details["adapter"] = unsafe_value

            store = SqliteStore(Path(directory) / "state.sqlite3")
            store.migrate()
            record = StoredRecord.new(
                record_id="TEST_AUDIT_EVENT",
                kind="audit_event",
                payload=event.to_dict(),
            )
            store.save_record(record)
            persisted = store.get_record("TEST_AUDIT_EVENT")

        self.assertIsNotNone(persisted)
        persisted_text = json.dumps(persisted.payload, ensure_ascii=False, sort_keys=True)
        for unsafe_value in unsafe_values:
            self.assertNotIn(unsafe_value, persisted_text)

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

    def test_mock_adapter_stays_non_executing_even_when_policy_allows_the_request(self) -> None:
        """Mock 的许可只用于合同演练，不能被误报为真实执行。"""

        from general_ai_business_os.adapters.mock import MockAdapter
        from general_ai_business_os.config import SystemConfig
        from general_ai_business_os.permissions.policy import PermissionPolicy

        result = MockAdapter(capability="content.image").execute(
            operation="generate",
            payload={"request_id": "TEST_REQUEST"},
            permission=PermissionPolicy(SystemConfig(external_actions_allowed=True)).authorize("content.generate"),
        )

        self.assertEqual("MOCK", result.status.value)
        self.assertFalse(result.executed)
        self.assertEqual("mock_dry_run", result.reason)

    def test_permission_policy_denies_empty_action(self) -> None:
        """空动作不允许落入默认分支，避免未知调用被误授权。"""

        from general_ai_business_os.config import SystemConfig
        from general_ai_business_os.permissions.policy import PermissionPolicy

        decision = PermissionPolicy(SystemConfig()).authorize(" ")

        self.assertFalse(decision.allowed)
        self.assertEqual("action_required", decision.reason)

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

    def test_local_api_rejects_every_non_loopback_host(self) -> None:
        """localhost 与 IPv6 也不作为隐式例外，防止运行环境差异扩大监听范围。"""

        from general_ai_business_os.config import SystemConfig
        from general_ai_business_os.interfaces.local_api import LocalApiApplication

        for host in ("0.0.0.0", "localhost", "::1"):
            with self.assertRaisesRegex(ValueError, "local_api_requires_loopback_host"):
                LocalApiApplication(SystemConfig(api_host=host)).create_server()

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
