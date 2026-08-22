"""验证 Acquisition Plugin 独立处理 B2B 潜客，并始终保持 Mock-only 外部边界。"""

from __future__ import annotations

from pathlib import Path
import unittest

from general_ai_business_os.plugins import PluginRegistry
from medical_tourism_os.acquisition.adapters import MockDirectoryProvider, MockEmailProvider
from medical_tourism_os.acquisition.domain import (
    BusinessCategory,
    BusinessEntity,
    BusinessEntityStatus,
    ContactPoint,
    ContactType,
    OutreachReviewStatus,
    ProspectPriority,
    ProspectStatus,
)
from medical_tourism_os.acquisition.schemas import (
    ContactExtractionResult,
    DirectorySearchResult,
    EmailSendResult,
    FeedbackOutcome,
    ProspectScoreDimensions,
)
from medical_tourism_os.acquisition.services import (
    BusinessClassifier,
    OutreachGenerator,
    ProspectScorer,
)
from medical_tourism_os.acquisition.workflows import (
    OutreachWorkflow,
    ProspectDiscoveryWorkflow,
)


class AcquisitionPluginTests(unittest.TestCase):
    """锁定企业潜客、人工复核和零真实外部动作的最小行为合同。"""

    @staticmethod
    def _entity() -> BusinessEntity:
        return BusinessEntity(
            id="business-test-001",
            company_name="TEST_TRAVEL_A",
            category=BusinessCategory.UNKNOWN,
            location="TEST_MARKET_A",
            website="https://business.test.invalid",
            description="A travel agency serving community groups",
            source_url="https://directory.test.invalid/business-test-001",
            evidence_refs=("evidence-test-001",),
            status=BusinessEntityStatus.DISCOVERED,
        )

    @staticmethod
    def _contact() -> ContactPoint:
        return ContactPoint(
            type=ContactType.PUBLIC_EMAIL,
            value_reference="public_contact_ref_00000000000000000000000000000001",
            source="https://business.test.invalid/contact",
            verified_at="2026-08-23T00:00:00+00:00",
        )

    @staticmethod
    def _high_dimensions() -> ProspectScoreDimensions:
        return ProspectScoreDimensions(
            category_fit=90,
            market_fit=80,
            audience_overlap=70,
            contact_quality=85,
            partnership_probability=75,
            evidence_refs=("evidence-test-001", "score-evidence-test-001"),
        )

    def test_business_entity_and_contact_point_can_be_created_without_consumer_lead_fields(self) -> None:
        """B2B 对象保存企业证据和公开联系引用，不出现 consent/intent/patient 字段。"""

        entity = self._entity()
        contact = self._contact()

        self.assertEqual("TEST_TRAVEL_A", entity.company_name)
        self.assertEqual(BusinessEntityStatus.DISCOVERED, entity.status)
        self.assertTrue(contact.value_reference.startswith("public_contact_ref_"))
        self.assertNotIn("consent", entity.to_dict())
        self.assertNotIn("intent", entity.to_dict())
        self.assertNotIn("patient", entity.to_dict())

    def test_contact_point_rejects_raw_phone_disguised_as_a_reference(self) -> None:
        """opaque reference 必须是固定 token 格式，不能只给真实手机号加前缀。"""

        with self.assertRaisesRegex(ValueError, "public_contact_reference_required"):
            ContactPoint(
                type=ContactType.PUBLIC_PHONE,
                value_reference="public_contact_ref_13800138000",
                source="https://business.test.invalid/contact",
                verified_at=None,
            )

    def test_prospect_scorer_uses_five_business_dimensions_and_routes_high_value(self) -> None:
        """合作潜客五维等权评分独立于 LeadScorer，并保留可审计 reason codes。"""

        prospect = ProspectScorer().score(
            business_entity_id=self._entity().id,
            dimensions=self._high_dimensions(),
        )

        self.assertEqual(80, prospect.fit_score)
        self.assertEqual(ProspectPriority.HIGH, prospect.priority)
        self.assertEqual(ProspectStatus.OUTREACH_QUEUE, prospect.status)
        self.assertEqual(
            (
                "category_fit=90",
                "market_fit=80",
                "audience_overlap=70",
                "contact_quality=85",
                "partnership_probability=75",
            ),
            prospect.reason_codes,
        )

    def test_prospect_scorer_holds_missing_evidence_instead_of_guessing(self) -> None:
        """没有真实评分证据时不得凭企业名称猜合作概率，只能等待更多证据。"""

        prospect = ProspectScorer().score(
            business_entity_id=self._entity().id,
            dimensions=ProspectScoreDimensions.empty(),
        )

        self.assertEqual(0, prospect.fit_score)
        self.assertEqual(ProspectPriority.LOW, prospect.priority)
        self.assertEqual(ProspectStatus.HOLD_FOR_MORE_EVIDENCE, prospect.status)
        self.assertIn("missing_score_evidence", prospect.reason_codes)

    def test_outreach_generator_creates_human_review_draft_with_required_reasoning(self) -> None:
        """触达生成只创建包含联系理由、合作假设与可验证价值的待审草稿。"""

        entity = BusinessClassifier().classify(self._entity())
        prospect = ProspectScorer().score(entity.id, self._high_dimensions())

        draft = OutreachGenerator().generate(entity=entity, prospect=prospect)

        self.assertEqual(OutreachReviewStatus.PENDING, draft.review_status)
        self.assertIn("Why we are contacting you", draft.body)
        self.assertIn("Partnership hypothesis", draft.body)
        self.assertIn("Verifiable value", draft.body)
        self.assertIn("has not been sent", draft.body)
        self.assertIn("travel_agency", draft.personalization_reason)

    def test_discovery_workflow_classifies_and_scores_mock_directory_results(self) -> None:
        """Mock 目录发现可串起分类与评分，但目录调用仍明确为非真实执行。"""

        provider = MockDirectoryProvider(fixtures=(self._entity(),))
        workflow = ProspectDiscoveryWorkflow(
            directory_provider=provider,
            classifier=BusinessClassifier(),
            scorer=ProspectScorer(),
        )

        result = workflow.run(
            market="TEST_MARKET_A",
            keywords=("travel",),
            score_dimensions_by_entity={self._entity().id: self._high_dimensions()},
        )

        self.assertTrue(result.directory_result.dry_run)
        self.assertFalse(result.directory_result.executed)
        self.assertEqual("mock_directory_only", result.directory_result.status)
        self.assertEqual(BusinessCategory.TRAVEL_AGENCY, result.entities[0].category)
        self.assertEqual(ProspectStatus.OUTREACH_QUEUE, result.prospects[0].status)

    def test_discovery_workflow_preserves_contact_extractor_execution_status(self) -> None:
        """可选联系方式提取结果必须跨 Workflow 保留 dry-run/executed/status 审计字段。"""

        class SafeContactExtractor:
            mock_only = True

            def extract(self, *, entity):
                return ContactExtractionResult(
                    contacts=(self_outer._contact(),),
                    dry_run=True,
                    executed=False,
                    status="mock_contact_extraction_only",
                )

        self_outer = self
        workflow = ProspectDiscoveryWorkflow(
            directory_provider=MockDirectoryProvider(fixtures=(self._entity(),)),
            classifier=BusinessClassifier(),
            scorer=ProspectScorer(),
            contact_extractor=SafeContactExtractor(),
        )

        result = workflow.run(market="TEST_MARKET_A", keywords=("travel",))
        extraction = result.contact_results_by_entity[self._entity().id]

        self.assertTrue(extraction.dry_run)
        self.assertFalse(extraction.executed)
        self.assertEqual("mock_contact_extraction_only", extraction.status)
        self.assertEqual((self._contact(),), extraction.contacts)

    def test_discovery_workflow_rejects_non_mock_or_executed_contact_extractors(self) -> None:
        """V1 不得调用现实网站提取器，也不能接受声称已执行的联系方式结果。"""

        class SideEffectExtractor:
            def __init__(self) -> None:
                self.calls = 0

            def extract(self, *, entity):
                self.calls += 1
                return ContactExtractionResult((), False, True, "real_executed")

        side_effect_extractor = SideEffectExtractor()
        with self.assertRaisesRegex(ValueError, "mock_contact_extractor_required"):
            ProspectDiscoveryWorkflow(
                directory_provider=MockDirectoryProvider(fixtures=(self._entity(),)),
                classifier=BusinessClassifier(),
                scorer=ProspectScorer(),
                contact_extractor=side_effect_extractor,
            )
        self.assertEqual(0, side_effect_extractor.calls)

        class FalseMockExtractor:
            mock_only = True

            def extract(self, *, entity):
                return ContactExtractionResult((), False, True, "real_executed")

        workflow = ProspectDiscoveryWorkflow(
            directory_provider=MockDirectoryProvider(fixtures=(self._entity(),)),
            classifier=BusinessClassifier(),
            scorer=ProspectScorer(),
            contact_extractor=FalseMockExtractor(),
        )
        with self.assertRaisesRegex(RuntimeError, "external_contact_extraction_forbidden"):
            workflow.run(market="TEST_MARKET_A", keywords=("travel",))

    def test_contact_extraction_result_rejects_raw_contact_values(self) -> None:
        """Extractor DTO 自身必须拒绝原始邮箱，不能把安全责任只留给类型提示。"""

        with self.assertRaisesRegex(ValueError, "contact_point_required"):
            ContactExtractionResult(
                contacts=("user@example.com",),
                dry_run=True,
                executed=False,
                status="mock_contact_extraction_only",
            )

    def test_discovery_workflow_rejects_non_mock_or_executed_directory_providers(self) -> None:
        """V1 不得调用现实目录 Provider，也不能接受声称已执行的目录结果。"""

        class SideEffectDirectoryProvider:
            def __init__(self) -> None:
                self.calls = 0

            def search(self, *, market, keywords):
                self.calls += 1
                return DirectorySearchResult((), False, True, "real_executed")

        side_effect_provider = SideEffectDirectoryProvider()
        with self.assertRaisesRegex(ValueError, "mock_directory_provider_required"):
            ProspectDiscoveryWorkflow(
                directory_provider=side_effect_provider,
                classifier=BusinessClassifier(),
                scorer=ProspectScorer(),
            )
        self.assertEqual(0, side_effect_provider.calls)

        class FalseMockDirectoryProvider:
            mock_only = True

            def search(self, *, market, keywords):
                return DirectorySearchResult((), False, True, "real_executed")

        workflow = ProspectDiscoveryWorkflow(
            directory_provider=FalseMockDirectoryProvider(),
            classifier=BusinessClassifier(),
            scorer=ProspectScorer(),
        )
        with self.assertRaisesRegex(RuntimeError, "external_directory_execution_forbidden"):
            workflow.run(market="TEST_MARKET_A", keywords=("travel",))

    def test_mock_adapters_never_produce_real_external_actions(self) -> None:
        """目录和邮件 Mock 即使收到完整输入，也不能访问现实目录或发送邮件。"""

        entity = BusinessClassifier().classify(self._entity())
        prospect = ProspectScorer().score(entity.id, self._high_dimensions())
        draft = OutreachGenerator().generate(entity=entity, prospect=prospect)

        directory_result = MockDirectoryProvider(fixtures=(entity,)).search(
            market="TEST_MARKET_A",
            keywords=("travel",),
        )
        email_result = MockEmailProvider().send(draft=draft, contact=self._contact())

        self.assertTrue(directory_result.dry_run)
        self.assertFalse(directory_result.executed)
        self.assertTrue(email_result.dry_run)
        self.assertFalse(email_result.executed)
        self.assertEqual("mock_email_not_sent", email_result.status)
        self.assertIsNone(email_result.provider_message_id)

    def test_mock_email_and_workflow_reject_raw_contact_strings_at_runtime(self) -> None:
        """Python type hint 不是安全闸门；运行时也必须拒绝原始邮箱字符串。"""

        entity = BusinessClassifier().classify(self._entity())
        prospect = ProspectScorer().score(entity.id, self._high_dimensions())
        draft = OutreachGenerator().generate(entity, prospect)
        provider = MockEmailProvider()

        with self.assertRaisesRegex(ValueError, "contact_point_required"):
            provider.send(draft=draft, contact="user@example.com")

        workflow = OutreachWorkflow(OutreachGenerator(), provider)
        workflow.prepare(entity, prospect)
        workflow.approve(prospect_id=prospect.id, reviewed_by="human-reviewer-test-001")
        with self.assertRaisesRegex(ValueError, "contact_point_required"):
            workflow.attempt_send(prospect_id=prospect.id, contact="user@example.com")
        self.assertEqual((), workflow.send_queue())

    def test_outreach_workflow_rejects_non_mock_and_false_mock_provider_results(self) -> None:
        """V1 Workflow 不得调用现实 Provider，也不能接受谎报 executed=true 的 Mock 结果。"""

        class SideEffectProvider:
            def __init__(self) -> None:
                self.send_calls = 0

            def send(self, *, draft, contact):
                self.send_calls += 1
                return EmailSendResult(draft.prospect_id, False, True, "real_sent", "real-id")

        side_effect_provider = SideEffectProvider()
        with self.assertRaisesRegex(ValueError, "mock_email_provider_required"):
            OutreachWorkflow(OutreachGenerator(), side_effect_provider)
        self.assertEqual(0, side_effect_provider.send_calls)

        class FalseMockProvider:
            mock_only = True

            def send(self, *, draft, contact):
                return EmailSendResult(draft.prospect_id, False, True, "real_sent", "real-id")

        entity = BusinessClassifier().classify(self._entity())
        prospect = ProspectScorer().score(entity.id, self._high_dimensions())
        workflow = OutreachWorkflow(OutreachGenerator(), FalseMockProvider())
        workflow.prepare(entity, prospect)
        workflow.approve(prospect_id=prospect.id, reviewed_by="human-reviewer-test-001")
        with self.assertRaisesRegex(RuntimeError, "external_email_execution_forbidden"):
            workflow.attempt_send(prospect_id=prospect.id, contact=self._contact())

    def test_outreach_workflow_requires_named_review_and_keeps_send_dry_run(self) -> None:
        """未审草稿不能进入发送；具名批准后也只进入 Mock send queue。"""

        entity = BusinessClassifier().classify(self._entity())
        prospect = ProspectScorer().score(entity.id, self._high_dimensions())
        workflow = OutreachWorkflow(
            generator=OutreachGenerator(),
            email_provider=MockEmailProvider(),
        )
        draft = workflow.prepare(entity=entity, prospect=prospect)

        with self.assertRaisesRegex(ValueError, "outreach_draft_not_approved"):
            workflow.attempt_send(prospect_id=prospect.id, contact=self._contact())
        with self.assertRaisesRegex(ValueError, "named_human_reviewer_required"):
            workflow.approve(prospect_id=prospect.id, reviewed_by="  ")

        approved = workflow.approve(prospect_id=prospect.id, reviewed_by="human-reviewer-test-001")
        send_result = workflow.attempt_send(prospect_id=prospect.id, contact=self._contact())

        self.assertEqual(OutreachReviewStatus.APPROVED, approved.review_status)
        self.assertEqual((prospect.id,), workflow.send_queue())
        self.assertTrue(send_result.dry_run)
        self.assertFalse(send_result.executed)
        self.assertEqual(draft.prospect_id, approved.prospect_id)

    def test_outreach_workflow_records_reply_reference_and_feedback_without_message_body(self) -> None:
        """回复与学习层只保存外部引用和结构化反馈，不把邮件正文带入系统。"""

        entity = BusinessClassifier().classify(self._entity())
        prospect = ProspectScorer().score(entity.id, self._high_dimensions())
        workflow = OutreachWorkflow(OutreachGenerator(), MockEmailProvider())
        workflow.prepare(entity, prospect)

        with self.assertRaisesRegex(ValueError, "feedback_requires_send_queue"):
            workflow.record_feedback(
                prospect_id=prospect.id,
                outcome=FeedbackOutcome.POSITIVE,
                evidence_refs=("reply_ref_test_001",),
            )
        with self.assertRaisesRegex(ValueError, "reply_requires_send_queue"):
            workflow.record_reply(
                prospect_id=prospect.id,
                reply_reference="reply_ref_test_001",
            )
        workflow.approve(prospect_id=prospect.id, reviewed_by="human-reviewer-test-001")
        workflow.attempt_send(prospect_id=prospect.id, contact=self._contact())
        with self.assertRaisesRegex(ValueError, "feedback_requires_reply"):
            workflow.record_feedback(
                prospect_id=prospect.id,
                outcome=FeedbackOutcome.POSITIVE,
                evidence_refs=("reply_ref_test_001",),
            )
        reply = workflow.record_reply(
            prospect_id=prospect.id,
            reply_reference="reply_ref_test_001",
        )
        with self.assertRaisesRegex(ValueError, "feedback_reply_evidence_required"):
            workflow.record_feedback(
                prospect_id=prospect.id,
                outcome=FeedbackOutcome.POSITIVE,
                evidence_refs=("reply_ref_other",),
            )
        feedback = workflow.record_feedback(
            prospect_id=prospect.id,
            outcome=FeedbackOutcome.POSITIVE,
            evidence_refs=("reply_ref_test_001",),
        )

        self.assertEqual("reply_ref_test_001", reply.reply_reference)
        self.assertEqual(FeedbackOutcome.POSITIVE, feedback.outcome)
        self.assertNotIn("body", reply.to_dict())
        self.assertNotIn("body", feedback.to_dict())

    def test_reply_and_feedback_factories_reject_blank_prospect_ids(self) -> None:
        """公共 DTO factory 自身必须拒绝孤儿记录，不能只依赖 Workflow 间接校验。"""

        from medical_tourism_os.acquisition.schemas import FeedbackRecord, ReplyIntakeRecord

        with self.assertRaisesRegex(ValueError, "prospect_id_required"):
            ReplyIntakeRecord.create(prospect_id="  ", reply_reference="reply_ref_test_001")
        with self.assertRaisesRegex(ValueError, "prospect_id_required"):
            FeedbackRecord.create(
                prospect_id="  ",
                outcome=FeedbackOutcome.POSITIVE,
                evidence_refs=("reply_ref_test_001",),
            )

    def test_core_registry_discovers_manifest_without_loading_business_code(self) -> None:
        """Acquisition 只以 Application Plugin manifest 被 Core 发现，不修改 Core 源码。"""

        plugin_root = Path(__file__).resolve().parents[1] / "medical_tourism_os"
        registry = PluginRegistry()

        self.assertIn("ACQUISITION", registry.discover(plugin_root))
        self.assertEqual((), registry.active())
        registry.activate("ACQUISITION")
        self.assertTrue(registry.authorize("ACQUISITION", "WORKFLOW_RUN"))
        self.assertFalse(registry.authorize("ACQUISITION", "TOOL_INVOKE"))


if __name__ == "__main__":
    unittest.main()
