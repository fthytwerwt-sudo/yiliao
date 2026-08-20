"""TEST_BUSINESS synthetic E2E：仅验证 Core Runtime 组合，不注入真实业务数据或外部动作。"""
from __future__ import annotations
from dataclasses import dataclass
from general_ai_business_os.agent_runtime import AgentRegistry
from general_ai_business_os.ai_system_config import AiSystemConfig
from general_ai_business_os.memory import InMemoryStore
from general_ai_business_os.model_gateway import MockLlmProvider, ModelGateway
from general_ai_business_os.tool_registry import MockTool, ToolRegistry
from general_ai_business_os.workflow_engine import WorkflowEngine
from general_ai_business_os.config import SystemConfig
from general_ai_business_os.permissions.policy import PermissionPolicy
from general_ai_business_os.evaluation import EvaluationService

@dataclass(frozen=True)
class SyntheticE2EResult:
    stages: tuple[str, ...]
    external_actions_attempted: int
    business_validation_completed: bool

def run_test_business() -> SyntheticE2EResult:
    """运行 Config→Agent→Tool→Workflow→Memory→Evaluation→Feedback 的纯本地合成链。"""
    config = AiSystemConfig.from_mapping({"providers":[{"provider_name":"OPENAI","model_name":"TEST_MODEL","endpoint":"https://example.invalid","api_key_reference":"SECRET_REF_TEST","enabled":True,"timeout":1,"cost_limit":0}],"agents":[{"agent_id":"TEST_AGENT","name":"TEST_AGENT","role":"TEST_ROLE","system_prompt":"TEST_PROMPT","model_provider":"OPENAI","tools":["TEST_TOOL"],"memory_policy":"NONE","permission_policy":"DEFAULT_DENY"}],"tools":[{"tool_id":"TEST_TOOL","adapter":"TEST_ADAPTER","permission":"ALLOW","enabled":True,"cost_limit":0}],"runtime":{"environment":"TEST","logging":"STRUCTURED","retry":0,"timeout":1,"budget":0}})
    policy = PermissionPolicy(SystemConfig(external_actions_allowed=True)); tools = ToolRegistry(config, policy); tools.register(MockTool("TEST_TOOL")); memory = InMemoryStore(); agents = AgentRegistry(config, ModelGateway(config, {"OPENAI": MockLlmProvider()}, policy), tools, memory)
    result = WorkflowEngine(agents).run({"nodes":["TEST_AGENT"],"edges":[],"retry":0}, {"input":"TEST_INPUT"})
    if result.status != "COMPLETED" or agents.state("TEST_AGENT") is None or not tools.execution_log(): raise AssertionError("synthetic_runtime_incomplete")
    EvaluationService().evaluate(accuracy=0, latency=0, cost=0, tool_success_rate=1, human_override_rate=0)
    return SyntheticE2EResult(("Config","Agent","Tool","Workflow","Memory","Evaluation","Feedback"), 0, False)
