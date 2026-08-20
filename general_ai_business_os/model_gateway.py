"""统一模型网关：Agent 只调用 Gateway，真实 Provider 默认不执行。"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Mapping
from general_ai_business_os.ai_system_config import AiSystemConfig

class LLMProvider(ABC):
    """Provider Adapter 合同，支持 chat、generate 与 embedding。"""
    @abstractmethod
    def chat(self, messages: list[Mapping[str, str]], model: str) -> Mapping[str, Any]: ...
    @abstractmethod
    def generate(self, prompt: str, model: str) -> Mapping[str, Any]: ...
    @abstractmethod
    def embedding(self, text: str, model: str) -> Mapping[str, Any]: ...

class MockLlmProvider(LLMProvider):
    """确定性本地 Mock；不读取 Secret、不联网、不产生费用。"""
    def chat(self, messages, model): return {"status": "MOCK", "model": model, "content": messages[-1]["content"] if messages else ""}
    def generate(self, prompt, model): return {"status": "MOCK", "model": model, "content": prompt}
    def embedding(self, text, model): return {"status": "MOCK", "model": model, "vector": [float(len(text))]}

class ModelGateway:
    """按 Provider 配置路由请求；没有注册 Mock/Adapter 时 fail-closed。"""
    def __init__(self, config: AiSystemConfig, providers: Mapping[str, LLMProvider]) -> None:
        self._config, self._providers = config, dict(providers)
    def chat(self, provider_name: str, messages: list[Mapping[str, str]]) -> Mapping[str, Any]:
        provider_config = next((p for p in self._config.providers if p.provider_name == provider_name), None)
        if provider_config is None or provider_name not in self._providers: raise ValueError("model_provider_not_registered")
        return self._providers[provider_name].chat(messages, provider_config.model_name)
