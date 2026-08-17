# 外部资料、Perplexity、事实裁决与 Reference 桥接

## 解决什么问题

外部资料可以帮助判断，但不能绕过事实裁决。研究报告、网页、Perplexity、竞品、用户转述、参考图和原感稿都先是输入，不是项目事实。

## 事实分类

必须区分：

- Research。
- Fact candidate。
- Confirmed fact。
- Inference。
- Hypothesis。
- Decision。
- Unknown。

研究报告 ≠ 项目决策。Perplexity / Web 输出也不是项目事实。

## 外部资料进入项目路径

```text
Perplexity / Web
→ source + date + scope
→ 原始主张
→ Research / Fact candidate / Inference / Hypothesis / Unknown
→ ChatGPT 判断
→ 用户拍板（如需要）
→ GitHub project_facts / decision record
```

缺来源、日期、范围、分类或有权拍板时，不得写成 Confirmed fact / Decision。

如果外部资料会改变当前业务方向，先回到真实意图和事实源裁决；如果只是帮助表达、页面、文案或研究结构，则进入 Reference 契约，不改变项目事实。

## Reference-to-Execution Contract

当资料用于执行效果，而不是事实判断时，先生成参考契约：

| 字段 | 要回答 |
| --- | --- |
| reference_anchor | 来源、类型、是否能查看、必须保留什么 |
| effect_targets | 观感、节奏、信息层级、人感或质量目标 |
| function_fields | 输入、动作、理由、验证、阻断、降级 |
| execution_mapping | 文案、表格、页面、研究或复审怎样使用 |
| deviation_check | 哪些可变，哪些偏离必须修 |
| done_when | 什么证据说明参考已落地 |

## 原感双层

用户原话和原感可以保存为参考层，但不能直接交给 Codex 猜。ChatGPT 要转成执行字段、禁止项和验收标准。Codex 不判断“味道对不对”，只按已锁字段执行。

## Scenario 5

Perplexity 给出一份市场报告。

正确处理：把它视为外部供料，不是项目事实。记录 source + date + scope，拆出主张，标注 Research / Fact candidate / Inference / Hypothesis / Unknown。若要影响战略，进入用户与 ChatGPT 决策流程，再写 GitHub。

## 反例

- 把外部价格当成本项目报价。
- 把竞品页面复制成自己的页面。
- 只做长摘要，不提可执行字段。
- 用“像这个”替代 must_preserve / can_vary / must_not_copy。

## 可执行模板

```text
external_material_bridge:
  source:
  date:
  scope:
  accessibility:
  raw_claims:
  classification:
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
