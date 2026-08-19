"""验证 Research 输入不能绕过清洗、人工复核和正式事实晋升。"""

from datetime import date
from pathlib import Path
import tempfile
import unittest

from medical_tourism_os.audit.logger import AuditLogger
from medical_tourism_os.domain.entities import FactClassification, ReviewStatus
from medical_tourism_os.exports.safe_export import export_canonical_facts
from medical_tourism_os.fixtures.synthetic import SYNTHETIC_RESEARCH_RECORD
from medical_tourism_os.repositories.core import FactRepository
from medical_tourism_os.services.data_governance import (
    DataGovernanceService,
    ReviewGateError,
    ValidationError,
)
from medical_tourism_os.storage.sqlite_store import SqliteStore


class DataGovernanceTests(unittest.TestCase):
    """锁住 Raw、Staging、Adjudicated、Canonical 的事实治理路径。"""

    def _service(self, directory: str) -> DataGovernanceService:
        """创建使用临时 SQLite 与脱敏审计日志的隔离治理服务。"""
        store = SqliteStore(Path(directory) / "governance.sqlite3")
        store.migrate()
        return DataGovernanceService(
            repository=FactRepository(store),
            audit_logger=AuditLogger(Path(directory) / "audit.jsonl"),
        )

    def test_research_import_runs_the_required_lifecycle_and_normalizes_claims(self) -> None:
        """研究输入必须从 Raw 经过清洗到待人工复核的候选，而非正式事实。"""
        with tempfile.TemporaryDirectory() as directory:
            result = self._service(directory).ingest_research(
                {
                    "claim": "  TEST_MARKET_A   has an unresolved access question ",
                    "source_date": "2026-08-19",
                    "scope": "synthetic fixture",
                },
                source="synthetic://research/001",
            )

        self.assertEqual(("RAW", "STAGING", "ADJUDICATED"), result.lifecycle)
        self.assertEqual("TEST_MARKET_A has an unresolved access question", result.record.claim)
        self.assertEqual(FactClassification.FACT_CANDIDATE, result.record.classification)
        self.assertEqual(ReviewStatus.PENDING, result.record.review_status)
        self.assertIsNone(result.duplicate_of)

    def test_duplicate_input_is_not_persisted_as_a_second_fact(self) -> None:
        """去重必须保留最早的候选与 provenance，而不是静默覆盖来源。"""
        with tempfile.TemporaryDirectory() as directory:
            service = self._service(directory)
            first = service.ingest_research(SYNTHETIC_RESEARCH_RECORD, "synthetic://research/001")
            duplicate = service.ingest_research(SYNTHETIC_RESEARCH_RECORD, "synthetic://research/001")

        self.assertIsNone(first.duplicate_of)
        self.assertEqual(first.record.id, duplicate.duplicate_of)
        self.assertTrue(duplicate.is_duplicate)

    def test_invalid_or_sensitive_research_input_is_rejected_before_storage(self) -> None:
        """数据校验必须拒绝空主张和疑似患者资料，避免敏感原文进入事实库。"""
        with tempfile.TemporaryDirectory() as directory:
            service = self._service(directory)
            with self.assertRaises(ValidationError):
                service.ingest_research({"claim": "   "}, "synthetic://research/invalid")
            with self.assertRaises(ValidationError):
                service.ingest_research(
                    {
                        "claim": "TEST_MARKET_A has an access question",
                        "patient_name": "must-not-enter-storage",
                    },
                    "synthetic://research/sensitive",
                )

    def test_conflict_and_freshness_are_explicit_review_signals(self) -> None:
        """冲突和过期只能标记给人工复核，不能被系统自行裁决为真或假。"""
        with tempfile.TemporaryDirectory() as directory:
            service = self._service(directory)
            older = service.ingest_research(
                {
                    "claim": "TEST_PRODUCT_A has an unresolved evidence question",
                    "source_date": "2020-01-01",
                    "scope": "synthetic fixture",
                },
                "synthetic://research/older",
            ).record
            other = service.ingest_research(
                {
                    "claim": "TEST_PRODUCT_A has a different unresolved evidence question",
                    "source_date": "2026-08-19",
                    "scope": "synthetic fixture",
                },
                "synthetic://research/other",
            ).record

            stale = service.check_freshness(older.id, as_of=date(2026, 8, 19), max_age_days=30)
            conflicted = service.mark_conflict(older.id, other.id)

        self.assertEqual("stale", stale.freshness)
        self.assertEqual("conflicted", conflicted[0].conflict_status)
        self.assertEqual("conflicted", conflicted[1].conflict_status)
        self.assertEqual(ReviewStatus.PENDING, conflicted[0].review_status)

    def test_canonical_promotion_requires_a_named_human_review_and_safe_export_filters_candidates(self) -> None:
        """Research 不得直达 Canonical；导出也只能看见已人工批准的非敏感事实。"""
        with tempfile.TemporaryDirectory() as directory:
            service = self._service(directory)
            candidate = service.ingest_research(SYNTHETIC_RESEARCH_RECORD, "synthetic://research/001").record

            with self.assertRaises(ReviewGateError):
                service.approve_fact(candidate.id, reviewed_by="")

            canonical = service.approve_fact(candidate.id, reviewed_by="human-reviewer-001")
            exported = export_canonical_facts([candidate, canonical])

        self.assertEqual(FactClassification.CANONICAL_FACT, canonical.classification)
        self.assertEqual(ReviewStatus.APPROVED, canonical.review_status)
        self.assertEqual("human-reviewer-001", canonical.reviewed_by)
        self.assertEqual(1, len(exported))
        self.assertEqual(canonical.id, exported[0]["id"])
        self.assertNotIn("source", exported[0])
        self.assertNotIn("provenance", exported[0])


if __name__ == "__main__":
    unittest.main()
