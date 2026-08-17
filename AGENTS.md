# 成都国际医疗旅游项目：接手与执行契约

## 项目身份

这是一个处于 strategy_definition_pending 的项目。项目已有研究资料，但业务方向、市场、客户、MVP、商业模式、价格、最小闭环、验证顺序、Go/No-Go 尚未由用户与 ChatGPT 正式锁定。

GitHub main 是唯一的动态项目事实源。ChatGPT Project 是长期协作机制层；本地是执行现场；Obsidian 是跨项目机制来源。

## 新会话读取顺序

1. AGENTS.md。
2. collaboration_system/00_总览_用户到现实反馈的完整闭环.md。
3. project_facts/00_项目身份.md、01_当前已确认事实.md、02_当前状态_project_state.yaml、03_当前未决策事项.md。
4. logs/latest.md 与 logs/current_target.md。
5. 当前任务对应的 collaboration_system、research_baselines 或 candidate_playbooks 文件。

## 权限

用户决定目标、红线、预算、外部动作、战略和最终验收。ChatGPT 负责真实意图、事实裁决、选项比较、Implementation Design、执行单和复审。Codex 负责读取、结构化、写入、验证、记录和 Git 收尾。

Codex 不得自行决定首发国家、首发用户、MVP、商业模式、定价、是否 Go、验证顺序、Supply First/Demand First、是否扩大投入、是否联系客户/机构或是否发布。未锁定时输出 blocked_strategy_not_locked。

## 事实与研究

project_facts 只保存已确认事实、状态、未决策事项与带 provenance 的正式决策。research_baselines 保存两份报告的版本关系和研究候选。研究输入、外部资料、Project 静态包、聊天记忆和历史归档不能自动改变 current facts。

## Canonical 来源

- 协作机制：collaboration_system/。
- 执行入口：collaboration_system/07_Codex执行单与执行器权限边界.md。
- 项目事实：project_facts/01_当前已确认事实.md。
- 当前状态：project_facts/02_当前状态_project_state.yaml。
- 未决策事项：project_facts/03_当前未决策事项.md。
- 最新日志：logs/latest.md。
- 研究基线：research_baselines/。

execution_rules 与 references 仅保留兼容入口，不再独立定义机制或事实。

## 外部动作与安全

external_execution_allowed: false。未经用户明确授权，不发送、联系、投放、收款、签约、发布或创建患者记录。不得在仓库、Project 静态包、聊天或日志保存患者/健康/个人资料、密钥、Token、私人授权或未经确认可公开的材料。

医疗、法律、数据、旅行、支付等专业责任见 collaboration_system/18_医疗项目特殊安全与专业责任边界.md。项目方与 AI 不提供诊断、治疗决定、疗效承诺或法律结论。

## Git 收尾

只暂存明确路径；验证后使用 Lore commit；push main 并回读 origin/main。commit、push、远端 readback 与用户/专业/业务验收必须分开报告。
