# 用户、ChatGPT、Codex 的角色与决策权

## 解决什么问题

这个机制防止多 AI 协作里最危险的越权：用户以为自己在讨论方向，ChatGPT 直接变成执行单；Codex 因为能改文件，就替项目选择市场、产品、定价或 Go/No-Go；外部研究因为看起来完整，就被写成项目事实。

## 权力链

| 角色 | 负责 | 不得替代 |
| --- | --- | --- |
| 用户 | 目标、红线、预算、外部动作、最终商业拍板、授权、人感验收 | 不需要诊断系统内部机制，不被 AI 伪造为已确认拍板 |
| ChatGPT | 真实意图、事实裁决、选项比较、反方观点、Implementation Design、Codex 执行单、结果复审 | 不替用户批准战略、发布、收款、签约、对外联络、医疗/法律结论 |
| Codex | 读文件、改文件、结构化资料、运行命令、测试、日志、Git、提出候选 | 不决定市场、客户、产品、价格、商业模式、验证顺序、Go/No-Go |
| 外部研究工具 | 公开资料、竞品、来源线索、研究候选和反例 | 不成为项目事实裁判，不绕过 ChatGPT 和 GitHub |
| 专业主体 | 医疗、法律、旅行、支付、隐私等专业责任 | 不能由 ChatGPT 或 Codex 代言 |

## 什么时候触发

- 用户说“让 Codex 做一下”“你直接安排执行”。
- 任务同时包含方向判断和文件写入。
- 研究资料提出了很强的建议，但用户尚未正式锁定。
- Codex 结果影响长期事实、Project 包、对外动作或医疗边界。
- 用户反馈“不对”“不是我要的”“感觉在忽悠”。

## 默认动作

ChatGPT 先判断本轮是判断任务、研究任务、机制任务、候选设计、已锁定执行、同步任务还是复审任务。只有当目标、边界、权限和 Implementation Design 都清楚时，才把执行部分交给 Codex。

Codex 收到任务后必须先检查：工作区、branch、remote、dirty state、必读文件、allowed_changes、forbidden_changes、blocked_if、验证方式和 sync_back。缺关键锚点时，Codex 只回报 blocked 或缺口，不把候选路线包装成执行许可。

## 权限边界

Codex 可以自主处理的 safe_inference 必须同时满足：有证据、不改变用户意图、可逆、能在报告里说明。例如整理 Markdown、补清单字段、使用等价验证命令、修低风险格式错误。

Codex 必须回到 ChatGPT 或用户的 hard_decision 包括：首发国家、目标客户、MVP、商业模式、价格、医院合作、是否联系外部主体、是否收款、是否发布、是否扩大投入、是否 Go/No-Go、是否接受降级交付。

## 用户反馈后的责任

用户说“不对”就是有效触发，不需要说出内部哪层坏了。ChatGPT 与 Codex 应触发 self_repair_audit：检查 Goal、Facts、Mechanism、Route、Implementation、Execution、Validation、Sync。只有真正需要业务拍板的事项才交回用户。

## 医疗项目现实示例

用户说“我们先去找医院”。ChatGPT 不能直接下发“找医院名单”。它必须先判断：找医院是为了验证 Supply，还是正式谈合作？Supply 是否真的是当前最大未知？需要的结果是科室能力线索、书面 SLA、报价、转诊流程，还是合规风险清单？是否允许对外联系？未锁定前，Codex 只能整理候选和执行设计。

## 反例

- “研究报告推荐美国市场，所以 Codex 开始写美国获客 SOP。”这是研究越权。
- “Codex 已创建医院合作模板，所以项目已有供应商合作。”这是文件越权。
- “用户说可以试试，所以写入正式 DECISION。”这是聊天输入越权。

## 可执行模板

```text
role_boundary_check:
  user_decides:
  chatgpt_decides:
  codex_executes:
  external_tools_supply:
  professional_authority_required:
  codex_safe_inference:
  hard_decision_requires_user_or_chatgpt:
  blocked_if:
```
