# 外部调研、Perplexity 与 Reference 桥接

## 解决什么问题

外部资料很容易被误用：研究报告变成项目决策，竞品素材变成可复制资产，Perplexity 摘要变成 confirmed fact，用户原感变成模糊执行要求。本机制规定外部资料先保真，再分类，再桥接执行。

## 什么时候触发

- 用户提供外部报告、网页、截图、参考、竞品、Perplexity 输出或 Web 资料。
- 需要判断市场、客户、价格、供应、合规或风险。
- 需要把资料转成 Codex 可执行字段。
- 资料与 GitHub main 当前事实冲突。

## 事实分类

必须区分：

- Research。
- Fact candidate。
- Confirmed fact。
- Inference。
- Hypothesis。
- Decision。
- Unknown。

研究报告 ≠ 项目决策。外部资料只能先进入 Research / Fact candidate / Inference / Hypothesis / Unknown。只有经 ChatGPT 裁决、用户或专业主体按权限拍板，并写回 GitHub，才可能成为 Confirmed fact 或 Decision。

## 外部研究进入路径

```text
Perplexity / Web
→ source + date + scope
→ 原始主张
→ 可观察事实 / 推断 / 假设 / 未知
→ 对当前项目的影响
→ ChatGPT 判断
→ 用户拍板（如需要）
→ GitHub project_facts 或 decision record
```

## Reference-to-Execution Contract

当外部资料用于执行，而不是事实判断时，必须生成参考契约：

| 字段 | 要写什么 |
| --- | --- |
| reference_anchor | 资料是谁、来自哪、是否能查看 |
| effect_targets | 要继承的效果、信息层级、人感或质量标准 |
| function_fields | 输入、动作、理由、验证、阻断、降级 |
| execution_mapping | 文案、表格、页面、研究、复审怎样使用 |
| deviation_check | 哪些可变，哪些偏离必须修 |
| done_when | 什么证据说明参考已正确落地 |

## 原感双层

用户原话、原感、语气和节奏可以作为 reference layer 保存，但不能直接变成执行规则。ChatGPT 要先保留原感，再转成执行字段、禁止项和验收标准。Codex 不判断原感是否对，只按已锁字段执行。

## 默认动作

1. 保存 source、date、scope、可访问性。
2. 提取可观察事实，避免长摘要。
3. 标注不可迁移内容：品牌、UI、第三方资产、个人资料、未授权内容。
4. 生成执行桥接字段或事实候选表。
5. 写明 Codex 能做什么、不能做什么。

## 医疗项目现实示例

Perplexity 给出一份市场报告。ChatGPT 应把它写成外部供料，不是项目事实：记录来源和日期，拆出主张，标为 Research / Fact candidate，说明它可能影响哪些候选问题，然后等用户与 ChatGPT 判断是否进入正式决策。

## 常见误用 / 反例

- 只做长摘要，不产出字段。
- 把外部价格当成本项目可报价价格。
- 复制第三方品牌、页面、案例或可识别个人信息。
- 用“像这个”替代 must_preserve / can_vary / must_not_copy。

## 可执行模板

```text
external_research_bridge:
  source:
  date:
  scope:
  accessibility:
  raw_claims:
  classification:
    research:
    fact_candidate:
    inference:
    hypothesis:
    unknown:
  project_impact:
  user_decision_required:
  codex_allowed_work:
  forbidden_use:

reference_contract:
  reference_anchor:
  effect_targets:
  function_fields:
  execution_mapping:
  deviation_check:
  done_when:
  blocked_if:
```
