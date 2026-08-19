"""
用途：
提供 loopback-only 的本地只读 API 壳层，用于离线调试当前系统状态。

上游：
测试和本地开发者通过 `handle()` 模拟读取接口响应。

下游：
复用 CLI 的 synthetic 构造逻辑，返回字符串响应而不启动真正的 HTTP server。

边界：
这里只声明 127.0.0.1 绑定与只读路由；不监听公网，不自动启动，不产生外部副作用。
"""

from __future__ import annotations

import json
from typing import Callable, Dict, Tuple

from medical_tourism_os.config import SystemConfig
from medical_tourism_os.interfaces.cli import _build_learning_state, _build_phase4_state
from medical_tourism_os.services import CommentIntake, LeadScorer, ProductMatcher, RiskRouter
from medical_tourism_os.workflows.e2e_scenario import run_synthetic_scenario


class LocalApiApplication:
    """
    作用：
    提供本地调试用的 loopback-only 接口表与请求处理器。

    关键边界：
    这里没有真正启动 server；只有显式 `handle()` 才返回只读调试结果。
    """

    def __init__(self) -> None:
        self.bind_host = "127.0.0.1"
        self.bind_port = 8765
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
            f"Adapter status: {'disabled' if not self.config.adapters_enabled else 'enabled'}\n"
            f"External execution allowed: {self.config.external_execution_allowed}\n"
            "Mode: read-only debug"
        )

    def _research(self) -> Dict[str, object]:
        state = _build_phase4_state()
        ingested = state["ingested"]
        return {
            "items": [
                {
                    "record_id": ingested.record.id,
                    "classification": ingested.record.classification.value,
                    "review_status": ingested.record.review_status.value,
                    "lifecycle": list(ingested.lifecycle),
                }
            ]
        }

    def _facts(self) -> Dict[str, object]:
        governance = _build_phase4_state()["governance"]
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
        signal = _build_phase4_state()["signal"]
        return {"items": [{"id": signal.id, "market": signal.market, "theme": signal.theme}]}

    def _products(self) -> Dict[str, object]:
        product = _build_phase4_state()["product"]
        return {"items": [{"code": product.code, "status": product.status}]}

    def _content(self) -> Dict[str, object]:
        drafts = _build_phase4_state()["drafts"]
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
        draft = _build_phase4_state()["drafts"][0]
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
        state = _build_phase4_state()
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
