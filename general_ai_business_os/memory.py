"""
用途：提供可替换的 Agent Memory Interface（Agent 记忆接口）。

上游：Agent Runtime 在一次本地执行后保存最小运行状态。

下游：未来持久化或向量 Memory Adapter 可实现同一接口。

边界：当前仅为进程内 Mock，不保存业务事实、个人资料或外部账户信息。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Mapping

class MemoryStore(ABC):
    @abstractmethod
    def put(self, key: str, value: Mapping[str, Any]) -> None: ...
    @abstractmethod
    def get(self, key: str) -> Mapping[str, Any] | None: ...
class InMemoryStore(MemoryStore):
    def __init__(self) -> None: self._items = {}
    def put(self, key, value): self._items[key] = dict(value)
    def get(self, key): return dict(self._items[key]) if key in self._items else None
