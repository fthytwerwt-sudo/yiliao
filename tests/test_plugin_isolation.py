"""验证 Plugin Manifest、Lifecycle 与 Permission Boundary 都停留在受限的 Core API 表面。"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from general_ai_business_os.plugins import PluginRegistry


class PluginIsolationTests(unittest.TestCase):
    """V1 Plugin 只登记声明，不导入或执行 entrypoint，更不能取得未声明的 Core capability。"""

    @staticmethod
    def _manifest(*, permissions: list[str] | None = None) -> dict[str, object]:
        return {
            "plugin_id": "TEST_PLUGIN",
            "version": "TEST_V1",
            "permissions": permissions if permissions is not None else ["TOOL_INVOKE"],
            "dependencies": [],
            "entrypoint": "test_plugin.entrypoint:build",
        }

    def test_discovery_registers_only_and_permission_boundary_denies_undeclared_capabilities(self) -> None:
        """发现 plugin.json 只能写入 Manifest；activate 前不得执行，未声明 capability 必须拒绝。"""

        with tempfile.TemporaryDirectory() as directory:
            plugin_directory = Path(directory) / "TEST_PLUGIN"
            plugin_directory.mkdir()
            (plugin_directory / "plugin.json").write_text(json.dumps(self._manifest()), encoding="utf-8")

            registry = PluginRegistry()
            self.assertEqual(("TEST_PLUGIN",), registry.discover(Path(directory)))

        self.assertEqual((), registry.active())
        self.assertFalse(registry.authorize("TEST_PLUGIN", "TOOL_INVOKE"))
        registry.activate("TEST_PLUGIN")
        self.assertTrue(registry.authorize("TEST_PLUGIN", "TOOL_INVOKE"))
        self.assertFalse(registry.authorize("TEST_PLUGIN", "MODEL_INVOKE"))

    def test_manifest_rejects_unknown_capability_and_invalid_entrypoint(self) -> None:
        """Plugin 不可声明 `BYPASS_CORE` 等私有能力，也不能以路径/自由文本伪装 entrypoint。"""

        registry = PluginRegistry()
        with self.assertRaisesRegex(ValueError, "plugin_manifest_invalid"):
            registry.register("TEST_PLUGIN", self._manifest(permissions=["BYPASS_CORE"]))

        invalid_entrypoint = self._manifest()
        invalid_entrypoint["entrypoint"] = "../../outside"
        with self.assertRaisesRegex(ValueError, "plugin_manifest_invalid"):
            registry.register("TEST_PLUGIN", invalid_entrypoint)

    def test_discovery_maps_invalid_json_to_closed_manifest_error(self) -> None:
        """坏的本地文件只能造成明确阻断，不能泄漏 JSON parser 异常给 Plugin 调用方。"""

        with tempfile.TemporaryDirectory() as directory:
            plugin_directory = Path(directory) / "TEST_PLUGIN"
            plugin_directory.mkdir()
            (plugin_directory / "plugin.json").write_text("{", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "plugin_manifest_invalid"):
                PluginRegistry().discover(Path(directory))


if __name__ == "__main__":
    unittest.main()
