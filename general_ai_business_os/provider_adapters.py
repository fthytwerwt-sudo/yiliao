"""Provider Adapter：OpenAI、DeepSeek、Kimi 统一接口，真实调用默认 disabled。"""
from __future__ import annotations
from general_ai_business_os.model_gateway import LLMProvider

class DisabledProviderAdapter(LLMProvider):
    def __init__(self, provider_name: str) -> None: self.provider_name = provider_name
    def chat(self, messages, model): return {"status": "BLOCKED", "reason": "provider_disabled", "provider": self.provider_name, "model": model}
    def generate(self, prompt, model): return {"status": "BLOCKED", "reason": "provider_disabled", "provider": self.provider_name, "model": model}
    def embedding(self, text, model): return {"status": "BLOCKED", "reason": "provider_disabled", "provider": self.provider_name, "model": model}
class OpenAIAdapter(DisabledProviderAdapter):
    def __init__(self) -> None: super().__init__("OPENAI")
class DeepSeekAdapter(DisabledProviderAdapter):
    def __init__(self) -> None: super().__init__("DEEPSEEK")
class KimiAdapter(DisabledProviderAdapter):
    def __init__(self) -> None: super().__init__("KIMI")
