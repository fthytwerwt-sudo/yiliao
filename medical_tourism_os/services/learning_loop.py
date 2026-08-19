"""
用途：
承载 Phase 5 的学习闭环原型：记录指标、创建实验、生成周复盘、形成 decision candidate
以及导出 GitHub dry-run 预览。

上游：
CLI、本地 API、synthetic E2E 和测试把匿名运营信号交给这里。

下游：
返回结构化学习记录，供工作流层和只读调试界面消费。

边界：
这里只处理合成的 strategy-agnostic 学习对象；不调用外部平台、不写真实业务结论、
不自动形成正式 Decision，也不输出敏感原文。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Mapping, Sequence
from uuid import uuid4

from medical_tourism_os.domain.entities import AdapterResult, _utc_now_isoformat
from medical_tourism_os.services.business_core import validate_source_channel_code


_ALLOWED_REVIEW_RESULTS = {"observed", "contradicted", "insufficient_sample"}


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    """稳定去重短字符串，避免学习闭环被重复字段污染。"""

    ordered: List[str] = []
    seen = set()
    for raw_value in values:
        value = str(raw_value).strip()
        if value and value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


@dataclass(frozen=True)
class MetricRecord:
    """
    作用：
    表示一条学习指标观测。

    输入：
    synthetic channel code、metric 名称与数值。

    输出：
    供 experiment review 聚合的最小指标记录。

    关键边界：
    指标只保存通用名称和值，不保存真实账号、句柄或外部平台响应。
    """

    id: str
    channel: str
    metric_name: str
    value: float
    recorded_at: str

    def to_dict(self) -> Dict[str, object]:
        """返回可 JSON 序列化的指标视图。"""

        return asdict(self)


@dataclass(frozen=True)
class Experiment:
    """
    作用：
    表示一个只允许单一 primary variable 的实验定义。

    输入：
    假设、唯一主变量、固定变量、观察窗口与指标集合。

    输出：
    供 review 与 weekly summary 使用的实验对象。

    关键边界：
    这里只声明实验结构，不自动推导业务策略或验证完成状态。
    """

    id: str
    hypothesis: str
    primary_variable: str
    fixed_variables: tuple[str, ...]
    window: str
    metrics: tuple[str, ...]
    status: str
    created_at: str

    def to_dict(self) -> Dict[str, object]:
        """返回可 JSON 序列化的实验定义。"""

        return asdict(self)


@dataclass(frozen=True)
class ExperimentReview:
    """
    作用：
    表示一次实验复盘结果。

    输入：
    experiment、允许的 result 枚举，以及 evidence/counterevidence/unknown/risk。

    输出：
    供 weekly review 聚合的结构化复盘。

    关键边界：
    result 只能是 observed / contradicted / insufficient_sample；
    这只是学习判断，不是业务成功或失败裁决。
    """

    id: str
    experiment_id: str
    result: str
    evidence: tuple[str, ...]
    counterevidence: tuple[str, ...]
    unknowns: tuple[str, ...]
    risks: tuple[str, ...]
    next_variables: tuple[str, ...]
    created_at: str

    def to_dict(self) -> Dict[str, object]:
        """返回可 JSON 序列化的实验复盘。"""

        return asdict(self)


@dataclass(frozen=True)
class WeeklyReview:
    """
    作用：
    汇总一周内实验复盘得到的下一步学习面板。

    输入：
    review 集合与主变量候选。

    输出：
    evidence、counterevidence、unknown、risk 与 next variables 的聚合结果。

    关键边界：
    这里输出的是学习摘要，不表示市场、价格或路线已经锁定。
    """

    id: str
    experiment_ids: tuple[str, ...]
    primary_variable_candidates: tuple[str, ...]
    evidence: tuple[str, ...]
    counterevidence: tuple[str, ...]
    unknowns: tuple[str, ...]
    risks: tuple[str, ...]
    next_variables: tuple[str, ...]
    created_at: str

    def to_dict(self) -> Dict[str, object]:
        """返回可 JSON 序列化的周复盘结果。"""

        return asdict(self)


@dataclass(frozen=True)
class DecisionCandidate:
    """
    作用：
    表示基于 weekly review 生成的候选判断。

    输入：
    周复盘 id、候选主变量与最小安全摘要。

    输出：
    status 固定为 `candidate` 的候选判断对象。

    关键边界：
    这里绝不能自动升级为正式 Decision，也不能声称 business validation 完成。
    """

    id: str
    weekly_review_id: str
    status: str
    primary_variable: str
    evidence_count: int
    counterevidence_count: int
    unknown_count: int
    risk_count: int
    next_variables: tuple[str, ...]
    business_validation_completed: bool
    created_at: str

    def to_dict(self) -> Dict[str, object]:
        """返回可 JSON 序列化的候选判断。"""

        return asdict(self)


class LearningLoopService:
    """
    作用：
    提供离线学习闭环的最小实现。

    输入：
    指标、实验定义和复盘动作。

    输出：
    `MetricRecord`、`Experiment`、`ExperimentReview`、`WeeklyReview` 和 `DecisionCandidate`。

    关键边界：
    所有输出都停留在 learning/candidate 层，不触发外部同步或正式业务决策。
    """

    def __init__(self) -> None:
        self._metrics: List[MetricRecord] = []
        self._experiments: Dict[str, Experiment] = {}
        self._reviews: Dict[str, ExperimentReview] = {}
        self._weekly_reviews: Dict[str, WeeklyReview] = {}
        self._decision_candidates: Dict[str, DecisionCandidate] = {}

    def record_metric(self, channel: str, metric_name: str, value: float) -> MetricRecord:
        """
        作用：
        记录一条 synthetic metric。

        关键边界：
        channel 必须通过安全 channel code 校验，防止把真实账号标识带进学习层。
        """

        safe_channel = validate_source_channel_code(channel)
        normalized_metric = metric_name.strip()
        if not normalized_metric:
            raise ValueError("metric_name_required")
        record = MetricRecord(
            id=f"metric_{uuid4().hex}",
            channel=safe_channel,
            metric_name=normalized_metric,
            value=float(value),
            recorded_at=_utc_now_isoformat(),
        )
        self._metrics.append(record)
        return record

    def create_experiment(
        self,
        *,
        hypothesis: str,
        primary_variable: str,
        fixed_variables: Sequence[str],
        window: str,
        metrics: Sequence[str],
    ) -> Experiment:
        """
        作用：
        创建一个单主变量实验。

        关键边界：
        primary variable 必须唯一且显式；固定变量只保存去重后的中性标签。
        """

        normalized_primary_variable = primary_variable.strip()
        if not normalized_primary_variable:
            raise ValueError("primary_variable_required")
        normalized_window = window.strip()
        if not normalized_window:
            raise ValueError("window_required")
        normalized_metrics = _dedupe(metrics)
        if not normalized_metrics:
            raise ValueError("metrics_required")
        normalized_fixed_variables = tuple(
            value
            for value in _dedupe(fixed_variables)
            if value != normalized_primary_variable
        )
        experiment = Experiment(
            id=f"experiment_{uuid4().hex}",
            hypothesis=hypothesis.strip(),
            primary_variable=normalized_primary_variable,
            fixed_variables=normalized_fixed_variables,
            window=normalized_window,
            metrics=normalized_metrics,
            status="active",
            created_at=_utc_now_isoformat(),
        )
        self._experiments[experiment.id] = experiment
        return experiment

    def review_experiment(self, experiment_id: str, *, result: str) -> ExperimentReview:
        """
        作用：
        对实验做一次允许枚举内的复盘。

        关键边界：
        复盘文本使用结构化短语，而不是敏感原文或夸张业务承诺。
        """

        experiment = self._experiments.get(experiment_id)
        if experiment is None:
            raise KeyError("experiment_not_found")
        normalized_result = result.strip()
        if normalized_result not in _ALLOWED_REVIEW_RESULTS:
            raise ValueError("invalid_experiment_result")

        metric_summary = self._metric_summary(experiment.metrics)
        evidence = ()
        counterevidence = ()
        unknowns = ()
        if normalized_result == "observed":
            evidence = tuple(f"{name}_signal_present" for name in metric_summary.keys())
        elif normalized_result == "contradicted":
            counterevidence = tuple(f"{name}_did_not_support_hypothesis" for name in metric_summary.keys())
        else:
            unknowns = tuple(f"{name}_sample_insufficient" for name in experiment.metrics)

        review = ExperimentReview(
            id=f"review_{uuid4().hex}",
            experiment_id=experiment.id,
            result=normalized_result,
            evidence=evidence,
            counterevidence=counterevidence,
            unknowns=unknowns,
            risks=("business_strategy_pending", "human_review_required"),
            next_variables=(experiment.primary_variable,),
            created_at=_utc_now_isoformat(),
        )
        self._reviews[review.id] = review
        return review

    def generate_weekly_review(self) -> WeeklyReview:
        """
        作用：
        聚合当前会话里的实验复盘，生成 weekly review。

        关键边界：
        若没有 experiment review，则不能伪造周复盘。
        """

        if not self._reviews:
            raise ValueError("review_required_before_weekly_review")
        reviews = list(self._reviews.values())
        related_experiments = [self._experiments[review.experiment_id] for review in reviews]
        weekly_review = WeeklyReview(
            id=f"weekly_review_{uuid4().hex}",
            experiment_ids=tuple(review.experiment_id for review in reviews),
            primary_variable_candidates=_dedupe(
                [experiment.primary_variable for experiment in related_experiments]
            ),
            evidence=_dedupe([item for review in reviews for item in review.evidence]),
            counterevidence=_dedupe([item for review in reviews for item in review.counterevidence]),
            unknowns=_dedupe([item for review in reviews for item in review.unknowns]),
            risks=_dedupe([item for review in reviews for item in review.risks]),
            next_variables=_dedupe([item for review in reviews for item in review.next_variables]),
            created_at=_utc_now_isoformat(),
        )
        self._weekly_reviews[weekly_review.id] = weekly_review
        return weekly_review

    def create_decision_candidate(self, weekly_review_id: str) -> DecisionCandidate:
        """
        作用：
        基于 weekly review 生成一个候选判断。

        关键边界：
        status 永远固定为 `candidate`，明确 business_validation_completed 为 false。
        """

        weekly_review = self._weekly_reviews.get(weekly_review_id)
        if weekly_review is None:
            raise KeyError("weekly_review_not_found")
        candidate = DecisionCandidate(
            id=f"decision_candidate_{uuid4().hex}",
            weekly_review_id=weekly_review.id,
            status="candidate",
            primary_variable=weekly_review.primary_variable_candidates[0],
            evidence_count=len(weekly_review.evidence),
            counterevidence_count=len(weekly_review.counterevidence),
            unknown_count=len(weekly_review.unknowns),
            risk_count=len(weekly_review.risks),
            next_variables=weekly_review.next_variables,
            business_validation_completed=False,
            created_at=_utc_now_isoformat(),
        )
        self._decision_candidates[candidate.id] = candidate
        return candidate

    def github_dry_run(self, candidate_id: str) -> AdapterResult:
        """
        作用：
        生成 GitHub sync 的 dry-run 安全预览。

        关键边界：
        这里只导出允许字段，不回传假设原文、原始指标文本或任何敏感上下文。
        """

        candidate = self._decision_candidates.get(candidate_id)
        if candidate is None:
            raise KeyError("decision_candidate_not_found")
        safe_payload = {
            "export_type": "decision_candidate",
            "allowed_fields": self.safe_sync_payload(candidate),
        }
        return AdapterResult(
            dry_run=True,
            executed=False,
            reason="github_sync_dry_run_only",
            payload=safe_payload,
        )

    def safe_sync_payload(self, candidate: DecisionCandidate) -> Dict[str, object]:
        """返回 GitHub dry-run 允许导出的最小字段集。"""

        return {
            "id": candidate.id,
            "weekly_review_id": candidate.weekly_review_id,
            "status": candidate.status,
            "primary_variable": candidate.primary_variable,
            "evidence_count": candidate.evidence_count,
            "counterevidence_count": candidate.counterevidence_count,
            "unknown_count": candidate.unknown_count,
            "risk_count": candidate.risk_count,
            "next_variables": list(candidate.next_variables),
            "business_validation_completed": candidate.business_validation_completed,
            "created_at": candidate.created_at,
        }

    def _metric_summary(self, allowed_metrics: Sequence[str]) -> Mapping[str, float]:
        """仅汇总实验显式声明的指标，避免把无关噪声带入复盘。"""

        summary: Dict[str, float] = {}
        for metric_name in allowed_metrics:
            values = [item.value for item in self._metrics if item.metric_name == metric_name]
            if values:
                summary[metric_name] = sum(values)
        return summary
