"""配置化 Workflow Engine：读取 nodes/edges，不写死任何行业 Agent 顺序。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from general_ai_business_os.agent_runtime import AgentRegistry
@dataclass(frozen=True)
class WorkflowResult: status: str; outputs: Mapping[str, Mapping[str, Any]]
class WorkflowEngine:
    def __init__(self, agents: AgentRegistry) -> None: self._agents = agents
    def run(self, definition: Mapping[str, Any], payload: Mapping[str, Any]) -> WorkflowResult:
        nodes = definition.get("nodes")
        if not isinstance(nodes, list) or not isinstance(definition.get("edges"), list): raise ValueError("workflow_definition_invalid")
        outputs = {node: self._agents.execute(node, payload) for node in nodes}
        return WorkflowResult(status="COMPLETED", outputs=outputs)
