"""验证 Phase 2 的业务配置导入、审核与版本注入边界。"""

from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from http.client import HTTPConnection
from pathlib import Path
import tempfile
from threading import Thread
import unittest


class BusinessConfigTests(unittest.TestCase):
    """先锁定中性配置包入口；具体导入和审核行为会在包存在后逐项补齐。"""

    def test_business_config_package_exists_in_the_general_operating_system(self) -> None:
        """配置能力必须进入中性主架构，而不是继续向旧医疗包叠加领域逻辑。"""

        self.assertIsNotNone(importlib.util.find_spec("general_ai_business_os.business_config"))

    def test_json_and_yaml_packages_follow_the_same_pending_review_path(self) -> None:
        """格式不同不能改变治理结果；两种输入均只能先成为 pending 配置候选。"""

        from general_ai_business_os.business_config.contracts import ConfigReviewStatus
        from general_ai_business_os.business_config.pipeline import BusinessConfigPipeline
        from general_ai_business_os.storage.sqlite_store import SqliteStore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = SqliteStore(root / "state.sqlite3")
            pipeline = BusinessConfigPipeline(store)
            json_package = self._write_package(
                root / "json_package",
                manifest=self._manifest(config_version="TEST_V1"),
                format_name="json",
            )
            yaml_package = self._write_package(
                root / "yaml_package",
                manifest=self._manifest(config_version="TEST_V2"),
                format_name="yaml",
            )

            imported_json = pipeline.import_package(json_package)
            imported_yaml = pipeline.import_package(yaml_package)

        self.assertEqual(ConfigReviewStatus.PENDING, imported_json.manifest.review_status)
        self.assertEqual(ConfigReviewStatus.PENDING, imported_yaml.manifest.review_status)
        self.assertEqual({"market", "sales_rules"}, set(imported_json.documents))
        self.assertEqual({"market", "sales_rules"}, set(imported_yaml.documents))

    def test_only_named_review_of_confirmed_input_makes_a_version_consumable(self) -> None:
        """Research 和未经审核的包不能进入 Agent 可读取的 confirmed registry。"""

        from general_ai_business_os.business_config.contracts import (
            ConfigClassification,
            ConfigNotConfirmedError,
            ConfigReviewStatus,
        )
        from general_ai_business_os.business_config.pipeline import BusinessConfigPipeline
        from general_ai_business_os.business_config.registry import BusinessConfigRegistry
        from general_ai_business_os.storage.sqlite_store import SqliteStore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = SqliteStore(root / "state.sqlite3")
            pipeline = BusinessConfigPipeline(store)
            registry = BusinessConfigRegistry(store)
            package_path = self._write_package(
                root / "confirmed_package",
                manifest=self._manifest(config_version="TEST_CONFIRMED", classification="CONFIRMED_FACT"),
                format_name="json",
            )
            imported = pipeline.import_package(package_path)

            with self.assertRaises(ConfigNotConfirmedError):
                registry.get_confirmed("TEST_BUSINESS", "TEST_CONFIRMED")

            approved = pipeline.approve("TEST_BUSINESS", "TEST_CONFIRMED", reviewer="TEST_REVIEWER")
            reopened_registry = BusinessConfigRegistry(SqliteStore(root / "state.sqlite3"))
            consumed = reopened_registry.get_confirmed("TEST_BUSINESS", "TEST_CONFIRMED")

        self.assertEqual(ConfigClassification.CONFIRMED_FACT, imported.manifest.classification)
        self.assertEqual(ConfigReviewStatus.APPROVED, approved.manifest.review_status)
        self.assertEqual("TEST_REVIEWER", approved.manifest.reviewed_by)
        self.assertEqual("TEST_CONFIRMED", consumed.manifest.config_version)

    def test_research_classification_cannot_be_promoted_by_config_import_or_review(self) -> None:
        """配置流程只能接收事实裁决结果，不得擅自把 Research 升级为 confirmed data。"""

        from general_ai_business_os.business_config.contracts import ConfigClassificationError
        from general_ai_business_os.business_config.pipeline import BusinessConfigPipeline
        from general_ai_business_os.storage.sqlite_store import SqliteStore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pipeline = BusinessConfigPipeline(SqliteStore(root / "state.sqlite3"))
            package_path = self._write_package(
                root / "research_package",
                manifest=self._manifest(config_version="TEST_RESEARCH", classification="RESEARCH"),
                format_name="yaml",
            )
            pipeline.import_package(package_path)

            with self.assertRaisesRegex(ConfigClassificationError, "config_classification_not_confirmed"):
                pipeline.approve("TEST_BUSINESS", "TEST_RESEARCH", reviewer="TEST_REVIEWER")

    def test_invalid_manifest_duplicate_version_and_injected_approval_fail_closed(self) -> None:
        """未知字段、缺 provenance、伪造批准和重复版本都不能静默覆盖正式配置。"""

        from general_ai_business_os.business_config.contracts import (
            ConfigDuplicateVersionError,
            ConfigValidationError,
        )
        from general_ai_business_os.business_config.pipeline import BusinessConfigPipeline
        from general_ai_business_os.storage.sqlite_store import SqliteStore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pipeline = BusinessConfigPipeline(SqliteStore(root / "state.sqlite3"))
            valid_manifest = self._manifest(config_version="TEST_DUPLICATE")
            pipeline.import_package(self._write_package(root / "first", manifest=valid_manifest, format_name="json"))
            with self.assertRaises(ConfigDuplicateVersionError):
                pipeline.import_package(self._write_package(root / "second", manifest=valid_manifest, format_name="yaml"))

            missing_source = self._manifest(config_version="TEST_MISSING_SOURCE")
            missing_source.pop("source_refs")
            with self.assertRaises(ConfigValidationError):
                pipeline.import_package(self._write_package(root / "missing_source", manifest=missing_source, format_name="json"))

            injected_approval = self._manifest(config_version="TEST_INJECTED_APPROVAL")
            injected_approval["review_status"] = "APPROVED"
            injected_approval["reviewed_by"] = "TEST_REVIEWER"
            with self.assertRaises(ConfigValidationError):
                pipeline.import_package(self._write_package(root / "injected", manifest=injected_approval, format_name="yaml"))

            unknown_field = self._manifest(config_version="TEST_UNKNOWN_FIELD")
            unknown_field["unknown_field"] = "TEST_VALUE"
            with self.assertRaises(ConfigValidationError):
                pipeline.import_package(self._write_package(root / "unknown", manifest=unknown_field, format_name="json"))

    def test_malformed_documents_and_unknown_document_names_are_rejected_before_storage(self) -> None:
        """Loader 只接受约定领域文件与 mapping 根，不能把畸形 YAML/JSON 当作空配置。"""

        from general_ai_business_os.business_config.contracts import ConfigLoadError, ConfigValidationError
        from general_ai_business_os.business_config.pipeline import BusinessConfigPipeline
        from general_ai_business_os.storage.sqlite_store import SqliteStore

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pipeline = BusinessConfigPipeline(SqliteStore(root / "state.sqlite3"))
            malformed = root / "malformed"
            malformed.mkdir()
            (malformed / "manifest.yaml").write_text("schema_version: [", encoding="utf-8")
            with self.assertRaises(ConfigLoadError):
                pipeline.import_package(malformed)

            unknown_document = self._write_package(
                root / "unknown_document",
                manifest=self._manifest(config_version="TEST_UNKNOWN_DOCUMENT"),
                format_name="json",
            )
            (unknown_document / "unexpected.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(ConfigValidationError):
                pipeline.import_package(unknown_document)

    def test_cli_config_import_persists_pending_config_without_enabling_external_actions(self) -> None:
        """CLI 可导入本地配置包，但只输出 pending 状态，不能借此产生外部动作。"""

        from general_ai_business_os.interfaces.cli import run_cli

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = self._write_package(
                root / "cli_package",
                manifest=self._manifest(config_version="TEST_CLI"),
                format_name="json",
            )
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = run_cli(
                    ["config", "import", "--state-root", str(root / "state"), "--path", str(package_path)]
                )
            payload = json.loads(output.getvalue())

        self.assertEqual(0, exit_code)
        self.assertEqual("PENDING", payload["review_status"])
        self.assertFalse(payload["external_actions_allowed"])

    def test_local_api_config_route_imports_a_package_locally_and_rejects_unknown_routes(self) -> None:
        """/config 是真实本地导入入口；未知路径不能伪装成系统能力。"""

        from general_ai_business_os.config import SystemConfig
        from general_ai_business_os.interfaces.local_api import LocalApiApplication

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package_path = self._write_package(
                root / "api_package",
                manifest=self._manifest(config_version="TEST_API"),
                format_name="yaml",
            )
            application = LocalApiApplication(SystemConfig(state_root=root / "state"))
            server = application.create_server()
            try:
                request_thread = Thread(target=server.handle_request)
                request_thread.start()
                connection = HTTPConnection("127.0.0.1", server.server_address[1])
                body = json.dumps({"package_path": str(package_path)})
                connection.request("POST", "/config", body=body, headers={"Content-Type": "application/json"})
                response = connection.getresponse()
                payload = json.loads(response.read().decode("utf-8"))
                request_thread.join(timeout=2)
                connection.close()

                request_thread = Thread(target=server.handle_request)
                request_thread.start()
                connection = HTTPConnection("127.0.0.1", server.server_address[1])
                connection.request("GET", "/not-a-route")
                unknown_response = connection.getresponse()
                unknown_response.read()
                request_thread.join(timeout=2)
                connection.close()
            finally:
                server.server_close()

        self.assertEqual(201, response.status)
        self.assertEqual("PENDING", payload["review_status"])
        self.assertFalse(payload["external_actions_allowed"])
        self.assertEqual(404, unknown_response.status)

    @staticmethod
    def _manifest(*, config_version: str, classification: str = "CONFIRMED_FACT") -> dict:
        """生成不含真实业务事实的最小测试 manifest。"""

        return {
            "schema_version": 1,
            "business_id": "TEST_BUSINESS",
            "config_version": config_version,
            "source_refs": ["TEST_SOURCE_A"],
            "classification": classification,
            "review_status": "PENDING",
            "reviewed_by": None,
        }

    @staticmethod
    def _write_package(path: Path, *, manifest: dict, format_name: str) -> Path:
        """写入 JSON/YAML 测试包；内容只使用虚构的 TEST_* 配置值。"""

        path.mkdir()
        documents = {
            "market": {"scope": "TEST_SCOPE"},
            "sales_rules": {"rule_code": "TEST_RULE"},
        }
        if format_name == "json":
            (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            for name, payload in documents.items():
                (path / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
            return path
        if format_name == "yaml":
            yaml_manifest = "\n".join(
                (
                    f"schema_version: {manifest['schema_version']}",
                    f"business_id: {manifest['business_id']}",
                    f"config_version: {manifest['config_version']}",
                    "source_refs:",
                    "  - TEST_SOURCE_A",
                    f"classification: {manifest['classification']}",
                    f"review_status: {manifest['review_status']}",
                    f"reviewed_by: {manifest['reviewed_by'] if manifest['reviewed_by'] is not None else 'null'}",
                )
            )
            (path / "manifest.yaml").write_text(yaml_manifest, encoding="utf-8")
            (path / "market.yaml").write_text("scope: TEST_SCOPE\n", encoding="utf-8")
            (path / "sales_rules.yaml").write_text("rule_code: TEST_RULE\n", encoding="utf-8")
            return path
        raise AssertionError("unsupported_test_format")


if __name__ == "__main__":
    unittest.main()
