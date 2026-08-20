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
        outputs = {}
        edges = definition["edges"]
        if any(not isinstance(edge, Mapping) or edge.get("from") not in nodes or edge.get("to") not in nodes for edge in edges): raise ValueError("workflow_edges_invalid")
        if len(set(nodes)) != len(nodes): raise ValueError("workflow_node_duplicate")
        outgoing, incoming = {node: [] for node in nodes}, {node: 0 for node in nodes}
        for edge in edges:
            outgoing[edge["from"]].append(edge["to"]); incoming[edge["to"]] += 1
        ordered, queue = [], [node for node in nodes if incoming[node] == 0]
        while queue:
            node = queue.pop(0); ordered.append(node)
            for target in outgoing[node]:
                incoming[target] -= 1
                if incoming[target] == 0: queue.append(target)
        if len(ordered) != len(nodes): raise ValueError("workflow_cycle_detected")
        for node in ordered:
            if node in outputs: continue
            attempts = 0
            while True:
                try:
                    outputs[node] = self._agents.execute(node, payload)
                    break
                except ValueError as error:
                    attempts += 1
                    if attempts > int(definition.get("retry", 0)):
                        fallback = definition.get("fallback")
                        if fallback in nodes and fallback not in outputs and fallback != node:
                            outputs[fallback] = self._agents.execute(fallback, payload)
                            break
                        else: raise error
        return WorkflowResult(status="BLOCKED" if any(result.get("state") == "BLOCKED" for result in outputs.values()) else "COMPLETED", outputs=outputs)
