"""
用途：
把当前 Phase 2–7 的核心模块串成一条 synthetic end-to-end 轨迹。

上游：
测试、CLI 调试和只读本地接口通过这里验证整条链路。

下游：
输出结构化 `SyntheticScenarioResult`，供技术验收与日志记录使用。

边界：
这里只运行 synthetic fixture，不联系外部系统、不声明业务验证完成，也不引入真实事实。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

from medical_tourism_os.audit.logger import AuditLogger
from medical_tourism_os.domain.entities import FactClassification
from medical_tourism_os.fixtures.synthetic import SYNTHETIC_RESEARCH_RECORD
from medical_tourism_os.repositories.core import FactRepository
from medical_tourism_os.services.business_core import DemandRadar, ProductCatalog, ProductMatcher
from medical_tourism_os.services.content_interaction import CommentIntake, ContentFactory, ContentIntelligence
from medical_tourism_os.services.data_governance import DataGovernanceService
from medical_tourism_os.services.risk_router import RiskRouter
from medical_tourism_os.storage.sqlite_store import SqliteStore
from medical_tourism_os.workflows.weekly_review import LearningLoop


@dataclass(frozen=True)
class SyntheticScenarioResult:
    """
    作用：
    表示一条 synthetic E2E 运行的最小验收结果。

    关键边界：
    business_validation_completed 固定为 false，提醒这是技术闭环而非业务闭环。
    """

    stages: tuple[str, ...]
    decision_candidate_status: str
    github_sync_dry_run: bool
    business_validation_completed: bool
    synthetic_identifiers: tuple[str, ...]


def _build_governance_service(directory: str) -> DataGovernanceService:
    """为 E2E 运行创建隔离的数据治理服务。"""

    store = SqliteStore(Path(directory) / "e2e.sqlite3")
    store.migrate()
    return DataGovernanceService(
        repository=FactRepository(store),
        audit_logger=AuditLogger(Path(directory) / "e2e-audit.jsonl"),
    )


def run_synthetic_scenario() -> SyntheticScenarioResult:
    """
    作用：
    跑完一条不触发外部动作的 synthetic 运营轨迹。

    关键边界：
    终点只能是 candidate + GitHub dry-run；不允许把技术走通误报为业务验证完成。
    """

    with tempfile.TemporaryDirectory() as directory:
        governance = _build_governance_service(directory)
        research = governance.ingest_research(
            dict(SYNTHETIC_RESEARCH_RECORD),
            source="synthetic://research/001",
        )
        facts = governance.list_review_queue()

        radar = DemandRadar()
        demand_signal = radar.record_signal(
            market="TEST_MARKET_A",
            theme="trust question",
            evidence_ids=(research.record.id,),
            classification=FactClassification.RESEARCH,
            dimensions=("region_known", "time_window_known", "channel_known", "goal_stated"),
        )
        catalog = ProductCatalog()
        product = catalog.create_candidate(
            code="TEST_PRODUCT_A",
            target_segment="TEST_SEGMENT_A",
            value_hypothesis="resolve a non-clinical coordination question",
            requirements=("region_known", "time_window_known", "channel_known", "goal_stated"),
            supply_evidence_ids=(research.record.id,),
            price_evidence_ids=(),
            risks=(),
        )
        drafts = ContentFactory().generate_drafts(
            ContentIntelligence().build_brief(
                demand_signal=demand_signal,
                product=product,
                fact_refs=(research.record.id,),
                experiment_id="TEST_EXPERIMENT_CONTEXT_A",
            )
        )

        comment_result = CommentIntake(risk_router=RiskRouter()).ingest(
            text="I have a general coordination question",
            source="TEST_CHANNEL_A",
            contact_reference="SAFE_OPAQUE_REF_001",
            consent_status="granted",
        )
        risk_result = RiskRouter().route("please diagnose this condition")

        matches = ProductMatcher().match(
            non_clinical_goal="general coordination question",
            region="TEST_REGION_A",
            time_window="TEST_WINDOW_A",
            channel="TEST_CHANNEL_A",
            evidence_status="candidate",
            products=(product,),
        )

        learning_loop = LearningLoop()
        learning_loop.record_metric("TEST_CHANNEL_A", "reach", 120)
        learning_loop.record_metric("TEST_CHANNEL_A", "lead", 5)
        experiment = learning_loop.create_experiment(
            hypothesis="TEST_PRODUCT_A message may clarify a non-clinical question",
            primary_variable="message_angle",
            fixed_variables=("TEST_MARKET_A", "TEST_WINDOW_A"),
            window="TEST_WINDOW_A",
            metrics=("reach", "lead"),
        )
        learning_loop.review_experiment(experiment.id, result="insufficient_sample")
        weekly_review = learning_loop.generate_weekly_review()
        candidate = learning_loop.create_decision_candidate(weekly_review.id)
        github_sync = learning_loop.github_dry_run(candidate.id)

    if not facts:
        raise AssertionError("synthetic_facts_required")
    if not drafts:
        raise AssertionError("synthetic_drafts_required")
    if comment_result.lead is None:
        raise AssertionError("synthetic_lead_required")
    if not risk_result.blocked:
        raise AssertionError("synthetic_risk_block_required")
    if not matches:
        raise AssertionError("synthetic_match_required")

    return SyntheticScenarioResult(
        stages=(
            "Research",
            "Fact",
            "Demand",
            "Product",
            "Content",
            "Comment/DM",
            "Risk",
            "Lead",
            "Match",
            "Metrics",
            "Experiment",
            "Weekly Review",
            "Decision Candidate",
            "GitHub Dry Run",
        ),
        decision_candidate_status=candidate.status,
        github_sync_dry_run=github_sync.dry_run,
        business_validation_completed=False,
        synthetic_identifiers=(
            "TEST_RESEARCH_001",
            "TEST_MARKET_A",
            "TEST_PRODUCT_A",
            "TEST_CHANNEL_A",
            "TEST_WINDOW_A",
        ),
    )
