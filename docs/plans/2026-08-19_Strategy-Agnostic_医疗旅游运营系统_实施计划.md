# Strategy-Agnostic Medical Tourism Operating System Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不锁定任何业务战略、不开启外部动作且不引入第三方依赖的前提下，交付可由模拟数据完整运行的本地医疗旅游运营系统。

**Architecture:** 领域模型与业务规则保持纯 Python；Application Service 通过 Repository、Storage 和 Adapter 端口调用 SQLite、CLI、Local API 和 Mock Adapter。所有事实先走 `Raw → Staging → Adjudicated → Canonical → Decision`，高风险、未授权和外部动作均 fail-closed。

**Tech Stack:** Python 3.9 标准库、`sqlite3`、`dataclasses`、`argparse`、`http.server`、`unittest`、JSON/CSV fixtures。

---

## 验收总表与依赖

| Phase | 交付 | 阻断条件 | 验证 |
| --- | --- | --- | --- |
| 0 | `DEC-ENG-001`、工程状态与脚本边界同步 | 仍存在“禁止系统开发”冲突 | 文档回读 + 旧协作测试 |
| 1 | 配置、领域、SQLite、迁移、审计、权限、Mock Adapter | 领域依赖平台/业务事实 | 领域、迁移、存储测试 |
| 2 | 导入、标准化、去重、校验、冲突/时效、人工复核与晋升 | Research 可绕过人工晋升 | 数据治理测试 |
| 3 | Research、Fact、Demand、Product、Risk、Lead、Match | 出现医学推荐或战略硬编码 | 业务核心与风险测试 |
| 4 | Content、Publishing、Comment、DM、CRM | 发布/私信可真实执行 | 内容互动与 dry-run 测试 |
| 5 | Metrics、Experiment、Weekly Review、Decision、GitHub dry-run | 自动形成正式决策 | 学习闭环测试 |
| 6 | CLI、Local API、Admin/Debug UI | 接口可跳过权限/风险规则 | CLI/API/UI 测试 |
| 7 | 完整 synthetic E2E、全量审计、Git 收尾 | 任意必交付项缺失 | 全套 unittest、硬编码/secret scan、remote readback |

## Task 1: Phase 0 — Governance Sync（治理同步）

**Files:**
- Modify: `project_facts/04_正式决策记录.md`
- Modify: `project_facts/02_当前状态_project_state.yaml`
- Modify: `scripts/README.md`
- Modify: `logs/latest.md`
- Modify: `logs/change_log.md`
- Test: `tests/test_governance_sync.py`

**Step 1: Write the failing test**

测试必须断言 `DEC-ENG-001` 由 `user` 锁定、工程 scope 只含内部架构/模拟/测试/dry-run、业务战略仍是 `false`、外部执行仍是 `false`，并且 `scripts/README.md` 同时列出禁用的战略依赖自动化与允许的通用基础设施。

**Step 2: Run the test to verify it fails**

Run: `/usr/bin/python3 -m unittest tests.test_governance_sync -v`  
Expected: FAIL，因为工程决定及精确脚本边界尚不存在。

**Step 3: Add minimal governance records**

写入 `DEC-ENG-001`，不修改 `stage.code`、任何市场/产品/价格/渠道状态或 `current_goal`。仅增加：

```yaml
engineering_scope:
  architecture_development_allowed: true
  business_strategy_locked: false
  external_execution_allowed: false
```

更新脚本规则以区分 `strategy-specific business automation` 与 `strategy-agnostic system infrastructure`；日志明确这不是业务战略决策。

**Step 4: Run regression tests**

Run: `/usr/bin/python3 -m unittest tests.test_governance_sync tests.test_collaboration_system -v`  
Expected: PASS。

**Step 5: Commit**

只暂存 Task 1 路径，使用 Lore commit，记录为工程范围治理而非战略锁定。

## Task 2: Phase 1 — Foundation（基础设施）

**Files:**
- Create: `medical_tourism_os/__init__.py`
- Create: `medical_tourism_os/config.py`
- Create: `medical_tourism_os/domain/__init__.py`
- Create: `medical_tourism_os/domain/entities.py`
- Create: `medical_tourism_os/domain/policies.py`
- Create: `medical_tourism_os/schemas/README_数据合同.md`
- Create: `medical_tourism_os/storage/contracts.py`
- Create: `medical_tourism_os/storage/sqlite_store.py`
- Create: `medical_tourism_os/repositories/core.py`
- Create: `medical_tourism_os/permissions/policy.py`
- Create: `medical_tourism_os/audit/logger.py`
- Create: `medical_tourism_os/adapters/base.py`
- Create: `medical_tourism_os/adapters/mock.py`
- Create: `medical_tourism_os/migrations/001_initial_schema.sql`
- Test: `tests/test_foundation.py`

**Step 1: Write failing tests**

覆盖：默认配置关闭外部动作；枚举不包含现实业务事实；SQLite migration 可重复；存储/仓库可保存与读取领域记录；未启用 adapter 必然返回 dry-run；审计不保存敏感 payload。

**Step 2: Verify RED**

Run: `/usr/bin/python3 -m unittest tests.test_foundation -v`  
Expected: FAIL，包和实现尚不存在。

**Step 3: Implement minimal ports and entities**

定义所有模块共享的 `Record`、`FactRecord`、`ReviewItem`、`RiskResult`、`AuditEvent` 及状态枚举。领域层不得导入 SQLite、HTTP 或适配器。SQLite 只实现 port，不在服务内嵌 SQL。

**Step 4: Verify GREEN**

Run: `/usr/bin/python3 -m unittest tests.test_foundation -v`  
Expected: PASS。

**Step 5: Commit**

暂存 Task 2 的明确路径并以 Lore commit 记录架构边界。

## Task 3: Phase 2 — Data Governance（数据治理）

**Files:**
- Create: `medical_tourism_os/imports/pipeline.py`
- Create: `medical_tourism_os/exports/safe_export.py`
- Create: `medical_tourism_os/services/data_governance.py`
- Create: `medical_tourism_os/fixtures/synthetic.py`
- Test: `tests/test_data_governance.py`

**Step 1: Write failing tests**

测试 CSV/JSON Research 导入，字段标准化，稳定 ID 去重，缺 provenance 拒绝，冲突/过期标记，`Fact candidate` 排队人工复核，未复核不能晋升、已授权人工复核后才可成为 canonical。加入患者/支付/secret 键名拒绝测试。

**Step 2: Verify RED**

Run: `/usr/bin/python3 -m unittest tests.test_data_governance -v`  
Expected: FAIL，管线未实现。

**Step 3: Implement one-stage-at-a-time pipeline**

每一步保留输入来源与审计 ID；不覆盖 Raw。不接受 `Research → Confirmed fact` 的快捷路径。导出只允许批准的非敏感字段。

**Step 4: Verify GREEN and foundation regression**

Run: `/usr/bin/python3 -m unittest tests.test_foundation tests.test_data_governance -v`  
Expected: PASS。

**Step 5: Commit**

暂存 Task 3 路径；commit trailer 指明人工审批为不可绕过边界。

## Task 4: Phase 3 — Business Core（业务核心）

**Files:**
- Create: `medical_tourism_os/services/business_core.py`
- Create: `medical_tourism_os/services/risk_router.py`
- Create: `medical_tourism_os/workflows/core.py`
- Test: `tests/test_business_core.py`
- Test: `tests/test_risk_and_permissions.py`

**Step 1: Write failing tests**

覆盖 01–05、10–13、14 模块：Research Intake、Fact Adjudication、Demand Radar、Product DB、Risk Router、Lead Scoring、匿名 CRM、Product Matching、Human Review。Risk 测试必须覆盖 PHI、clinical、treatment、medication、emergency、legal、visa、payment、privacy、guarantee、minor；Matching 只能返回 `candidate match`，不得产生医疗推荐。

**Step 2: Verify RED**

Run: `/usr/bin/python3 -m unittest tests.test_business_core tests.test_risk_and_permissions -v`  
Expected: FAIL，服务不存在。

**Step 3: Implement configuration-driven services**

评分规则来自配置对象。风险规则优先，且所有高风险结果停止后续写入。所有候选都以 `TEST_*` fixture 证明配置改变可替换，而不修改服务代码。

**Step 4: Verify GREEN**

Run: `/usr/bin/python3 -m unittest tests.test_business_core tests.test_risk_and_permissions -v`  
Expected: PASS。

**Step 5: Commit**

只提交 Task 4 路径。

## Task 5: Phase 4 — Content & Interaction（内容与互动）

**Files:**
- Create: `medical_tourism_os/services/content_interaction.py`
- Test: `tests/test_content_and_interaction.py`

**Step 1: Write failing tests**

覆盖 06–09 与 12：Content Intelligence 从非决策输入形成 `ContentBrief`；Content Factory 只生成 draft Video Script/Carousel/FAQ/SEO/Reply；Publishing Queue 的状态机合法且 adapter 关闭时不发布；Comment/DM 只接收脱敏模拟导入并经风险路由；CRM 只保存允许字段。

**Step 2: Verify RED**

Run: `/usr/bin/python3 -m unittest tests.test_content_and_interaction -v`  
Expected: FAIL。

**Step 3: Implement draft-only state machines**

状态允许 `draft → review → approved → queued`，但 `published` 仅能由明确启用的 adapter 未来实现；本轮禁止实际副作用。

**Step 4: Verify GREEN**

Run: `/usr/bin/python3 -m unittest tests.test_content_and_interaction -v`  
Expected: PASS。

**Step 5: Commit**

只提交 Task 5 路径。

## Task 6: Phase 5 — Learning Loop（学习反馈闭环）

**Files:**
- Create: `medical_tourism_os/services/learning_loop.py`
- Create: `medical_tourism_os/workflows/weekly_review.py`
- Test: `tests/test_learning_loop.py`

**Step 1: Write failing tests**

覆盖 15–19：指标漏斗、带唯一 `primary_variable` 的实验、`observed/contradicted/insufficient_sample` 结果、周复盘、Decision Candidate、GitHub Sync dry-run 和敏感导出拒绝。必须断言系统不会自动锁定 Decision。

**Step 2: Verify RED**

Run: `/usr/bin/python3 -m unittest tests.test_learning_loop -v`  
Expected: FAIL。

**Step 3: Implement reviewable learning loop**

每个 summary 链接来源数据 IDs 和审计事件。`DecisionCandidate` 始终是候选，除非显式进入 Task 3 的人工审查接口。

**Step 4: Verify GREEN**

Run: `/usr/bin/python3 -m unittest tests.test_learning_loop -v`  
Expected: PASS。

**Step 5: Commit**

只提交 Task 6 路径。

## Task 7: Phase 6 — Interfaces（交互接口）

**Files:**
- Create: `medical_tourism_os/interfaces/cli.py`
- Create: `medical_tourism_os/interfaces/local_api.py`
- Create: `medical_tourism_os/interfaces/admin_debug.py`
- Create: `medical_tourism_os/__main__.py`
- Create: `medical_tourism_os/docs/README_本地运行与接口.md`
- Test: `tests/test_interfaces.py`

**Step 1: Write failing tests**

使用 `argparse` 测试全部 prompt 要求的 CLI 命令与 `--dry-run`。通过本地 server 测试所有 15 个 API route 和根路径 Admin/Debug HTML；路由必须经同一服务/权限层，不得直接操作数据库。

**Step 2: Verify RED**

Run: `/usr/bin/python3 -m unittest tests.test_interfaces -v`  
Expected: FAIL。

**Step 3: Implement local-only interfaces**

接口只绑定 `127.0.0.1`，不自动启动。错误以不暴露敏感输入的 JSON 返回，Admin 页面只显示聚合和关闭状态。

**Step 4: Verify GREEN**

Run: `/usr/bin/python3 -m unittest tests.test_interfaces -v`  
Expected: PASS。

**Step 5: Commit**

只提交 Task 7 路径。

## Task 8: Phase 7 — End-to-End Validation and Closeout（端到端验证与收尾）

**Files:**
- Create: `medical_tourism_os/workflows/e2e_scenario.py`
- Create: `tests/test_e2e_synthetic_scenario.py`
- Modify: `README.md`
- Modify: `logs/latest.md`
- Modify: `logs/change_log.md`
- Test: `tests/test_no_strategy_hardcoding.py`

**Step 1: Write failing E2E and static-policy tests**

E2E 必须跑 `Research → Fact → Demand → Product → Content → Comment/DM → Risk → Lead → Match → Metrics → Experiment → Weekly Review → Decision Candidate → GitHub Dry Run`。静态测试扫描核心代码，拒绝任何现实候选战略字面量，并验证必需模块均有实际可调用代码而非 `pass`/空类/TODO。

**Step 2: Verify RED**

Run: `/usr/bin/python3 -m unittest tests.test_e2e_synthetic_scenario tests.test_no_strategy_hardcoding -v`  
Expected: FAIL，完整场景或检查器尚不存在。

**Step 3: Implement minimal orchestration and user documentation**

Scenario 仅注入 synthetic fixture，产生可审计报告。README 清晰标注如何运行测试、CLI、API 以及仍为 Mock/blocked 的能力；日志区分技术、业务与同步完成态。

**Step 4: Run all validations**

Run:

```bash
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/git diff --check
/usr/bin/git status --short
```

并以 Python 静态扫描检查 secret-like、PHI-like 和硬编码现实策略字面量；必须人工回读关键中文文件头、关键风险/晋升/权限注释与 required output inventory。

**Step 5: Commit, push, and remote readback**

仅暂存明确文件；使用 Lore commit。执行 `/usr/bin/git push origin main`、`/usr/bin/git fetch origin`，比较 `HEAD` 与 `origin/main`。最终报告列出 commit SHA、push 状态、远端回读、测试、Mock adapter、external blocked 与 remaining work。
