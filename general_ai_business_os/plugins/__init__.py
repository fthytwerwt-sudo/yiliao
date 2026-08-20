"""业务插件注册表；插件只能声明 Core API 合同，不能改写 Core Runtime。"""
from __future__ import annotations
from typing import Any, Mapping
class PluginRegistry:
    def __init__(self) -> None: self._plugins = {}
    def register(self, plugin_id: str, manifest: Mapping[str, Any]) -> None:
        if not isinstance(plugin_id, str) or not isinstance(manifest, Mapping) or set(manifest) != {"plugin_version", "core_api"}: raise ValueError("plugin_manifest_invalid")
        if plugin_id in self._plugins: raise ValueError("plugin_duplicate")
        self._plugins[plugin_id] = dict(manifest)
    def get(self, plugin_id: str) -> Mapping[str, Any]:
        if plugin_id not in self._plugins: raise ValueError("plugin_not_found")
        return dict(self._plugins[plugin_id])
