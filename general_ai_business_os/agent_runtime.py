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

    def _record_state(self, agent_id: str, agent_memory_policy: str, state: Mapping[str, Any]) -> None:
        """只在 Agent 明确选择 Memory 时写入状态；`NONE` 不能留下隐式运行残留。"""

        if agent_memory_policy != "NONE":
            self._memory.put(f"agent:{agent_id}", state)
    def execute(self, agent_id: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        作用：执行一个已注册 Agent，并通过唯一的 Gateway/Tool/Memory 边界记录结果。

        关键边界：Agent 自身的 `permission_policy` 是全局 PermissionPolicy 之前的
        第二道闸门。`DEFAULT_DENY` 必须在调用模型或 Tool 前退出，避免测试或未来配置
        打开全局开关后意外扩大某个 Agent 的执行能力。
        """

        agent = self._agents.get(agent_id)
        if agent is None:
            raise ValueError("agent_not_registered")
        if agent.permission_policy != "ALLOW":
            result = {
                "agent_id": agent_id,
                "state": "BLOCKED",
                "model_status": "BLOCKED",
                "response": "",
                "tool_results": [],
                "reason": "agent_permission_denied",
            }
            self._record_state(agent_id, agent.memory_policy, {"state": result["state"], "reason": result["reason"]})
            return result
        response = self._gateway.chat(agent.model_provider, [{"role": "system", "content": agent.system_prompt}, {"role": "user", "content": str(payload.get("input", ""))}])
        tool_results = [self._tools.execute(tool, payload) for tool in agent.tools]
        state = "COMPLETED" if response["status"] == "MOCK" and all(item["status"] != "BLOCKED" for item in tool_results) else "BLOCKED"
        result = {"agent_id": agent_id, "state": state, "model_status": response["status"], "response": response.get("content", ""), "tool_results": tool_results}
        self._record_state(agent_id, agent.memory_policy, {"state": state, "model_status": response["status"]})
        return result

    def state(self, agent_id: str) -> Mapping[str, Any] | None:
        """返回 Agent 的隔离状态快照，而非 Memory 内部的可变对象。"""

        return self._memory.get(f"agent:{agent_id}")
