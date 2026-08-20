"""
用途：提供可替换的 Agent Memory Interface（Agent 记忆接口）。

上游：Agent Runtime 在一次本地执行后保存最小运行状态。

下游：未来持久化或向量 Memory Adapter 可实现同一接口。

边界：当前仅为进程内 Mock，不保存业务事实、个人资料或外部账户信息。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Mapping

class MemoryStore(ABC):
    @abstractmethod
    def put(self, key: str, value: Mapping[str, Any]) -> None: ...
    @abstractmethod
    def get(self, key: str) -> Mapping[str, Any] | None: ...
class InMemoryStore(MemoryStore):
    """进程内 Memory 实现；以深拷贝维持调用方与内部快照之间的隔离。"""

    def __init__(self) -> None:
        self._items: dict[str, Mapping[str, Any]] = {}

    def put(self, key: str, value: Mapping[str, Any]) -> None:
        # Agent 结果通常含嵌套 Tool/Evaluation 数据。这里必须复制整棵结构，
        # 否则调用方保留的 payload 可以在 put() 后改写 Memory 的历史快照。
        self._items[key] = deepcopy(dict(value))

    def get(self, key: str) -> Mapping[str, Any] | None:
        # 同样不能返回内部引用；读取方的局部整理不得反向篡改已记录的运行状态。
        return deepcopy(self._items[key]) if key in self._items else None

class LocalMemoryAdapter(InMemoryStore):
    """本地短期/任务/运行状态 Memory，不连接外部服务。"""

class VectorMemoryAdapter(InMemoryStore):
    """Vector Memory 适配接口的本地 Mock；未来可连接 Qdrant/Chroma。"""

class DatabaseMemoryAdapter(InMemoryStore):
    """Database Memory 适配接口的本地 Mock；未来可连接 pgvector。"""
