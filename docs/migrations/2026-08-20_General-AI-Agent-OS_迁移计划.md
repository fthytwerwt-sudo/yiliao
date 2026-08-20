# General AI Agent OS 迁移计划

| 当前资产 | 迁移定位 | 处理方式 |
| --- | --- | --- |
| `medical_tourism_os/` | 未来业务实例兼容层 | 保留，不删除、不破坏测试。 |
| `general_ai_business_os/` Foundation | 可复用基础实现 | 暂作兼容基础，逐项由 `general_ai_agent_os/` 吸收或适配。 |
| `general_ai_business_os/business_config/` | 被停止的旧 Core Phase 2 尝试 | 不再扩展；保留失败审查与代码作为迁移历史，不作为新 Core 输入。 |
| `general_ai_agent_os/` | 新 Core Runtime | 从 AI System Config 开始建立稳定公开接口。 |

## 新 Phase 顺序

1. Foundation（已完成、保留）。
2. AI System Configuration：Provider/Agent/Tool/Runtime/Secret reference config。
3. Agent Runtime。
4. Model Gateway。
5. Tool Registry。
6. Workflow Engine。
7. Application Plugins（此时才承载可选业务数据）。
8. External Integrations 与开源评估。
9. `TEST_BUSINESS` End-to-End Validation。

每一阶段仍须独立 `gpt-5.6-sol` 高推理审查通过，才可进入下一阶段。
