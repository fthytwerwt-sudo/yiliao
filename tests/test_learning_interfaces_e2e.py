"""验证学习闭环、离线接口与全链路模拟都不产生业务决定或外部副作用。"""

from io import StringIO
import json
import unittest

from medical_tourism_os.interfaces.cli import run_cli
from medical_tourism_os.interfaces.local_api import LocalApiApplication
from medical_tourism_os.workflows.e2e_scenario import run_synthetic_scenario
from medical_tourism_os.workflows.weekly_review import LearningLoop


class LearningInterfacesE2ETests(unittest.TestCase):
    """锁住 Phase 5–7 的 metrics、decision candidate、本地接口与 synthetic E2E。"""

    def test_learning_loop_records_metrics_and_only_creates_decision_candidate(self) -> None:
        """实验与周复盘可以产生候选判断，不能自动写成正式 Decision。"""
        loop = LearningLoop()
        loop.record_metric("TEST_CHANNEL_A", "reach", 100)
        loop.record_metric("TEST_CHANNEL_A", "lead", 4)
        experiment = loop.create_experiment(
            hypothesis="TEST_PRODUCT_A message may clarify a non-clinical question",
            primary_variable="message_angle",
            fixed_variables=("TEST_MARKET_A",),
            window="TEST_WINDOW_A",
            metrics=("reach", "lead"),
        )
        review = loop.review_experiment(experiment.id, result="insufficient_sample")
        weekly = loop.generate_weekly_review()
        candidate = loop.create_decision_candidate(weekly.id)
        sync = loop.github_dry_run(candidate.id)

        self.assertEqual("insufficient_sample", review.result)
        self.assertEqual("message_angle", weekly.primary_variable_candidates[0])
        self.assertEqual("candidate", candidate.status)
        self.assertFalse(sync.executed)
        self.assertTrue(sync.dry_run)
        self.assertNotIn("Decision", candidate.status)

    def test_cli_exposes_required_commands_without_external_execution(self) -> None:
        """CLI 必须提供系统入口与 dry-run 同步命令，且默认输出关闭状态。"""
        output = StringIO()
        code = run_cli(["system", "init"], output=output)
        init_payload = json.loads(output.getvalue())

        sync_output = StringIO()
        sync_code = run_cli(["sync", "github", "--dry-run"], output=sync_output)
        sync_payload = json.loads(sync_output.getvalue())

        self.assertEqual(0, code)
        self.assertFalse(init_payload["external_execution_allowed"])
        self.assertEqual(0, sync_code)
        self.assertTrue(sync_payload["dry_run"])
        self.assertFalse(sync_payload["executed"])

    def test_local_api_and_admin_debug_are_loopback_only_and_list_required_routes(self) -> None:
        """本地接口不能绑定公网；Admin 只显示调试状态与 adapter 关闭状态。"""
        app = LocalApiApplication()
        index_status, index_body = app.handle("GET", "/")
        facts_status, facts_body = app.handle("GET", "/facts")

        self.assertEqual("127.0.0.1", app.bind_host)
        self.assertEqual(200, index_status)
        self.assertIn("Adapter status: disabled", index_body)
        self.assertEqual(200, facts_status)
        self.assertIn("items", facts_body)
        for route in (
            "/research", "/facts", "/demand", "/products", "/content", "/publishing",
            "/comments", "/dms", "/risks", "/leads", "/matches", "/metrics",
            "/experiments", "/reviews", "/decisions",
        ):
            self.assertIn(route, app.routes)

    def test_synthetic_e2e_runs_every_stage_and_never_claims_business_validation(self) -> None:
        """完整 synthetic 轨迹必须可跑完，但终点只能是 candidate 与 GitHub dry-run。"""
        result = run_synthetic_scenario()

        self.assertEqual(
            (
                "Research", "Fact", "Demand", "Product", "Content", "Comment/DM", "Risk",
                "Lead", "Match", "Metrics", "Experiment", "Weekly Review", "Decision Candidate",
                "GitHub Dry Run",
            ),
            result.stages,
        )
        self.assertEqual("candidate", result.decision_candidate_status)
        self.assertTrue(result.github_sync_dry_run)
        self.assertFalse(result.business_validation_completed)
        self.assertTrue(all(item.startswith("TEST_") for item in result.synthetic_identifiers))


if __name__ == "__main__":
    unittest.main()
