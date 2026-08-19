"""验证内容和互动模块保持草稿、匿名和默认不外发。"""

import unittest

from medical_tourism_os.adapters.mock import MockAdapter
from medical_tourism_os.config import SystemConfig
from medical_tourism_os.domain.entities import FactClassification
from medical_tourism_os.services.business_core import DemandRadar, ProductCatalog
from medical_tourism_os.services.content_interaction import (
    CommentIntake,
    ContentFactory,
    ContentIntelligence,
    DirectMessageIntake,
    PublishingQueue,
)
from medical_tourism_os.services.risk_router import RiskRouter


class ContentAndInteractionTests(unittest.TestCase):
    """锁住草稿生成、发布队列、互动风控和匿名 CRM 的边界。"""

    def _brief_inputs(self):
        """创建只含 synthetic candidate 的内容判断输入。"""
        radar = DemandRadar()
        signal = radar.record_signal(
            market="TEST_MARKET_A",
            theme="trust question",
            evidence_ids=("fact-test-001",),
            classification=FactClassification.RESEARCH,
        )
        product = ProductCatalog().create_candidate(
            code="TEST_PRODUCT_A",
            target_segment="TEST_SEGMENT_A",
            value_hypothesis="resolve a non-clinical coordination question",
            requirements=("evidence_pending",),
            supply_evidence_ids=("fact-test-001",),
            price_evidence_ids=(),
            risks=(),
        )
        return signal, product

    def test_content_intelligence_and_factory_produce_drafts_only(self) -> None:
        """候选输入可形成 brief 与五类草稿，但不得形成发布或医疗承诺。"""
        signal, product = self._brief_inputs()
        brief = ContentIntelligence().build_brief(
            demand_signal=signal,
            product=product,
            fact_refs=("fact-test-001",),
            experiment_id="experiment-test-001",
        )

        drafts = ContentFactory().generate_drafts(brief)

        self.assertEqual("candidate", brief.evidence_status)
        self.assertEqual(
            {"video_script", "carousel", "faq", "seo_brief", "reply_candidate"},
            {draft.content_type for draft in drafts},
        )
        self.assertTrue(all(draft.status == "draft" for draft in drafts))
        self.assertTrue(all(draft.publication_id is None for draft in drafts))

    def test_publishing_queue_never_publishes_when_adapter_is_disabled(self) -> None:
        """合法状态流转不等于外部动作许可；关闭 adapter 时只能保留 queued/dry-run。"""
        signal, product = self._brief_inputs()
        brief = ContentIntelligence().build_brief(signal, product, ("fact-test-001",), "experiment-test-001")
        draft = ContentFactory().generate_drafts(brief)[0]
        queue = PublishingQueue(adapter=MockAdapter(enabled=False))

        queue.submit_for_review(draft.id)
        queue.approve(draft.id, reviewed_by="human-reviewer-001")
        queue.enqueue(draft.id)
        result = queue.attempt_publish(draft.id)

        self.assertTrue(result.dry_run)
        self.assertFalse(result.executed)
        self.assertEqual("queued", queue.get(draft.id).status)
        self.assertIsNone(queue.get(draft.id).publication_id)

    def test_comment_and_dm_intake_route_risk_before_anonymous_crm_capture(self) -> None:
        """评论和 DM 只接收安全模拟文本；高风险内容不能成为 CRM 线索。"""
        router = RiskRouter()
        comments = CommentIntake(risk_router=router)
        dms = DirectMessageIntake(risk_router=router)

        safe_comment = comments.ingest(
            text="I have a general coordination question",
            source="TEST_CHANNEL_A",
            contact_reference="contact-ref-test-001",
        )
        blocked_dm = dms.ingest(
            text="please diagnose this condition",
            source="TEST_CHANNEL_A",
            contact_reference="contact-ref-test-002",
        )

        self.assertFalse(safe_comment.blocked)
        self.assertIsNotNone(safe_comment.lead)
        self.assertTrue(blocked_dm.blocked)
        self.assertIsNone(blocked_dm.lead)
        assert safe_comment.lead is not None
        self.assertTrue(safe_comment.lead.contact_reference.startswith("contact_ref_"))

    def test_publishing_queue_rejects_invalid_transition_and_blank_reviewer(self) -> None:
        """发布队列只能沿既定状态机前进，且审批必须是具名人工。"""
        signal, product = self._brief_inputs()
        brief = ContentIntelligence().build_brief(signal, product, ("fact-test-001",), "experiment-test-001")
        draft = ContentFactory().generate_drafts(brief)[0]
        queue = PublishingQueue(adapter=MockAdapter(enabled=False))

        with self.assertRaisesRegex(ValueError, "invalid_status_transition"):
            queue.enqueue(draft.id)

        queue.submit_for_review(draft.id)
        with self.assertRaisesRegex(ValueError, "named_human_reviewer_required"):
            queue.approve(draft.id, reviewed_by="   ")

    def test_publishing_queue_stays_queued_under_default_deny_config_even_if_adapter_enabled(self) -> None:
        """默认配置未放开 external execution 时，即使 adapter 打开也只能 dry-run。"""
        signal, product = self._brief_inputs()
        brief = ContentIntelligence().build_brief(signal, product, ("fact-test-001",), "experiment-test-001")
        draft = ContentFactory().generate_drafts(brief)[0]
        queue = PublishingQueue(
            adapter=MockAdapter(enabled=True),
            config=SystemConfig.default(),
        )

        queue.submit_for_review(draft.id)
        queue.approve(draft.id, reviewed_by="human-reviewer-001")
        queue.enqueue(draft.id)
        result = queue.attempt_publish(draft.id)

        self.assertTrue(result.dry_run)
        self.assertFalse(result.executed)
        self.assertEqual("permission_denied", result.reason)
        self.assertEqual("queued", queue.get(draft.id).status)
        self.assertIsNone(queue.get(draft.id).publication_id)

    def test_content_generation_fails_closed_on_clinical_or_guarantee_language(self) -> None:
        """即使上游允许记录信号，内容层仍必须拦截临床/保证措辞。"""
        signal = DemandRadar().record_signal(
            market="TEST_MARKET_A",
            theme="guarantee result",
            evidence_ids=("fact-test-001",),
            classification=FactClassification.RESEARCH,
        )
        product = ProductCatalog().create_candidate(
            code="TEST_PRODUCT_A",
            target_segment="TEST_SEGMENT_A",
            value_hypothesis="resolve a non-clinical coordination question",
            requirements=("evidence_pending",),
            supply_evidence_ids=("fact-test-001",),
            price_evidence_ids=(),
            risks=(),
        )

        with self.assertRaisesRegex(ValueError, "demand_theme_contains_clinical_or_guarantee_language"):
            ContentIntelligence().build_brief(
                demand_signal=signal,
                product=product,
                fact_refs=("fact-test-001",),
                experiment_id="experiment-test-001",
            )


if __name__ == "__main__":
    unittest.main()
