"""
用途：记录 Evaluation 指标，并把可复核的 Feedback 事件回写到抽象 Memory。

上游：Agent Runtime、Tool Registry 和 Workflow 交付本次本地运行的结构化结果。

下游：Memory Store 保存 Feedback 快照；未来人工复核或学习组件只能消费该结构化证据。

边界：这里不调用模型、不改写业务事实，也不把 `OBSERVED` 自动升级为正确或可发布。
"""
from __future__ import annotations
from dataclasses import dataclass
from general_ai_business_os.memory import MemoryStore


@dataclass(frozen=True)
class EvaluationResult:
    accuracy: float
    latency: float
    cost: float
    tool_success_rate: float
    human_override_rate: float
    verdict: str


@dataclass(frozen=True)
class FeedbackRecord:
    """Evaluation 产生的本地反馈证据；不代表业务学习或真实人工决定。"""

    agent_id: str
    evaluation_verdict: str
    tool_success_rate: float
    human_override_rate: float
    status: str


class EvaluationService:
    """校验并归一化运行指标；只生成 `OBSERVED` 观察结果。"""

    def evaluate(self, *, accuracy: float, latency: float, cost: float, tool_success_rate: float, human_override_rate: float) -> EvaluationResult:
        values = (accuracy, latency, cost, tool_success_rate, human_override_rate)
        if any(not isinstance(value, (int, float)) or value < 0 for value in values):
            raise ValueError("evaluation_metric_invalid")
        return EvaluationResult(*map(float, values), "OBSERVED")


class FeedbackLoop:
    """把 Evaluation 结果写入 Memory；没有这条记录时不得声称已形成 Feedback 闭环。"""

    def record(self, *, agent_id: str, evaluation: EvaluationResult, memory: MemoryStore) -> FeedbackRecord:
        feedback = FeedbackRecord(
            agent_id=agent_id,
            evaluation_verdict=evaluation.verdict,
            tool_success_rate=evaluation.tool_success_rate,
            human_override_rate=evaluation.human_override_rate,
            status="RECORDED",
        )
        memory.put(
            f"feedback:{agent_id}",
            {
                "evaluation_verdict": feedback.evaluation_verdict,
                "tool_success_rate": feedback.tool_success_rate,
                "human_override_rate": feedback.human_override_rate,
                "status": feedback.status,
            },
        )
        return feedback
