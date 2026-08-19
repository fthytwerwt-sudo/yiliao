"""
用途：
承载 Phase 3 的业务核心原型：Demand Radar、Product Catalog、Lead Scoring、Product Matching
以及与 Phase 2 Canonical gate 对接的人审边界。

上游：
workflow、测试和未来本地 API 把已脱敏的非临床输入交给这里。

下游：
返回匿名候选 lead、候选产品、需求聚类与 candidate match，供人工复核与后续编排使用。

边界：
这里不生成正式价格、不形成医疗建议、不创建 canonical fact，也不接触真实国家/平台/医院/医生。
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Dict, Iterable, List, Mapping, Optional, Sequence
from uuid import uuid4

from medical_tourism_os.domain.entities import (
    AnonymousLead,
    DemandCluster,
    DemandSignal,
    FactClassification,
    LeadScoreCard,
    ProductCandidate,
    ProductMatch,
    _utc_now_isoformat,
)


def _normalize_phrase(value: str) -> str:
    """统一短语格式，确保聚类与匹配不受大小写和多空格干扰。"""

    return " ".join(value.strip().lower().split())


_UNSAFE_OFFER_OR_CLINICAL_PATTERNS = (
    re.compile(r"\bguarantee\b"),
    re.compile(r"\bcure\b"),
    re.compile(r"(?<!non-)\bclinical\b"),
    re.compile(r"\bdiagnos"),
    re.compile(r"\btreatment\b"),
    re.compile(r"\bmedication\b"),
    re.compile(r"保证"),
    re.compile(r"治愈"),
    re.compile(r"临床"),
    re.compile(r"诊断"),
    re.compile(r"治疗"),
    re.compile(r"用药"),
)
_CONTACT_VALUE_PATTERNS = (
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
    re.compile(r"\+?\d[\d\s-]{7,}\d"),
    re.compile(r"\bemail\b", re.IGNORECASE),
    re.compile(r"\bphone\b", re.IGNORECASE),
    re.compile(r"\bmobile\b", re.IGNORECASE),
    re.compile(r"\btelegram\b", re.IGNORECASE),
    re.compile(r"\bline(?:\s+id)?\b", re.IGNORECASE),
    re.compile(r"\bqq\b", re.IGNORECASE),
    re.compile(r"\bwechat\b", re.IGNORECASE),
    re.compile(r"\bwhatsapp\b", re.IGNORECASE),
    re.compile(r"微信"),
    re.compile(r"邮箱"),
    re.compile(r"电话"),
    re.compile(r"手机"),
    re.compile(r"护照"),
    re.compile(r"passport", re.IGNORECASE),
    re.compile(r"身份证"),
    re.compile(r"\bid\b", re.IGNORECASE),
)
_SAFE_CHANNEL_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_SAFE_OPAQUE_REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,64}$")
_TOKENIZED_CONTACT_REFERENCE_PATTERN = re.compile(r"^contact_ref_[a-f0-9]{20}$")
_TEST_CHANNEL_PREFIX = "TEST_"
_DISALLOWED_CHANNEL_CODES = {"EMAIL", "PHONE", "MOBILE", "TELEGRAM", "LINE", "QQ", "WECHAT", "WHATSAPP"}


def _ensure_non_clinical_text(*, field_name: str, value: str) -> str:
    """
    作用：
    拒绝任何带临床判断或结果保证措辞的自由文本。

    输入：
    字段名和原始字符串。

    输出：
    清理后的原始字符串。

    关键边界：
    这些字段后续会进入候选库或匹配链路，因此必须先 fail-closed，
    避免“只是候选文本”逐步演化成医疗承诺。
    """

    normalized = value.strip()
    lowered = normalized.lower()
    for pattern in _UNSAFE_OFFER_OR_CLINICAL_PATTERNS:
        if pattern.search(lowered) or pattern.search(normalized):
            raise ValueError(f"{field_name}_contains_clinical_or_guarantee_language")
    return normalized


def tokenize_contact_reference(contact_reference: str) -> str:
    """
    作用：
    把已确认安全的 opaque reference 变成不可逆 token。

    输入：
    不含邮箱/电话/证件/IM handle 的中性引用码。

    输出：
    `contact_ref_` 前缀的哈希 token。

    关键边界：
    即使上游给了“看起来安全”的引用，也不直接保存原文，防止未来与外部系统拼接后反推个人身份。
    """

    normalized = contact_reference.strip()
    if not normalized:
        raise ValueError("contact_reference_required")
    if _TOKENIZED_CONTACT_REFERENCE_PATTERN.fullmatch(normalized):
        # LeadScorer 是公共 API，可能既接收 workflow 新生成的 token，
        # 也接收上游已经保存过的 lead。这里必须幂等，避免重复哈希导致同一线索断链。
        return normalized
    if any(pattern.search(normalized) for pattern in _CONTACT_VALUE_PATTERNS):
        raise ValueError("contact_reference_contains_pii")
    if not _SAFE_OPAQUE_REFERENCE_PATTERN.fullmatch(normalized):
        raise ValueError("contact_reference_must_be_safe_opaque_code")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]
    return f"contact_ref_{digest}"


def validate_source_channel_code(
    source: str,
    allowed_channel_codes: Sequence[str] = (),
) -> str:
    """
    作用：
    约束 Phase 3 只保存受限安全 channel code，而不是外部账号句柄。

    输入：
    上游传入的 source。

    输出：
    合法的 channel code。

    关键边界：
    这里要求 source 是受限代码格式，是因为 raw chat ID / handle 一旦进入 lead，
    会绕过风险路由成为另一条 PII 泄漏通道。
    """

    normalized = source.strip()
    if not normalized:
        raise ValueError("source_required")
    if any(pattern.search(normalized) for pattern in _CONTACT_VALUE_PATTERNS):
        raise ValueError("source_contains_contact_value")
    if not _SAFE_CHANNEL_CODE_PATTERN.fullmatch(normalized):
        raise ValueError("source_must_be_safe_channel_code")
    if normalized in _DISALLOWED_CHANNEL_CODES:
        raise ValueError("source_uses_contact_hint_keyword")
    normalized_allowlist = tuple(item.strip() for item in allowed_channel_codes if item.strip())
    if normalized.startswith(_TEST_CHANNEL_PREFIX):
        return normalized
    if normalized_allowlist and normalized in normalized_allowlist:
        return normalized
    raise ValueError("source_requires_explicit_allowlist")
    return normalized


def _normalize_tokens(value: str) -> tuple[str, ...]:
    """
    作用：
    将自由文本压成通用 token 集合，供非临床匹配与主题聚类使用。

    输入：
    任意短文本。

    输出：
    去噪后的 token 元组。

    关键边界：
    这里只做通用字符串处理，不推断国家、平台、科室或治疗类型。
    """

    tokens = re.findall(r"[a-z0-9_]+", value.lower())
    stopwords = {"a", "an", "and", "for", "has", "have", "is", "of", "the", "to"}
    return tuple(token for token in tokens if token not in stopwords)


@dataclass(frozen=True)
class HumanReviewDecision:
    """
    作用：
    表示业务核心对 Phase 2 人工 gate 的调用结果。

    输入：
    candidate_fact_id、reviewer 与 canonical classification。

    输出：
    供上游确认“这次确实经过了 Canonical 门”的轻量结果。

    关键边界：
    这里不自造批准逻辑，只转发到 `DataGovernanceService.approve_fact`。
    """

    candidate_fact_id: str
    reviewed_by: str
    resulting_classification: str


class DemandRadar:
    """
    作用：
    收集需求信号并按主题/维度做基础聚类。

    输入：
    市场、主题、evidence IDs、分类与可选维度。

    输出：
    `DemandSignal` 与 `DemandCluster`。

    关键边界：
    聚类结果只反映“有哪些相似信号”，不能被当作 confirmed fact。
    """

    def __init__(self) -> None:
        self._signals: List[DemandSignal] = []

    def record_signal(
        self,
        *,
        market: str,
        theme: str,
        evidence_ids: Sequence[str],
        classification: FactClassification,
        dimensions: Sequence[str] = (),
    ) -> DemandSignal:
        """
        作用：
        记录一条需求信号。

        输入：
        通用市场标识、主题、证据 ID、分类和维度。

        输出：
        新创建的 `DemandSignal`。

        关键边界：
        这里保留原 classification，不自动升级为 `CANONICAL_FACT`。
        """

        normalized_theme = _normalize_phrase(theme)
        normalized_dimensions = tuple(sorted(_normalize_phrase(item) for item in dimensions if item.strip()))
        signal = DemandSignal(
            id=f"signal_{uuid4().hex}",
            market=market.strip(),
            theme=normalized_theme,
            cluster_key="::".join((market.strip(), normalized_theme, "|".join(normalized_dimensions))),
            evidence_ids=tuple(dict.fromkeys(item.strip() for item in evidence_ids if item.strip())),
            classification=classification,
            dimensions=normalized_dimensions,
            created_at=_utc_now_isoformat(),
        )
        self._signals.append(signal)
        return signal

    def cluster_signals(self) -> List[DemandCluster]:
        """
        作用：
        输出当前所有需求信号的主题/维度聚类。

        输入：
        无。

        输出：
        `DemandCluster` 列表，按 signal_count 倒序、theme 升序稳定排序。

        关键边界：
        即使多个信号被聚到一起，也只保留 evidence_ids 与 classifications，
        以提醒调用者它们依然是“证据中的模式”，不是已判定事实。
        """

        buckets: Dict[str, List[DemandSignal]] = {}
        for signal in self._signals:
            buckets.setdefault(signal.cluster_key, []).append(signal)

        clusters: List[DemandCluster] = []
        for cluster_key, signals in buckets.items():
            evidence_ids: List[str] = []
            seen_evidence = set()
            for signal in signals:
                for evidence_id in signal.evidence_ids:
                    if evidence_id not in seen_evidence:
                        seen_evidence.add(evidence_id)
                        evidence_ids.append(evidence_id)
            clusters.append(
                DemandCluster(
                    cluster_key=cluster_key,
                    market=signals[0].market,
                    theme=signals[0].theme,
                    dimensions=signals[0].dimensions,
                    signal_ids=tuple(signal.id for signal in signals),
                    evidence_ids=tuple(evidence_ids),
                    classifications=tuple(signal.classification for signal in signals),
                    signal_count=len(signals),
                )
            )
        return sorted(clusters, key=lambda item: (-item.signal_count, item.theme, item.market))


class ProductCatalog:
    """
    作用：
    管理待验证的产品候选。

    输入：
    目标分群、价值假设、requirements、供给/价格证据和风险。

    输出：
    `ProductCandidate`。

    关键边界：
    所有候选固定处于 `hypothesis`；供给和价格证据只能说明“有待核验的依据”，
    不能直接形成正式报价或对外承诺。
    """

    def __init__(self) -> None:
        self._products: List[ProductCandidate] = []

    def create_candidate(
        self,
        *,
        code: str,
        target_segment: str,
        value_hypothesis: str,
        requirements: Sequence[str],
        supply_evidence_ids: Sequence[str],
        price_evidence_ids: Sequence[str],
        risks: Sequence[str],
    ) -> ProductCandidate:
        """创建并保存一个产品候选。"""

        candidate = ProductCandidate(
            code=code.strip(),
            target_segment=_ensure_non_clinical_text(
                field_name="target_segment",
                value=target_segment,
            ),
            value_hypothesis=_ensure_non_clinical_text(
                field_name="value_hypothesis",
                value=value_hypothesis,
            ),
            requirements=tuple(item.strip() for item in requirements if item.strip()),
            supply_evidence_ids=tuple(item.strip() for item in supply_evidence_ids if item.strip()),
            price_evidence_ids=tuple(item.strip() for item in price_evidence_ids if item.strip()),
            risks=tuple(item.strip() for item in risks if item.strip()),
            status="hypothesis",
            created_at=_utc_now_isoformat(),
        )
        self._products.append(candidate)
        return candidate

    def list_candidates(self) -> List[ProductCandidate]:
        """返回当前内存中的候选产品。"""

        return list(self._products)


class LeadScorer:
    """
    作用：
    对匿名线索做完全配置化的运营优先级评分。

    输入：
    权重、可选 value_scores、band_thresholds 与 next_action_map。

    输出：
    `LeadScoreCard`。

    关键边界：
    评分只基于通用运营字段，不根据国家、平台、医疗服务类型硬编码规则。
    """

    def __init__(
        self,
        *,
        weights: Mapping[str, int],
        value_scores: Optional[Mapping[str, Mapping[str, float]]] = None,
        band_thresholds: Optional[Mapping[str, int]] = None,
        next_action_map: Optional[Mapping[str, str]] = None,
        allowed_channel_codes: Sequence[str] = (),
    ) -> None:
        self.weights = dict(weights)
        self.allowed_channel_codes = tuple(item.strip() for item in allowed_channel_codes if item.strip())
        self.value_scores = {
            "consent": {
                "granted": 1.0,
                "provided": 1.0,
                "yes": 1.0,
                "unknown": 0.0,
                "withdrawn": 0.0,
                "denied": 0.0,
            },
            "intent": {
                "high": 1.0,
                "medium": 2.0 / 3.0,
                "low": 1.0 / 3.0,
                "unknown": 0.0,
            },
        }
        if value_scores:
            for field_name, mapping in value_scores.items():
                self.value_scores[field_name] = dict(mapping)
        self.band_thresholds = {"high": 8, "medium": 4}
        if band_thresholds:
            self.band_thresholds.update({key: int(value) for key, value in band_thresholds.items()})
        self.next_action_map = {
            "high": "human_review_queue",
            "medium": "nurture_queue",
            "low": "hold_for_more_evidence",
        }
        if next_action_map:
            self.next_action_map.update(dict(next_action_map))

    def score(
        self,
        *,
        anonymous_lead_id: str,
        contact_reference: str,
        source: str,
        consent_status: str,
        intent: str,
    ) -> LeadScoreCard:
        """
        作用：
        计算匿名线索分数与建议动作。

        输入：
        匿名线索标识、联系引用、来源、同意状态与意图等级。

        输出：
        `LeadScoreCard`。

        关键边界：
        输出不包含 patient/diagnosis/clinical record 等字段；即使调用者持有这些内容，
        评分卡也不会接收或回写它们。
        """

        safe_contact_reference = tokenize_contact_reference(contact_reference)
        safe_source = validate_source_channel_code(
            source,
            allowed_channel_codes=self.allowed_channel_codes,
        )
        features = {
            "consent": _normalize_phrase(consent_status or "unknown"),
            "contact_reference": safe_contact_reference,
            "source": safe_source,
            "intent": _normalize_phrase(intent or "unknown"),
        }
        total = 0
        reason_codes: List[str] = []
        for field_name, weight in self.weights.items():
            raw_value = features.get(field_name, "")
            if not raw_value:
                reason_codes.append(f"{field_name}_missing")
                continue
            mapping = self.value_scores.get(field_name)
            if mapping is None:
                total += int(weight)
                reason_codes.append(f"{field_name}_present")
                continue
            multiplier = float(mapping.get(raw_value, mapping.get("*", 0.0)))
            contribution = int(round(weight * multiplier))
            total += contribution
            reason_codes.append(f"{field_name}_{raw_value}")

        band = self._band_for_score(total)
        next_action = self.next_action_map[band]
        if features["consent"] not in {"granted", "provided", "yes"}:
            # 未获得明确 consent 时不允许进入积极跟进动作，避免运营流程超越授权边界。
            next_action = "manual_consent_check"

        return LeadScoreCard(
            anonymous_lead_id=anonymous_lead_id,
            contact_reference=features["contact_reference"],
            source=features["source"],
            status="scored",
            consent_status=features["consent"],
            next_action=next_action,
            score=total,
            band=band,
            reason_codes=tuple(reason_codes),
        )

    def _band_for_score(self, score: int) -> str:
        if score >= int(self.band_thresholds["high"]):
            return "high"
        if score >= int(self.band_thresholds["medium"]):
            return "medium"
        return "low"


class ProductMatcher:
    """
    作用：
    根据非临床目标和候选产品条件，给出可人工复核的 candidate match。

    输入：
    非临床 goal/region/time/channel/evidence status 与产品候选列表。

    输出：
    `ProductMatch` 列表。

    关键边界：
    匹配结果只表达“可能适合进一步人工评估的候选”；它不是医疗推荐，
    缺证据或存在风险信号时必须降级为不输出匹配。
    """

    def match(
        self,
        *,
        non_clinical_goal: str,
        region: str,
        time_window: str,
        channel: str,
        evidence_status: str,
        products: Iterable[ProductCandidate],
    ) -> List[ProductMatch]:
        """执行非临床候选匹配。"""

        normalized_goal = _normalize_phrase(non_clinical_goal)
        _ensure_non_clinical_text(
            field_name="non_clinical_goal",
            value=non_clinical_goal,
        )
        input_signals = self._build_input_signals(
            region=region,
            time_window=time_window,
            channel=channel,
            evidence_status=evidence_status,
            non_clinical_goal=normalized_goal,
        )
        matches: List[ProductMatch] = []
        for product in products:
            if product.status != "hypothesis":
                continue
            if not product.supply_evidence_ids:
                # 没有供给证据就连候选层都不应继续，避免凭空推荐。
                continue
            if product.risks:
                # 一旦候选自带风险标记，必须回到人工 review，而不是自动匹配。
                continue
            if input_signals["evidence_status"] not in {"candidate", "canonical"}:
                continue

            matched_requirements = tuple(
                requirement for requirement in product.requirements if requirement in input_signals["flags"]
            )
            missing_requirements = tuple(
                requirement for requirement in product.requirements if requirement not in input_signals["flags"]
            )
            if missing_requirements:
                continue
            if not self._goal_matches(normalized_goal, product.value_hypothesis):
                continue

            reason_codes = ["supply_evidence_present", f"evidence_status_{input_signals['evidence_status']}"]
            if not product.price_evidence_ids:
                # 价格证据缺失时仍可保留 candidate_match，但必须显式表明不能当正式报价。
                reason_codes.append("price_evidence_pending")
            matches.append(
                ProductMatch(
                    product_code=product.code,
                    target_segment=product.target_segment,
                    status="candidate_match",
                    safety_boundary="not_a_medical_recommendation",
                    evidence_status=input_signals["evidence_status"],
                    matched_requirements=matched_requirements,
                    missing_requirements=missing_requirements,
                    reason_codes=tuple(reason_codes),
                )
            )
        return matches

    def _build_input_signals(
        self,
        *,
        region: str,
        time_window: str,
        channel: str,
        evidence_status: str,
        non_clinical_goal: str,
    ) -> Dict[str, object]:
        flags = set()
        if region.strip():
            flags.add("region_known")
        if time_window.strip():
            flags.add("time_window_known")
        if channel.strip():
            flags.add("channel_known")
        if non_clinical_goal:
            flags.add("goal_stated")
        return {
            "flags": flags,
            "evidence_status": _normalize_phrase(evidence_status),
        }

    def _goal_matches(self, non_clinical_goal: str, value_hypothesis: str) -> bool:
        goal_tokens = set(_normalize_tokens(non_clinical_goal))
        hypothesis_tokens = set(_normalize_tokens(value_hypothesis))
        if not goal_tokens or not hypothesis_tokens:
            return False
        return bool(goal_tokens & hypothesis_tokens)


class HumanReviewCoordinator:
    """
    作用：
    把 Phase 3 的“需要升级为正式事实”动作显式委托给 Phase 2 gate。

    输入：
    一个提供 `approve_fact(record_id, reviewed_by)` 的治理服务。

    输出：
    `HumanReviewDecision`。

    关键边界：
    这里绝不自己改 classification；所有 canonical promotion 都必须经过 Phase 2。
    """

    def promote_candidate_fact(
        self,
        *,
        governance_service: object,
        candidate_fact_id: str,
        reviewed_by: str,
    ) -> HumanReviewDecision:
        """调用 Phase 2 `approve_fact`，避免业务核心绕过 Canonical 门。"""

        approved_record = governance_service.approve_fact(candidate_fact_id, reviewed_by=reviewed_by)
        return HumanReviewDecision(
            candidate_fact_id=approved_record.id,
            reviewed_by=reviewed_by.strip(),
            resulting_classification=approved_record.classification.value,
        )


def build_anonymous_lead(
    *,
    contact_reference: str,
    source: str,
    consent_status: str = "unknown",
    allowed_channel_codes: Sequence[str] = (),
) -> AnonymousLead:
    """
    作用：
    生成匿名 lead。

    输入：
    联系引用、来源与 consent 状态。

    输出：
    `AnonymousLead`。

    关键边界：
    这里只接受已经通过风险清洗的非敏感字段，避免把自由文本直接塞进 CRM 候选层。
    """

    normalized_consent = _normalize_phrase(consent_status or "unknown")
    safe_contact_reference = tokenize_contact_reference(contact_reference)
    safe_source = validate_source_channel_code(
        source,
        allowed_channel_codes=allowed_channel_codes,
    )
    next_action = "manual_consent_check"
    if normalized_consent in {"granted", "provided", "yes"}:
        next_action = "human_review_queue"
    return AnonymousLead(
        anonymous_lead_id=f"lead_{uuid4().hex}",
        contact_reference=safe_contact_reference,
        source=safe_source,
        status="anonymous",
        consent_status=normalized_consent,
        next_action=next_action,
        created_at=_utc_now_isoformat(),
    )
