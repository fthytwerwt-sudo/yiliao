# Open Source Evaluation 开源评估

| project | purpose | advantage | limitation | integration_mode | decision |
| --- | --- | --- | --- | --- | --- |
| LiteLLM | 多 Provider LLM Gateway | 统一模型格式、成本与代理能力 | Proxy/密钥运维面 | Adapter | Deferred：本地 Gateway 合同先稳定。 |
| LangGraph | 状态化 Agent/Workflow | durable orchestration、human-in-loop | 运行时状态依赖 | Wrapper | Deferred：仅在需持久执行时接入。 |
| Temporal | durable workflow | 故障后恢复 | 服务端运维成本 | Adapter | Deferred：当前同步 TEST workflow 足够。 |
| n8n | 自动化编排 | 可视化集成丰富 | 不能绕过 Core Permission/Tool gate | Wrapper | Reject for V1 runtime。 |
| Qdrant | vector retrieval | 向量检索 | embedding/collection 生命周期 | Adapter | Deferred：Memory Interface 已预留。 |
| Twenty CRM | CRM | 自托管/API | 属于业务应用而非 Core | Adapter | Deferred：仅 Plugin 可调用。 |
| OpenTelemetry | observability | vendor-neutral telemetry | 不提供 backend | Adapter | Deferred：未来导出 telemetry。 |

所有结论不表示已安装、已连接或已授权真实服务；真实运行需要独立 Secret 与外部执行授权。
