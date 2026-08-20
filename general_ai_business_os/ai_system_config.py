"""
用途：
定义 General AI Agent OS 的 Provider、Agent、Tool 与 Runtime 配置合同。

上游：
本地 JSON/YAML loader、CLI 或未来控制台将结构化系统配置传入此模块。

下游：
Model Gateway、Agent Runtime 与 Tool Registry 只读取这里验证后的对象。

边界：
不保存 API key 原文、市场、客户、产品、价格或行业事实；真实 Provider 是否启用仍须经过权限与 Adapter 闸门。
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Tuple


class ConfigError(ValueError):
    """AI 系统配置不符合核心合同的阻断错误。"""


_PROVIDERS = {"OPENAI", "DEEPSEEK", "KIMI", "CLAUDE", "GEMINI"}
_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_SECRET_REFERENCE = re.compile(r"^SECRET_REF_[A-Z0-9_]{3,63}$")


def _code(value: Any, field: str) -> str:
    """校验稳定配置代码；配置身份不得由自由文本或凭据原文承担。"""

    if not isinstance(value, str) or not _CODE.fullmatch(value):
        raise ConfigError(f"{field}_invalid")
    return value


def _number(value: Any, field: str) -> int:
    """校验非负整数预算/超时，避免 bool 或负数被隐式接受。"""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ConfigError(f"{field}_invalid")
    return value


@dataclass(frozen=True)
class ProviderConfig:
    """模型 Provider 配置；只引用 Secret，不持有 Secret 值。"""

    provider_name: str
    model_name: str
    endpoint: str
    api_key_reference: str
    enabled: bool
    timeout: int
    cost_limit: int


@dataclass(frozen=True)
class AgentConfig:
    """动态 Agent 配置；模型选择从 model_provider 配置读取，不写进 Runtime。"""

    agent_id: str
    name: str
    role: str
    system_prompt: str
    model_provider: str
    tools: Tuple[str, ...]
    memory_policy: str
    permission_policy: str


@dataclass(frozen=True)
class ToolConfig:
    """Tool 注册前的配置项；enabled 不等于已获得外部执行权限。"""

    tool_id: str
    adapter: str
    permission: str
    enabled: bool
    cost_limit: int


@dataclass(frozen=True)
class RuntimeConfig:
    """运行时重试、超时与预算配置；不含任何行业业务参数。"""

    environment: str
    logging: str
    retry: int
    timeout: int
    budget: int


@dataclass(frozen=True)
class AiSystemConfig:
    """经过核心验证的完整 AI System Configuration 快照。"""

    providers: Tuple[ProviderConfig, ...]
    agents: Tuple[AgentConfig, ...]
    tools: Tuple[ToolConfig, ...]
    runtime: RuntimeConfig

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "AiSystemConfig":
        """从 mapping 动态创建配置，并验证 Provider/Agent/Tool 的引用完整性。"""

        if not isinstance(payload, Mapping) or set(payload) != {"providers", "agents", "tools", "runtime"}:
            raise ConfigError("system_config_fields_invalid")
        providers = tuple(cls._provider(item) for item in cls._list(payload["providers"], "providers"))
        agents = tuple(cls._agent(item) for item in cls._list(payload["agents"], "agents"))
        tools = tuple(cls._tool(item) for item in cls._list(payload["tools"], "tools"))
        if not isinstance(payload["runtime"], Mapping):
            raise ConfigError("runtime_invalid")
        runtime = cls._runtime(payload["runtime"])
        provider_names = {item.provider_name for item in providers}
        tool_ids = {item.tool_id for item in tools}
        if len(provider_names) != len(providers) or len(tool_ids) != len(tools):
            raise ConfigError("config_identifier_duplicate")
        for agent in agents:
            if agent.model_provider not in provider_names or not set(agent.tools).issubset(tool_ids):
                raise ConfigError("agent_reference_invalid")
        return cls(providers=providers, agents=agents, tools=tools, runtime=runtime)

    @staticmethod
    def _list(value: Any, field: str) -> list[Mapping[str, Any]]:
        if not isinstance(value, list) or any(not isinstance(item, Mapping) for item in value):
            raise ConfigError(f"{field}_invalid")
        return value

    @staticmethod
    def _provider(item: Mapping[str, Any]) -> ProviderConfig:
        if set(item) != {"provider_name", "model_name", "endpoint", "api_key_reference", "enabled", "timeout", "cost_limit"}:
            raise ConfigError("provider_fields_invalid")
        provider = _code(item["provider_name"], "provider_name")
        if provider not in _PROVIDERS:
            raise ConfigError("provider_name_invalid")
        if not isinstance(item["model_name"], str) or not item["model_name"].strip() or not isinstance(item["endpoint"], str):
            raise ConfigError("provider_model_or_endpoint_invalid")
        if not isinstance(item["api_key_reference"], str) or not _SECRET_REFERENCE.fullmatch(item["api_key_reference"]):
            raise ConfigError("api_key_reference_invalid")
        if not isinstance(item["enabled"], bool):
            raise ConfigError("provider_enabled_invalid")
        return ProviderConfig(provider, item["model_name"], item["endpoint"], item["api_key_reference"], item["enabled"], _number(item["timeout"], "provider_timeout"), _number(item["cost_limit"], "provider_cost_limit"))

    @staticmethod
    def _agent(item: Mapping[str, Any]) -> AgentConfig:
        if set(item) != {"agent_id", "name", "role", "system_prompt", "model_provider", "tools", "memory_policy", "permission_policy"}:
            raise ConfigError("agent_fields_invalid")
        tools = tuple(_code(value, "agent_tool") for value in AiSystemConfig._list_codes(item["tools"], "agent_tools"))
        return AgentConfig(_code(item["agent_id"], "agent_id"), _code(item["name"], "agent_name"), _code(item["role"], "agent_role"), str(item["system_prompt"]), _code(item["model_provider"], "model_provider"), tools, _code(item["memory_policy"], "memory_policy"), _code(item["permission_policy"], "permission_policy"))

    @staticmethod
    def _tool(item: Mapping[str, Any]) -> ToolConfig:
        if set(item) != {"tool_id", "adapter", "permission", "enabled", "cost_limit"} or not isinstance(item["enabled"], bool):
            raise ConfigError("tool_fields_invalid")
        return ToolConfig(_code(item["tool_id"], "tool_id"), _code(item["adapter"], "tool_adapter"), _code(item["permission"], "tool_permission"), item["enabled"], _number(item["cost_limit"], "tool_cost_limit"))

    @staticmethod
    def _runtime(item: Mapping[str, Any]) -> RuntimeConfig:
        if set(item) != {"environment", "logging", "retry", "timeout", "budget"}:
            raise ConfigError("runtime_fields_invalid")
        return RuntimeConfig(_code(item["environment"], "runtime_environment"), _code(item["logging"], "runtime_logging"), _number(item["retry"], "runtime_retry"), _number(item["timeout"], "runtime_timeout"), _number(item["budget"], "runtime_budget"))

    @staticmethod
    def _list_codes(value: Any, field: str) -> list[str]:
        if not isinstance(value, list):
            raise ConfigError(f"{field}_invalid")
        return value
