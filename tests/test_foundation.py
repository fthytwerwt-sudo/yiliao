"""战略无关系统基础设施的最小可运行合同。"""

from pathlib import Path
import tempfile
import unittest

from medical_tourism_os.adapters.mock import MockAdapter
from medical_tourism_os.audit.logger import AuditLogger
from medical_tourism_os.config import SystemConfig
from medical_tourism_os.domain.entities import (
    FactClassification,
    FactRecord,
    PermissionDecision,
    ReviewStatus,
)
from medical_tourism_os.permissions.policy import PermissionPolicy
from medical_tourism_os.repositories.core import FactRepository
from medical_tourism_os.storage.sqlite_store import SqliteStore


class FoundationTests(unittest.TestCase):
    """锁住默认关闭、可替换存储和最小敏感审计的系统基础。"""

    def test_default_configuration_disables_every_external_action(self) -> None:
        """没有明确本地配置时，任何现实 adapter 都不得获得执行许可。"""
        config = SystemConfig.default()
        self.assertFalse(config.external_execution_allowed)
        self.assertFalse(config.adapters_enabled)
        self.assertEqual("sqlite", config.storage_backend)

    def test_sqlite_repository_round_trips_a_fact_without_platform_dependency(self) -> None:
        """领域事实必须可经 SQLite port 保存和读取，且无特定平台字段。"""
        with tempfile.TemporaryDirectory() as directory:
            store = SqliteStore(Path(directory) / "operating-system.sqlite3")
            store.migrate()
            repository = FactRepository(store)
            record = FactRecord.new_candidate(
                claim="TEST_MARKET_A has an unresolved access question",
                source="synthetic://research/001",
                source_date="2026-08-19",
                scope="synthetic fixture",
                provenance="fixture:research-001",
            )

            repository.save(record)
            loaded = repository.get(record.id)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(record.claim, loaded.claim)
        self.assertEqual(FactClassification.FACT_CANDIDATE, loaded.classification)
        self.assertEqual(ReviewStatus.PENDING, loaded.review_status)
        self.assertNotIn("platform", loaded.to_dict())

    def test_mock_adapter_stays_dry_run_when_configuration_is_disabled(self) -> None:
        """适配器必须显式报告未执行，而不是悄悄产生外部副作用。"""
        adapter = MockAdapter(enabled=False)

        result = adapter.publish({"content_id": "synthetic-content-001"})

        self.assertTrue(result.dry_run)
        self.assertFalse(result.executed)
        self.assertEqual("adapter_disabled", result.reason)

    def test_mock_adapter_requires_explicit_permission_even_when_enabled(self) -> None:
        """开启 mock adapter 不等于获得权限，缺审批时必须继续 dry-run。"""
        adapter = MockAdapter(enabled=True)

        missing_permission = adapter.publish({"content_id": "synthetic-content-001"})
        denied_permission = adapter.publish(
            {"content_id": "synthetic-content-001"},
            permission=PermissionDecision(allowed=False, reason="external_execution_disabled"),
        )
        approved_permission = adapter.publish(
            {"content_id": "synthetic-content-001"},
            permission=PermissionDecision(allowed=True, reason="allowed"),
        )

        self.assertTrue(missing_permission.dry_run)
        self.assertFalse(missing_permission.executed)
        self.assertEqual("permission_required", missing_permission.reason)

        self.assertTrue(denied_permission.dry_run)
        self.assertFalse(denied_permission.executed)
        self.assertEqual("permission_denied", denied_permission.reason)

        self.assertFalse(approved_permission.dry_run)
        self.assertTrue(approved_permission.executed)
        self.assertEqual("mock_executed", approved_permission.reason)

    def test_mock_adapter_cannot_bypass_default_policy_denial(self) -> None:
        """即使 adapter 本身 enabled，默认权限拒绝也必须阻止执行。"""
        adapter = MockAdapter(enabled=True)
        policy = PermissionPolicy(SystemConfig.default())

        permission = policy.check_external_action("publish", adapter_enabled=True)
        result = adapter.publish(
            {"content_id": "synthetic-content-001"},
            permission=permission,
        )

        self.assertFalse(permission.allowed)
        self.assertTrue(result.dry_run)
        self.assertFalse(result.executed)
        self.assertEqual("permission_denied", result.reason)

    def test_permission_policy_denies_external_execution_by_default(self) -> None:
        """权限层是外部动作的第二道门，不能只依赖调用者自觉。"""
        policy = PermissionPolicy(SystemConfig.default())

        decision = policy.check_external_action("publish")

        self.assertFalse(decision.allowed)
        self.assertEqual("external_execution_disabled", decision.reason)

    def test_audit_logger_redacts_sensitive_values_before_persistence(self) -> None:
        """审计需要说明拒绝原因，但不能反向保存患者或密钥内容。"""
        with tempfile.TemporaryDirectory() as directory:
            logger = AuditLogger(Path(directory) / "audit.jsonl")
            event = logger.record(
                action="import_rejected",
                outcome="blocked",
                details={
                    "record_id": "fact_001",
                    "stage": "staging",
                    "reason": "sensitive_input_detected",
                    "count": 2,
                    "patient_name": "should-not-persist",
                    "name": "Alice",
                    "email": "alice@example.com",
                    "phone": "+1-555-0100",
                    "password": "super-secret",
                    "authorization": "Bearer secret-token",
                    "notes": "token=abc",
                    "context": {"raw_text": "patient detail should never persist"},
                    "items": ["safe-looking", {"raw_text": "nested token=abc"}],
                },
            )
            persisted = (Path(directory) / "audit.jsonl").read_text(encoding="utf-8")

        self.assertEqual("blocked", event.outcome)
        self.assertEqual("fact_001", event.details["record_id"])
        self.assertEqual("staging", event.details["stage"])
        self.assertEqual("sensitive_input_detected", event.details["reason"])
        self.assertEqual(2, event.details["count"])
        self.assertEqual("[REDACTED]", event.details["name"])
        self.assertEqual("[REDACTED]", event.details["notes"])
        self.assertEqual("[REDACTED]", event.details["context"])
        self.assertEqual("[REDACTED]", event.details["items"])
        self.assertNotIn("should-not-persist", persisted)
        self.assertNotIn("Alice", persisted)
        self.assertNotIn("alice@example.com", persisted)
        self.assertNotIn("+1-555-0100", persisted)
        self.assertNotIn("super-secret", persisted)
        self.assertNotIn("Bearer secret-token", persisted)
        self.assertNotIn("token=abc", persisted)
        self.assertNotIn("patient detail should never persist", persisted)
        self.assertIn("[REDACTED]", persisted)
        self.assertIn("fact_001", persisted)


if __name__ == "__main__":
    unittest.main()
