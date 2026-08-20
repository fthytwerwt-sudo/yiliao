# General AI Business Operating System V1 Implementation Plan

> **For Codex:** Execute this plan sequentially. Every Phase requires a fresh, independent `gpt-5.6-sol` high-reasoning review before work on the next Phase may begin.

**Goal:** Build a strategy-agnostic, configuration-driven AI business operating system without breaking the existing `medical_tourism_os` compatibility surface.

**Architecture:** Add `general_ai_business_os` as a dependency-free (except safe YAML parsing) capability layer. Domain services depend on typed contracts, storage ports, permission policy and adapter ports; local SQLite and disabled/Mock adapters are infrastructure details. `medical_tourism_os` remains intact until a future, tested compatibility bridge is explicitly introduced.

**Tech Stack:** Python 3.9 standard library, SQLite, `unittest`, `http.server`, `PyYAML` safe loader for the user-required YAML configuration format.

---

## Universal execution rules

- Before each implementation step, add or extend the relevant `unittest` case and run it to observe the intended failure.
- Core modules require file-level Chinese boundary documentation; non-trivial classes/functions require Chinese explanation of inputs, outputs, key gates and failure behavior.
- Use only `TEST_BUSINESS` and `TEST_*` fixture values. Do not add real countries, brands, customers, platforms, pricing, hospitals or healthcare facts.
- Never implement a real external connection. An adapter may be `IMPLEMENTED` only when it has local deterministic behavior; a third-party operation remains `MOCK`, `DISABLED` or `BLOCKED` until separately authorized.
- At the end of every Phase: run the Phase tests and full suite, run `git diff --check`, inspect changed paths, commit using the Lore protocol, then ask an independent reviewer for the required review schema. Do not start the next Phase until the reviewer permits continuation.

## Phase 1: Foundation（基础架构）

**Goal:** Establish the neutral package, shared domain contracts, default-deny permission/audit boundaries, SQLite port, local CLI/API skeleton and compatibility/migration documentation without changing old behavior.

**Files:**
- Create: `general_ai_business_os/__init__.py`, `general_ai_business_os/__main__.py`, `general_ai_business_os/config.py`
- Create: `general_ai_business_os/domain/__init__.py`, `general_ai_business_os/domain/entities.py`
- Create: `general_ai_business_os/permissions/__init__.py`, `general_ai_business_os/permissions/policy.py`
- Create: `general_ai_business_os/audit/__init__.py`, `general_ai_business_os/audit/logger.py`
- Create: `general_ai_business_os/adapters/__init__.py`, `general_ai_business_os/adapters/base.py`, `general_ai_business_os/adapters/mock.py`
- Create: `general_ai_business_os/storage/__init__.py`, `general_ai_business_os/storage/contracts.py`, `general_ai_business_os/storage/sqlite_store.py`
- Create: `general_ai_business_os/interfaces/__init__.py`, `general_ai_business_os/interfaces/cli.py`, `general_ai_business_os/interfaces/local_api.py`
- Create: `general_ai_business_os/compatibility/__init__.py`
- Create: `tests/test_general_foundation.py`, `docs/migrations/2026-08-20_medical_tourism_os_to_general_os.md`

**Step 1: Write failing foundation tests.**

Test package import, default external-action denial, safe audit redaction, Mock adapter dry-run behavior, SQLite round trip through `StoragePort`, local API route inventory and loopback-only server construction. Assert `medical_tourism_os` imports still work unchanged.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_general_foundation.py -v`

Expected: fail because `general_ai_business_os` does not exist.

**Step 2: Implement the smallest neutral foundation.**

Define the common `AdapterStatus`, `PermissionDecision`, `AuditEvent`, `StoredRecord` and `OperationResult` dataclasses/enums. Implement a default-deny `PermissionPolicy`, allowlist-only `AuditLogger`, abstract `StoragePort`, SQLite implementation, `BaseAdapter` and deterministic `MockAdapter`. Build a non-starting `LocalApiApplication` binding only `127.0.0.1`; expose a `system init` CLI command. No module imports `medical_tourism_os`.

**Step 3: Run focused and full verification.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_general_foundation.py -v && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check`

Expected: all tests pass; old 74 baseline tests remain green.

**Step 4: Record the migration boundary.**

Write the migration record with old package status `retained`, new package status `active_for_new_capabilities`, no active delegation and explicit rollback rule.

**Step 5: Commit and independent review.**

Provide the reviewer the Phase Goal, this Phase plan, `git diff <phase-base>..HEAD --name-only`, architecture impact, verification output, limitations, remaining work and current commit SHA. Persist its unmodified result under `docs/reviews/phase-01-foundation.md`.

## Phase 2: Business Config（业务配置层）

**Goal:** Import, normalize, validate, review and version JSON/YAML business configuration packages, making only confirmed versions consumable by agents.

**Files:**
- Create: `requirements.txt`
- Create: `general_ai_business_os/business_config/__init__.py`, `contracts.py`, `loader.py`, `validator.py`, `registry.py`, `pipeline.py`
- Modify: `general_ai_business_os/storage/contracts.py`, `general_ai_business_os/storage/sqlite_store.py`, `general_ai_business_os/interfaces/cli.py`, `general_ai_business_os/interfaces/local_api.py`
- Create: `general_ai_business_os/fixtures/test_business_config.json`, `general_ai_business_os/fixtures/test_business_config.yaml`
- Create: `tests/test_business_config.py`

**Step 1: Write failing configuration tests.**

Cover safe JSON/YAML load; normalized manifest/domain files; rejected malformed syntax; unknown fields; duplicate versions; missing provenance; absent reviewer; rejected/unreviewed package lookup; and a named approval path that makes exactly one immutable `config_version` consumable. Verify an input marked `RESEARCH` cannot become confirmed automatically.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_business_config.py -v`

Expected: fail because configuration contracts and registry do not exist.

**Step 2: Add minimal safe parser and contracts.**

Add only `PyYAML` to `requirements.txt`, use `yaml.safe_load`, require mapping roots, and define closed field sets for manifest plus each optional domain file. Represent configuration with immutable dataclasses. `BusinessConfigPipeline` must write lifecycle events and expose a named-review method; it must never self-approve research/candidate/hypothesis input.

**Step 3: Persist and expose config versions.**

Extend Storage Port and SQLite schema without embedding business-specific columns. `BusinessConfigRegistry.get_confirmed()` returns only approval-backed versions. Add `config import` and `GET/POST /config` dry-run/local endpoints.

**Step 4: Verify, commit and review.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_business_config.py -v && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check`

Then create `docs/reviews/phase-02-business-config.md` from an independent review before Phase 3.

## Phase 3: Media Production Agent（媒体 Agent）

**Goal:** Build a configuration-gated, provider-neutral content workflow that returns local draft assets and quality results with explicit adapter states.

**Files:**
- Create: `general_ai_business_os/agents/__init__.py`, `general_ai_business_os/agents/media/__init__.py`, `contracts.py`, `service.py`, `quality.py`, `asset_library.py`
- Create: `general_ai_business_os/adapters/content.py`
- Modify: `general_ai_business_os/interfaces/cli.py`, `general_ai_business_os/interfaces/local_api.py`
- Create: `tests/test_media_agent.py`

**Step 1: Write failing media tests.**

Cover `ContentBrief -> PromptPlan -> AssetRecord` with a confirmed config version; reject missing/unconfirmed config; show image/video/voice/subtitle adapter status; require a deterministic quality result; and verify a disabled or blocked adapter never claims media creation or publication.

**Step 2: Implement real local orchestration, not a shell.**

Implement deterministic prompt composition from injected rules, typed media request/result objects, a local Mock content adapter, quality checks for complete request/result metadata, and an in-memory/SQLite asset library. `content generate` and `/content` only produce draft records.

**Step 3: Verify, commit and review.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_media_agent.py -v && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check`

Create and retain `docs/reviews/phase-03-media-agent.md` before Phase 4.

## Phase 4: Lead Discovery Agent（线索发现 Agent）

**Goal:** Accept a generic target profile and CSV data, normalize candidate leads, score them transparently and keep all external discovery actions disabled.

**Files:**
- Create: `general_ai_business_os/agents/leads/__init__.py`, `contracts.py`, `service.py`, `csv_import.py`, `scoring.py`
- Create: `general_ai_business_os/adapters/search.py`
- Modify: `general_ai_business_os/interfaces/cli.py`, `general_ai_business_os/interfaces/local_api.py`
- Create: `tests/test_lead_discovery_agent.py`

**Step 1: Write failing lead tests.**

Test profile validation, CSV rows entering one validation path, status/reason/confidence computation, source/website preservation, raw contact rejection/tokenization, attempted API/scraper invocation returning `BLOCKED`, and no send action.

**Step 2: Implement candidate-only discovery.**

Implement `TargetProfile`, `LeadCandidate`, CSV reader, deterministic rules-based scorer, anonymized contact reference policy and `SearchAdapterPort`. API/Scraper Mock adapters must return explicit `BLOCKED`/`MOCK` results and no external calls.

**Step 3: Verify, commit and review.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_lead_discovery_agent.py -v && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check`

Create `docs/reviews/phase-04-lead-discovery.md` before Phase 5.

## Phase 5: Sales Draft Agent（销售回复 Agent）

**Goal:** Turn a safe inbound message into a typed, human-review-required reply candidate without sending, pricing or making promises.

**Files:**
- Create: `general_ai_business_os/agents/sales/__init__.py`, `contracts.py`, `intent.py`, `risk.py`, `service.py`, `approval.py`
- Create: `general_ai_business_os/adapters/messaging.py`
- Modify: `general_ai_business_os/interfaces/cli.py`, `general_ai_business_os/interfaces/local_api.py`
- Create: `tests/test_sales_draft_agent.py`

**Step 1: Write failing sales tests.**

Cover deterministic intent classification, generic policy-rule risk blocking, reply candidate generation from confirmed sales rules, named human approval transition, unapproved no-send condition, and external messaging adapter denial.

**Step 2: Implement intake-to-draft workflow.**

Implement typed `MessageIntake`, `IntentResult`, `RiskCheckResult`, `ReplyCandidate` and approval state machine. Use injectable generic prohibited-pattern/rule sets; do not hardcode healthcare, product, price or platform content. `message analyze` and `/messages` never execute adapters.

**Step 3: Verify, commit and review.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_sales_draft_agent.py -v && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check`

Create `docs/reviews/phase-05-sales-draft.md` before Phase 6.

## Phase 6: CRM Agent（客户管理 Agent）

**Goal:** Persist anonymous lead lifecycle records and permitted follow-up/outcome state with valid transitions.

**Files:**
- Create: `general_ai_business_os/agents/crm/__init__.py`, `contracts.py`, `service.py`, `lifecycle.py`
- Create: `general_ai_business_os/adapters/crm.py`
- Modify: `general_ai_business_os/storage/contracts.py`, `general_ai_business_os/storage/sqlite_store.py`, `general_ai_business_os/interfaces/cli.py`, `general_ai_business_os/interfaces/local_api.py`
- Create: `tests/test_crm_agent.py`

**Step 1: Write failing CRM tests.**

Cover anonymous lead creation, all valid lifecycle transitions, invalid transition rejection, follow-up/outcome persistence, no raw contact/health data accepted, and disabled external CRM adapter behavior.

**Step 2: Implement lifecycle service.**

Implement typed state and event objects, `CrmService`, persistent Storage Port methods and a local CRM adapter Mock. `crm update` and `/crm` require valid `lead_id`, transition and safety-clean payload.

**Step 3: Verify, commit and review.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_crm_agent.py -v && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check`

Create `docs/reviews/phase-06-crm.md` before Phase 7.

## Phase 7: Knowledge System + Experiment Engine（知识与实验）

**Goal:** Store source-tracked knowledge and run configuration-gated experiments that produce observations rather than business decisions.

**Files:**
- Create: `general_ai_business_os/agents/knowledge/__init__.py`, `contracts.py`, `service.py`, `retrieval.py`
- Create: `general_ai_business_os/agents/experiments/__init__.py`, `contracts.py`, `service.py`, `feedback.py`
- Modify: `general_ai_business_os/storage/contracts.py`, `general_ai_business_os/storage/sqlite_store.py`, `general_ai_business_os/interfaces/cli.py`, `general_ai_business_os/interfaces/local_api.py`
- Create: `tests/test_knowledge_and_experiments.py`

**Step 1: Write failing knowledge/experiment tests.**

Verify required source tracking fields, classifications stay unchanged through retrieval, source refs are returned, experiment rejects zero/multiple primary variables, all three outcomes work, insufficient sample stays non-decisive, and feedback produces a review candidate only.

**Step 2: Implement typed source and experiment services.**

Use SQLite metadata lookup as V1 retrieval; define an explicit future `KnowledgeRetrievalPort`. Implement hypothesis/variable/metric/result records and a feedback summary that cannot set a business decision.

**Step 3: Verify, commit and review.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_knowledge_and_experiments.py -v && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check`

Create `docs/reviews/phase-07-knowledge-experiment.md` before Phase 8.

## Phase 8: Open Source Integration（开源接入）

**Goal:** Produce evidence-backed evaluation for required projects, expose future integration seams and prove no third-party runtime is falsely represented as integrated.

**Files:**
- Create: `docs/research/2026-08-20_Open-Source-Integration-Evaluation_开源接入评估.md`
- Create: `general_ai_business_os/adapters/integration_catalog.py`
- Create: `tests/test_open_source_integration.py`

**Step 1: Write failing integration tests.**

Assert every candidate has capability, source URL, date checked, coverage estimate, decision, adapter status, rationale and next trigger. Assert catalog decisions do not enable network actions and contain no real business facts.

**Step 2: Research official sources and implement catalog.**

Use only official primary documentation for LangGraph, CrewAI, AutoGen, Semantic Kernel, Temporal, Qdrant/Chroma/Weaviate, Twenty/SuiteCRM/ERPNext, ComfyUI/Stable Diffusion WebUI and n8n. Record whether the candidate meets the 70% threshold, and choose `adapter_integration`, `wrapper_layer`, `fork`, or `deferred` with reasons.

**Step 3: Verify, commit and review.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_open_source_integration.py -v && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check`

Create `docs/reviews/phase-08-open-source-integration.md` before Phase 9.

## Phase 9: End-to-End Validation（端到端验证）

**Goal:** Run one full `TEST_BUSINESS` configuration through config import, content draft, lead import/score, sales draft, CRM update, knowledge insertion/retrieval, experiment/feedback, Local API/CLI status and adapter inventory without external action.

**Files:**
- Create: `general_ai_business_os/workflows/__init__.py`, `general_ai_business_os/workflows/test_business_e2e.py`
- Create: `tests/test_general_e2e.py`
- Create: `docs/architecture/General-AI-Business-Operating-System-V1_Module-Map_模块地图.md`
- Create: `docs/reports/2026-08-20_General-AI-Business-Operating-System-V1_Remaining-Work_剩余工作.md`
- Modify: `README.md`

**Step 1: Write failing synthetic E2E test.**

Assert all required phase names are present, every adapter has a truthful status, zero external execution attempts occurred, all artifacts use `TEST_BUSINESS`, data classifications were never wrongly promoted, and result flags say `technical_validation=true`, `human_review_pending/recorded` truthfully, `business_validation_pending=true`.

**Step 2: Implement orchestrator and reporting.**

Compose the real services already built; do not fabricate output. Add CLI/API integration smoke tests using a shared temporary state root. Document module map, migration state, implemented/Mock/Blocked inventory, exact data injection entry point and remaining work.

**Step 3: Full verification and final independent audit.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_general_e2e.py -v && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v && git diff --check && git status --short`

After commit, ask a fresh independent `gpt-5.6-sol` reviewer for a full system audit. It must verify architecture consistency, module completeness, data injection, open-source evaluation, test coverage, future extensibility and the five completion states. Persist the exact result at `docs/reviews/final-system-audit.md`.

**Step 4: Integrate safely.**

Only after the final audit permits continuation: merge the reviewed feature branch into `main`, push `main`, fetch and compare local `main`, `origin/main` and remote SHA. Report only evidence-backed technical/sync states; do not report business validation.

