"""动态 Agent Runtime：从配置注册 Agent，并仅经 Model Gateway 调用模型。"""
from __future__ import annotations
from typing import Any, Mapping
from general_ai_business_os.ai_system_config import AiSystemConfig
from general_ai_business_os.model_gateway import ModelGateway
from general_ai_business_os.memory import InMemoryStore, MemoryStore
from general_ai_business_os.tool_registry import ToolRegistry

class AgentRegistry:
    def __init__(self, config: AiSystemConfig, gateway: ModelGateway, tools: ToolRegistry, memory: MemoryStore | None = None) -> None:
        self._config, self._gateway, self._tools = config, gateway, tools
        self._memory = memory or InMemoryStore()
        self._agents = {agent.agent_id: agent for agent in config.agents}
        if len(self._agents) != len(config.agents): raise ValueError("agent_identifier_duplicate")
    def execute(self, agent_id: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        agent = self._agents.get(agent_id)
        if agent is None: raise ValueError("agent_not_registered")
        response = self._gateway.chat(agent.model_provider, [{"role": "system", "content": agent.system_prompt}, {"role": "user", "content": str(payload.get("input", ""))}])
        tool_results = [self._tools.execute(tool, payload) for tool in agent.tools]
        state = "COMPLETED" if response["status"] == "MOCK" and all(item["status"] != "BLOCKED" for item in tool_results) else "BLOCKED"
        result = {"agent_id": agent_id, "state": state, "model_status": response["status"], "response": response.get("content", ""), "tool_results": tool_results}
        self._memory.put(f"agent:{agent_id}", {"state": state, "model_status": response["status"]})
        return result
    def state(self, agent_id: str): return self._memory.get(f"agent:{agent_id}")
