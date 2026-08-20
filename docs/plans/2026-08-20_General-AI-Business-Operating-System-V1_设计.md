# General AI Business Operating System V1 设计（已归档）

**Status: Superseded**

本文件的原始设计曾把 `Business Config Package`、市场、客户、产品、渠道和 CRM 等业务语义放入 `general_ai_business_os` 的 Core Phase 2。该方向已被 [ADR-0002](../adr/0002-General-AI-Agent-OS_通用AI-Agent操作系统核心.md) 正式否决，不能再作为当前实现依据。

## 当前权威架构

请以以下文件作为唯一当前来源：

- [ADR-0002](../adr/0002-General-AI-Agent-OS_通用AI-Agent操作系统核心.md)：Core Runtime 只负责 Model Gateway、Agent Runtime、Workflow、Tool Registry、Memory/Context、Permission、Audit、Secret reference 和 AI System Config。
- [迁移计划](../migrations/2026-08-20_General-AI-Agent-OS_迁移计划.md)：旧业务配置实现已从 Core runtime 移除；失败审查与 Git history 仅保留为迁移证据。
- [当前架构图](../architecture/General-AI-Agent-OS-V1_架构图.md)：医疗旅游和其他业务只能作为 future Application Plugin。

## 已否决的做法

- 不在 `general_ai_business_os/` 中导入、注册或执行业务配置、市场、客户、产品、价格、医院、CRM 或渠道逻辑。
- 不通过 Core CLI 或 Core Local API 导入任何业务配置包。
- 不以旧配置审核、事实确认或 SQLite 覆盖记录作为 General AI Core 的信任根。

## 后续准入规则

未来需要业务数据治理时，必须先创建独立 Application Plugin 设计，并满足：独立数据合同、明确 provenance、独立存储信任链、PermissionPolicy/ModelGateway/ToolRegistry 三重边界、失败关闭测试，以及单独的 ADR/Review。该工作不属于本 V1 Core 交付。

原始详细设计已由 Git history 保留，避免把历史假设误读为当前任务。
