"""
用途：
编排触达草稿、具名人工审核、Mock 发送队列、回复引用和反馈信号。

上游：
Prospect Discovery 输出的 BusinessEntity / Prospect，以及人工 reviewer id。

下游：
EmailProvider 结果、ReplyIntakeRecord 与 FeedbackRecord。

边界：
未审核草稿不得发送；批准只表示可进入 send queue；V1 Email Provider 仍不会真实发送。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict

from medical_tourism_os.acquisition.domain import (
    BusinessEntity,
    ContactPoint,
    OutreachDraft,
    OutreachReviewStatus,
    Prospect,
)
from medical_tourism_os.acquisition.interfaces import EmailProvider
from medical_tourism_os.acquisition.schemas import (
    EmailSendResult,
    FeedbackOutcome,
    FeedbackRecord,
    ReplyIntakeRecord,
)
from medical_tourism_os.acquisition.services import OutreachGenerator


class OutreachWorkflow:
    """维护一个本地会话内的触达审核、队列、回复引用和反馈状态。"""

    def __init__(self, generator: OutreachGenerator, email_provider: EmailProvider) -> None:
        # V1 只允许显式 mock-only Provider；未来真实发送必须走单独权限与审计设计。
        if getattr(email_provider, "mock_only", False) is not True:
            raise ValueError("mock_email_provider_required")
        self.generator = generator
        self.email_provider = email_provider
        self._drafts: Dict[str, OutreachDraft] = {}
        self._reviewed_by: Dict[str, str] = {}
        self._send_queue: list[str] = []
        self._replies: list[ReplyIntakeRecord] = []
        self._feedback: list[FeedbackRecord] = []

    def prepare(self, entity: BusinessEntity, prospect: Prospect) -> OutreachDraft:
        """生成并保存 pending 草稿；重复 prepare 会覆盖同一 Prospect 的未外发草稿。"""

        draft = self.generator.generate(entity=entity, prospect=prospect)
        self._drafts[prospect.id] = draft
        return draft

    def approve(self, *, prospect_id: str, reviewed_by: str) -> OutreachDraft:
        """
        由具名人工把草稿转为 approved。

        关键边界：reviewer 不能为空；approved 不写 sent 状态，也不调用 EmailProvider。
        """

        reviewer = reviewed_by.strip()
        if not reviewer:
            raise ValueError("named_human_reviewer_required")
        draft = self._get_draft(prospect_id)
        approved = replace(draft, review_status=OutreachReviewStatus.APPROVED)
        self._drafts[prospect_id] = approved
        self._reviewed_by[prospect_id] = reviewer
        return approved

    def attempt_send(self, *, prospect_id: str, contact: ContactPoint) -> EmailSendResult:
        """
        把已批准草稿加入 send queue 并交给 EmailProvider。

        关键边界：V1 的具体 Provider 是 Mock；queue membership 与 dry-run 都不能表述为已发送。
        """

        draft = self._get_draft(prospect_id)
        if draft.review_status is not OutreachReviewStatus.APPROVED:
            raise ValueError("outreach_draft_not_approved")
        if not isinstance(contact, ContactPoint):
            raise ValueError("contact_point_required")
        result = self.email_provider.send(draft=draft, contact=contact)
        # Provider 返回值是最后一道结果闸门；Mock 不能以任何状态声称真实执行。
        if not isinstance(result, EmailSendResult) or not result.dry_run or result.executed:
            raise RuntimeError("external_email_execution_forbidden")
        if prospect_id not in self._send_queue:
            self._send_queue.append(prospect_id)
        return result

    def send_queue(self) -> tuple[str, ...]:
        """返回稳定的本地 send queue 快照；它不代表 Provider 已执行。"""

        return tuple(self._send_queue)

    def record_reply(self, *, prospect_id: str, reply_reference: str) -> ReplyIntakeRecord:
        """保存回复引用，不保存正文。"""

        self._get_draft(prospect_id)
        if prospect_id not in self._send_queue:
            raise ValueError("reply_requires_send_queue")
        reply = ReplyIntakeRecord.create(
            prospect_id=prospect_id,
            reply_reference=reply_reference,
        )
        self._replies.append(reply)
        return reply

    def record_feedback(
        self,
        *,
        prospect_id: str,
        outcome: FeedbackOutcome,
        evidence_refs: tuple[str, ...],
    ) -> FeedbackRecord:
        """保存带证据的反馈信号；不自动改写 Prospect 分数或业务事实。"""

        self._get_draft(prospect_id)
        if prospect_id not in self._send_queue:
            raise ValueError("feedback_requires_send_queue")
        normalized_outcome = FeedbackOutcome(outcome)
        reply_refs = {
            reply.reply_reference for reply in self._replies if reply.prospect_id == prospect_id
        }
        # positive/negative 等回复型反馈必须引用已记录的 Reply Intake；
        # 只有 no_response_observed 可以在无回复时作为观察结果进入。
        if normalized_outcome is not FeedbackOutcome.NO_RESPONSE_OBSERVED:
            if not reply_refs:
                raise ValueError("feedback_requires_reply")
            if reply_refs.isdisjoint(evidence_refs):
                raise ValueError("feedback_reply_evidence_required")
        feedback = FeedbackRecord.create(
            prospect_id=prospect_id,
            outcome=normalized_outcome,
            evidence_refs=evidence_refs,
        )
        self._feedback.append(feedback)
        return feedback

    def _get_draft(self, prospect_id: str) -> OutreachDraft:
        try:
            return self._drafts[prospect_id]
        except KeyError as exc:
            raise ValueError("outreach_draft_not_found") from exc
