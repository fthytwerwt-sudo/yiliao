"""锁定 General AI Core 与 Application Plugin 的目录和导入边界。"""

from __future__ import annotations

from pathlib import Path
import unittest


class CorePluginBoundaryTests(unittest.TestCase):
    """业务配置治理可以作为可选插件存在，但不能重新成为 Core Runtime 的一部分。"""

    def test_business_config_lives_only_in_application_plugin_layer(self) -> None:
        """ADR-0002 要求市场/销售规则等业务语义从 `general_ai_business_os` 完全移出。"""

        core_root = Path(__file__).resolve().parents[1] / "general_ai_business_os"

        # `__pycache__` 可能由上一轮测试遗留；边界应检查可导入的源码入口，
        # 而不是把解释器生成的缓存目录误判为仍在运行的 Core 子包。
        self.assertFalse((core_root / "business_config" / "__init__.py").exists())

        for source_path in core_root.rglob("*.py"):
            self.assertNotIn("business_config", source_path.read_text(encoding="utf-8"), source_path)

    def test_superseded_core_business_config_plans_cannot_be_mistaken_for_current_instructions(self) -> None:
        """已被 ADR-0002 否决的计划必须显式归档，防止下一轮开发把业务事实重新写回 Core。"""

        plans_root = Path(__file__).resolve().parents[1] / "docs" / "plans"
        for filename in (
            "2026-08-20_General-AI-Business-Operating-System-V1_设计.md",
            "2026-08-20_General-AI-Business-Operating-System-V1_实施计划.md",
        ):
            content = (plans_root / filename).read_text(encoding="utf-8")
            self.assertIn("Status: Superseded", content)
            self.assertIn("ADR-0002", content)
            self.assertNotIn("Create: `general_ai_business_os/business_config/", content)


if __name__ == "__main__":
    unittest.main()
