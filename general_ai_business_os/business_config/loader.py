"""
用途：
从一个 Business Config Package 目录安全读取 JSON/YAML manifest 与能力域文档。

上游：
CLI、Local API 或离线工具传入本地配置包路径。

下游：
Validator 取得 mapping 根结构并构造领域对象。

边界：
这里只负责安全读取和文件名白名单，不批准、不推断、不修改任何业务值。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping

import yaml

from general_ai_business_os.business_config.contracts import ConfigLoadError, ConfigValidationError


_ALLOWED_DOCUMENT_NAMES = {
    "market",
    "customer",
    "product",
    "channel",
    "content_rules",
    "sales_rules",
    "lead_rules",
}
_SUPPORTED_SUFFIXES = {".json", ".yaml", ".yml"}


class BusinessConfigLoader:
    """安全读取单一目录中的配置包，并拒绝未声明文件名和多份 manifest。"""

    def load(self, package_path: Path) -> tuple[Mapping[str, Any], Dict[str, Mapping[str, Any]]]:
        """返回 manifest 与按能力域命名的文档 mapping；所有格式差异在此处收敛。"""

        if not package_path.is_dir():
            raise ConfigLoadError("config_package_directory_required")
        manifest_files = []
        documents: Dict[str, Mapping[str, Any]] = {}
        for path in sorted(package_path.iterdir()):
            if not path.is_file():
                raise ConfigValidationError("config_package_contains_non_file_entry")
            if path.suffix.lower() not in _SUPPORTED_SUFFIXES:
                raise ConfigValidationError("config_package_file_suffix_not_supported")
            name = path.stem
            payload = self._read_mapping(path)
            if name == "manifest":
                manifest_files.append(payload)
                continue
            if name not in _ALLOWED_DOCUMENT_NAMES:
                raise ConfigValidationError("config_document_name_not_allowed")
            if name in documents:
                raise ConfigValidationError("config_document_duplicate")
            documents[name] = payload
        if len(manifest_files) != 1:
            raise ConfigValidationError("config_manifest_must_exist_once")
        return manifest_files[0], documents

    @staticmethod
    def _read_mapping(path: Path) -> Mapping[str, Any]:
        """使用 JSON 标准库或 yaml.safe_load 读取 mapping 根，禁止对象构造和 list 根。"""

        try:
            content = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".json":
                payload = json.loads(content)
            else:
                payload = yaml.safe_load(content)
        except (OSError, json.JSONDecodeError, yaml.YAMLError) as error:
            raise ConfigLoadError("config_document_parse_failed") from error
        if not isinstance(payload, Mapping):
            raise ConfigLoadError("config_document_mapping_required")
        try:
            BusinessConfigLoader._ensure_acyclic(payload, active_container_ids=set())
        except RecursionError as error:
            raise ConfigLoadError("config_document_cycle_not_allowed") from error
        return payload

    @staticmethod
    def _ensure_acyclic(value: Any, *, active_container_ids: set[int]) -> None:
        """拒绝 YAML alias 形成的循环容器，避免冻结/序列化递归耗尽并统一返回结构化错误。"""

        if isinstance(value, Mapping):
            identifier = id(value)
            if identifier in active_container_ids:
                raise ConfigLoadError("config_document_cycle_not_allowed")
            active_container_ids.add(identifier)
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ConfigLoadError("config_document_key_not_string")
                BusinessConfigLoader._ensure_acyclic(item, active_container_ids=active_container_ids)
            active_container_ids.remove(identifier)
        elif isinstance(value, list):
            identifier = id(value)
            if identifier in active_container_ids:
                raise ConfigLoadError("config_document_cycle_not_allowed")
            active_container_ids.add(identifier)
            for item in value:
                BusinessConfigLoader._ensure_acyclic(item, active_container_ids=active_container_ids)
            active_container_ids.remove(identifier)
