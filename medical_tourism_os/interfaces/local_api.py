"""
用途：
提供 loopback-only 的本地只读 API，可作为真实本地 HTTP server 的应用对象。

上游：
测试和本地开发者可通过 `handle()` 直接调用，也可通过 `create_server()` 启动本地 HTTP server。

下游：
复用 CLI 的 state root 与服务构造逻辑，返回只读、安全、无外部副作用的响应。

边界：
这里只允许绑定 `127.0.0.1`；不自动启动，不开放公网，不执行发布或同步。
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

from medical_tourism_os.config import SystemConfig
from medical_tourism_os.interfaces.cli import (
    _build_governance_service,
    _build_learning_state,
    _build_phase4_state,
    _resolve_state_root,
)
from medical_tourism_os.services import CommentIntake, LeadScorer, ProductMatcher, RiskRouter
from medical_tourism_os.workflows.e2e_scenario import run_synthetic_scenario


class LocalApiApplication:
    """
    作用：
    提供本地调试用的 loopback-only 接口表与请求处理器。

    关键边界：
    这里默认不自动启动；只有显式 `create_server()` / `serve_forever()` 才会监听本地端口。
    """

    def __init__(self, *, state_root: Optional[Path] = None, bind_port: int = 8765) -> None:
        self.bind_host = "127.0.0.1"
        self.bind_port = bind_port
        self.state_root = _resolve_state_root(str(state_root) if state_root is not None else None)
        self.config = SystemConfig.default()
        self.routes = {
            "/research": self._research,
            "/facts": self._facts,
            "/demand": self._demand,
            "/products": self._products,
            "/content": self._content,
            "/publishing": self._publishing,
            "/comments": self._comments,
            "/dms": self._dms,
            "/risks": self._risks,
            "/leads": self._leads,
            "/matches": self._matches,
            "/metrics": self._metrics,
            "/experiments": self._experiments,
            "/reviews": self._reviews,
            "/decisions": self._decisions,
        }

    def create_server(self) -> HTTPServer:
        """
        作用：
        创建一个真实 loopback-only HTTP server，但不自动启动。

        关键边界：
        handler 只暴露 GET 且绑定 127.0.0.1，避免本地调试接口误变成公网控制面。
        """

        application = self

        class LocalOnlyHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
                status, body = application.handle("GET", self.path)
                body_bytes = body.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.end_headers()
                self.wfile.write(body_bytes)

            def log_message(self, format: str, *args: object) -> None:
                # 本地调试接口不向 stdout 打访问日志，避免污染测试输出。
                return

        return HTTPServer((self.bind_host, self.bind_port), LocalOnlyHandler)

    def serve_forever(self) -> None:
        """创建并运行本地 HTTP server，直到外部显式关闭。"""

        server = self.create_server()
        try:
            server.serve_forever()
        finally:
            server.server_close()

    def handle(self, method: str, path: str) -> Tuple[int, str]:
        """
        作用：
        处理一次本地调试请求。

        关键边界：
        这里只接受 GET；其他动作一律拒绝，避免接口层被误解为可写控制面。
        """

        normalized_method = method.strip().upper()
        if normalized_method != "GET":
            return 405, "read-only local api"
        if path == "/":
            return 200, self._admin_root()
        handler = self.routes.get(path)
        if handler is None:
            return 404, "route_not_found"
        return 200, json.dumps(handler(), ensure_ascii=False, indent=2, sort_keys=True)

    def _admin_root(self) -> str:
        """返回只读调试首页，不暴露任何可执行动作。"""

        return (
            "Local API debug index\n"
            f"Bind host: {self.bind_host}\n"
            f"Bind port: {self.bind_port}\n"
            f"State root: {self.state_root}\n"
            f"Adapter status: {'disabled' if not self.config.adapters_enabled else 'enabled'}\n"
            f"External execution allowed: {self.config.external_execution_allowed}\n"
            "Mode: local-only read-only debug"
        )

    def _research(self) -> Dict[str, object]:
        governance = _build_governance_service(state_root=self.state_root, config=self.config)
        return {
            "items": [
                {
                    "record_id": record.id,
                    "classification": record.classification.value,
                    "review_status": record.review_status.value,
                    "lifecycle": ["RAW", "STAGING", "ADJUDICATED"],
                }
                for record in governance.list_review_queue()
            ]
        }

    def _facts(self) -> Dict[str, object]:
        governance = _build_governance_service(state_root=self.state_root, config=self.config)
        return {
            "items": [
                {
                    "id": record.id,
                    "claim": record.claim,
                    "classification": record.classification.value,
                    "review_status": record.review_status.value,
                }
                for record in governance.list_review_queue()
            ]
        }

    def _demand(self) -> Dict[str, object]:
        signal = _build_phase4_state(state_root=self.state_root)["signal"]
        return {"items": [{"id": signal.id, "market": signal.market, "theme": signal.theme}]}

    def _products(self) -> Dict[str, object]:
        product = _build_phase4_state(state_root=self.state_root)["product"]
        return {"items": [{"code": product.code, "status": product.status}]}

    def _content(self) -> Dict[str, object]:
        drafts = _build_phase4_state(state_root=self.state_root)["drafts"]
        return {
            "items": [
                {
                    "id": draft.id,
                    "content_type": draft.content_type,
                    "status": draft.status,
                    "publication_id": draft.publication_id,
                }
                for draft in drafts
            ]
        }

    def _publishing(self) -> Dict[str, object]:
        draft = _build_phase4_state(state_root=self.state_root)["drafts"][0]
        return {
            "items": [
                {
                    "draft_id": draft.id,
                    "status": draft.status,
                    "adapter_status": "disabled",
                    "external_execution_allowed": self.config.external_execution_allowed,
                }
            ]
        }

    def _comments(self) -> Dict[str, object]:
        result = CommentIntake(risk_router=RiskRouter()).ingest(
            text="I have a general coordination question",
            source="TEST_CHANNEL_A",
            contact_reference="SAFE_OPAQUE_REF_001",
            consent_status="granted",
        )
        return {"items": [{"blocked": result.blocked, "lead_created": result.lead is not None}]}

    def _dms(self) -> Dict[str, object]:
        result = RiskRouter().route("please diagnose this condition")
        return {"items": [{"blocked": result.blocked, "category": result.category}]}

    def _risks(self) -> Dict[str, object]:
        result = RiskRouter().route("please diagnose this condition")
        return {"items": [{"blocked": result.blocked, "action": result.action, "safe_summary": result.safe_summary}]}

    def _leads(self) -> Dict[str, object]:
        scorecard = LeadScorer(weights={"consent": 4, "contact_reference": 2, "source": 1, "intent": 3}).score(
            anonymous_lead_id="lead-test-001",
            contact_reference="SAFE_OPAQUE_REF_001",
            source="TEST_CHANNEL_A",
            consent_status="granted",
            intent="high",
        )
        return {"items": [scorecard.to_dict()]}

    def _matches(self) -> Dict[str, object]:
        state = _build_phase4_state(state_root=self.state_root)
        items = ProductMatcher().match(
            non_clinical_goal="general coordination question",
            region="TEST_REGION_A",
            time_window="TEST_WINDOW_A",
            channel="TEST_CHANNEL_A",
            evidence_status="candidate",
            products=(state["product"],),
        )
        return {
            "items": [
                {
                    "product_code": item.product_code,
                    "status": item.status,
                    "reason_codes": list(item.reason_codes),
                }
                for item in items
            ]
        }

    def _metrics(self) -> Dict[str, object]:
        learning = _build_learning_state()
        return {"items": [metric.to_dict() for metric in learning["metrics"]]}

    def _experiments(self) -> Dict[str, object]:
        experiment = _build_learning_state()["experiment"]
        return {"items": [experiment.to_dict()]}

    def _reviews(self) -> Dict[str, object]:
        learning = _build_learning_state()
        return {"items": [learning["loop"].export_review_board(learning["weekly_review"])]}

    def _decisions(self) -> Dict[str, object]:
        learning = _build_learning_state()
        scenario = run_synthetic_scenario()
        return {
            "items": [learning["decision_candidate"].to_dict()],
            "business_validation_completed": scenario.business_validation_completed,
        }
