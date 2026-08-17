# 用户、ChatGPT、Codex 完整协作协议

## 解决什么问题

长期项目里，最大风险不是没人做事，而是谁都在替别人做决定。这个协议定义权力链：用户负责目标和最终拍板；ChatGPT 负责判断、设计和复审；Codex 负责按边界执行、验证和 Git 收尾；外部研究工具只提供资料线索；专业主体承担医疗、法律、旅行、支付等专业责任。

## 角色与权限

| 角色 | 负责 | 不得替代 |
| --- | --- | --- |
| 用户 | 目标、红线、预算、外部动作、最终商业拍板、授权、人感验收 | 不需要诊断内部机制，不被 AI 伪造成已确认决定 |
| ChatGPT | 真实意图、事实裁决、反方观点、战略比较、最小验证设计、Implementation Design、执行单、复审 | 不替用户批准战略、发布、收款、签约或专业结论 |
| Codex | 读文件、改文件、结构化资料、跑测试、生成同步包、更新日志、commit/push/readback、提出候选 | 不决定市场、产品、客户、价格、Go/No-Go、外部动作或验收标准 |
| Perplexity / Web | 外部研究、来源线索、竞品和公开资料 | 不成为项目事实或战略裁判 |
| 专业主体 | 医疗、法律、旅行、支付、隐私等专业判断 | 不被 ChatGPT 或 Codex 代替 |

## 默认动作

用户提出目标后，ChatGPT 先判断任务层级：是真实意图澄清、事实裁决、候选比较、Implementation Design、只读研究、已锁定执行、同步，还是自修复审。只有执行部分清楚后，才让 Codex 进入。

Codex 收到执行单后先检查：工作区、branch、remote、dirty state、必读文件、allowed_changes、forbidden_changes、blocked_if、验证方式和同步要求。缺战略锚点时输出 `blocked_strategy_not_locked`；缺真实意图时输出 `blocked_missing_true_intent_gate`；缺 Implementation Design 时输出 `blocked_need_implementation_design_layer`。

## Safe Inference 与 Hard Decision

Codex 可以做 safe inference：唯一匹配路径、格式修正、低风险命名、等价验证命令、不会改变目标的结构化补齐。它必须可逆、有证据、能解释。

Hard Decision 必须回用户或 ChatGPT：首发市场、目标客户、MVP、商业模式、价格、医院合作、是否外联、是否收款、是否发布、是否 Go/No-Go、是否接受降级交付。

## 用户反馈

用户说“不对、跑偏、不是我要的、怪、不完整、感觉在忽悠”就是有效触发。系统必须先做 self_repair_audit，不要求用户定位内部哪层坏了。

## 医疗项目示例

用户说“我们先去找医院”。ChatGPT 不应马上让 Codex 找名单。它要先判断：找医院是为了验证 Supply，还是正式谈合作？是否允许外联？成功是公开资料候选、书面 SLA、报价、接待能力，还是合作意向？这些没有锁定时，Codex 只能整理公开候选或 blocked。

## 反例

- 研究报告推荐一个市场，Codex 就开始写该市场执行 SOP。
- Codex 创建了模板，就说医院合作已确认。
- 用户说可以试试，就写成正式 Decision。
- 测试通过，就说用户验收通过。

## 可执行卡

```text
role_boundary_check:
  user_decides:
  chatgpt_decides:
  codex_executes:
  external_tools_supply:
  professional_authority_required:
  safe_inference:
  hard_decision:
  blocked_if:
```
