# 失败反馈与 Self Repair Audit

## 解决什么问题

用户不需要懂内部机制，才能说“这个不对”。Self Repair Audit 要求 ChatGPT 与 Codex 在收到负反馈后自行定位偏差层级、给出最小修复和回归范围，而不是把诊断责任转给用户。

## 什么时候触发

用户说以下任意信号都有效：

- 不对。
- 跑偏。
- 不是我要的。
- 怪。
- 不完整。
- 感觉在忽悠。
- 当前交付不合格。
- 技术做了，但不是我想要的。

系统自身发现事实冲突、验证失败、同步失败、范围漂移、完成态偷换，也必须触发。

## 用户不负责内部诊断

用户只需说明可见结果与期望不符。用户不需要指出哪份测试、哪个字段、哪层机制、哪条 Git 状态或哪个 Project 包错了。系统先自查，再把真正需要用户拍板的问题单独提出。

## 自修检查顺序

```text
Goal
Facts
Mechanism
Route
Implementation
Execution
Validation
Sync
```

| 层 | 检查问题 | 常见修复 |
| --- | --- | --- |
| Goal | 是否误解真实意图、本轮不做什么是否丢失 | 回真实意图闸门 |
| Facts | 是否把研究、记忆、Project 包当 current fact | 回事实源裁决 |
| Mechanism | 权限、状态、完成态规则是否互相冲突 | 修机制并加测试 |
| Route | 任务类型、allowed/forbidden、must_read 是否错 | 重写 route_decision |
| Implementation | primary_route、fallback、probe、blocked_if 是否缺 | 回六层需求 |
| Execution | 是否漏读、越界、错改、未验证 | 最小修复执行路径 |
| Validation | 是否把技术/内容/人工/业务混写 | 补验证和完成态 |
| Sync | 日志、Project 包、commit、push、readback 是否漏 | 补同步或 blocked |

## 必须输出的字段

```text
observed_mismatch:
expected:
actual:
fault_layer:
root_cause:
minimal_fix:
regression_scope:
done_when:
```

## 默认动作

1. 复述用户反馈对应的 mismatch，不争辩。
2. 回读执行单、相关机制、改动文件、测试和同步状态。
3. 定位 fault_layer。
4. 选择 minimal_fix，不扩大到无关重构。
5. 写 regression_scope，防止修一处坏一片。
6. 修后跑对应验证和 Completion Relay。

## Blocked 条件

- 需要用户重新定义目标或授权。
- 缺关键源文件或无法验证。
- 修复会改变战略、外部动作、医疗/法律责任或敏感数据处理。
- 原目标不可达，必须进入 No Degrade 而不是硬写 completed。

## 医疗项目现实示例

用户说：“Codex 做完了，但是我觉得不对。”系统不能回“哪里不对？”就停住。应先自查：是不是只生成了结构文件但语义不完整；是不是把研究候选写成事实；是不是 Project 包太薄；是不是测试只测文件存在；是不是没有 source vs target 抽查。然后给出 minimal_fix 和回归测试。

## 常见误用 / 反例

- 用户说不对，AI 让用户找内部 bug。
- 失败后只 retry，不判断 fault_layer。
- 为了通过反馈，扩大范围重做战略。
- 用“已补充说明”掩盖原目标仍未满足。

## 可执行模板

```text
self_repair_audit:
  trigger_signal:
  observed_mismatch:
  expected:
  actual:
  fault_layer:
  root_cause:
  minimal_fix:
  regression_scope:
  validation:
  done_when:
  user_decision_needed:
  blocked_if:
```
