"""Regression checks for the collaboration-system refactor.

These checks protect the boundary between research inputs, dynamic project
facts, the static ChatGPT Project package, and Codex execution authority.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
COLLABORATION = ROOT / "collaboration_system"
PACKAGE = (
    ROOT
    / "dist"
    / "gpt_project_sync_packages"
    / "2026-08-18_medical_project_collaboration_os"
)
AUDIT = COLLABORATION / "99_Obsidian机制迁移审计.md"

EXPECTED_COLLABORATION_FILES = {
    "00_总览_用户到现实反馈的完整闭环.md",
    "01_用户_ChatGPT_Codex角色与决策权.md",
    "02_真实意图澄清闸门.md",
    "03_目标_边界_验收_停止线.md",
    "04_六层需求确认与Implementation_Design.md",
    "05_事实源裁决与No_Guess_Routing.md",
    "06_任务路由_State_Action_Router.md",
    "07_Codex执行单与执行器权限边界.md",
    "08_Completion_Relay_Gate_做到底机制.md",
    "09_技术_内容_人工_业务_同步完成态.md",
    "10_失败反馈与Self_Repair_Audit.md",
    "11_No_Degrade_禁止降级完成.md",
    "12_Data_Goal_Anchor与单主变量.md",
    "13_外部调研_Perplexity_Reference桥接.md",
    "14_Project_GitHub_本地_Obsidian物理分层.md",
    "15_Log_Commit_Push_Readback状态回写.md",
    "16_Project静态协作包同步机制.md",
    "17_新会话接手与AGENTS机制.md",
    "18_医疗项目特殊安全与专业责任边界.md",
    "99_Obsidian机制迁移审计.md",
}

EXPECTED_PACKAGE_FILES = {
    "00_上传说明_UPLOAD_MANIFEST.md",
    "01_Project总控指令_PROJECT_INSTRUCTIONS.md",
    "02_用户与ChatGPT协作协议.md",
    "03_真实意图澄清闸门.md",
    "04_目标_边界_验收_停止线.md",
    "05_六层需求确认与Implementation_Design.md",
    "06_事实源裁决与No_Guess_Routing.md",
    "07_任务路由与State_Action_Router.md",
    "08_Codex执行单与权限边界.md",
    "09_Completion_Relay_Gate.md",
    "10_完成态与No_Degrade.md",
    "11_失败反馈与Self_Repair_Audit.md",
    "12_Data_Goal_Anchor与单主变量.md",
    "13_外部资料_Perplexity_Reference桥接.md",
    "14_Project_GitHub_本地_Obsidian同步.md",
    "15_新会话接手机制.md",
    "16_医疗项目协作特殊红线.md",
}

EXPECTED_OBSIDIAN_SOURCE_COUNT = 31
FORBIDDEN_PROJECT_PACKAGE_FACTS = (
    "成都东方健康管理",
    "美国首发",
    "USD 3,800",
    "USD 4,800",
    "USD 2,200",
    "5 笔真实订金",
    "Day 0-30 Supply + Compliance",
)
FORBIDDEN_PROJECT_FACT_KEYS = (
    "primary_market",
    "primary_product",
    "conditional_go",
    "day_0_30",
    "supply_and_compliance",
)


class CollaborationSystemContractTests(unittest.TestCase):
    """Lock the user-approved collaboration and fact-source boundaries."""

    def test_canonical_collaboration_system_is_complete(self) -> None:
        """Every required canonical mechanism document must exist once."""
        actual = {path.name for path in COLLABORATION.glob("*.md")}
        self.assertEqual(EXPECTED_COLLABORATION_FILES, actual)

    def test_obsidian_migration_audit_covers_every_source_file(self) -> None:
        """The audit must expose all 31 source mechanisms and a valid status."""
        text = AUDIT.read_text(encoding="utf-8")
        self.assertIn("源文件总数：31", text)
        statuses = re.findall(
            r"\|\s*(migrated|adapted|not_applicable_with_reason|superseded)\s*\|",
            text,
        )
        self.assertEqual(EXPECTED_OBSIDIAN_SOURCE_COUNT, len(statuses))
        self.assertNotIn("| unknown |", text)

    def test_strategy_is_explicitly_unlocked(self) -> None:
        """Research candidates must not be represented as active strategy."""
        state = (ROOT / "project_facts/02_当前状态_project_state.yaml").read_text(
            encoding="utf-8"
        )
        facts = (ROOT / "project_facts/01_当前已确认事实.md").read_text(
            encoding="utf-8"
        )
        current_target = (ROOT / "logs/current_target.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("strategy_definition_pending", state)
        self.assertIn("strategy_locked: false", state)
        self.assertIn("尚未最终锁定", facts)
        self.assertIn("锁定第一轮最小验证闭环", current_target)
        for key in FORBIDDEN_PROJECT_FACT_KEYS:
            self.assertNotIn(key, state)
            self.assertNotIn(key, facts)

    def test_codex_cannot_lock_strategy(self) -> None:
        """AGENTS must block Codex when a strategic choice remains unlocked."""
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("blocked_strategy_not_locked", agents)
        self.assertIn("不得自行决定", agents)

    def test_project_package_contains_mechanisms_not_dynamic_business_facts(
        self,
    ) -> None:
        """The static Project package must be a reusable collaboration OS."""
        actual = {path.name for path in PACKAGE.glob("*.md")}
        self.assertEqual(EXPECTED_PACKAGE_FILES, actual)
        package_text = "\n".join(
            path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.md")
        )
        for fact in FORBIDDEN_PROJECT_PACKAGE_FACTS:
            self.assertNotIn(fact, package_text)

    def test_legacy_project_package_is_deprecated_not_current(self) -> None:
        """The old business-snapshot package must not remain upload-canonical."""
        old_live_path = (
            ROOT
            / "dist"
            / "gpt_project_sync_packages"
            / "2026-08-17_initial_medical_tourism_project"
        )
        archive_marker = (
            ROOT
            / "dist"
            / "project_context_snapshots"
            / "2026-08-17_initial_medical_tourism_project_DEPRECATED_DO_NOT_UPLOAD"
            / "DEPRECATED_DO_NOT_UPLOAD.md"
        )
        self.assertFalse(old_live_path.exists())
        self.assertTrue(archive_marker.exists())

    def test_legacy_execution_rules_are_pointers_only(self) -> None:
        """Compatibility paths must point at, not redefine, the canonical OS."""
        for path in (ROOT / "execution_rules").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("collaboration_system/", text)
            self.assertIn("canonical", text.lower())


if __name__ == "__main__":
    unittest.main()
