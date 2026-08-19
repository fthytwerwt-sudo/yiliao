"""验证学习闭环、离线接口与全链路模拟都不产生业务决定或外部副作用。"""

from io import StringIO
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.request import urlopen

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

    def test_cli_state_root_persists_sqlite_and_review_targets_same_record(self) -> None:
        """同一临时 state_root 下，init/import/list/review 必须命中同一 SQLite 与同一 fact。"""
        with tempfile.TemporaryDirectory() as directory:
            state_root = Path(directory)
            database_path = state_root / "medical-tourism-os.sqlite3"

            init_output = StringIO()
            init_code = run_cli(["--state-root", str(state_root), "system", "init"], output=init_output)
            init_payload = json.loads(init_output.getvalue())

            import_output = StringIO()
            import_code = run_cli(["--state-root", str(state_root), "research", "import"], output=import_output)
            import_payload = json.loads(import_output.getvalue())

            list_output = StringIO()
            list_code = run_cli(["--state-root", str(state_root), "facts", "list"], output=list_output)
            list_payload = json.loads(list_output.getvalue())

            review_output = StringIO()
            review_code = run_cli(
                ["--state-root", str(state_root), "facts", "review", import_payload["record_id"]],
                output=review_output,
            )
            review_payload = json.loads(review_output.getvalue())
            self.assertEqual(0, init_code)
            self.assertTrue(database_path.exists())
            self.assertEqual(str(database_path), init_payload["database_path"])
            self.assertEqual(0, import_code)
            self.assertEqual(0, list_code)
            self.assertEqual(0, review_code)
            self.assertEqual(
                [import_payload["record_id"]],
                [item["id"] for item in list_payload["items"]],
            )
            self.assertEqual(import_payload["record_id"], review_payload["items"][0]["id"])

    def test_local_api_reads_the_same_state_root_as_cli(self) -> None:
        """Local API 若指向同一 state_root，必须看见 CLI 导入的同一 fact。"""
        with tempfile.TemporaryDirectory() as directory:
            state_root = Path(directory)
            import_output = StringIO()
            run_cli(["--state-root", str(state_root), "system", "init"], output=StringIO())
            run_cli(["--state-root", str(state_root), "research", "import"], output=import_output)
            import_payload = json.loads(import_output.getvalue())

            app = LocalApiApplication(state_root=state_root)
            facts_status, facts_body = app.handle("GET", "/facts")
            facts_payload = json.loads(facts_body)

        self.assertEqual(200, facts_status)
        self.assertEqual(import_payload["record_id"], facts_payload["items"][0]["id"])

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

    def test_local_api_can_create_a_loopback_only_http_server_without_auto_starting(self) -> None:
        """本地接口必须能创建真实 loopback HTTP server，并可手动启动/关闭。"""
        with tempfile.TemporaryDirectory() as directory:
            state_root = Path(directory)
            run_cli(["--state-root", str(state_root), "system", "init"], output=StringIO())
            run_cli(["--state-root", str(state_root), "research", "import"], output=StringIO())

            app = LocalApiApplication(state_root=state_root, bind_port=0)
            server = app.create_server()

            self.assertEqual("127.0.0.1", server.server_address[0])

            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                root_response = urlopen(
                    f"http://{server.server_address[0]}:{server.server_address[1]}/",
                    timeout=2,
                )
                response = urlopen(
                    f"http://{server.server_address[0]}:{server.server_address[1]}/facts",
                    timeout=2,
                )
                root_body = root_response.read().decode("utf-8")
                payload = json.loads(response.read().decode("utf-8"))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

        self.assertEqual("text/plain; charset=utf-8", root_response.headers.get_content_type() + "; charset=" + root_response.headers.get_content_charset())
        self.assertEqual("application/json", response.headers.get_content_type())
        self.assertIn("Local API debug index", root_body)
        self.assertIn("items", payload)
        self.assertFalse(thread.is_alive())

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
