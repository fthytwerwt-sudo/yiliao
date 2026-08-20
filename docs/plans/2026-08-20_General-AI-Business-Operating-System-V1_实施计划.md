# General AI Business Operating System V1 实施计划（已归档）

**Status: Superseded**

本文件的原始实施步骤要求在 General AI Core 中建设业务配置导入、审核、市场/客户/产品/渠道合同和对应 CLI/API。该计划已被 [ADR-0002](../adr/0002-General-AI-Agent-OS_通用AI-Agent操作系统核心.md) 与 [迁移计划](../migrations/2026-08-20_General-AI-Agent-OS_迁移计划.md) 取代；其中的旧 Core Phase 2 指令不得执行。

## 当前已完成的 Core 范围

- AI System Configuration：Provider、Agent、Tool、Runtime 与 Secret reference 的闭合配置合同。
- Model Gateway / Agent Runtime / Tool Registry / Workflow Engine：Provider-neutral、动态注册、全局 default-deny 和 Agent-level deny。
- Memory Interface：`MemoryStore` 抽象与 Local/Vector/Database adapter seam；运行快照深拷贝隔离。
- Plugin Isolation：closed manifest、register/load/activate/deactivate lifecycle、capability declaration，并且 V1 不执行 Plugin entrypoint。
- TEST_BUSINESS：在 `external_actions_allowed=false` 下，经过本地 Tool、Evaluation 与 persisted Feedback evidence 的 synthetic E2E。
- 开源评估：见 [Open Source Evaluation](../research/2026-08-20_Open-Source-Evaluation_开源评估.md)，只做案头判断，未安装、未授权、未调用真实服务。

## 当前执行与验证入口

1. 阅读 [ADR-0002](../adr/0002-General-AI-Agent-OS_通用AI-Agent操作系统核心.md)、[迁移计划](../migrations/2026-08-20_General-AI-Agent-OS_迁移计划.md) 和 `docs/progress/`。
2. 运行 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`、`python3 -m compileall general_ai_business_os medical_tourism_os tests` 与 Core boundary/security scans。
3. 在任何后续 Application Plugin 工作前，独立建立其数据模型、权限和审查契约；不得重新把业务事实写回 Core。

## 不属于本计划的事项

- 真实 Provider、API key、账号、发送、发布、付款、签约、客户联系或业务战略。
- 任意业务事实治理、CRM/ERP/市场/产品/价格逻辑的 Core 化。
- 因测试、Mock、文档或 Git 操作通过而宣称真实业务验证完成。

原始详细任务步骤已由 Git history 保留；本归档页防止它被误当作当前执行单。
