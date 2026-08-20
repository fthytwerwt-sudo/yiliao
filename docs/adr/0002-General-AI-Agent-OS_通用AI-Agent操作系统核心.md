# ADR-0002：General AI Agent OS 通用 AI Agent 操作系统核心

## Status

Accepted（2026-08-20，用户架构纠偏）。

## Context

原 Phase 2 把 Business Fact Governance、市场/产品/客户配置和确认事实审核放进 `general_ai_business_os` 的 Core Runtime。独立审查暴露了其信任根复杂度；更重要的是，用户已明确系统的主目标是可跨行业复用的 General AI Agent Operating System，而非医疗旅游或任何业务事实治理系统。

## Decision

1. 新建 `general_ai_agent_os/` 作为未来核心包。
2. Core Runtime 只负责 Model Gateway、Agent Runtime、Workflow Engine、Tool Registry、Memory/Context、Permission、Audit、Secret 与 AI System Config。
3. Business Config/Facts 移至 Application Plugin 的 optional business data layer；不再作为 Core Phase 2 的依赖。
4. `medical_tourism_os/` 不删除，保留为未来 plugin/compatibility layer；`general_ai_business_os/` 保留为已实现基础能力与迁移历史，不再扩展旧 Business Config Core 路线。
5. 所有 Provider Adapter 默认 Mock/disabled；API key 仅保存 reference，绝不进入 Git。

## Consequences

- Core 可在不修改代码的前提下接入不同行业插件。
- 旧 Phase 2 的 failed review 工件保留为“为何不把业务事实治理放进 Core”的可回读证据。
- 新 Phase 2 改为 AI System Configuration Layer：Provider、Agent、Tool、Runtime 与 optional plugin config，不导入市场、价格或客户事实。
- Business Data Governance 将在 Phase 7 Application Plugin 内重新设计，不能复用为 Core 的确认事实来源。
