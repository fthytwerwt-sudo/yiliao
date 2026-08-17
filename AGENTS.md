# 成都国际医疗旅游项目：AI 接手与执行契约

## 项目身份与当前阶段

项目：成都国际医疗旅游项目。

阶段：pre_validation / 90-day validation preparation。

当前阶段不是成熟运营、医院合作已落地或商业模式已验证。当前正式方向是以居住美国、具有中国经验的华人/亚裔 wellness 客群，验证成都东方健康管理 6 日体验的合规供给、真实订金、成行交付与单位经济。

## 动态事实源

GitHub main 是跨会话的动态项目事实源。任何会长期影响项目方向、状态、证据、指标、操作流程或停止线的变化，只有在 main 回读确认后才可称为 formal_synced。

状态层级：

- local_only：只在本机存在，未提交或未推送。
- task_branch_only：已提交到分支，未合入 main。
- pr_open_not_merged：已推送但尚未合入 main。
- formal_synced：已写入 main、push 成功且远端回读。

技术文件存在、测试通过、生成静态包、聊天中说“完成”均不等于商业、合规或项目完成。

## 新会话最低阅读顺序

1. AGENTS.md
2. project_facts/00_项目总述.md
3. project_facts/01_当前正式事实.md
4. project_facts/02_当前状态_project_state.yaml
5. logs/latest.md
6. logs/current_target.md
7. 当前任务相关的 execution_rules、review_loop、operations、references 文件

若上述入口缺失、互相冲突或未能定位当前任务路由，先标记 blocked_need_alignment；不得由聊天记忆补全。

## 事实优先级与冲突裁决

从高到低：

1. GitHub main 中当前正式项目事实和 machine-readable state。
2. 已核验的真实执行、报价、合同、交易、履约、事故和法律意见证据。
3. logs/latest.md 与 logs/current_target.md，且须和 main 内事实一致。
4. 用户本轮明确的新决定；其长期化必须回写 main。
5. 当前基础市场报告 v3。
6. 早期市场研究报告。
7. 新的外部研究、竞品、法规线索。
8. ChatGPT Project 静态包。
9. 聊天记忆、旧归档或未回读的本地文件。

外部研究是线索，不自动成为项目事实。若与 current facts 冲突，记录证据、判断可信度和拟议变更，再由用户/ChatGPT 作事实裁决。

## 角色与权限

| 角色 | 可以做 | 不可以替代 |
| --- | --- | --- |
| 用户 | 目标、红线、预算、商业拍板、发布、真实外发与最终验收 | 由 AI 伪造的事实或专业意见 |
| ChatGPT | 总控判断、范围、事实裁决、执行单、结果真实性复审 | 把静态包或聊天记忆当实时状态 |
| Codex | 文件、数据结构、可复现检查、日志、Git 收尾 | 医疗判断、法律结论、对外承诺、自动外发 |
| Perplexity / Web | 外部市场、竞品、法规和供给线索 | 自动改变项目事实 |
| 医院 / 持证机构 / 律师 / 旅行伙伴 | 各自专业及责任范围内的书面确认 | 被项目方代言或替代 |

## 任务路由

| 任务类型 | 先读 | 允许动作 | 必须阻断条件 |
| --- | --- | --- | --- |
| 战略与阶段判断 | project_facts、logs、references | 提出 DECISION 草案和证据缺口 | 需要用户商业拍板或事实冲突未裁决 |
| 外部市场研究 | execution_rules/03、references/02 | 收集、分级、标注日期和来源 | 将外部线索写成 current fact |
| 机构供给验证 | operations/03、review_loop/supplier_validation | 形成问题清单、证据矩阵、缺口 | 没有书面 SLA、价格或责任边界却宣布可卖 |
| 产品与定价 | project_facts/04-05、operations/02 | 更新 HYPOTHESIS、报价草案、敏感性 | 把候选价格或利润写成已实现 |
| 获客与客户流程 | project_facts/06、operations/00-01 | 设计不含 PII 的流程与实验 | 未过 Supply + Compliance Gate 就扩大投放 |
| 合规与数据 | project_facts/07、execution_rules/05 | 列出需专业复核事项和禁止项 | 代替律师、医院作结论，或收集/传输 PHI |
| 数据复盘 | review_loop | 记录真实观测、计算口径、反证 | 用预测/空白字段冒充结果 |
| 项目机制修改 | execution_rules、AGENTS、logs | 小范围修改并验证入口一致性 | 修改导致事实源、权限或完成态冲突 |

## 医疗项目红线

项目方不是医院。不得诊断、修改治疗方案、推荐患者改变用药、承诺疗效/治愈/医疗签证、保证医生/名额、将公开资料包装为已授权合作，或将健康资料存入 Git、个人设备或普通聊天工具。

医疗或持证健康服务由有资质机构负责；旅行责任由合法旅行服务伙伴承担；项目方仅可在明确授权和合规范围内提供筛选、协调、翻译组织、预约、时间管理、行程衔接和随访协调。

## 外部动作与敏感数据

默认 external_execution_allowed: false。

没有用户明确授权，不发送邮件/消息、不联系机构、不投放广告、不收款、不签约、不创建患者记录、不上传敏感文件。仓库不得提交患者资料、健康数据、个人身份信息、密钥、Token、私人授权或未确认可公开的原始材料。

## 每个 Codex 执行单必须包含

- route_decision：project_route、task_type、responsibility_layer、allowed_changes、forbidden_paths、blocked_if。
- workflow_route_decision：本任务属于事实、研究、运营、复盘或机制层。
- state_action_router：当前状态、唯一下一动作、触发证据和停止线。
- required_output_inventory：期望文件/证据。
- completion_check：技术、内容、人工、业务四层分别说明。
- sync_back_check：是否需要更新事实、日志、静态包和 GitHub main。

## 完成态与失败回路

报告完成时必须分别陈述：

- 技术：文件、格式、链接、YAML、计算是否通过。
- 内容：是否符合当前事实、边界和模板目的。
- 人工：是否仍需要用户、律师、医院、旅行伙伴或客户确认。
- 业务：是否已得到真实报价、订金、成行或财务结果。

失败不是笼统 retry。先定位在目标、机制、设计、执行、素材/证据或验收哪一层；只修复该层最小范围，回归检查后再更新状态。

## 当前阶段闸门

在以下全部有可核验书面证据前，不得把状态推进至正式获客：

1. 至少两家候选机构完成真实访谈记录。
2. 至少一家机构提供外籍患者流程、书面价格、双语交付和异常/转诊 SLA。
3. 三账报价、退款取消和责任分界可供专业审核。
4. 数据、广告、合同、支付、旅行和医疗责任边界有待审清单及相应专业复核路径。
5. 完成一次无患者全流程彩排并记录结果。
