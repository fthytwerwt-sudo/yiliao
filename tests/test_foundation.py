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
                details={"patient_name": "should-not-persist", "api_token": "secret-value"},
            )
            persisted = (Path(directory) / "audit.jsonl").read_text(encoding="utf-8")

        self.assertEqual("blocked", event.outcome)
        self.assertNotIn("should-not-persist", persisted)
        self.assertNotIn("secret-value", persisted)
        self.assertIn("[REDACTED]", persisted)


if __name__ == "__main__":
    unittest.main()
