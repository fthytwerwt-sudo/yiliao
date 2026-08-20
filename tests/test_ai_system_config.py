"""验证 AI System Configuration Layer 的中性配置合同。"""

from __future__ import annotations

import unittest


class AiSystemConfigTests(unittest.TestCase):
    """Phase 2 只测试模型、Agent、Tool、Runtime 与 secret reference，不引入业务数据。"""

    def test_provider_agent_tool_and_runtime_configs_are_dynamic_and_secret_safe(self) -> None:
        """Core 根据配置创建能力，不保存真实 API key 或业务事实。"""

        from general_ai_business_os.ai_system_config import AiSystemConfig, ConfigError

        config = AiSystemConfig.from_mapping(
            {
                "providers": [
                    {
                        "provider_name": "OPENAI",
                        "model_name": "TEST_MODEL",
                        "endpoint": "https://example.invalid/api",
                        "api_key_reference": "SECRET_REF_TEST",
                        "enabled": False,
                        "timeout": 30,
                        "cost_limit": 10,
                    }
                ],
                "agents": [
                    {
                        "agent_id": "TEST_AGENT",
                        "name": "TEST_AGENT",
                        "role": "TEST_ROLE",
                        "system_prompt": "TEST_PROMPT",
                        "model_provider": "OPENAI",
                        "tools": ["TEST_TOOL"],
                        "memory_policy": "NONE",
                        "permission_policy": "DEFAULT_DENY",
                    }
                ],
                "tools": [
                    {"tool_id": "TEST_TOOL", "adapter": "TEST_ADAPTER", "permission": "DEFAULT_DENY", "enabled": False, "cost_limit": 0}
                ],
                "runtime": {"environment": "TEST", "logging": "STRUCTURED", "retry": 1, "timeout": 30, "budget": 10},
            }
        )

        self.assertEqual("TEST_MODEL", config.providers[0].model_name)
        self.assertFalse(config.providers[0].enabled)
        self.assertEqual("OPENAI", config.agents[0].model_provider)
        with self.assertRaisesRegex(ConfigError, "api_key_reference_invalid"):
            AiSystemConfig.from_mapping({"providers": [{"provider_name": "OPENAI", "model_name": "TEST_MODEL", "endpoint": "https://example.invalid", "api_key_reference": "sk-real-key", "enabled": False, "timeout": 1, "cost_limit": 0}], "agents": [], "tools": [], "runtime": {"environment": "TEST", "logging": "STRUCTURED", "retry": 0, "timeout": 1, "budget": 0}})

    def test_provider_requires_nonempty_endpoint_and_agent_uses_closed_policy_vocabularies(self) -> None:
        """空 endpoint 与自造 policy 都会在配置边界拒绝，不能留给 Runtime 的隐式分支。"""

        from general_ai_business_os.ai_system_config import AiSystemConfig, ConfigError

        valid_runtime = {"environment": "TEST", "logging": "STRUCTURED", "retry": 0, "timeout": 1, "budget": 0}
        blank_endpoint = {"provider_name": "OPENAI", "model_name": "TEST_MODEL", "endpoint": " ", "api_key_reference": "SECRET_REF_TEST", "enabled": False, "timeout": 1, "cost_limit": 0}
        with self.assertRaisesRegex(ConfigError, "provider_model_or_endpoint_invalid"):
            AiSystemConfig.from_mapping({"providers": [blank_endpoint], "agents": [], "tools": [], "runtime": valid_runtime})

        invalid_policy_agent = {"agent_id": "TEST_AGENT", "name": "TEST_AGENT", "role": "TEST_ROLE", "system_prompt": "TEST_PROMPT", "model_provider": "OPENAI", "tools": [], "memory_policy": "BYPASS_MEMORY", "permission_policy": "BYPASS_POLICY"}
        valid_provider = {**blank_endpoint, "endpoint": "https://example.invalid"}
        with self.assertRaisesRegex(ConfigError, "agent_memory_policy_invalid"):
            AiSystemConfig.from_mapping({"providers": [valid_provider], "agents": [invalid_policy_agent], "tools": [], "runtime": valid_runtime})


if __name__ == "__main__":
    unittest.main()
