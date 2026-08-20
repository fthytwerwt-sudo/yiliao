"""
用途：管理 Application Plugin 的 Manifest 与 Lifecycle，不加载或执行 Plugin 代码。

上游：本地插件目录或宿主进程登记受限的 `plugin.json`。

下游：未来受控的 Plugin Host 可读取 active Manifest，并仍须通过 Model Gateway、
Tool Registry 与 PermissionPolicy 请求实际能力。

边界：V1 不 import entrypoint、不把 Core 对象交给 Plugin，也不提供通用执行器；
因此 Manifest 不能借本注册表绕过任何 Core security gate。
"""
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
import re
from typing import Any, Mapping


_PLUGIN_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
_ENTRYPOINT = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*$")
_CAPABILITIES = frozenset({"MODEL_INVOKE", "TOOL_INVOKE", "MEMORY_READ", "WORKFLOW_RUN"})


class PluginRegistry:
    """只保存深拷贝 Manifest；生命周期状态不等同于 Plugin 代码已执行。"""

    def __init__(self) -> None:
        self._plugins: dict[str, dict[str, Any]] = {}
        self._active: set[str] = set()

    def register(self, plugin_id: str, manifest: Mapping[str, Any]) -> None:
        """校验 closed Manifest；未知权限或路径型 entrypoint 都在登记前拒绝。"""

        required = {"plugin_id", "version", "permissions", "dependencies", "entrypoint"}
        permissions = manifest.get("permissions") if isinstance(manifest, Mapping) else None
        dependencies = manifest.get("dependencies") if isinstance(manifest, Mapping) else None
        if (
            not isinstance(plugin_id, str)
            or not _PLUGIN_CODE.fullmatch(plugin_id)
            or not isinstance(manifest, Mapping)
            or set(manifest) != required
            or manifest.get("plugin_id") != plugin_id
            or not isinstance(manifest["version"], str)
            or not manifest["version"].strip()
            or not isinstance(manifest["entrypoint"], str)
            or not _ENTRYPOINT.fullmatch(manifest["entrypoint"])
            or not isinstance(permissions, list)
            or any(not isinstance(item, str) or item not in _CAPABILITIES for item in permissions)
            or len(set(permissions)) != len(permissions)
            or not isinstance(dependencies, list)
            or any(not isinstance(item, str) or not _PLUGIN_CODE.fullmatch(item) for item in dependencies)
            or len(set(dependencies)) != len(dependencies)
        ):
            raise ValueError("plugin_manifest_invalid")
        if plugin_id in self._plugins:
            raise ValueError("plugin_duplicate")
        self._plugins[plugin_id] = deepcopy(dict(manifest))

    def get(self, plugin_id: str) -> Mapping[str, Any]:
        """返回独立的 Manifest 快照，防止读取方篡改注册表内部权限声明。"""

        if plugin_id not in self._plugins:
            raise ValueError("plugin_not_found")
        return deepcopy(self._plugins[plugin_id])

    def install(self, plugin_id: str, manifest: Mapping[str, Any]) -> None:
        """安装仅登记 Manifest；不执行 `entrypoint`。"""

        self.register(plugin_id, manifest)

    def load(self, plugin_id: str) -> Mapping[str, Any]:
        """读取登记的 Manifest；名称兼容 Lifecycle 术语但不触发 import。"""

        return self.get(plugin_id)

    def enable(self, plugin_id: str) -> None:
        """将已登记 Plugin 标为 active；真正 capability 调用仍需宿主的额外安全闸门。"""

        self.get(plugin_id)
        self._active.add(plugin_id)

    def disable(self, plugin_id: str) -> None:
        self._active.discard(plugin_id)

    def activate(self, plugin_id: str) -> None:
        self.enable(plugin_id)

    def deactivate(self, plugin_id: str) -> None:
        self.disable(plugin_id)

    def uninstall(self, plugin_id: str) -> None:
        self.disable(plugin_id)
        self._plugins.pop(plugin_id, None)

    def active(self) -> tuple[str, ...]:
        return tuple(sorted(self._active))

    def authorize(self, plugin_id: str, capability: str) -> bool:
        """检查 active Plugin 的声明能力；它不替代 Model/Tool 的全局 PermissionPolicy。"""

        return plugin_id in self._active and capability in self._plugins.get(plugin_id, {}).get("permissions", ())

    def discover(self, directory: Path) -> tuple[str, ...]:
        """发现本地 plugin.json；只读取 manifest，不执行插件代码或加载业务数据。"""

        if not directory.is_dir():
            raise ValueError("plugin_directory_not_found")
        discovered = []
        for path in sorted(directory.glob("*/plugin.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ValueError("plugin_manifest_invalid") from error
            self.register(path.parent.name.upper(), payload)
            discovered.append(path.parent.name.upper())
        return tuple(discovered)
