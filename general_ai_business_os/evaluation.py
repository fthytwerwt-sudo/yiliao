"""Evaluation Layer：记录质量指标，不自动认定模型输出正确。"""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class EvaluationResult:
    accuracy: float; latency: float; cost: float; tool_success_rate: float; human_override_rate: float; verdict: str
class EvaluationService:
    def evaluate(self, *, accuracy, latency, cost, tool_success_rate, human_override_rate):
        values = (accuracy, latency, cost, tool_success_rate, human_override_rate)
        if any(not isinstance(value, (int, float)) or value < 0 for value in values): raise ValueError("evaluation_metric_invalid")
        return EvaluationResult(*map(float, values), "OBSERVED")
