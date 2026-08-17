# Data Goal Anchor：现实验证与反馈

## 解决什么问题

Data Goal Anchor 让现实验证可解释。它防止一轮同时改变国家、产品、定价、渠道、话术和交付方式，最后无法判断到底什么有效。

## 使用前提

只有当用户与 ChatGPT 锁定某一轮验证设计后，才设置具体市场、产品、价格或渠道的 active anchor。未锁定前，只能做候选比较锚点，不得让 Codex 擅自启动真实执行。

## 必填字段

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
| current_stage_goal | 当前阶段真正要减少哪一个未知 |
| main_bottleneck | 当前最可能卡住结果的主短板 |
| primary_variable | 本轮唯一主动改变和观察的变量 |
| supporting_variables | 为主变量成立允许微调的少量协同项 |
| forbidden_variables | 本轮不动，避免归因混乱 |
| success_metric | 什么算靠近目标 |
| failure_metric | 什么说明不该继续自我安慰 |
| post_validation_metric | 反馈回来后看什么决定下一轮 |
| confidence | 高/中/低及依据 |
| evidence | 来源、日期、范围、验证方式 |
| revisit_trigger | 什么变化触发重设锚点 |

## 单主变量规则

普通试验只允许 1 个 primary_variable，最多 2 个 supporting_variables。较大调整必须标 major_revision，只能观察方向。超过 4 个变量，不得假装是单变量验证。

## 医疗项目示例

如果验证首发客户，不能同时换：

- 国家。
- 产品。
- 定价。
- 渠道。
- 话术。

然后声称知道哪一个有效。

正确做法是先锁一个主变量。例如只比较“候选验证顺序”，其他市场、产品、价格和渠道保持 pending_decision。真正外部验证开始前，再写清成功、失败和 post_validation_metric。

## Done When

一张锚点卡完成时，另一个新 ChatGPT 应能回答：本轮只测什么，什么不动，成功是什么，失败是什么，反馈后看什么，什么情况下重设，Codex 可以改哪些执行结构，不能改哪些上游决定。

## 反例

- 宏观市场资料充足，就说需求已验证。
- 访谈对象说感兴趣，就写成付费意愿。
- 数据不足，却输出“数据驱动执行”。
- Codex 为了表格完整，自行补指标。

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
