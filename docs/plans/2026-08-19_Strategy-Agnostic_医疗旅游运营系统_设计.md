# Strategy-Agnostic Medical Tourism Operating System 设计

**状态：** 已由用户在 2026-08-19 授权实施。  
**工程决定：** `DEC-ENG-001` 将在 Phase 0 写入正式决策记录；它只允许系统工程，不锁定任何业务战略。  
**不在本轮决定：** 市场、客户、产品、价格、医院、渠道、商业模式、Supply/Demand 优先级、Go / No-Go，以及任何外部现实动作。

## 1. 目标与边界

本轮建立可以离线运行的国际医疗旅游项目运营系统。它让未来经过人工确认的业务事实以数据、配置和受审计的审批流程进入系统，而不是要求修改核心代码。

系统只能使用 synthetic fixture（模拟数据）完成端到端验证。所有现实适配器默认 `disabled`，因此 API、CLI、队列和同步能力在本轮均不产生发布、私信、外联、付款、患者管理或医学判断等外部副作用。

医疗安全边界不在系统内被“自动判断为合规”。风险模块只按规则路由和阻断；涉及 PHI、诊断、治疗、处方、紧急情况、法律、签证、支付、隐私或未成年人时，必须 `fail_closed`。

## 2. 方案比较与选定路线

| 方案 | 描述 | 取舍 |
| --- | --- | --- |
| A（采用） | Python 标准库、SQLite、内置 HTTP server、静态本地 Admin/Debug 页面 | 无新增依赖、离线可跑、边界可单测；UI 和 HTTP 功能刻意保持本地调试级别。 |
| B | FastAPI + SQLAlchemy + React | 开发体验更丰富，但本轮需要新增依赖、构建链和版本治理，超出当前无外部依赖启动的约束。 |
| C | 只写数据模型和 Markdown 文档 | 成本较低，但无法兑现本轮要求的 API、CLI、数据库、导入清洗、工作流和端到端验证。 |

选择方案 A。未来需要生产级 Web、认证、队列、PostgreSQL 或平台 SDK 时，保留的 `Storage`、`Adapter`、`Repository` 和 `Application Service` 边界允许替换基础设施，而不是重写领域规则。

## 3. 分层架构

```text
Interface Layer
  CLI / Local API / Admin Debug UI
          ↓
Application Layer
  workflows / services / review gates / metrics / dry-run sync
          ↓
Domain Layer
  facts / demand / products / content / leads / risks / experiments / decisions
          ↓
Ports
  repositories / storage / external adapter interfaces
          ↓
Infrastructure Layer
  SQLite / migrations / import-export / audit / mock adapters / fixtures
```

### Domain Layer（领域层）

领域模型是纯 Python `dataclass` 和枚举，不导入 HTTP、SQLite 或任何平台代码。它们定义事实分类、审查状态、内容状态、风险判定、线索、候选匹配、实验和决策候选的合法状态。

`Confirmed fact` 与 `Decision` 的生成不能由导入、AI 输出或普通服务直接调用：必须经过 `HumanReviewGate`，并记录 `reviewed_by`、时间和 `provenance（数据来源证明）`。

### Application Layer（应用层）

服务将领域规则编排为可测试的工作流。各服务的输入和输出是领域对象或显式 DTO；服务不根据名称、国家、平台、医院或产品类别分支。

工作流包含：

```text
Research → Raw → Staging → validation / de-duplication / conflict / freshness
         → review queue → Canonical fact → decision candidate
Demand / Product / Fact / Experiment → content brief → draft content
Comment / DM → risk route → anonymous lead → score → candidate match
Metrics → experiment result → weekly review → decision candidate → GitHub dry run
```

### Adapter 与存储（端口）

- `Storage` 协议由 SQLite 实现；领域与服务只看仓库接口。数据库迁移为可重复、可审计的版本脚本。
- 所有真实平台都实现统一的 adapter port，并且默认 `enabled=False`。本轮只注册 `MockAdapter`；即使传入发布或同步命令，也会返回明确 dry-run 结果。
- GitHub 同步只导出已批准、非敏感、允许同步的摘要，默认只生成计划而不联网。

## 4. 数据合同与治理

每条 `FactRecord` 至少保存：

`id`、`claim`、`source`、`source_date`、`scope`、`classification`、`confidence`、`freshness`、`conflict_status`、`review_status`、`reviewed_by`、`created_at`、`updated_at`、`provenance`。

数据层状态是不可跳过的：

```text
Raw → Staging → Adjudicated → Canonical → Decision
```

研究资料只能进入 `Raw` / `Staging` / `Adjudicated`。只有人工复核接口可以把符合证据要求的 `Fact candidate` 提升为 `Canonical`，而 `DecisionCandidate` 只能由用户、用户与 ChatGPT 或专业主体锁定。本轮 fixture 不创建任何 `Confirmed fact` 或正式业务决策。

导入清洗管道是可组合的六个小组件：Importer、Normalizer、Deduplicator、Validator、ConflictDetector、FreshnessChecker。每一步产出原始记录的 ID 与审计事件，避免覆盖来源事实。

## 5. 风险、权限与敏感数据

`PermissionPolicy` 采用 deny-by-default：操作必须同时满足本地允许、权限允许、适配器启用和非高风险。`RiskRouter` 优先于 Lead、Content、Publishing 与 Sync 流程运行；高风险输入不会写入业务记录，只留下最小化的非敏感审计标记。

CRM 仅允许 `anonymous_lead_id`、脱敏 `contact_reference`、来源、状态、下一步和同意状态。输入键名或内容疑似包含患者、健康、支付、身份或秘密信息时，导入服务拒绝保存其原文。

## 6. 接口设计

### CLI

`python3 -m medical_tourism_os` 提供主体 prompt 要求的 12 个命令组：初始化、研究导入、事实列表与复核、需求/产品查询、内容草稿生成、风险检查、线索评分、实验创建与复核、周复盘、决策候选、GitHub dry-run。

### Local API

本地 HTTP 路由提供 `/research`、`/facts`、`/demand`、`/products`、`/content`、`/publishing`、`/comments`、`/dms`、`/risks`、`/leads`、`/matches`、`/metrics`、`/experiments`、`/reviews`、`/decisions`。它不暴露认证、真实平台凭据或生产服务；请求只接收安全测试/本地数据。

### Admin / Debug UI

服务根路径提供一页只读 HTML：显示领域对象数量、审查待办、风险事件和所有 adapter 的关闭状态。它用于本地审计，不是对外管理后台。

## 7. 测试与验收策略

每个行为先以 `unittest` 写成失败测试，再写最小实现。测试分为：领域、存储、迁移、导入清洗、权限、风险、工作流、API/CLI、adapter dry-run 与端到端模拟。

端到端 fixture 只使用 `TEST_MARKET_A`、`TEST_PRODUCT_A`、`TEST_CHANNEL_A`、`TEST_PROVIDER_A` 之类合成标识；测试断言不出现现实国家、平台、医院、医生、价格或医疗服务名。

本轮完成的技术证据是：全部测试通过、无业务战略硬编码、外部 adapter 关闭、事实提升与风险阻断均有负向测试、完整模拟链路运行。它不等于任何市场、临床、合规、商业或用户验收。

## 8. 子任务依赖图

```text
Phase 0 Governance Sync
        ↓
Phase 1 Foundation ──→ Phase 2 Data Governance
        ↓                        ↓
        └──────────────→ Phase 3 Business Core
                                      ↓
                              Phase 4 Content & Interaction
                                      ↓
                              Phase 5 Learning Loop
                                      ↓
                              Phase 6 Interfaces
                                      ↓
                           Phase 7 End-to-End Validation
                                      ↓
                         Git commit / push / remote readback
```

每一阶段结束前执行本阶段测试和覆盖检查；下一阶段不能把上一阶段的 TODO 或空实现当作可用能力。所有阶段完成后才可以报告 `technical implementation completed`。

## 9. 明确的降级路线与阻断

- 真实 API 无法或不应连接：继续使用 Mock Adapter，不改变领域模型。
- SQLite 不适用于未来规模：替换 Storage 实现，保留 Repository 协议。
- Admin UI 无法覆盖某项调试：使用 JSON API/CLI，不引入现实外部访问。
- 发现业务事实、个人/健康信息、临床请求、外部动作或凭据：拒绝写入，记录最小安全审计，并维持 blocked。
- 若无法保持“战略未锁定”与“系统工程允许”同时成立：返回 `blocked_governance_conflict`，不开始系统代码。

## 10. 完成态边界

本设计授权的是 `technical_validation` 与 Git 同步，不授权业务执行。最终报告必须独立列出技术、内容、人工、业务和同步状态；业务战略依旧为 `strategy_definition_pending`，外部执行依旧为 `false`。
