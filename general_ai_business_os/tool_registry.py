"""动态 Tool Registry：注册、权限边界与本地执行结果。"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Mapping
from general_ai_business_os.ai_system_config import AiSystemConfig

class Tool(ABC):
    @property
    @abstractmethod
    def tool_id(self) -> str: ...
    @abstractmethod
    def execute(self, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...

class MockTool(Tool):
    def __init__(self, tool_id: str) -> None: self._tool_id = tool_id
    @property
    def tool_id(self) -> str: return self._tool_id
    def execute(self, payload): return {"status": "MOCK", "tool_id": self.tool_id, "payload": dict(payload)}

class ToolRegistry:
    """Tool 仅可动态注册；disabled Tool 不执行，避免配置存在即外部动作。"""
    def __init__(self, config: AiSystemConfig) -> None: self._config, self._tools, self._log = config, {}, []
    def register(self, tool: Tool) -> None:
        if tool.tool_id in self._tools: raise ValueError("tool_identifier_duplicate")
        self._tools[tool.tool_id] = tool
    def execute(self, tool_id: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        configured = next((t for t in self._config.tools if t.tool_id == tool_id), None)
        if configured is None or tool_id not in self._tools: raise ValueError("tool_not_registered")
        result = {"status": "BLOCKED", "reason": "tool_permission_denied"} if not configured.enabled or configured.permission != "ALLOW" else self._tools[tool_id].execute(payload)
        self._log.append({"tool_id": tool_id, "status": result["status"]})
        return result
    def execution_log(self): return tuple(dict(item) for item in self._log)
