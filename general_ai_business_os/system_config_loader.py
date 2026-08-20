"""读取 AI System Configuration 的 JSON/YAML 文件，并以 Secret Reference 解析器隔离密钥原文。"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping
import yaml
from general_ai_business_os.ai_system_config import AiSystemConfig, ConfigError

class SecretResolver:
    """本地运行时才解析 Secret Reference；配置、日志与 Git 永远只持有 reference。"""
    def __init__(self, values: Mapping[str, str]) -> None: self._values = dict(values)
    def resolve(self, reference: str) -> str:
        if reference not in self._values: raise ConfigError("secret_reference_unavailable")
        return self._values[reference]

def load_system_config(path: Path) -> AiSystemConfig:
    """读取 mapping 根的 JSON/YAML 系统配置；未支持格式和解析失败均 fail-closed。"""
    try:
        content = path.read_text(encoding="utf-8")
        payload: Any = json.loads(content) if path.suffix == ".json" else yaml.safe_load(content) if path.suffix in {".yaml", ".yml"} else None
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as error:
        raise ConfigError("system_config_load_failed") from error
    if not isinstance(payload, Mapping): raise ConfigError("system_config_mapping_required")
    return AiSystemConfig.from_mapping(payload)
