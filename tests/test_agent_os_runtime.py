"""验证 General AI Agent OS 的模型、Agent、Tool、Workflow 与 Plugin 最小闭环。"""

from __future__ import annotations

import unittest


class AgentOsRuntimeTests(unittest.TestCase):
    """所有输入都是 TEST_*，用于证明核心可组合而不承载业务事实或外部动作。"""

    def test_default_deny_agent_cannot_reach_model_gateway_or_registered_tools(self) -> None:
        """Agent-level `DEFAULT_DENY` 是第二道闸门，不能因全局测试开关而失效。"""
        from general_ai_business_os.agent_runtime import AgentRegistry
        from general_ai_business_os.ai_system_config import AiSystemConfig
        from general_ai_business_os.model_gateway import ModelGateway, MockLlmProvider
        from general_ai_business_os.tool_registry import MockTool, ToolRegistry
        from general_ai_business_os.workflow_engine import WorkflowEngine
        from general_ai_business_os.config import SystemConfig
        from general_ai_business_os.permissions.policy import PermissionPolicy

        config = AiSystemConfig.from_mapping(
            {
                "providers": [{"provider_name": "OPENAI", "model_name": "TEST_MODEL", "endpoint": "https://example.invalid", "api_key_reference": "SECRET_REF_TEST", "enabled": True, "timeout": 1, "cost_limit": 0}],
                "agents": [{"agent_id": "TEST_AGENT", "name": "TEST_AGENT", "role": "TEST_ROLE", "system_prompt": "TEST_PROMPT", "model_provider": "OPENAI", "tools": ["TEST_TOOL"], "memory_policy": "NONE", "permission_policy": "DEFAULT_DENY"}],
                "tools": [{"tool_id": "TEST_TOOL", "adapter": "TEST_ADAPTER", "permission": "ALLOW", "enabled": True, "cost_limit": 0}],
                "runtime": {"environment": "TEST", "logging": "STRUCTURED", "retry": 0, "timeout": 1, "budget": 0},
            }
        )
        policy = PermissionPolicy(SystemConfig(external_actions_allowed=True))
        gateway = ModelGateway(config, {"OPENAI": MockLlmProvider()}, policy)
        tools = ToolRegistry(config, policy)
        tools.register(MockTool("TEST_TOOL"))
        agents = AgentRegistry(config, gateway, tools)
        workflow = WorkflowEngine(agents)

        result = workflow.run({"nodes": ["TEST_AGENT"], "edges": []}, {"input": "TEST_INPUT"})

        self.assertEqual("BLOCKED", result.status)
        self.assertEqual("BLOCKED", result.outputs["TEST_AGENT"]["model_status"])
        self.assertEqual("BLOCKED", result.outputs["TEST_AGENT"]["state"])
        self.assertEqual("agent_permission_denied", result.outputs["TEST_AGENT"]["reason"])
        self.assertEqual([], result.outputs["TEST_AGENT"]["tool_results"])
        self.assertIsNone(agents.state("TEST_AGENT"))

    def test_plugin_registry_accepts_only_core_api_plugins_without_business_fact_import(self) -> None:
        from general_ai_business_os.plugins import PluginRegistry

        registry = PluginRegistry()
        registry.register("TEST_PLUGIN", {"plugin_id": "TEST_PLUGIN", "version": "TEST_V1", "permissions": [], "dependencies": [], "entrypoint": "test_plugin.entrypoint:build"})

        self.assertEqual("TEST_V1", registry.get("TEST_PLUGIN")["version"])

    def test_real_capability_adapters_remain_blocked_while_local_test_runtime_executes(self) -> None:
        """Mock 的本地执行例外不能扩展到真实 Provider/Tool；外部总闸关闭时两者均不得被调用。"""

        from general_ai_business_os.ai_system_config import AiSystemConfig
        from general_ai_business_os.config import SystemConfig
        from general_ai_business_os.model_gateway import LLMProvider, ModelGateway
        from general_ai_business_os.permissions.policy import PermissionPolicy
        from general_ai_business_os.tool_registry import Tool, ToolRegistry

        class ExternalTestProvider(LLMProvider):
            def __init__(self) -> None:
                self.calls = 0

            def chat(self, messages, model):
                self.calls += 1
                return {"status": "EXTERNAL", "content": "UNEXPECTED"}

            def generate(self, prompt, model):
                raise AssertionError("not_used")

            def embedding(self, text, model):
                raise AssertionError("not_used")

        class ExternalTestTool(Tool):
            @property
            def tool_id(self) -> str:
                return "TEST_TOOL"

            def __init__(self) -> None:
                self.calls = 0

            def execute(self, payload):
                self.calls += 1
                return {"status": "EXTERNAL"}

        config = AiSystemConfig.from_mapping(
            {
                "providers": [{"provider_name": "OPENAI", "model_name": "TEST_MODEL", "endpoint": "https://example.invalid", "api_key_reference": "SECRET_REF_TEST", "enabled": True, "timeout": 1, "cost_limit": 0}],
                "agents": [],
                "tools": [{"tool_id": "TEST_TOOL", "adapter": "TEST_ADAPTER", "permission": "ALLOW", "enabled": True, "cost_limit": 0}],
                "runtime": {"environment": "TEST", "logging": "STRUCTURED", "retry": 0, "timeout": 1, "budget": 0},
            }
        )
        policy = PermissionPolicy(SystemConfig())
        provider = ExternalTestProvider()
        tool = ExternalTestTool()
        tools = ToolRegistry(config, policy)
        tools.register(tool)

        model_result = ModelGateway(config, {"OPENAI": provider}, policy).chat("OPENAI", [])
        tool_result = tools.execute("TEST_TOOL", {"input": "TEST_INPUT"})

        self.assertEqual({"status": "BLOCKED", "reason": "external_actions_disabled", "content": ""}, model_result)
        self.assertEqual({"status": "BLOCKED", "reason": "external_actions_disabled"}, tool_result)
        self.assertEqual(0, provider.calls)
        self.assertEqual(0, tool.calls)


if __name__ == "__main__":
    unittest.main()
