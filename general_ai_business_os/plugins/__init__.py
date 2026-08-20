"""业务插件注册表；插件只能声明 Core API 合同，不能改写 Core Runtime。"""
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping
class PluginRegistry:
    def __init__(self) -> None: self._plugins, self._active = {}, set()
    def register(self, plugin_id: str, manifest: Mapping[str, Any]) -> None:
        required = {"plugin_id", "version", "permissions", "dependencies", "entrypoint"}
        if not isinstance(plugin_id, str) or not isinstance(manifest, Mapping) or set(manifest) != required or manifest.get("plugin_id") != plugin_id or not isinstance(manifest["version"], str) or not isinstance(manifest["entrypoint"], str) or not isinstance(manifest["permissions"], list) or not isinstance(manifest["dependencies"], list): raise ValueError("plugin_manifest_invalid")
        if plugin_id in self._plugins: raise ValueError("plugin_duplicate")
        self._plugins[plugin_id] = deepcopy(dict(manifest))
    def get(self, plugin_id: str) -> Mapping[str, Any]:
        if plugin_id not in self._plugins: raise ValueError("plugin_not_found")
        return deepcopy(self._plugins[plugin_id])
    def install(self, plugin_id: str, manifest: Mapping[str, Any]) -> None: self.register(plugin_id, manifest)
    def load(self, plugin_id: str) -> Mapping[str, Any]: return self.get(plugin_id)
    def enable(self, plugin_id: str) -> None:
        self.get(plugin_id); self._active.add(plugin_id)
    def disable(self, plugin_id: str) -> None: self._active.discard(plugin_id)
    def activate(self, plugin_id: str) -> None: self.enable(plugin_id)
    def deactivate(self, plugin_id: str) -> None: self.disable(plugin_id)
    def uninstall(self, plugin_id: str) -> None: self.disable(plugin_id); self._plugins.pop(plugin_id, None)
    def active(self) -> tuple[str, ...]: return tuple(sorted(self._active))
    def discover(self, directory: Path) -> tuple[str, ...]:
        """发现本地 plugin.json；只读取 manifest，不执行插件代码或加载业务数据。"""
        if not directory.is_dir(): raise ValueError("plugin_directory_not_found")
        discovered = []
        for path in sorted(directory.glob("*/plugin.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.register(path.parent.name.upper(), payload)
            discovered.append(path.parent.name.upper())
        return tuple(discovered)
