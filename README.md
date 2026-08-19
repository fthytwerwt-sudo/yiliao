# 成都国际医疗旅游项目

这是一个已建立协作与事实系统、但尚未由用户与 ChatGPT 锁定具体商业战略的项目仓库。

## 当前真实状态

- 项目存在、两份基础研究资料和协作机制均已确认。
- 市场、首发客户、产品、商业模式、价格、最小闭环、验证顺序、Go/No-Go 均尚未最终锁定。
- 当前阶段：strategy_definition_pending。
- `DEC-ENG-001` 已允许战略无关系统基础设施继续开发，但这不构成业务战略锁定。
- 当前唯一工作目标：由用户与 ChatGPT 锁定第一轮最小商业闭环和最低成本验证路径。
- Codex 不得从研究资料自行选择路线；缺锁定战略时返回 blocked_strategy_not_locked。

## 当前技术实现状态

- `medical_tourism_os/` 已覆盖 Phase 1–7 的离线系统骨架：
  数据治理、风险路由、候选需求/产品/内容、学习闭环、CLI、本地 API、synthetic E2E。
- 所有外部 adapter 仍为 Mock / disabled。
- GitHub sync 仅支持 dry-run 预览，不执行真实同步。
- Local API 可创建并运行只绑定 `127.0.0.1` 的本地 HTTP server，但默认不自动启动。
- 当前测试通过只说明技术合同成立，不说明市场、业务、医疗、合规或商业验证完成。

## Canonical 入口

| 需要回答的问题 | 读取位置 |
| --- | --- |
| 我们怎样协作 | collaboration_system/00_总览_用户到现实反馈的完整闭环.md |
| 当前已确认的项目事实 | project_facts/01_当前已确认事实.md |
| 当前机器可读状态 | project_facts/02_当前状态_project_state.yaml |
| 当前尚未决定什么 | project_facts/03_当前未决策事项.md |
| 已正式锁定的决定 | project_facts/04_正式决策记录.md |
| 研究给出的候选，不是决定 | research_baselines/ |
| 当前目标与最新动态 | logs/current_target.md 与 logs/latest.md |
| 未锁定路线的草案模板 | candidate_playbooks/ |

## 分层原则

Project 保存我们怎么配合；GitHub main 保存项目现在真实是什么；研究资料只告诉我们可能怎么做；Codex 只执行已锁定的决定。

## 不在当前范围

不自动启动真实获客、机构联系、收款、签约、广告、医疗服务、旅行服务、患者资料处理、平台建设或任何尚未由用户授权的外部动作。
