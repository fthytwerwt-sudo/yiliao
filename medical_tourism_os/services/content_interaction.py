"""
用途：
承载 Phase 4 的内容与互动原型：把候选需求/产品转成 content brief、结构化草稿、
受限发布队列，以及评论/私信的风险前置 intake。

上游：
Phase 3 的 DemandSignal、ProductCandidate、RiskRouter 与 InboundWorkflow。

下游：
测试、未来本地 API 与人工 review 流程读取这里的 draft/queue/intake 结果。

边界：
这里只生成 `draft` 内容、维护受限状态机、复用匿名 lead 工作流；
不自动发布、不生成真实患者记录、不形成医疗承诺，也不保存真实联系信息。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence
from uuid import uuid4

from medical_tourism_os.adapters.base import BaseAdapter
from medical_tourism_os.adapters.mock import MockAdapter
from medical_tourism_os.config import SystemConfig
from medical_tourism_os.domain.entities import (
    AdapterResult,
    ContentBrief,
    ContentDraft,
    DemandSignal,
    FactClassification,
    ProductCandidate,
    WorkflowResult,
    _utc_now_isoformat,
)
from medical_tourism_os.services.business_core import _ensure_non_clinical_text
from medical_tourism_os.services.risk_router import RiskRouter
from medical_tourism_os.workflows.core import InboundWorkflow

_CONTENT_TYPES = (
    "video_script",
    "carousel",
    "faq",
    "seo_brief",
    "reply_candidate",
)
_ALLOWED_QUEUE_TRANSITIONS = {
    "draft": "review",
    "review": "approved",
    "approved": "queued",
}
_ALLOWED_CONTENT_CLASSIFICATIONS = {
    FactClassification.RESEARCH,
    FactClassification.FACT_CANDIDATE,
    FactClassification.INFERENCE,
    FactClassification.HYPOTHESIS,
    FactClassification.UNKNOWN,
}


def _dedupe_refs(*groups: Iterable[str]) -> tuple[str, ...]:
    """稳定去重证据 ID，避免同一候选证据在 brief 中重复出现。"""

    ordered: List[str] = []
    seen = set()
    for group in groups:
        for raw_value in group:
            value = str(raw_value).strip()
            if value and value not in seen:
                seen.add(value)
                ordered.append(value)
    return tuple(ordered)


def _ensure_safe_text(field_name: str, value: str) -> str:
    """
    作用：
    对内容层自由文本继续执行 fail-closed 校验。

    输入：
    字段名与字符串值。

    输出：
    去空白后的安全文本。

    关键边界：
    即使上游已经做过一次校验，这里仍重复检查，因为内容层会重新拼接文案；
    一旦出现临床/保证措辞，就必须在生成前阻断。
    """

    return _ensure_non_clinical_text(field_name=field_name, value=value)


def _ensure_safe_payload(value: Any, *, path: str) -> Any:
    """
    作用：
    递归检查结构化内容里的字符串字段是否越过安全边界。

    输入：
    任意 dict/list/tuple/str 结构。

    输出：
    原值本身；仅用于校验通过。

    关键边界：
    这里不清洗成另一段“看起来安全”的文本，而是直接 fail-closed，
    防止把临床/承诺文案悄悄改写后继续流转。
    """

    if isinstance(value, str):
        return _ensure_safe_text(path, value)
    if isinstance(value, dict):
        for key, item in value.items():
            _ensure_safe_payload(item, path=f"{path}.{key}")
        return value
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _ensure_safe_payload(item, path=f"{path}[{index}]")
        return value
    return value


class DraftStore:
    """
    作用：
    保存一个 Phase 4 会话内创建的内容草稿。

    输入：
    `ContentDraft` 与 draft id。

    输出：
    由同一实例内的工厂和发布队列共享的草稿视图。

    关键边界：
    这里必须是实例级 store，而不是模块全局注册表。
    原因：Phase 4 还没有正式仓储层；若使用全局内存，会让不同测试、不同 queue、
    不同未来会话彼此污染，等价于把“未审草稿”错误提升为全局可见事实。
    """

    def __init__(self) -> None:
        self._drafts: Dict[str, ContentDraft] = {}

    def save(self, draft: ContentDraft) -> ContentDraft:
        """保存或覆盖当前 store 中的草稿。"""

        self._drafts[draft.id] = draft
        return draft

    def get(self, draft_id: str) -> ContentDraft:
        """按 id 读取当前 store 中的草稿。"""

        try:
            return self._drafts[draft_id]
        except KeyError as exc:
            raise KeyError("content_draft_not_found") from exc


class ContentIntelligence:
    """
    作用：
    把候选需求信号、候选产品和证据引用整理成结构化内容 brief。

    输入：
    `DemandSignal`、`ProductCandidate`、fact refs、experiment id。

    输出：
    `ContentBrief`。

    关键边界：
    输出必须显式保留 candidate evidence 状态，不能把候选线索升级成已确认事实、
    正式报价或任何医疗承诺。
    """

    def build_brief(
        self,
        demand_signal: DemandSignal,
        product: ProductCandidate,
        fact_refs: Sequence[str],
        experiment_id: str,
    ) -> ContentBrief:
        """生成一个只面向草稿生产的结构化 brief。"""

        normalized_experiment_id = experiment_id.strip()
        if not normalized_experiment_id:
            raise ValueError("experiment_id_required")
        self._validate_candidate_input_classification(demand_signal.classification)

        normalized_theme = _ensure_safe_text("demand_theme", demand_signal.theme)
        target_segment = _ensure_safe_text("target_segment", product.target_segment)
        value_hypothesis = _ensure_safe_text("value_hypothesis", product.value_hypothesis)
        normalized_fact_refs = _dedupe_refs(fact_refs)
        candidate_evidence_ids = _dedupe_refs(
            normalized_fact_refs,
            demand_signal.evidence_ids,
            product.supply_evidence_ids,
            product.price_evidence_ids,
        )
        evidence_status = self._evidence_status(
            candidate_evidence_ids=candidate_evidence_ids,
        )
        return ContentBrief(
            id=f"brief_{uuid4().hex}",
            demand_signal_id=demand_signal.id,
            product_code=product.code,
            market=demand_signal.market.strip(),
            theme=normalized_theme,
            target_segment=target_segment,
            value_hypothesis=value_hypothesis,
            fact_refs=normalized_fact_refs,
            candidate_evidence_ids=candidate_evidence_ids,
            experiment_id=normalized_experiment_id,
            evidence_status=evidence_status,
            safety_boundary="candidate_evidence_only_human_review_required",
            created_at=_utc_now_isoformat(),
        )

    def _evidence_status(self, *, candidate_evidence_ids: tuple[str, ...]) -> str:
        if candidate_evidence_ids:
            return "candidate"
        return "pending"

    def _validate_candidate_input_classification(self, classification: FactClassification) -> None:
        """
        作用：
        拒绝一切已经被系统定义为“高于候选层”的事实等级进入内容生产。

        关键边界：
        Phase 4 只是 candidate content。若把 canonical/decision 输入直接放进内容层，
        brief 上再写 `candidate` 也只是自欺欺人，会让下游误以为这是一条已批准的外发依据。
        """

        if classification not in _ALLOWED_CONTENT_CLASSIFICATIONS:
            raise ValueError("content_candidate_inputs_only")


class ContentFactory:
    """
    作用：
    根据 brief 生成多种可人工复核的结构化草稿。

    输入：
    `ContentBrief`。

    输出：
    五种 `ContentDraft`。

    关键边界：
    所有输出固定为 `draft`，且 `publication_id` 必须为空；这里只做内容草稿，
    不产生任何真实发布动作。
    """

    def __init__(self, *, store: Optional[DraftStore] = None) -> None:
        self.store = store or DraftStore()

    def generate_drafts(self, brief: ContentBrief) -> List[ContentDraft]:
        """为一个 brief 生成 Phase 4 所需的五类草稿。"""

        payloads = {
            "video_script": self._video_script(brief),
            "carousel": self._carousel(brief),
            "faq": self._faq(brief),
            "seo_brief": self._seo_brief(brief),
            "reply_candidate": self._reply_candidate(brief),
        }
        drafts: List[ContentDraft] = []
        for content_type in _CONTENT_TYPES:
            payload = payloads[content_type]
            title = _ensure_safe_text("draft_title", payload["title"])
            content = payload["content"]
            _ensure_safe_payload(content, path=f"{content_type}.content")
            draft = ContentDraft(
                id=f"draft_{uuid4().hex}",
                brief_id=brief.id,
                content_type=content_type,
                title=title,
                content=content,
                status="draft",
                fact_refs=brief.fact_refs,
                experiment_id=brief.experiment_id,
                evidence_status=brief.evidence_status,
                publication_id=None,
                reviewed_by=None,
                created_at=_utc_now_isoformat(),
                updated_at=_utc_now_isoformat(),
            )
            drafts.append(self.store.save(draft))
        return drafts

    def _video_script(self, brief: ContentBrief) -> Dict[str, Any]:
        return {
            "title": f"Coordination outline for {brief.theme}",
            "content": {
                "format": "video_script",
                "hook": f"Question theme: {brief.theme}",
                "audience": brief.target_segment,
                "sections": (
                    f"Context: {brief.value_hypothesis}.",
                    f"Evidence status: {brief.evidence_status}; refs: {', '.join(brief.fact_refs) or 'pending'}.",
                    "Boundary: candidate evidence only; human review required before any outbound use.",
                ),
                "cta": "Invite a general coordination question for human review.",
            },
        }

    def _carousel(self, brief: ContentBrief) -> Dict[str, Any]:
        return {
            "title": f"Carousel candidate for {brief.product_code}",
            "content": {
                "format": "carousel",
                "slides": (
                    {
                        "headline": f"Theme: {brief.theme}",
                        "body": "Keep the discussion on coordination and evidence review.",
                    },
                    {
                        "headline": f"Candidate fit: {brief.target_segment}",
                        "body": f"Value hypothesis: {brief.value_hypothesis}.",
                    },
                    {
                        "headline": "Evidence boundary",
                        "body": f"Status: {brief.evidence_status}; refs: {', '.join(brief.fact_refs) or 'pending'}.",
                    },
                ),
            },
        }

    def _faq(self, brief: ContentBrief) -> Dict[str, Any]:
        return {
            "title": f"FAQ draft for {brief.theme}",
            "content": {
                "format": "faq",
                "pairs": (
                    {
                        "question": f"What coordination issue does {brief.product_code} explore?",
                        "answer": brief.value_hypothesis,
                    },
                    {
                        "question": "What evidence can this draft cite right now?",
                        "answer": f"Only candidate refs: {', '.join(brief.fact_refs) or 'pending'}",
                    },
                    {
                        "question": "What must happen before any outbound use?",
                        "answer": "A named human review must confirm the draft and its evidence boundary.",
                    },
                ),
            },
        }

    def _seo_brief(self, brief: ContentBrief) -> Dict[str, Any]:
        return {
            "title": f"SEO brief candidate for {brief.theme}",
            "content": {
                "format": "seo_brief",
                "primary_topic": brief.theme,
                "supporting_points": (
                    brief.value_hypothesis,
                    f"Audience: {brief.target_segment}",
                    f"Evidence status: {brief.evidence_status}",
                ),
                "meta_description": "Candidate coordination brief pending human review and evidence confirmation.",
            },
        }

    def _reply_candidate(self, brief: ContentBrief) -> Dict[str, Any]:
        return {
            "title": f"Reply candidate for {brief.theme}",
            "content": {
                "format": "reply_candidate",
                "reply_text": (
                    f"We can log your coordination question under experiment {brief.experiment_id} "
                    "and route it for human review."
                ),
                "boundary_note": "This reply is a draft and may only cite candidate evidence references.",
            },
        }


class PublishingQueue:
    """
    作用：
    管理内容草稿的人工 review 与受限发布状态机。

    输入：
    Draft id、reviewer 名称、本地配置与 adapter。

    输出：
    更新后的 `ContentDraft` 状态，或一次 `AdapterResult`。

    关键边界：
    这里只允许 `draft -> review -> approved -> queued`；
    `attempt_publish()` 在 Phase 4 永远是 dry-run，占位验证队列状态，但不触发真实发布。
    """

    def __init__(
        self,
        *,
        store: Optional[DraftStore] = None,
        adapter: Optional[BaseAdapter] = None,
        config: Optional[SystemConfig] = None,
    ) -> None:
        self.store = store or DraftStore()
        self.adapter = adapter or MockAdapter(enabled=False)
        self.config = config or SystemConfig.default()

    def get(self, draft_id: str) -> ContentDraft:
        """返回当前草稿状态。"""

        return self.store.get(draft_id)

    def submit_for_review(self, draft_id: str) -> ContentDraft:
        """把草稿推进到 review。"""

        return self._transition(draft_id, expected="draft", target="review")

    def approve(self, draft_id: str, *, reviewed_by: str) -> ContentDraft:
        """
        作用：
        只有具名 human reviewer 才能把草稿从 review 推进到 approved。

        关键边界：
        reviewer 为空时必须 fail-closed；不能出现“系统自动审批”或匿名审批。
        """

        reviewer_name = reviewed_by.strip()
        if not reviewer_name:
            raise ValueError("named_human_reviewer_required")
        draft = self._transition(draft_id, expected="review", target="approved")
        updated = draft.with_updates(reviewed_by=reviewer_name)
        return self.store.save(updated)

    def enqueue(self, draft_id: str) -> ContentDraft:
        """把已批准草稿推进到 queued，等待显式 publish 尝试。"""

        return self._transition(draft_id, expected="approved", target="queued")

    def attempt_publish(self, draft_id: str) -> AdapterResult:
        """
        作用：
        对一个已 queued 的草稿发起受限 publish 尝试。

        输入：
        draft id。

        输出：
        `AdapterResult`。

        关键边界：
        只有队列态才能尝试 publish；若权限未放开或 adapter 关闭，结果必须是 dry-run，
        草稿仍保留在 `queued`，不能伪装成已发布。
        """

        draft = self.store.get(draft_id)
        if draft.status != "queued":
            raise ValueError("publish_requires_queued_status")

        # Phase 4 的 publish 仍是制度化 dry-run：即使调用者把 config 和 adapter 人为打开，
        # 也不能真的触发 adapter 分支。原因是当前阶段只允许验证“队列是否准备好”，
        # 不允许验证“真实对外发布是否成功”，否则会把未获授权的未来能力提前变成当前行为。
        return AdapterResult(
            dry_run=True,
            executed=False,
            reason="phase4_publish_dry_run_only",
            payload={
                "draft_id": draft.id,
                "content_type": draft.content_type,
                "status": draft.status,
            },
        )

    def _transition(self, draft_id: str, *, expected: str, target: str) -> ContentDraft:
        draft = self.store.get(draft_id)
        allowed_target = _ALLOWED_QUEUE_TRANSITIONS.get(draft.status)
        if draft.status != expected or allowed_target != target:
            raise ValueError("invalid_status_transition")
        updated = draft.with_updates(status=target)
        return self.store.save(updated)


class CommentIntake:
    """
    作用：
    处理公开评论入口，先风控再匿名 lead。

    输入：
    RiskRouter、来源和 contact reference。

    输出：
    `WorkflowResult`。

    关键边界：
    高风险评论不能创建 CRM lead；安全评论也只输出匿名 lead，不保存原始联系信息。
    """

    def __init__(
        self,
        *,
        risk_router: RiskRouter,
        allowed_channel_codes: tuple[str, ...] = (),
    ) -> None:
        self.workflow = InboundWorkflow(
            risk_router=risk_router,
            allowed_channel_codes=allowed_channel_codes,
        )

    def ingest(
        self,
        *,
        text: str,
        source: str,
        contact_reference: str,
        consent_status: str = "unknown",
    ) -> WorkflowResult:
        """把评论入口转成统一的 inbound workflow 调用。"""

        return self.workflow.process(
            text=text,
            source=source,
            contact_reference=contact_reference,
            consent_status=consent_status,
            intent="comment_inbound",
        )


class DirectMessageIntake:
    """
    作用：
    处理私信入口，复用同一套风险优先与匿名 lead 逻辑。

    输入：
    RiskRouter、来源和 contact reference。

    输出：
    `WorkflowResult`。

    关键边界：
    私信不因为“更私密”就放宽规则；一旦命中诊断、支付、隐私等高风险文本，
    仍必须先阻断，不能创建 lead。
    """

    def __init__(
        self,
        *,
        risk_router: RiskRouter,
        allowed_channel_codes: tuple[str, ...] = (),
    ) -> None:
        self.workflow = InboundWorkflow(
            risk_router=risk_router,
            allowed_channel_codes=allowed_channel_codes,
        )

    def ingest(
        self,
        *,
        text: str,
        source: str,
        contact_reference: str,
        consent_status: str = "unknown",
    ) -> WorkflowResult:
        """把 DM 入口转成统一的 inbound workflow 调用。"""

        return self.workflow.process(
            text=text,
            source=source,
            contact_reference=contact_reference,
            consent_status=consent_status,
            intent="dm_inbound",
        )
