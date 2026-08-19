"""验证需求、产品、线索与匹配均保持战略无关且受风险规则约束。"""

import unittest

from medical_tourism_os.domain.entities import FactClassification
from medical_tourism_os.services.business_core import (
    DemandRadar,
    HumanReviewCoordinator,
    LeadScorer,
    ProductCatalog,
    ProductMatcher,
)
from medical_tourism_os.services.risk_router import RiskRouter
from medical_tourism_os.workflows.core import InboundWorkflow


class BusinessCoreTests(unittest.TestCase):
    """锁住 Phase 3 的候选管理、风险阻断和非临床匹配边界。"""

    def test_demand_radar_clusters_signals_without_turning_them_into_facts(self) -> None:
        """需求信号可聚类，但仍必须保留 evidence 与非正式分类。"""
        radar = DemandRadar()
        first = radar.record_signal(
            market="TEST_MARKET_A",
            theme="trust question",
            evidence_ids=("fact-test-001",),
            classification=FactClassification.RESEARCH,
        )
        second = radar.record_signal(
            market="TEST_MARKET_A",
            theme="trust question",
            evidence_ids=("fact-test-002",),
            classification=FactClassification.HYPOTHESIS,
        )

        clusters = radar.cluster_signals()

        self.assertEqual(1, len(clusters))
        self.assertEqual("trust question", clusters[0].theme)
        self.assertEqual({first.id, second.id}, set(clusters[0].signal_ids))
        self.assertNotEqual(FactClassification.CANONICAL_FACT, first.classification)

    def test_product_catalog_keeps_product_as_hypothesis_with_evidence_gaps(self) -> None:
        """产品库只保存候选的价值、依赖、证据和风险，不能变成正式 offer。"""
        catalog = ProductCatalog()

        product = catalog.create_candidate(
            code="TEST_PRODUCT_A",
            target_segment="TEST_SEGMENT_A",
            value_hypothesis="resolve a non-clinical coordination question",
            requirements=("evidence_pending",),
            supply_evidence_ids=("fact-test-001",),
            price_evidence_ids=("fact-test-002",),
            risks=("professional_review_required",),
        )

        self.assertEqual("hypothesis", product.status)
        self.assertEqual("TEST_PRODUCT_A", product.code)
        self.assertEqual(("fact-test-002",), product.price_evidence_ids)
        self.assertIn("professional_review_required", product.risks)

    def test_risk_router_fail_closes_every_required_high_risk_category(self) -> None:
        """PHI、临床、支付与其他高风险文字都必须在核心流程前被阻断。"""
        router = RiskRouter()
        samples = {
            "PHI": "patient record attached",
            "diagnosis": "please diagnose this condition",
            "treatment": "choose a treatment for me",
            "medication": "recommend medication",
            "emergency": "this is an emergency",
            "legal": "give a legal conclusion",
            "visa": "guarantee a visa",
            "payment": "take a payment now",
            "privacy": "share private details",
            "guarantee": "guarantee an outcome",
            "minor": "a minor needs service",
        }

        for expected_category, text in samples.items():
            with self.subTest(expected_category=expected_category):
                result = router.route(text)
                self.assertTrue(result.blocked)
                self.assertEqual(expected_category, result.category)
                self.assertEqual("fail_closed", result.action)

    def test_risk_router_returns_only_safe_summary_for_high_risk_text(self) -> None:
        """高风险原文不能进入 route 结果的安全摘要。"""
        text = "patient record attached with private details"
        result = RiskRouter().route(text)

        self.assertTrue(result.blocked)
        self.assertNotIn(text, str(result.safe_summary))
        self.assertEqual("PHI", result.safe_summary["matched_category"])

    def test_lead_score_is_configuration_driven_and_stores_no_patient_record(self) -> None:
        """评分权重由调用配置提供，输出只保留匿名线索所需字段。"""
        scorer = LeadScorer(
            weights={"consent": 4, "contact_reference": 2, "source": 1, "intent": 3}
        )

        scored = scorer.score(
            anonymous_lead_id="lead-test-001",
            contact_reference="contact-ref-test-001",
            source="TEST_CHANNEL_A",
            consent_status="granted",
            intent="high",
        )

        self.assertEqual(10, scored.score)
        self.assertEqual("high", scored.band)
        self.assertNotIn("patient", scored.to_dict())
        self.assertNotIn("diagnosis", scored.to_dict())

    def test_product_matching_returns_candidate_only_not_a_medical_recommendation(self) -> None:
        """匹配只能解释候选满足的非临床条件，不能给出医疗建议。"""
        catalog = ProductCatalog()
        product = catalog.create_candidate(
            code="TEST_PRODUCT_A",
            target_segment="TEST_SEGMENT_A",
            value_hypothesis="resolve a non-clinical coordination question",
            requirements=("time_window_known",),
            supply_evidence_ids=("fact-test-001",),
            price_evidence_ids=(),
            risks=(),
        )
        matcher = ProductMatcher()

        matches = matcher.match(
            non_clinical_goal="coordination question",
            region="TEST_MARKET_A",
            time_window="TEST_WINDOW_A",
            channel="TEST_CHANNEL_A",
            evidence_status="candidate",
            products=[product],
        )

        self.assertEqual(1, len(matches))
        self.assertEqual("candidate_match", matches[0].status)
        self.assertEqual("not_a_medical_recommendation", matches[0].safety_boundary)

    def test_product_matching_rejects_candidates_with_risk_or_missing_supply_evidence(self) -> None:
        """缺供给证据或自带风险标记的候选不得被自动匹配。"""
        catalog = ProductCatalog()
        risky = catalog.create_candidate(
            code="TEST_PRODUCT_RISK",
            target_segment="TEST_SEGMENT_A",
            value_hypothesis="resolve a non-clinical coordination question",
            requirements=("time_window_known",),
            supply_evidence_ids=("fact-test-001",),
            price_evidence_ids=(),
            risks=("professional_review_required",),
        )
        evidence_free = catalog.create_candidate(
            code="TEST_PRODUCT_EMPTY",
            target_segment="TEST_SEGMENT_A",
            value_hypothesis="resolve a non-clinical coordination question",
            requirements=("time_window_known",),
            supply_evidence_ids=(),
            price_evidence_ids=(),
            risks=(),
        )

        matches = ProductMatcher().match(
            non_clinical_goal="coordination question",
            region="TEST_MARKET_A",
            time_window="TEST_WINDOW_A",
            channel="TEST_CHANNEL_A",
            evidence_status="candidate",
            products=[risky, evidence_free],
        )

        self.assertEqual([], matches)

    def test_human_review_coordinator_delegates_canonical_promotion_to_phase2_gate(self) -> None:
        """业务核心若要升级正式事实，必须显式调用 Phase 2 approve_fact。"""

        class StubRecord:
            def __init__(self) -> None:
                self.id = "fact-test-001"
                self.classification = FactClassification.CANONICAL_FACT

        class StubGovernance:
            def __init__(self) -> None:
                self.calls = []

            def approve_fact(self, record_id: str, reviewed_by: str) -> StubRecord:
                self.calls.append((record_id, reviewed_by))
                return StubRecord()

        governance = StubGovernance()
        decision = HumanReviewCoordinator().promote_candidate_fact(
            governance_service=governance,
            candidate_fact_id="fact-test-001",
            reviewed_by="human-reviewer-001",
        )

        self.assertEqual([("fact-test-001", "human-reviewer-001")], governance.calls)
        self.assertEqual("CANONICAL_FACT", decision.resulting_classification)

    def test_inbound_workflow_blocks_risk_before_creating_anonymous_lead(self) -> None:
        """高风险输入不能落入 CRM；安全模拟输入才可形成匿名候选线索。"""
        workflow = InboundWorkflow(risk_router=RiskRouter())

        blocked = workflow.process(
            text="please diagnose this condition",
            source="TEST_CHANNEL_A",
            contact_reference="contact-ref-test-001",
        )
        allowed = workflow.process(
            text="I have a general coordination question",
            source="TEST_CHANNEL_A",
            contact_reference="contact-ref-test-002",
        )

        self.assertTrue(blocked.blocked)
        self.assertIsNone(blocked.lead)
        self.assertFalse(allowed.blocked)
        self.assertIsNotNone(allowed.lead)
        assert allowed.lead is not None
        self.assertEqual("anonymous", allowed.lead.status)


if __name__ == "__main__":
    unittest.main()
