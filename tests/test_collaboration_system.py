"""Regression checks for the collaboration-system semantic migration.

These checks protect the boundary between research inputs, dynamic project
facts, the static ChatGPT Project package, and Codex execution authority.
They also guard against the earlier failure mode where files existed but the
mechanism behavior had been reduced to short summaries.
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
    / "2026-08-18_medical_project_collaboration_os_v2"
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
    "02_用户_ChatGPT_Codex完整协作协议.md",
    "03_判断系统_真实意图_目标_边界_验收_停止线.md",
    "04_Implementation_Design_任务路由_No_Guess.md",
    "05_Codex执行合同_Completion_Relay_完成态.md",
    "06_失败反馈_Self_Repair_No_Degrade.md",
    "07_Data_Goal_Anchor_现实验证与反馈.md",
    "08_外部资料_Perplexity_事实裁决_Reference桥接.md",
    "09_Project_GitHub_本地_Obsidian_同步与接手.md",
    "10_医疗项目特殊协作与安全边界.md",
}

EXPECTED_OBSIDIAN_SOURCE_COUNT = 31
EXPECTED_BEHAVIOR_ELEMENTS_PER_SOURCE = 20
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
FORBIDDEN_AUDIT_STATUSES = (
    "| summary |",
    "| roughly covered |",
    "| mentioned |",
    "| implicit |",
)


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(case: unittest.TestCase, body: str, required: tuple[str, ...]) -> None:
    for item in required:
        case.assertIn(item, body)


class CollaborationSystemContractTests(unittest.TestCase):
    """Lock the user-approved collaboration and fact-source boundaries."""

    def test_canonical_collaboration_system_is_complete(self) -> None:
        """Every required canonical mechanism document must exist once."""
        actual = {path.name for path in COLLABORATION.glob("*.md")}
        self.assertEqual(EXPECTED_COLLABORATION_FILES, actual)

    def test_semantic_audit_covers_every_source_and_behavior_element(self) -> None:
        """The audit must expose section-level coverage, not file-level labels."""
        body = text(AUDIT)
        assert_contains_all(
            self,
            body,
            (
                "Section-level Semantic Coverage Audit",
                "source_files_read: 31",
                "core_behavior_elements_per_source: 20",
                "total_behavior_elements: 620",
                "missing_elements: 0",
                "semantic_coverage: 100%",
                "Human-style semantic audit: pass",
            ),
        )
        for forbidden in FORBIDDEN_AUDIT_STATUSES:
            self.assertNotIn(forbidden, body)

        source_rows = re.findall(
            r"^\| S\d{2} \|\s*(?:preserved|adapted_preserved|not_applicable_with_reason|intentionally_merged_into)",
            body,
            flags=re.MULTILINE,
        )
        self.assertEqual(EXPECTED_OBSIDIAN_SOURCE_COUNT, len(source_rows))

        detailed_rows = re.findall(
            r"\b(?:adapted_preserved|not_applicable_with_reason|intentionally_merged_into|preserved)\b",
            body,
        )
        self.assertGreaterEqual(
            len(detailed_rows),
            EXPECTED_OBSIDIAN_SOURCE_COUNT * EXPECTED_BEHAVIOR_ELEMENTS_PER_SOURCE,
        )

    def test_core_mechanisms_are_executable_not_suspiciously_thin(self) -> None:
        """Byte size is only a probe, but it catches summary-shell regressions."""
        core_collaboration = [
            "02_真实意图澄清闸门.md",
            "04_六层需求确认与Implementation_Design.md",
            "07_Codex执行单与执行器权限边界.md",
            "08_Completion_Relay_Gate_做到底机制.md",
            "10_失败反馈与Self_Repair_Audit.md",
            "11_No_Degrade_禁止降级完成.md",
            "12_Data_Goal_Anchor与单主变量.md",
            "13_外部调研_Perplexity_Reference桥接.md",
            "16_Project静态协作包同步机制.md",
            "18_医疗项目特殊安全与专业责任边界.md",
        ]
        for name in core_collaboration:
            self.assertGreaterEqual((COLLABORATION / name).stat().st_size, 1800, name)

        for path in PACKAGE.glob("*.md"):
            minimum = 1400 if path.name.startswith(("00_", "01_")) else 2600
            self.assertGreaterEqual(path.stat().st_size, minimum, path.name)

    def test_true_intent_gate_preserves_behavior(self) -> None:
        body = text(COLLABORATION / "02_真实意图澄清闸门.md")
        assert_contains_all(
            self,
            body,
            (
                "本轮真正要判断",
                "本轮不判断",
                "成功",
                "失败",
                "停止",
                "GPT 必须先回答",
                "Codex",
                "blocked_missing_true_intent_gate",
                "我们先去找医院",
                "Supply 是否真的是此刻最大未知",
            ),
        )

    def test_implementation_design_and_routing_fields_are_preserved(self) -> None:
        body = text(COLLABORATION / "04_六层需求确认与Implementation_Design.md")
        assert_contains_all(
            self,
            body,
            (
                "1 Goal",
                "2 Mechanism",
                "3 Implementation Design",
                "4 Workflow",
                "5 Acceptance",
                "6 Feedback",
                "primary_route",
                "fallback_route",
                "capability_status",
                "probe_required",
                "allowed_codex_autonomy",
                "forbidden_codex_guessing",
                "blocked_if",
                "不能只说：去找美国客户",
            ),
        )

    def test_codex_contract_completion_and_self_repair_fields_are_preserved(self) -> None:
        codex_contract = text(COLLABORATION / "07_Codex执行单与执行器权限边界.md")
        assert_contains_all(
            self,
            codex_contract,
            (
                "Goal",
                "Context",
                "Current State",
                "Locked Anchors",
                "Constraints",
                "Impact Check",
                "Allowed Changes",
                "Forbidden Changes",
                "Must Read",
                "Implementation Design",
                "Execution Steps",
                "Done When",
                "Blocked If",
                "Validation",
                "Sync Back",
                "Final Output",
            ),
        )

        relay = text(COLLABORATION / "08_Completion_Relay_Gate_做到底机制.md")
        assert_contains_all(
            self,
            relay,
            (
                "required_output_inventory",
                "child_task_graph",
                "remaining_work_check",
                "sync_back_check",
                "局部结果",
                "不得 completed",
            ),
        )

        repair = text(COLLABORATION / "10_失败反馈与Self_Repair_Audit.md")
        assert_contains_all(
            self,
            repair,
            (
                "observed_mismatch",
                "expected",
                "actual",
                "fault_layer",
                "root_cause",
                "minimal_fix",
                "regression_scope",
                "done_when",
                "用户不负责内部诊断",
            ),
        )

    def test_data_goal_and_research_bridge_fields_are_preserved(self) -> None:
        data_goal = text(COLLABORATION / "12_Data_Goal_Anchor与单主变量.md")
        assert_contains_all(
            self,
            data_goal,
            (
                "current_stage_goal",
                "main_bottleneck",
                "primary_variable",
                "supporting_variables",
                "forbidden_variables",
                "success_metric",
                "failure_metric",
                "post_validation_metric",
                "confidence",
                "revisit_trigger",
            ),
        )

        research = text(COLLABORATION / "13_外部调研_Perplexity_Reference桥接.md")
        assert_contains_all(
            self,
            research,
            (
                "Research",
                "Fact candidate",
                "Confirmed fact",
                "Inference",
                "Hypothesis",
                "Decision",
                "Unknown",
                "研究报告",
                "项目决策",
                "source + date + scope",
            ),
        )

    def test_strategy_is_explicitly_unlocked(self) -> None:
        """Research candidates must not be represented as active strategy."""
        state = text(ROOT / "project_facts/02_当前状态_project_state.yaml")
        facts = text(ROOT / "project_facts/01_当前已确认事实.md")
        current_target = text(ROOT / "logs/current_target.md")
        self.assertIn("strategy_definition_pending", state)
        self.assertIn("strategy_locked: false", state)
        self.assertIn("尚未最终锁定", facts)
        self.assertIn("锁定第一轮最小验证闭环", current_target)
        for key in FORBIDDEN_PROJECT_FACT_KEYS:
            self.assertNotIn(key, state)
            self.assertNotIn(key, facts)

    def test_codex_cannot_lock_strategy(self) -> None:
        """AGENTS must block Codex when a strategic choice remains unlocked."""
        agents = text(ROOT / "AGENTS.md")
        self.assertIn("blocked_strategy_not_locked", agents)
        self.assertIn("不得自行决定", agents)
        self.assertIn("collaboration_system/00_总览_用户到现实反馈的完整闭环.md", agents)

    def test_project_package_contains_self_contained_mechanisms_not_business_facts(self) -> None:
        """The static Project package must be a reusable collaboration OS."""
        actual = {path.name for path in PACKAGE.glob("*.md")}
        self.assertEqual(EXPECTED_PACKAGE_FILES, actual)
        package_text = "\n".join(text(path) for path in PACKAGE.glob("*.md"))
        for fact in FORBIDDEN_PROJECT_PACKAGE_FACTS:
            self.assertNotIn(fact, package_text)

        assert_contains_all(
            self,
            package_text,
            (
                "Scenario 1",
                "我觉得先做美国市场",
                "候选输入，不是自动 DECISION",
                "Scenario 2",
                "你直接让 Codex 开始找医院",
                "真实意图",
                "Scenario 3",
                "Codex 做完了，但是我觉得不对",
                "self_repair_audit",
                "Scenario 4",
                "文件已创建、测试通过",
                "Completion Relay",
                "Scenario 5",
                "Perplexity 给出一份市场报告",
                "外部供料，不是项目事实",
                "Scenario 6",
                "明天用户把美国改英国",
                "Project 包不需要改",
            ),
        )

    def test_project_package_v2_is_canonical_and_old_packages_are_deprecated(self) -> None:
        """Semantic v2 must replace the thin package without reviving old facts."""
        old_thin_live_path = (
            ROOT
            / "dist"
            / "gpt_project_sync_packages"
            / "2026-08-18_medical_project_collaboration_os"
        )
        old_thin_archive_marker = (
            ROOT
            / "dist"
            / "gpt_project_sync_packages"
            / "2026-08-18_medical_project_collaboration_os_DEPRECATED_SEMANTICALLY_INCOMPLETE_DO_NOT_UPLOAD"
            / "DEPRECATED_SEMANTICALLY_INCOMPLETE_DO_NOT_UPLOAD.md"
        )
        old_business_marker = (
            ROOT
            / "dist"
            / "project_context_snapshots"
            / "2026-08-17_initial_medical_tourism_project_DEPRECATED_DO_NOT_UPLOAD"
            / "DEPRECATED_DO_NOT_UPLOAD.md"
        )
        index = text(ROOT / "local_path_index.md")
        self.assertFalse(old_thin_live_path.exists())
        self.assertTrue(old_thin_archive_marker.exists())
        self.assertTrue(old_business_marker.exists())
        self.assertIn(str(PACKAGE), index)
        self.assertIn("DEPRECATED_SEMANTICALLY_INCOMPLETE_DO_NOT_UPLOAD", index)

    def test_legacy_execution_rules_are_pointers_only(self) -> None:
        """Compatibility paths must point at, not redefine, the canonical OS."""
        for path in (ROOT / "execution_rules").glob("*.md"):
            body = text(path)
            self.assertIn("collaboration_system/", body)
            self.assertIn("canonical", body.lower())


if __name__ == "__main__":
    unittest.main()
