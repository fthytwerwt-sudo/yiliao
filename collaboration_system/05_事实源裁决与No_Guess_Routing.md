# 事实源裁决与 No-Guess Routing

## 解决什么问题

fact_source_arbitration 解决“谁有资格决定当前事实”。No-Guess Routing 解决“哪些事可以安全推断，哪些必须由用户或 ChatGPT 锁定”。两者合在一起，防止研究报告、聊天记忆、Project 静态包、外部搜索或 Codex 便利判断覆盖当前项目事实。

## 事实分类

| 类型 | 含义 | 能否直接进入项目事实 |
| --- | --- | --- |
| Research | 研究报告、网页、Perplexity、竞品资料、行业资料 | 否 |
| Fact candidate | 有来源但未被项目确认的事实候选 | 否 |
| Confirmed fact | 当前仓库事实、验证证据或有权主体确认并已记录 | 是 |
| Inference | 基于事实的解释或推导 | 否，需标推断 |
| Hypothesis | 准备验证的假设 | 否 |
| Decision | 用户、用户+ChatGPT 或专业主体按权限锁定的正式决定 | 是，需 provenance |
| Unknown | 不知道、无法回读或证据不足 | 否 |

研究报告 ≠ 项目决策。研究材料可以改变讨论问题，但不能自动改变 project_facts。

## 来源优先级

1. P0：用户本轮明确输入、禁止项和更正，决定本轮如何处理。
2. P1：GitHub main 当前事实、正式决策记录、真实执行证据、测试和远端 readback。
3. P2：研究基线、Project 静态包、外部研究、聊天记忆、历史归档和跨项目机制。

冲突规则是 `P0 > P1 > P2`。但 P0 要成为长期事实，仍必须写回 GitHub main；P2 只能提供候选和方法。

## No-Guess 边界

Codex 可以安全推断：唯一匹配路径、格式修复、低风险命名、等价验证命令、不会改变目标的结构化补充。

Codex 不得猜：战略、首发市场、产品、客户、价格、商业模式、医院合作、合规结论、医疗判断、外部授权、是否发布、是否收款、完成态、人审或业务结果。

ChatGPT 不得把 Research、Fact candidate、Inference 或 Hypothesis 写成 Confirmed fact 或 Decision。

## 外部资料进入路径

```text
Perplexity / Web / report
→ source + date + scope
→ Research / Fact candidate / Inference / Hypothesis / Unknown
→ ChatGPT 判断影响
→ 用户或专业主体拍板（如需要）
→ project_facts / decision record
→ Git commit / push / readback
```

缺任一步都不能写成项目事实。

## 判断流程

1. 列出所有来源、时间、范围、是否可回读。
2. 给每条主张贴事实分类。
3. 检查是否与 GitHub main 冲突。
4. 冲突时按优先级裁决；战略或高风险事项交用户/专业主体。
5. 进入任务路由前，写清哪些可执行、哪些只能保留为候选。

## 医疗项目现实示例

Perplexity 给出某国家医疗旅游需求增长报告。正确处理是：记录 source + date + scope，把它归类为 Research 或 Fact candidate；ChatGPT 判断它是否影响候选比较；如果要把该国写成首发市场，必须由用户与 ChatGPT 正式锁定并写入决策记录。不能因为报告看起来权威就写“本项目首发市场已确定”。

## 常见误用 / 反例

- 研究报告中出现价格区间，就把它写成项目定价。
- Project 包里有旧机制，就覆盖 GitHub main 当前状态。
- RAG/搜索结果没有原文回读，就让 Codex 执行。
- “以前别的项目成功”被当成本项目能力已确认。

## 可执行模板

```text
fact_arbitration:
  claim:
  source:
  date:
  scope:
  source_type:
  classification: Research / Fact candidate / Confirmed fact / Inference / Hypothesis / Decision / Unknown
  conflicts:
  current_authority:
  can_codex_act:
  user_decision_required:
  write_back_required:
```
