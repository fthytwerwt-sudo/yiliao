"""
用途：
提供 Phase 6 的离线 CLI，覆盖系统初始化、synthetic 数据治理、候选业务流和学习闭环命令。

上游：
`python -m medical_tourism_os`、测试和本地开发者通过这里调用 `run_cli()`。

下游：
输出安全 JSON，供人工查看和接口层复用。

边界：
CLI 只运行 synthetic / dry-run 路径；不发起外部调用，不输出敏感原文，也不宣称业务验证完成。
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from typing import Dict, IO, Optional, Sequence

from medical_tourism_os.audit.logger import AuditLogger
from medical_tourism_os.config import SystemConfig
from medical_tourism_os.domain.entities import FactClassification
from medical_tourism_os.exports.safe_export import export_canonical_facts
from medical_tourism_os.fixtures.synthetic import SYNTHETIC_RESEARCH_RECORD
from medical_tourism_os.repositories.core import FactRepository
from medical_tourism_os.services import (
    CommentIntake,
    ContentFactory,
    ContentIntelligence,
    DataGovernanceService,
    DemandRadar,
    LeadScorer,
    ProductCatalog,
    ProductMatcher,
    RiskRouter,
)
from medical_tourism_os.storage.sqlite_store import SqliteStore
from medical_tourism_os.workflows.e2e_scenario import run_synthetic_scenario
from medical_tourism_os.workflows.weekly_review import LearningLoop


def _write_json(payload: Dict[str, object], output: IO[str]) -> int:
    """统一写出 JSON，避免不同命令自行发明输出格式。"""

    output.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    output.write("\n")
    return 0


def _build_governance_service() -> DataGovernanceService:
    """为单次 CLI 调用创建隔离的数据治理服务。"""

    directory = Path(tempfile.mkdtemp(prefix="medical-tourism-os-cli-"))
    store = SqliteStore(directory / "cli.sqlite3")
    store.migrate()
    return DataGovernanceService(
        repository=FactRepository(store),
        audit_logger=AuditLogger(directory / "cli-audit.jsonl"),
    )


def _build_phase4_state() -> Dict[str, object]:
    """构建一个最小 synthetic candidate state，供多条 CLI 路径复用。"""

    governance = _build_governance_service()
    ingested = governance.ingest_research(
        dict(SYNTHETIC_RESEARCH_RECORD),
        source="synthetic://research/001",
    )
    radar = DemandRadar()
    signal = radar.record_signal(
        market="TEST_MARKET_A",
        theme="trust question",
        evidence_ids=(ingested.record.id,),
        classification=FactClassification.RESEARCH,
        dimensions=("region_known", "time_window_known", "channel_known", "goal_stated"),
    )
    product = ProductCatalog().create_candidate(
        code="TEST_PRODUCT_A",
        target_segment="TEST_SEGMENT_A",
        value_hypothesis="resolve a non-clinical coordination question",
        requirements=("region_known", "time_window_known", "channel_known", "goal_stated"),
        supply_evidence_ids=(ingested.record.id,),
        price_evidence_ids=(),
        risks=(),
    )
    brief = ContentIntelligence().build_brief(
        demand_signal=signal,
        product=product,
        fact_refs=(ingested.record.id,),
        experiment_id="TEST_EXPERIMENT_CONTEXT_A",
    )
    drafts = ContentFactory().generate_drafts(brief)
    return {
        "governance": governance,
        "ingested": ingested,
        "signal": signal,
        "product": product,
        "brief": brief,
        "drafts": drafts,
    }


def _build_learning_state() -> Dict[str, object]:
    """构建学习闭环示例状态，供 CLI/API 复用。"""

    loop = LearningLoop()
    metric_reach = loop.record_metric("TEST_CHANNEL_A", "reach", 120)
    metric_lead = loop.record_metric("TEST_CHANNEL_A", "lead", 5)
    experiment = loop.create_experiment(
        hypothesis="TEST_PRODUCT_A message may clarify a non-clinical question",
        primary_variable="message_angle",
        fixed_variables=("TEST_MARKET_A", "TEST_WINDOW_A"),
        window="TEST_WINDOW_A",
        metrics=("reach", "lead"),
    )
    review = loop.review_experiment(experiment.id, result="insufficient_sample")
    weekly_review = loop.generate_weekly_review()
    decision_candidate = loop.create_decision_candidate(weekly_review.id)
    github_sync = loop.github_dry_run(decision_candidate.id)
    return {
        "loop": loop,
        "metrics": (metric_reach, metric_lead),
        "experiment": experiment,
        "review": review,
        "weekly_review": weekly_review,
        "decision_candidate": decision_candidate,
        "github_sync": github_sync,
    }


def _help_payload() -> Dict[str, object]:
    """返回 CLI 命令清单，供无参或错误输入时查看。"""

    return {
        "usage": [
            "system init",
            "research import",
            "facts list",
            "facts review",
            "demand list",
            "products list",
            "content generate",
            "lead score",
            "risk check",
            "experiment create",
            "experiment review",
            "weekly-review generate",
            "decision candidate",
            "sync github --dry-run",
        ],
        "external_execution_allowed": False,
        "adapters_enabled": False,
    }


def run_cli(argv: Optional[Sequence[str]] = None, *, output: Optional[IO[str]] = None) -> int:
    """
    作用：
    执行离线 CLI 命令并输出 JSON。

    关键边界：
    所有命令都必须保持 synthetic / dry-run；即使用户传了 sync，也不能执行真实外部动作。
    """

    args = list(argv or [])
    stream = output if output is not None else __import__("sys").stdout
    config = SystemConfig.default()
    if not args:
        return _write_json(_help_payload(), stream)

    if args[:2] == ["system", "init"]:
        return _write_json(
            {
                "command": "system init",
                "storage_backend": config.storage_backend,
                "external_execution_allowed": config.external_execution_allowed,
                "adapters_enabled": config.adapters_enabled,
                "adapter_status": "disabled",
                "mode": "offline_safe",
            },
            stream,
        )

    if args[:2] == ["research", "import"]:
        state = _build_phase4_state()
        ingested = state["ingested"]
        return _write_json(
            {
                "command": "research import",
                "record_id": ingested.record.id,
                "classification": ingested.record.classification.value,
                "review_status": ingested.record.review_status.value,
                "lifecycle": list(ingested.lifecycle),
                "scope": ingested.record.scope,
            },
            stream,
        )

    if args[:2] == ["facts", "list"]:
        state = _build_phase4_state()
        governance = state["governance"]
        items = [
            {
                "id": record.id,
                "claim": record.claim,
                "classification": record.classification.value,
                "review_status": record.review_status.value,
            }
            for record in governance.list_review_queue()
        ]
        return _write_json({"command": "facts list", "items": items}, stream)

    if args[:2] == ["facts", "review"]:
        state = _build_phase4_state()
        governance = state["governance"]
        approved = governance.approve_fact(state["ingested"].record.id, reviewed_by="human-reviewer-001")
        return _write_json(
            {
                "command": "facts review",
                "items": export_canonical_facts((approved,)),
            },
            stream,
        )

    if args[:2] == ["demand", "list"]:
        state = _build_phase4_state()
        signal = state["signal"]
        return _write_json(
            {
                "command": "demand list",
                "items": [
                    {
                        "id": signal.id,
                        "market": signal.market,
                        "theme": signal.theme,
                        "classification": signal.classification.value,
                    }
                ],
            },
            stream,
        )

    if args[:2] == ["products", "list"]:
        product = _build_phase4_state()["product"]
        return _write_json(
            {
                "command": "products list",
                "items": [
                    {
                        "code": product.code,
                        "status": product.status,
                        "requirements": list(product.requirements),
                        "supply_evidence_ids": list(product.supply_evidence_ids),
                        "price_evidence_ids": list(product.price_evidence_ids),
                    }
                ],
            },
            stream,
        )

    if args[:2] == ["content", "generate"]:
        state = _build_phase4_state()
        return _write_json(
            {
                "command": "content generate",
                "brief_id": state["brief"].id,
                "items": [
                    {
                        "id": draft.id,
                        "content_type": draft.content_type,
                        "status": draft.status,
                        "evidence_status": draft.evidence_status,
                    }
                    for draft in state["drafts"]
                ],
            },
            stream,
        )

    if args[:2] == ["lead", "score"]:
        scorer = LeadScorer(weights={"consent": 4, "contact_reference": 2, "source": 1, "intent": 3})
        scorecard = scorer.score(
            anonymous_lead_id="lead-test-001",
            contact_reference="SAFE_OPAQUE_REF_001",
            source="TEST_CHANNEL_A",
            consent_status="granted",
            intent="high",
        )
        return _write_json({"command": "lead score", "item": scorecard.to_dict()}, stream)

    if args[:2] == ["risk", "check"]:
        result = RiskRouter().route("please diagnose this condition")
        return _write_json(
            {
                "command": "risk check",
                "blocked": result.blocked,
                "category": result.category,
                "action": result.action,
                "safe_summary": result.safe_summary,
            },
            stream,
        )

    if args[:2] == ["experiment", "create"]:
        learning = _build_learning_state()
        return _write_json(
            {
                "command": "experiment create",
                "item": learning["experiment"].to_dict(),
            },
            stream,
        )

    if args[:2] == ["experiment", "review"]:
        learning = _build_learning_state()
        return _write_json(
            {
                "command": "experiment review",
                "item": learning["review"].to_dict(),
            },
            stream,
        )

    if args[:2] == ["weekly-review", "generate"]:
        learning = _build_learning_state()
        board = learning["loop"].export_review_board(learning["weekly_review"])
        return _write_json({"command": "weekly-review generate", "item": board}, stream)

    if args[:2] == ["decision", "candidate"]:
        learning = _build_learning_state()
        return _write_json(
            {
                "command": "decision candidate",
                "item": learning["decision_candidate"].to_dict(),
            },
            stream,
        )

    if args[:3] == ["sync", "github", "--dry-run"]:
        learning = _build_learning_state()
        sync_result = learning["github_sync"]
        return _write_json(
            {
                "command": "sync github --dry-run",
                "dry_run": sync_result.dry_run,
                "executed": sync_result.executed,
                "reason": sync_result.reason,
                "payload": sync_result.payload,
            },
            stream,
        )

    if args[:2] == ["scenario", "e2e"]:
        scenario = run_synthetic_scenario()
        return _write_json({"command": "scenario e2e", "item": asdict(scenario)}, stream)

    return _write_json({"error": "unknown_command", **_help_payload()}, stream)
