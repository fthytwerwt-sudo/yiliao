"""
用途：
编排 Phase 3 的 inbound 入口：先风险路由，再生成安全匿名 lead，并可选接上配置化评分。

上游：
测试、CLI 和未来本地接口把外部自由文本入口交给这里。

下游：
返回 `WorkflowResult`，供 CRM 候选层或人工 review 队列消费。

边界：
这里不落高风险原文、不创建患者记录、不跳过 Phase 2 gate，也不做医疗推荐。
"""

from __future__ import annotations

from typing import Optional

from medical_tourism_os.domain.entities import WorkflowResult
from medical_tourism_os.services.business_core import LeadScorer, build_anonymous_lead
from medical_tourism_os.services.risk_router import RiskRouter


class InboundWorkflow:
    """
    作用：
    处理最早期入站文本，把高风险阻断和匿名候选 lead 创建串起来。

    输入：
    风险路由器与可选线索评分器。

    输出：
    `WorkflowResult`。

    关键边界：
    风险 blocked 时绝不创建 anonymous lead；只有安全合成后的非敏感字段才允许进入 lead。
    """

    def __init__(
        self,
        *,
        risk_router: RiskRouter,
        lead_scorer: Optional[LeadScorer] = None,
        allowed_channel_codes: tuple[str, ...] = (),
    ) -> None:
        self.risk_router = risk_router
        self.lead_scorer = lead_scorer
        self.allowed_channel_codes = tuple(item.strip() for item in allowed_channel_codes if item.strip())

    def process(
        self,
        *,
        text: str,
        source: str,
        contact_reference: str,
        consent_status: str = "unknown",
        intent: str = "unknown",
    ) -> WorkflowResult:
        """
        作用：
        处理一次 inbound 输入。

        输入：
        自由文本、来源、联系引用、可选 consent 与 intent。

        输出：
        `WorkflowResult`。

        关键边界：
        先路由风险再做任何 lead 动作，是为了防止 PHI/诊断/支付文本先写入 CRM 再清洗。
        """

        risk_decision = self.risk_router.route(text)
        if risk_decision.blocked:
            return WorkflowResult(
                blocked=True,
                category=risk_decision.category,
                action=risk_decision.action,
                lead=None,
                scorecard=None,
                safe_summary=risk_decision.safe_summary,
            )

        try:
            lead = build_anonymous_lead(
                contact_reference=contact_reference,
                source=source,
                consent_status=consent_status,
                allowed_channel_codes=self.allowed_channel_codes,
            )
        except ValueError as exc:
            # contact_reference/source 是另一条可能绕过正文风险路由的输入通道；
            # 一旦发现像邮箱、电话、handle 或非受限 channel code，必须直接阻断。
            safe_summary = dict(risk_decision.safe_summary)
            safe_summary.update(
                {
                    "blocked_field": "contact_or_source",
                    "reason_code": str(exc),
                }
            )
            return WorkflowResult(
                blocked=True,
                category="privacy",
                action="fail_closed",
                lead=None,
                scorecard=None,
                safe_summary=safe_summary,
            )
        scorecard = None
        if self.lead_scorer is not None:
            # 评分读取的是匿名 lead 结果和通用运营字段，而不是原始自由文本。
            scorecard = self.lead_scorer.score(
                anonymous_lead_id=lead.anonymous_lead_id,
                contact_reference=lead.contact_reference,
                source=lead.source,
                consent_status=lead.consent_status,
                intent=intent,
            )
        safe_summary = dict(risk_decision.safe_summary)
        safe_summary["lead_created"] = True
        return WorkflowResult(
            blocked=False,
            category=risk_decision.category,
            action="candidate_created",
            lead=lead,
            scorecard=scorecard,
            safe_summary=safe_summary,
        )
