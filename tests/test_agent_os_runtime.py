"""验证 General AI Agent OS 的模型、Agent、Tool、Workflow 与 Plugin 最小闭环。"""

from __future__ import annotations

import unittest


class AgentOsRuntimeTests(unittest.TestCase):
    """所有输入都是 TEST_*，用于证明核心可组合而不承载业务事实或外部动作。"""

    def test_configured_agent_runs_only_through_mock_model_gateway_and_registered_tools(self) -> None:
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
                "tools": [{"tool_id": "TEST_TOOL", "adapter": "TEST_ADAPTER", "permission": "DEFAULT_DENY", "enabled": False, "cost_limit": 0}],
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
        self.assertEqual("MOCK", result.outputs["TEST_AGENT"]["model_status"])
        self.assertEqual("BLOCKED", result.outputs["TEST_AGENT"]["state"])
        self.assertEqual("BLOCKED", result.outputs["TEST_AGENT"]["tool_results"][0]["status"])

    def test_plugin_registry_accepts_only_core_api_plugins_without_business_fact_import(self) -> None:
        from general_ai_business_os.plugins import PluginRegistry

        registry = PluginRegistry()
        registry.register("TEST_PLUGIN", {"plugin_id": "TEST_PLUGIN", "version": "TEST_V1", "permissions": [], "dependencies": [], "entrypoint": "TEST_ENTRY"})

        self.assertEqual("TEST_V1", registry.get("TEST_PLUGIN")["version"])


if __name__ == "__main__":
    unittest.main()
