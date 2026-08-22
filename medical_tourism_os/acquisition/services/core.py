"""
用途：
把 Business Entity 候选转换为分类、B2B Prospect 评分和待人工审核的 Outreach Draft。

上游：
Discovery Workflow 传入目录候选和显式五维评分；Outreach Workflow 传入 Prospect。

下游：
Prospect queue 与 Human Review queue 使用本文件的稳定领域输出。

边界：
分类只是候选归类；评分只读调用方提供的证据化维度；草稿不发送、不形成医疗承诺。
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from medical_tourism_os.acquisition.domain import (
    BusinessCategory,
    BusinessEntity,
    BusinessEntityStatus,
    OutreachDraft,
    OutreachReviewStatus,
    Prospect,
    ProspectPriority,
    ProspectStatus,
)
from medical_tourism_os.acquisition.schemas import ProspectScoreDimensions


_CATEGORY_KEYWORDS = (
    (BusinessCategory.TRAVEL_AGENCY, ("travel", "tour", "agency")),
    (BusinessCategory.COMMUNITY, ("community", "association", "cultural group")),
    (BusinessCategory.INSURANCE, ("insurance", "benefits", "coverage")),
    (BusinessCategory.HEALTH_SERVICE, ("health service", "wellness", "care coordination")),
)


class BusinessClassifier:
    """用显式类别或可审计关键词形成初步企业分类。"""

    def classify(self, entity: BusinessEntity) -> BusinessEntity:
        """
        输出 classified 候选。

        关键边界：关键词命中只是分类候选，不证明企业事实；UNKNOWN 会被保留而不是强行猜测。
        """

        category = entity.category
        if category is BusinessCategory.UNKNOWN:
            haystack = " ".join((entity.company_name, entity.description)).casefold()
            for candidate, keywords in _CATEGORY_KEYWORDS:
                if any(keyword in haystack for keyword in keywords):
                    category = candidate
                    break
        return replace(entity, category=category, status=BusinessEntityStatus.CLASSIFIED)


class ProspectScorer:
    """独立计算 B2B 合作 fit score；绝不复用 LeadScorer。"""

    _DIMENSION_NAMES = (
        "category_fit",
        "market_fit",
        "audience_overlap",
        "contact_quality",
        "partnership_probability",
    )

    def score(
        self,
        business_entity_id: str,
        dimensions: ProspectScoreDimensions,
    ) -> Prospect:
        """
        对五个 0–100 维度等权评分，并选择人工复核/outreach/hold 队列。

        关键边界：没有 evidence refs 时，无论数值为何都必须 hold，避免无来源分数触发触达。
        """

        entity_id = business_entity_id.strip()
        if not entity_id:
            raise ValueError("business_entity_id_required")
        values = tuple(int(getattr(dimensions, name)) for name in self._DIMENSION_NAMES)
        fit_score = sum(values) // len(values)
        reason_codes = tuple(
            f"{name}={value}" for name, value in zip(self._DIMENSION_NAMES, values)
        )

        if fit_score >= 75:
            priority = ProspectPriority.HIGH
        elif fit_score >= 50:
            priority = ProspectPriority.MEDIUM
        else:
            priority = ProspectPriority.LOW

        # evidence_refs（评分证据引用）是队列推进前提；分数不能代替来源证明。
        if not dimensions.evidence_refs:
            status = ProspectStatus.HOLD_FOR_MORE_EVIDENCE
            reason_codes = reason_codes + ("missing_score_evidence",)
        elif priority is ProspectPriority.HIGH:
            status = ProspectStatus.OUTREACH_QUEUE
        elif priority is ProspectPriority.MEDIUM:
            status = ProspectStatus.HUMAN_REVIEW_QUEUE
        else:
            status = ProspectStatus.HOLD_FOR_MORE_EVIDENCE

        return Prospect(
            id=f"prospect_{uuid4().hex}",
            business_entity_id=entity_id,
            fit_score=fit_score,
            priority=priority,
            reason_codes=reason_codes,
            status=status,
        )


class OutreachGenerator:
    """把企业证据和 Prospect 转为明确“未发送”的人工审核邮件草稿。"""

    def generate(self, entity: BusinessEntity, prospect: Prospect) -> OutreachDraft:
        """
        生成包含联系原因、合作假设和可验证价值的草稿。

        关键边界：只引用领域对象已有信息，不补写患者、临床能力、价格、合作承诺或结果。
        """

        if prospect.business_entity_id != entity.id:
            raise ValueError("prospect_business_entity_mismatch")
        personalization_reason = (
            f"{entity.company_name} is classified as {entity.category.value} "
            f"in {entity.location}, based on supplied public evidence references."
        )
        body = (
            f"Hello {entity.company_name} team,\n\n"
            f"Why we are contacting you: {personalization_reason}\n\n"
            "Partnership hypothesis: We could jointly test whether clear, public, non-clinical "
            "coordination information is useful to the audience you serve.\n\n"
            "Verifiable value: Start with a small human-reviewed pilot, agree on observable "
            "metrics in advance, and use no patient data or clinical claims.\n\n"
            "Human review required: This is a draft and has not been sent."
        )
        return OutreachDraft(
            prospect_id=prospect.id,
            subject=f"Exploring a verifiable coordination pilot with {entity.company_name}",
            body=body,
            personalization_reason=personalization_reason,
            review_status=OutreachReviewStatus.PENDING,
        )
