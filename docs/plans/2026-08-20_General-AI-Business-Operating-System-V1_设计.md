# General AI Business Operating System V1 设计

## 1. 目标与边界

本设计构建 `General AI Business Operating System V1`（通用 AI 商业运营系统）。它是可被不同商业项目复用的能力层，覆盖 Research、Content、Lead Generation、Sales、CRM、Knowledge、Feedback 与 Experiment。

它不是任何具体业务的战略、市场选择、客户名单、产品定义、价格、渠道计划或 Go/No-Go 结论。现实业务值只能通过已审核的 `Business Config Package`（业务配置包）注入；核心 Python 不得写入国家、客户、产品、价格、平台、医院或商业模式事实。

外部动作保持 fail-closed：默认不发送、不发布、不抓取、不连接第三方服务。Mock、dry-run、`Implemented` 与真实外部执行是不同状态，所有接口必须显式报告状态。

## 2. 已选迁移策略

采用方案 A：新建 `general_ai_business_os/` 作为 V1 主架构，保留 `medical_tourism_os/` 作为兼容入口。

迁移采用 strangler migration（绞杀式迁移）：

1. 新通用包永不导入旧包，防止核心倒向医疗语义。
2. 新能力只写入通用包；旧包继续运行已经存在、已测试的实现。
3. 当某项通用能力在新包拥有等价行为和回归证据时，才由旧包新增一个窄 compatibility adapter（兼容适配器）委托给新包。
4. 旧入口、旧 CLI/API、旧测试均不得删除或暴力重命名；迁移完成前保留可回滚路径。
5. 每一项迁移都在 `docs/migrations/` 记录旧入口、替代入口、兼容策略、回归测试、状态和回滚方法。

## 3. V1 模块地图

```text
Business Config Package
        |
        v
BusinessConfigRegistry -----> Operating Brain / Workflow Orchestrator
                                      |
       +------------------------------+-----------------------------+
       |              |               |             |                |
   Media Agent   Lead Agent      Sales Agent     CRM Agent    Knowledge System
       |              |               |             |                |
       +------------------------------+-----------------------------+
                                      |
                                      v
                              Experiment Engine
                                      |
                                      v
                              Feedback / Review Loop

All external integrations pass through Adapter Ports and Permission Policy.
```

目标目录：

```text
general_ai_business_os/
  business_config/       # 配置合同、JSON/YAML 导入、校验、审核与版本注册
  domain/                # 通用领域实体、分类、生命周期和结果类型
  agents/
    media/               # 内容 brief、prompt、asset、quality workflow
    leads/               # profile、发现、CSV 导入、评分与候选状态
    sales/               # message intake、intent、risk、draft、approval
    crm/                 # 匿名 lead lifecycle、follow-up 与 outcome
    knowledge/           # source-tracked document/fact/rule/FAQ/template
    experiments/         # hypothesis、variables、metric、outcome
  adapters/              # content/search/crm/email/social 的 Port + Mock
  storage/               # Storage Port、SQLite 开发实现、迁移接口
  permissions/           # 默认拒绝的外部动作与人工审批判断
  audit/                 # 安全 allowlist 审计
  interfaces/            # CLI、loopback-only Local API
  workflows/             # 内部编排、反馈循环与 synthetic E2E
  fixtures/              # 仅 TEST_BUSINESS 等虚构数据
  compatibility/         # 供旧包逐步接入的明确桥接对象

medical_tourism_os/
  ...existing modules...
  compatibility/         # 仅放入已验证的委托，不删除原入口
```

## 4. Business Config 与数据注入

### 4.1 配置包合同

一份业务配置包由 manifest（清单）和可选领域文件组成：

```text
manifest.json|yaml
market.json|yaml
customer.json|yaml
product.json|yaml
channel.json|yaml
content_rules.json|yaml
sales_rules.json|yaml
lead_rules.json|yaml
```

`manifest` 至少包含 `schema_version`、`business_id`、`config_version`、`source_refs`、`classification`、`review_status` 与 `reviewed_by`。文件名、字段名和代码中允许出现通用合同名；任何具体业务值只存在于导入包或测试 fixture。

JSON 使用标准库解析；YAML 使用安全解析器，禁止构造任意 Python 对象。解析器只接受 mapping/document 类型，并在语法、未知字段、缺少必填字段和重复版本时返回可审计错误。

### 4.2 数据状态

```text
Raw -> Normalized -> Validated -> Fact Review -> Canonical Config Version
```

导入不能把 `RESEARCH`、`FACT_CANDIDATE`、`HYPOTHESIS` 或 `UNKNOWN` 自动升级为 `CONFIRMED_FACT`/`DECISION`。只有包含 provenance（来源证明）、具名审核者、通过冲突/新鲜度检查、且状态为批准的包才可注册为可消费版本。

`BusinessConfigRegistry` 只返回已确认的不可变版本；Agent 必须以明确 `config_version` 请求配置。缺失、未审核、被拒绝或版本冲突的输入必须阻断，不回退到隐藏默认业务数据。

### 4.3 存储与安全

领域服务依赖 Storage Port，不依赖 SQLite。V1 提供 SQLite 开发适配器，保留 PostgreSQL 实现接口。审计只记录允许字段与摘要；不得持久化患者身份、病历、健康信息、原始联系人、密钥或 Token。

配置不能覆盖权限：即使包含 adapter 选项，`external_action` 仍默认关闭，真实连接必须同时满足 Adapter enabled、明确权限与人工审批。

## 5. Agent 合同

### 5.1 Media Production Agent

输入为 `ContentBrief`，依次生成 `PromptPlan`、图片/视频/语音/字幕请求、`QualityCheckResult` 与 `AssetRecord`。图片、视频、TTS、字幕均使用独立 Adapter Port。V1 的本地 Mock 生成结构化候选产物和质量结果；不会声称已生成真实媒体，也不会发布。

### 5.2 Lead Discovery Agent

输入为 `TargetProfile`（通用行业、需求、地点、关键词等）；输出为 `LeadCandidate`（来源、网站、匿名联系方式引用、理由、置信度、状态）。CSV 走同一 Normalize/Validate 流程；API 和 Scraper 仅有明确 Port 与 disabled Mock。发现、评分、导入均不自动发送，不保存原始敏感联系方式。

### 5.3 Sales Draft Agent

输入为 `MessageIntake`，输出依次经过 `IntentClassification`、`RiskCheck`、`ReplyDraft`、`HumanApproval`。V1 使用可测试的确定性规则和可替换模型 Adapter；只产生 `reply_candidate`，默认不自动回复、报价、承诺或采取外部动作。

### 5.4 CRM Agent

维护 `Lead -> Conversation -> Stage -> FollowUp -> Outcome`。生命周期使用通用状态：`NEW`、`INTERESTED`、`QUALIFIED`、`CONSULTING`、`CONVERTED`、`LOST`。记录匿名标识、状态、时间和审核安全摘要；不保存患者/健康信息，也不连接真实 CRM。

### 5.5 Knowledge System

保存带 `source`、`date`、`scope`、`classification`、`confidence` 的 `Document`、`Fact`、`Rule`、`FAQ` 与 `ContentTemplate`。检索接口必须回传 `source_ref`；Research 仍是 Research，检索不能绕过审核成为事实裁决。

### 5.6 Experiment Engine 与反馈闭环

实验包含 `Hypothesis`、一个 `primary_variable`、零到多个 `supporting_variables`、指标、观察窗口、`Result` 与结果 `OBSERVED`、`CONTRADICTED` 或 `INSUFFICIENT_SAMPLE`。反馈只产生复核候选和下一步实验建议，不产生业务 Decision。

## 6. Adapter、权限与运行状态

所有外部连接使用统一 Adapter Port，最少拥有：名称、能力、状态、输入校验、dry-run 结果与失败原因。状态枚举为：

| 状态 | 含义 |
| --- | --- |
| `IMPLEMENTED` | 有真实的本地业务逻辑，但不代表连接到第三方。 |
| `MOCK` | 仅生成确定性测试/开发结果。 |
| `BLOCKED` | 因权限、配置、凭据、实现缺失或风险规则不可执行。 |
| `DISABLED` | 明确关闭，不能被调用。 |

V1 的外部平台一律为 `MOCK` 或 `BLOCKED`，即使未来真实 Adapter 可实现，也必须由 Permission Policy 和人工审批单独放行。

## 7. Local API 与 CLI

Local API 仅绑定 `127.0.0.1`，默认不启动。它至少提供：

```text
/config  /content  /leads  /messages  /crm  /knowledge  /experiments  /metrics
```

CLI 至少提供：

```text
system init
config import
content generate
lead import
lead score
message analyze
crm update
experiment create
weekly review
```

所有命令返回结构化状态、审计标识和阻断原因；没有命令产生外部发送、发布、同步或真实数据抓取。

## 8. 开源项目评估和接入原则

不重复造轮子，但也不在 V1 提前耦合大型运行时。Phase 8 输出 `Open Source Evaluation`，逐项记录覆盖率、许可/运维/安全影响、是否满足 70% 需求、接入方式与拒绝理由。

初步定位：

| 领域 | 候选 | V1 决策 |
| --- | --- | --- |
| Agent workflow | LangGraph、CrewAI、AutoGen、Semantic Kernel | 建 Port 与 workflow 契约；不引入运行时依赖。 |
| Durable workflow | Temporal | 仅定义 future integration seam；当前本地同步 workflow 足够。 |
| Vector retrieval | Chroma、Qdrant、Weaviate | 保留 Knowledge Retrieval Port；当前 SQLite metadata lookup。 |
| CRM | Twenty CRM、SuiteCRM、ERPNext | 保留 CRM Adapter Port；V1 本地 CRM 状态机为真实实现。 |
| Content | ComfyUI、Stable Diffusion WebUI | 建 Content Adapter Port 和 Mock；真实 provider 不连接。 |
| Automation | n8n | 不直接依赖；以 webhook/workflow adapter 作为未来边界。 |

只有候选满足至少 70% 已确认能力需求、不会绕过 data/permission gate、并具备清晰部署和回滚路径时，才以 Adapter Integration、Fork 或 Wrapper Layer 接入。不能接入时必须记录理由，不伪称已整合。

## 9. 测试与完成态

测试分为：单元测试、模块集成测试、跨 Agent workflow 测试、端到端 synthetic test。唯一业务 fixture 是 `TEST_BUSINESS`；不使用真实医疗项目、真实市场、真实客户或真实外部账户。

系统报告必须单独列出：

- `technical_validation`：代码与测试的证据。
- `content_validation`：内容产物是否完成规定质量检查；V1 可为 not_applicable 或 local_mock_only。
- `human_review`：逐 Phase 独立技术审查结果。
- `business_observation`：真实业务观察；V1 始终 pending/not_started。
- `sync_status`：本地、分支、`main` 与 `origin/main` 的已验证同步状态。

测试通过、Mock 返回、文件存在和 Git push 都不能被描述为商业验证、真实发布、客户接收或业务完成。

## 10. 逐 Phase 实施与审查协议

实施顺序固定为：

1. Foundation（基础架构）
2. Business Config（业务配置层）
3. Media Agent（媒体 Agent）
4. Lead Discovery Agent（线索发现 Agent）
5. Sales Draft Agent（销售回复 Agent）
6. CRM Agent（客户管理 Agent）
7. Knowledge System（知识系统）
8. Open Source Integration（开源接入）
9. End-to-End Validation（端到端验证）

每一个 Phase 都严格执行：`Build -> Review -> Fix -> Continue`。完成当前 Phase 后，Builder 先运行该 Phase 的全量适用测试、静态检查与需求清单；随后由独立、只读的 `gpt-5.6-sol` 高推理 Reviewer 审查实际 diff、提交、测试输出和运行结果。

Reviewer 不写代码、不扩展需求、不决定市场/产品/价格/商业模式/医疗方案/Go-No-Go。审查输入固定包括：Phase Goal、Implementation Plan、Changed Files、Architecture Impact、Tests Result、Known Limitations、Remaining Work。审查输出固定包含：

```yaml
phase_review:
  phase_name:
  status: PASS | PASS_WITH_LIMITATIONS | FAIL
  evidence:
  completed_items:
  missing_items:
  architecture_risk:
  code_risk:
  data_risk:
  security_risk:
  must_fix_before_next_phase:
  can_continue:
  next_action:
```

仅 `PASS`，或限制不影响下一阶段依赖的 `PASS_WITH_LIMITATIONS`，可启动下一 Phase。`FAIL` 必须先修复、重新验证、重新审查。审查报告保存到 `docs/reviews/`，并与审查时对应的提交 SHA 绑定。

## 11. Phase 迁移计划

| Phase | 主交付 | 对旧包影响 | 审查闸门 |
| --- | --- | --- | --- |
| 1 | 通用包骨架、领域基础、权限、审计、Storage Port、CLI/API 基础 | 无行为变更 | Foundation Review |
| 2 | JSON/YAML 配置包、导入、审核、版本注册与持久化 | 无行为变更 | Config Review |
| 3 | Media Agent、质量检查、Asset Library、Mock adapters | 无行为变更 | Media Review |
| 4 | Lead profile/discovery/CSV/scoring 与 disabled adapters | 无行为变更 | Lead Review |
| 5 | Message intake/intent/risk/reply candidate/approval | 无行为变更 | Sales Review |
| 6 | CRM lifecycle、匿名记录、follow-up/outcome | 无行为变更 | CRM Review |
| 7 | Knowledge、source tracking、experiment、feedback loop | 无行为变更 | Knowledge Review |
| 8 | 官方资料核验、70% fit 评估、integration wrappers/blocked adapters | 可选窄兼容委托 | Integration Review |
| 9 | TEST_BUSINESS 全流程、CLI/API 互通、Module Map、迁移报告 | 可选兼容 smoke test | Final System Review |

## 12. 明确不在 V1 范围

- 真实业务战略、市场、客户、产品、价格、渠道或商业模式选择。
- 真实发送、发布、爬取、联系人联络、付款、订单、广告或第三方账号操作。
- 患者身份、病历、健康信息、诊断、治疗建议或医疗承诺。
- 因测试或 Mock 通过而宣称真实业务、内容或合规结果。

