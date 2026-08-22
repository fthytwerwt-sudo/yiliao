# Acquisition Plugin 获客插件设计

**状态：** 已由用户在 2026-08-23 的实施任务中锁定并授权本地 Mock 实现。
**适用范围：** 成都国际医疗旅游项目的 B2B Business Prospect（商业潜客）发现与 Outreach（主动触达）准备层。
**现实边界：** `external_execution_allowed=false`；不访问真实目录、网站或邮箱，不保存患者资料，不发送真实邮件。

## 1. 目标

在 `medical_tourism_os/acquisition/` 建立独立 Application Plugin（应用插件），把企业目录发现、企业分类、合作潜客评分、公开联系方式引用、触达草稿、人工复核、发送队列、回复引用和反馈信号串成可替换的执行层。

本版本只证明：

- 领域合同、Provider 接口、服务和 Workflow 可以离线协作；
- Mock Adapter 会明确返回 `dry_run=true`、`executed=false`；
- Business Prospect 与 Consumer Lead 使用不同模型、评分器和工作流；
- 未来真实连接器可以在不修改 `general_ai_business_os/` 的前提下替换 Mock。

本版本不证明真实企业存在、联系方式有效、邮件可投递、合作意愿、患者需求或商业结果。

## 2. 架构边界与方案选择

### 采用：独立纵向 Acquisition Plugin

```text
medical_tourism_os/acquisition/
  domain/       BusinessEntity / Prospect / ContactPoint / OutreachDraft
  interfaces/   DirectoryProvider / ContactExtractor / EmailProvider
  services/     BusinessClassifier / ProspectScorer / OutreachGenerator
  workflows/    ProspectDiscoveryWorkflow / OutreachWorkflow
  adapters/     MockDirectoryProvider / MockEmailProvider
  schemas/      输入、评分、Provider 结果、回复与反馈合同
```

优点是业务语义只留在医疗旅游 Application Plugin；接口可替换，Mock 可验证，Consumer Lead 边界不受影响。代价是第一版会保留一些显式 DTO 和状态对象，但这些对象正是未来真实 Adapter 的稳定替换面。

### 否决：复用 AnonymousLead / LeadScorer

Consumer Lead 表达获得联系授权的潜在患者咨询，拥有 `consent`、`intent` 与匿名联系方式规则；Business Prospect 表达公开企业和合作可能性。复用会混淆隐私、评分和生命周期，因此 Acquisition 使用独立 `ProspectScorer`，不导入 `LeadScorer`。

### 否决：把获客能力放入 general_ai_business_os

ADR-0002 规定 Core 只负责 Agent Runtime、Workflow Engine、Tool Registry、Memory、Permission、Audit 和 AI System Config。企业、市场、联系人和触达均属业务语义，只能通过 Application Plugin 扩展；本轮不修改 Core。

## 3. 数据模型

### BusinessEntity（企业实体）

字段：`id`、`company_name`、`category`、`location`、`website`、`description`、`source_url`、`evidence_refs`、`status`。

- `source_url` 和 `evidence_refs` 保存来源引用，不代表来源已被人工验证。
- Mock fixture 只能使用 `TEST_*` / `.invalid` 等 synthetic 标识。
- `status` 区分 `discovered`、`classified`、`held`，不表达真实合作关系。

### Prospect（合作潜客）

字段：`id`、`business_entity_id`、`fit_score`、`priority`、`reason_codes`、`status`。

- `fit_score` 为 0–100 的证据化综合分，不复用 Consumer Lead 分数。
- `priority` 为 `high` / `medium` / `low`。
- `status` 为 `human_review_queue` / `outreach_queue` / `hold_for_more_evidence`。

### ContactPoint（商业联系方式）

字段：`type`、`value_reference`、`source`、`verified_at`。

- `value_reference` 只保存公开联系方式的引用，不在领域对象或 Mock 发送载荷中保存真实邮箱/电话。
- `verified_at=None` 表示尚未核验，不得被描述为有效联系方式。

### OutreachDraft（触达草稿）

字段：`prospect_id`、`subject`、`body`、`personalization_reason`、`review_status`。

- 默认 `review_status=pending`。
- 正文必须明确联系原因、合作假设、可验证价值和“尚未发送”。
- 只有具名人工复核才可转为 `approved`；批准不等于真实发送。

### Schema（数据合同）

`schemas/` 保存跨层 DTO：目录/联系人 Provider 结果、五维评分、发现流程结果、邮件 Mock 结果、回复引用和反馈信号。Adapter 结果必须同时表达 `dry_run` 与 `executed`，避免把“没有动作”误报为成功。

## 4. 接口与 Adapter 边界

### DirectoryProvider

`search(market, keywords) -> DirectorySearchResult`。结果包含 `BusinessEntity` 集合以及执行状态。V1 Workflow 只接受显式 `mock_only` Provider 并拒绝真实执行结果。未来 Google、Yelp、Yellow Pages 或本地目录连接器只能实现该接口，不能把 SDK 类型传入领域层。

### ContactExtractor

`extract(entity) -> ContactExtractionResult`。只返回 `ContactPoint` 引用和 provenance；真实网站采集必须在后续独立审批中加入网络权限、robots/条款、限速、证据时间和失败关闭测试。本轮没有真实或 Mock 提取器。

### EmailProvider

`send(draft, contact) -> EmailSendResult`。接口只描述发送边界；本轮 `MockEmailProvider` 永远 `dry_run=true`、`executed=false`，不创建 SMTP/Gmail/WhatsApp/LinkedIn 客户端。`OutreachWorkflow` 只接受显式 `mock_only` Provider，并会拒绝任何声称发生真实执行的结果。

### Plugin Manifest

`medical_tourism_os/acquisition/plugin.json` 只声明 `WORKFLOW_RUN` capability。Core V1 的 `PluginRegistry` 只发现并登记 manifest，不 import 或执行 entrypoint；因此该 manifest 是隔离边界证明，不是生产插件托管或外部权限。

## 5. 服务规则

### BusinessClassifier

优先接受已归一化的显式类别；未知类别只用可审计关键词做初步候选分类，输出仍是 `classified` 候选，不升级为已验证企业事实。

### ProspectScorer

五个维度等权：

- `category_fit`
- `market_fit`
- `audience_overlap`
- `contact_quality`
- `partnership_probability`

每项必须是 0–100。综合分向下取整为整数；`>=75` 为 high，`>=50` 为 medium，否则 low。没有显式评分证据时全部为 0，并进入 `hold_for_more_evidence`。high 进入 `outreach_queue`，medium 进入 `human_review_queue`，low 进入 hold。`reason_codes` 保留每个维度和缺证据原因，避免黑箱分数。

### OutreachGenerator

根据 `BusinessEntity` 和 `Prospect` 生成结构化英文草稿。个性化只引用企业名称、分类、所在地和已提供的证据引用；不得虚构合作、患者、临床能力、价格或结果。生成后始终进入人工复核。

## 6. Workflow

### ProspectDiscoveryWorkflow

```text
market + keywords
  -> DirectoryProvider.search
  -> BusinessEntity
  -> BusinessClassifier
  -> optional ContactExtractor
  -> ProspectScorer
  -> ProspectDiscoveryResult / Prospect Queue
```

Mock 查询可产生 synthetic 企业对象，但 `executed=false`。如果没有五维评分输入，流程仍会创建可审计 Prospect，并 fail-closed 到 `hold_for_more_evidence`。

### OutreachWorkflow

```text
Prospect + BusinessEntity
  -> OutreachGenerator
  -> pending Human Review
  -> named approval
  -> Send Queue
  -> EmailProvider.send (V1 always dry-run)
  -> Reply reference intake
  -> Feedback signal
```

流程不保存回复正文；只保存可回读引用和结构化结果。回复必须建立在 send queue 记录之后；非 `no_response_observed` 的反馈必须引用该 Prospect 已记录的 Reply Intake。即使草稿已批准，Mock 邮件仍不会外发，`approved` / `queued` / `dry_run` 都不等于 `sent`。

## 7. 错误与安全处理

- 缺企业名称、来源 URL、证据引用、非法评分或空关键词：抛出稳定 `ValueError`，不静默清洗成“成功”。
- 未批准草稿不能进入发送尝试。
- 空人工 reviewer 不能批准。
- Email Mock 不接受原始邮箱字符串，只接收 `public_contact_ref_` 加 32 位 hex token 的 `value_reference`。
- 不导入或修改 Consumer Lead、LeadScorer、患者字段、Core Runtime、真实 SDK 或 API key。

## 8. 测试策略

采用 `unittest` + TDD：

1. 领域对象可创建且校验关键不变量；
2. 五维评分得到稳定分数、优先级、原因和队列；
3. OutreachDraft 包含联系原因、合作假设、可验证价值并默认待审；
4. ProspectDiscoveryWorkflow 串起 Mock 目录、分类和评分；
5. OutreachWorkflow 要求具名人工批准；
6. 两个 Mock Adapter 均不产生真实外部动作；
7. Core 源码不新增 Acquisition 业务语义；Consumer Lead 测试保持通过。

## 9. 开源项目接入位置

| 能力 | 未来接入位置 | 必须保持的边界 |
| --- | --- | --- |
| 企业目录 SDK / 数据集 | `adapters/` 实现 `DirectoryProvider` | SDK 对象不得进入 domain；记录 source/evidence；默认 disabled |
| 网站公开信息提取器 | `adapters/` 实现 `ContactExtractor` | 单独网络权限与条款审查；只返回公开联系方式引用 |
| 分类 / Enrichment 模型 | `services/` 的可替换分类实现或新增受限 port | 不把模型猜测写成事实；保留 provenance 与人工复核 |
| 邮件客户端 | `adapters/` 实现 `EmailProvider` | 独立批准、权限、审计、DNC/退订和真实发送测试 |
| LangGraph / durable workflow | Application Plugin 外围封装 `workflows/` | 不成为 Core 依赖；先证明需要 checkpoint/retry 后再引入 |

当前可以开始做开源项目的“接口适配评估和离线 fixture 验证”，但不能开始真实账号、API、网站采集或邮件发送接入；任何第三方依赖都需单独选择、许可与安全审查。

## 10. 完成态边界

本轮完成只表示本地技术架构与 Mock 合同成立。`strategy_definition_pending`、`external_execution_allowed=false`、真实合作验证未开始、真实联系方式未核验、真实发送为零。
