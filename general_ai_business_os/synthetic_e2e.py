"""
用途：运行 `TEST_BUSINESS` 的纯本地 E2E，验证 Core Runtime 的可组合性。

上游：测试与未来演示入口调用 `run_test_business()`。

下游：依次经过 Config、Agent、Model Gateway、Tool、Workflow、Memory、Evaluation 和 Feedback。

边界：所有输入均为 `TEST_*`，Provider 是本地 Mock，Tool 只执行确定性本地计算；
不会读取 API key、连接外部服务或产生任何业务验证结论。
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from general_ai_business_os.agent_runtime import AgentRegistry
from general_ai_business_os.ai_system_config import AiSystemConfig
from general_ai_business_os.memory import InMemoryStore
from general_ai_business_os.model_gateway import MockLlmProvider, ModelGateway
from general_ai_business_os.tool_registry import Tool, ToolRegistry
from general_ai_business_os.workflow_engine import WorkflowEngine
from general_ai_business_os.config import SystemConfig
from general_ai_business_os.permissions.policy import PermissionPolicy
from general_ai_business_os.evaluation import EvaluationResult, EvaluationService, FeedbackLoop, FeedbackRecord


class TestBusinessTool(Tool):
    """确定性本地 Tool：生成可审计的输入长度证据，而不是返回预写的 Mock 输出。"""

    @property
    def tool_id(self) -> str:
        return "TEST_TOOL"

    @property
    def requires_external_permission(self) -> bool:
        """该 Tool 只有进程内字符串计算，不属于外部动作。"""

        return False

    def execute(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        input_value = payload.get("input")
        if not isinstance(input_value, str) or not input_value.startswith("TEST_"):
            return {"status": "BLOCKED", "reason": "test_business_input_invalid"}
        return {
            "status": "COMPLETED",
            "tool_id": self.tool_id,
            "evidence": {"input_length": len(input_value)},
        }

@dataclass(frozen=True)
class SyntheticE2EResult:
    stages: tuple[str, ...]
    external_actions_allowed: bool
    external_actions_attempted: int
    business_validation_completed: bool
    tool_execution_count: int
    tool_evidence: tuple[Mapping[str, Any], ...]
    evaluation: EvaluationResult
    feedback: FeedbackRecord


def run_test_business() -> SyntheticE2EResult:
    """运行并返回完整证据；任何阶段缺失都会在本地测试中被当作 E2E 不完整。"""

    config = AiSystemConfig.from_mapping(
        {
            "providers": [{"provider_name": "OPENAI", "model_name": "TEST_MODEL", "endpoint": "https://example.invalid", "api_key_reference": "SECRET_REF_TEST", "enabled": True, "timeout": 1, "cost_limit": 0}],
            "agents": [{"agent_id": "TEST_AGENT", "name": "TEST_AGENT", "role": "TEST_ROLE", "system_prompt": "TEST_PROMPT", "model_provider": "OPENAI", "tools": ["TEST_TOOL"], "memory_policy": "LOCAL", "permission_policy": "ALLOW"}],
            "tools": [{"tool_id": "TEST_TOOL", "adapter": "TEST_ADAPTER", "permission": "ALLOW", "enabled": True, "cost_limit": 0}],
            "runtime": {"environment": "TEST", "logging": "STRUCTURED", "retry": 0, "timeout": 1, "budget": 0},
        }
    )
    system_config = SystemConfig()
    policy = PermissionPolicy(system_config)
    tools = ToolRegistry(config, policy)
    tools.register(TestBusinessTool())
    memory = InMemoryStore()
    agents = AgentRegistry(config, ModelGateway(config, {"OPENAI": MockLlmProvider()}, policy), tools, memory)
    result = WorkflowEngine(agents).run({"nodes":["TEST_AGENT"],"edges":[],"retry":0}, {"input":"TEST_INPUT"})
    tool_evidence = tuple(result.outputs["TEST_AGENT"]["tool_results"])
    if result.status != "COMPLETED" or agents.state("TEST_AGENT") is None or len(tool_evidence) != 1 or not tools.execution_log():
        raise AssertionError("synthetic_runtime_incomplete")
    evaluation = EvaluationService().evaluate(
        accuracy=1,
        latency=0,
        cost=0,
        tool_success_rate=sum(item["status"] == "COMPLETED" for item in tool_evidence) / len(tool_evidence),
        human_override_rate=0,
    )
    feedback = FeedbackLoop().record(agent_id="TEST_AGENT", evaluation=evaluation, memory=memory)
    if memory.get("feedback:TEST_AGENT") is None:
        raise AssertionError("synthetic_feedback_not_recorded")
    return SyntheticE2EResult(
        stages=("Config", "Agent", "Tool", "Workflow", "Memory", "Evaluation", "Feedback"),
        external_actions_allowed=system_config.external_actions_allowed,
        external_actions_attempted=0,
        business_validation_completed=False,
        tool_execution_count=len(tool_evidence),
        tool_evidence=tool_evidence,
        evaluation=evaluation,
        feedback=feedback,
    )
