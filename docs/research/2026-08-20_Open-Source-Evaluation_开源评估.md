# Open Source Evaluation 开源评估

范围：只基于官方一手文档和官方仓库做案头评估；未安装、未授权、未做真实外部调用。
原则：只评估可放进 General AI Core 或 application Plugin 的候选项，不把业务应用误塞进 Core。

| project | purpose | advantage | limitation | integration_mode | decision | source |
| --- | --- | --- | --- | --- | --- | --- |
| LiteLLM | 统一 LLM Gateway / Proxy | OpenAI-compatible；单一接口接入多 provider；适合做 model abstraction | 需要维护 proxy、keys、routing、rate limit 和审计面 | Core Adapter | Deferred：作为 Core 的 gateway 候选，先把本地 gateway 合同稳定住；边界：未安装/未授权/无真实外部调用。 | [Docs](https://docs.litellm.ai/docs/) |
| LangGraph | 状态化 agent workflow | durable execution、streaming、human-in-the-loop 支持强 | graph/state/checkpoint 设计会把运行时复杂度前移 | Workflow Plugin | Deferred：仅在需要持久状态和可恢复 agent flow 时进入 Plugin 层；边界：未安装/未授权/无真实外部调用。 | [Docs](https://docs.langchain.com/oss/python/langgraph/overview) |
| Temporal | durable workflow runtime | crash-proof recovery、replay、长事务场景成熟 | 需要独立 service/worker/cluster 运维 | Workflow Adapter | Deferred：只有 long-running、retry-heavy 的业务流才值得引入；边界：未安装/未授权/无真实外部调用。 | [Docs](https://docs.temporal.io/) |
| n8n | 自动化编排 | 可视化节点丰富，适合快速串接 SaaS/API | fair-code + 强外部副作用，不应穿透 Core permission/tool gate | Ops Plugin | Reject for Core：只可作为独立运维/增长自动化插件候选；边界：未安装/未授权/无真实外部调用。 | [Docs](https://docs.n8n.io/) |
| Qdrant | vector retrieval | Rust 实现，过滤和检索能力强，适合生产级向量服务 | 需要单独管理 collection、索引和存储生命周期 | Retrieval Adapter | Deferred：作为外部向量库候选保留，不在当前 Core 内直接落地；边界：未安装/未授权/无真实外部调用。 | [Docs](https://qdrant.tech/documentation/) |
| Chroma | 轻量向量存储 / local-first retrieval | 上手快，适合本地和原型验证 | 更偏轻量起步，生产取舍需和 Qdrant/pgvector 再比较 | Retrieval Plugin | Deferred：只保留本地/开发候选，不作为当前默认生产向量层；边界：未安装/未授权/无真实外部调用。 | [Docs](https://docs.trychroma.com/docs/overview/introduction) |
| pgvector | Postgres vector search extension | 直接复用现有 Postgres；从任意语言都能走 Postgres client | 受限于 Postgres 扩展和数据库调优边界 | Core Data Adapter | Preferred：如果系统已经有 Postgres，优先用 pgvector 做最小增量向量层；边界：未安装/未授权/无真实外部调用。 | [GitHub](https://github.com/pgvector/pgvector) |
| OpenTelemetry | telemetry / observability | vendor-neutral；traces、metrics、logs 一套 API/SDK | 只负责采集/导出，不提供 backend | Core Observability Adapter | Adopt：作为默认观测标准更合适；边界：未安装/未授权/无真实外部调用。 | [Docs](https://opentelemetry.io/docs/) |
| LangSmith | LLM observability / eval | tracing、evaluation、debugging 面向 AI 应用很完整 | 闭源 SaaS，外部数据路径和授权边界更重 | External Observability Plugin | Reject for Core：不作为 General AI Core 依赖，只在单独授权时考虑；边界：未安装/未授权/无真实外部调用。 | [Docs](https://docs.langchain.com/langsmith/observability) |
| Twenty CRM | open-source CRM | self-hostable，API / webhooks / custom objects 适合业务扩展 | 这是业务应用，不是 Core 基础设施 | Application Plugin | Accept as Plugin candidate：需要 CRM 时再接入，不进入 Core；边界：未安装/未授权/无真实外部调用。 | [Docs](https://docs.twenty.com/developers/introduction) |
| ERPNext | open-source ERP | 覆盖财务、库存、项目、销售等全套业务管理 | 平台很重，领域很宽，不适合塞进 AI Core | Application Plugin | Reject for Core：只适合独立业务后端或 Plugin 层，不进入核心链路；边界：未安装/未授权/无真实外部调用。 | [Docs](https://docs.frappe.io/erpnext/introduction) |

结论只表示案头评估结果，不表示已安装、已连接或已授权真实服务；真实落地仍需要单独的 secret、permission 和 external execution gate。
