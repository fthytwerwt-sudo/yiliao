"""验证 Research 输入不能绕过清洗、人工复核和正式事实晋升。"""

from datetime import date
import json
from pathlib import Path
import sqlite3
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

    def test_sensitive_free_text_is_rejected_before_raw_persistence_and_never_leaks(self) -> None:
        """即使 key 合法，只要自由文本像患者/PHI，系统也必须在 Raw 前 fail-closed。"""
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "governance.sqlite3"
            service = self._service(directory)
            with self.assertRaises(ValidationError):
                service.ingest_research(
                    {
                        "claim": "Patient John Doe has a cardiac surgery booking",
                        "source_date": "2026-08-19",
                        "scope": "synthetic fixture",
                    },
                    "synthetic://research/free-text-sensitive",
                )
            with self.assertRaises(ValidationError):
                service.ingest_research(
                    {
                        "claim": "TEST_MARKET_A has an unresolved access question",
                        "source_date": "2026-08-19",
                        "scope": "synthetic fixture",
                        "metadata": {
                            "note": "Patient Jane Roe passport number sample"
                        },
                    },
                    "synthetic://research/nested-sensitive",
                )

            with sqlite3.connect(database_path) as connection:
                facts_count = connection.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
                lifecycle_count = connection.execute("SELECT COUNT(*) FROM lifecycle_events").fetchone()[0]

            audit_text = (Path(directory) / "audit.jsonl").read_text(encoding="utf-8")

        self.assertEqual(0, facts_count)
        self.assertEqual(0, lifecycle_count)
        self.assertNotIn("Patient John Doe", audit_text)
        self.assertNotIn("cardiac surgery booking", audit_text)
        self.assertNotIn("Patient Jane Roe passport number sample", audit_text)

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

    def test_stale_or_conflicted_candidates_require_named_resolution_before_approval(self) -> None:
        """过期和冲突都必须先经过具名人工 resolution，不能直接 approve。"""
        with tempfile.TemporaryDirectory() as directory:
            service = self._service(directory)
            stale_candidate = service.ingest_research(
                {
                    "claim": "TEST_PRODUCT_A has an unresolved evidence question",
                    "source_date": "2020-01-01",
                    "scope": "synthetic fixture",
                },
                "synthetic://research/stale",
            ).record
            left = service.ingest_research(
                {
                    "claim": "TEST_PRODUCT_A has one unresolved access note",
                    "source_date": "2026-08-19",
                    "scope": "synthetic fixture",
                },
                "synthetic://research/conflict-left",
            ).record
            right = service.ingest_research(
                {
                    "claim": "TEST_PRODUCT_A has another unresolved access note",
                    "source_date": "2026-08-19",
                    "scope": "synthetic fixture",
                },
                "synthetic://research/conflict-right",
            ).record

            stale_candidate = service.check_freshness(
                stale_candidate.id,
                as_of=date(2026, 8, 19),
                max_age_days=30,
            )
            conflicted_left, conflicted_right = service.mark_conflict(left.id, right.id)

            with self.assertRaises(ReviewGateError):
                service.approve_fact(stale_candidate.id, reviewed_by="human-reviewer-001")
            with self.assertRaises(ReviewGateError):
                service.approve_fact(conflicted_left.id, reviewed_by="human-reviewer-001")
            with self.assertRaises(ReviewGateError):
                service.resolve_freshness(stale_candidate.id, reviewed_by="")
            with self.assertRaises(ReviewGateError):
                service.resolve_conflict(conflicted_left.id, conflicted_right.id, reviewed_by="")

            resolved_stale = service.resolve_freshness(
                stale_candidate.id,
                reviewed_by="human-reviewer-001",
            )
            resolved_left, resolved_right = service.resolve_conflict(
                conflicted_left.id,
                conflicted_right.id,
                reviewed_by="human-reviewer-001",
            )
            canonical_from_stale = service.approve_fact(
                resolved_stale.id,
                reviewed_by="human-reviewer-001",
            )
            canonical_from_conflict = service.approve_fact(
                resolved_left.id,
                reviewed_by="human-reviewer-001",
            )

        self.assertEqual("fresh", resolved_stale.freshness)
        self.assertEqual("resolved", resolved_left.conflict_status)
        self.assertEqual("resolved", resolved_right.conflict_status)
        self.assertEqual(FactClassification.CANONICAL_FACT, canonical_from_stale.classification)
        self.assertEqual(FactClassification.CANONICAL_FACT, canonical_from_conflict.classification)

    def test_lifecycle_events_are_returned_in_causal_sequence_and_upgrade_path_keeps_facts_readable(self) -> None:
        """回读顺序必须按持久单调 sequence，而不是碰运气依赖时间戳或 UUID。"""
        with tempfile.TemporaryDirectory() as directory:
            service = self._service(directory)
            record = service.ingest_research(
                SYNTHETIC_RESEARCH_RECORD,
                "synthetic://research/ordered",
            ).record

            events = service.repository.list_lifecycle_events(record.id)
            loaded = service.repository.get(record.id)

        assert loaded is not None
        self.assertEqual(["RAW", "STAGING", "ADJUDICATED"], [event.stage.value for event in events])
        self.assertEqual([1, 2, 3], [event.sequence for event in events])
        self.assertIn("payload_hash", events[0].details)
        self.assertIn("field_count", events[1].details)
        self.assertNotIn("claim", events[1].details)
        self.assertNotIn("provenance", events[1].details)
        self.assertNotIn("source", events[0].details)
        self.assertEqual(record.id, loaded.id)

    def test_json_and_csv_importers_use_the_same_governance_path(self) -> None:
        """JSON 和 CSV 入口必须走同一清洗、候选创建与生命周期轨迹。"""
        with tempfile.TemporaryDirectory() as directory:
            service = self._service(directory)
            json_result = service.ingest_research_json(
                json.dumps(
                    {
                        "claim": "  TEST_MARKET_A   has a JSON access question ",
                        "source_date": "2026-08-19",
                        "scope": "synthetic fixture",
                    }
                ),
                "synthetic://research/json",
            )
            csv_result = service.ingest_research_csv(
                "claim,source_date,scope\n  TEST_MARKET_A   has a CSV access question ,2026-08-19,synthetic fixture\n",
                "synthetic://research/csv",
            )

            json_events = service.repository.list_lifecycle_events(json_result.record.id)
            csv_events = service.repository.list_lifecycle_events(csv_result.record.id)

        self.assertEqual(("RAW", "STAGING", "ADJUDICATED"), json_result.lifecycle)
        self.assertEqual(("RAW", "STAGING", "ADJUDICATED"), csv_result.lifecycle)
        self.assertEqual("TEST_MARKET_A has a JSON access question", json_result.record.claim)
        self.assertEqual("TEST_MARKET_A has a CSV access question", csv_result.record.claim)
        self.assertEqual([1, 2, 3], [event.sequence for event in json_events])
        self.assertEqual([1, 2, 3], [event.sequence for event in csv_events])

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
