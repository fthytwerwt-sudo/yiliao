"""验证工程范围决策不会被误写成业务战略决策。"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    """读取仓库内的治理文件，供边界回归测试使用。"""
    return (ROOT / relative_path).read_text(encoding="utf-8")


class GovernanceSyncTests(unittest.TestCase):
    """锁住系统工程许可与业务战略未锁定这两个同时成立的状态。"""

    def test_engineering_scope_is_a_user_locked_non_strategy_decision(self) -> None:
        """工程范围决定必须完整记录，且不得借此锁定任何业务路线。"""
        decisions = read("project_facts/04_正式决策记录.md")
        self.assertIn("DEC-ENG-001", decisions)
        self.assertIn("允许建设战略无关系统骨架，但不因此锁定任何业务战略", decisions)
        self.assertIn("decided_by | user", decisions)
        self.assertIn("status | locked", decisions)
        self.assertIn("不需要修改核心领域代码", decisions)

    def test_project_state_allows_architecture_but_keeps_strategy_and_external_execution_off(self) -> None:
        """工程权限只扩大内部开发能力，绝不放开战略或现实执行。"""
        state = read("project_facts/02_当前状态_project_state.yaml")
        self.assertIn("architecture_development_allowed: true", state)
        self.assertIn("business_strategy_locked: false", state)
        self.assertIn("external_execution_allowed: false", state)
        self.assertIn("code: strategy_definition_pending", state)

    def test_script_policy_distinguishes_infrastructure_from_business_automation(self) -> None:
        """脚本规则必须精确允许本地基础设施，同时保留高风险自动化禁令。"""
        policy = read("scripts/README.md")
        for required in (
            "strategy-agnostic system infrastructure",
            "domain models",
            "storage abstraction",
            "Mock adapters",
            "local API",
            "automated tests",
            "自动营销",
            "自动发布",
            "自动 DM",
            "自动医院外联",
            "自动支付",
            "自动医疗判断",
            "Confirmed Fact",
        ):
            self.assertIn(required, policy)

    def test_latest_log_preserves_the_completion_boundary(self) -> None:
        """日志必须可让下一会话识别工程授权不是业务完成。"""
        latest = read("logs/latest.md")
        self.assertIn("engineering_scope_decision", latest)
        self.assertIn("technical implementation", latest)
        self.assertIn("不构成业务战略锁定", latest)


if __name__ == "__main__":
    unittest.main()
