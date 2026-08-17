# Data Goal Anchor 与单主变量

## 解决什么问题

Data Goal Anchor 把“我们要验证一下”变成可解释的现实反馈设计。它锁住当前阶段目标、主短板、唯一主变量、禁止变量和成功/失败指标，防止一轮同时改市场、产品、价格、渠道和话术，最后不知道是什么导致结果变化。

## 什么时候触发

- 用户与 ChatGPT 已准备设计第一轮最小商业闭环。
- 任何真实市场、客户、供应、价格、渠道或转化验证即将启动。
- 复盘需要解释为什么结果变好或变差。
- Codex 要根据验证设计写表格、落地页、话术或记录模板。

## 什么时候不触发

当前项目仍处于 strategy_definition_pending 时，不能生成具体市场/产品/价格的 active anchor。此时只能使用“候选比较锚点”：比较哪条最小闭环最值得先验证。

## 锚点字段

```text
current_stage_goal:
main_bottleneck:
primary_variable:
supporting_variables:
forbidden_variables:
success_metric:
failure_metric:
post_validation_metric:
confidence:
evidence:
revisit_trigger:
```

| 字段 | 含义 |
| --- | --- |
| current_stage_goal | 当前阶段真正要减少哪一个关键未知 |
| main_bottleneck | 当前最可能卡住结果的主短板 |
| primary_variable | 本轮唯一主动改变并观察的变量 |
| supporting_variables | 为让主变量成立而允许微调的少数协同变量 |
| forbidden_variables | 本轮明确不动，保留归因价值 |
| success_metric | 什么出现算向目标靠近 |
| failure_metric | 什么出现说明不该继续自我安慰 |
| post_validation_metric | 真实反馈后看什么决定下一轮 |
| confidence | 高/中/低，并说明证据 |
| evidence | 来源、日期、范围、验证方式 |
| revisit_trigger | 什么变化触发重设锚点 |

## 单主变量规则

| 情况 | 允许范围 | 状态 |
| --- | --- | --- |
| 普通试验 | 1 个 primary_variable，最多 2 个 supporting_variables | 可解释 |
| 较大调整 | 最多 4 个变量，必须标 major_revision | 只能观察方向 |
| 超过 4 个变量 | 不得称为单变量验证 | 方向重做观察 |

## 角色和权限

用户和 ChatGPT 锁定阶段目标、主短板、主变量和指标。Codex 可以把锚点传递到表格、话术、记录模板和验证清单，但不能改主短板、主变量、禁止变量或成功/失败标准。

## 医疗项目现实示例

如果验证首发客户，不能同时换国家、产品、定价、渠道、话术，然后声称知道哪一个有效。

正确写法可能是：

- current_stage_goal：比较哪条最小闭环最能产生真实反馈。
- main_bottleneck：未知，不可由 Codex猜。
- primary_variable：候选验证顺序的选择标准。
- forbidden_variables：不锁定首发市场、产品、价格、渠道。
- success_metric：用户与 ChatGPT 形成带 provenance 的第一轮验证设计。

当战略锁定后，才可换成具体 Demand/Supply/价格/渠道锚点。

## Done When

一个数据锚点完成时，应能回答：这轮只测什么；哪些变量不动；成功和失败各是什么；结果出来后看什么；什么情况下重设锚点；Codex 哪些调整被允许。

## 常见误用 / 反例

- 同时改国家、服务包、价格、获客渠道和话术，却说验证了 demand。
- 只有宏观市场报告，没有真实行为指标。
- 数据不足时硬写“数据驱动决策”。
- Codex 为了让表格完整，补造 success metric。

## 可执行模板

```text
data_goal_anchor:
  current_stage_goal:
  main_bottleneck:
  primary_variable:
  supporting_variables:
  forbidden_variables:
  success_metric:
  failure_metric:
  post_validation_metric:
  confidence:
  evidence:
  revisit_trigger:
  allowed_codex_changes:
  forbidden_codex_changes:
```
