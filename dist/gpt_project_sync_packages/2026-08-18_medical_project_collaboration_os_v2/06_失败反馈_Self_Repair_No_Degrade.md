# 失败反馈、Self Repair 与 No Degrade

## 解决什么问题

用户说“不对”以后，系统不能让用户负责内部排障。Self Repair 负责定位偏差层级；No Degrade 负责防止达不到原目标时，把低标准产物换个名字写成完成。

## 触发信号

用户说以下任意内容都触发：

- 不对。
- 跑偏。
- 不是我要的。
- 怪。
- 不完整。
- 感觉在忽悠。
- Codex 做完了，但是我觉得不对。

系统自己发现事实冲突、验证失败、同步失败、范围漂移或完成态被质疑，也必须触发。

## Self Repair 检查层

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

| 层 | 检查 |
| --- | --- |
| Goal | 是否误解真实意图或丢了本轮不做 |
| Facts | 是否把研究、记忆、Project 包当 current fact |
| Mechanism | 权限、路由、状态、完成态是否冲突 |
| Route | task_type、allowed/forbidden、must_read 是否错 |
| Implementation | primary_route、fallback、probe、blocked_if 是否缺 |
| Execution | 是否漏读、越界、错改、未验证 |
| Validation | 是否把技术/内容/人工/业务混写 |
| Sync | 日志、Project 包、commit、push、readback 是否漏 |

## 必须输出

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

## No Degrade 字段

```text
original_goal:
why_unavailable:
missing_requirement:
fallback_option:
fallback_loss:
user_approval_required:
status:
```

没有用户批准，fallback 只是建议，不是交付。

## Scenario 3

用户：“Codex 做完了，但是我觉得不对。”

正确处理：触发 `self_repair_audit`。ChatGPT/Codex 先自查 Goal、Facts、Mechanism、Route、Implementation、Execution、Validation、Sync。输出 observed_mismatch、expected、actual、fault_layer、root_cause、minimal_fix、regression_scope、done_when。用户不负责内部诊断。

## 正确状态

| 实际结果 | 状态 |
| --- | --- |
| 技术预览、probe、局部报告 | internal_diagnostic_only |
| 候选路线或候选事实 | candidate / pending_decision |
| 本地生成未同步 | local_only / sync_pending |
| Project 包生成 | package_generated |
| 用户未上传 Project | user_uploaded_to_project_ui unknown |
| 专业主体未复核 | professional_review_pending |

## 医疗项目示例

目标是获得医院书面合作意向，但本轮只有公开资料表。正确说法是：公开资料候选表完成；合作意向、报价、SLA、外联授权和专业复核仍缺失。状态不是 completed，而是 Fact candidate / next_decision_pending。

## 可执行模板

```text
self_repair_no_degrade:
  trigger_signal:
  observed_mismatch:
  expected:
  actual:
  fault_layer:
  root_cause:
  minimal_fix:
  regression_scope:
  original_goal:
  fallback_option:
  fallback_loss:
  user_approval_required:
  status:
  done_when:
```
