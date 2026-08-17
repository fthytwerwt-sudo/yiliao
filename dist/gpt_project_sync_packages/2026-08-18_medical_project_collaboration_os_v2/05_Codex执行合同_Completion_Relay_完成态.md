# Codex 执行合同、Completion Relay 与完成态

## 解决什么问题

这份机制保证 Codex 不会收到“你看着办”的任务，也不会把局部结果、文件存在或测试通过写成 completed。

## Codex 执行单必填字段

```text
Goal
Context
Current State
Locked Anchors
Constraints
Impact Check
Allowed Changes
Forbidden Changes
Must Read
Implementation Design
Execution Steps
Done When
Blocked If
Validation
Sync Back
Final Output
```

缺 Goal、Allowed/Forbidden、Implementation Design、Done When 或 Blocked If，复杂任务不得执行。

## 执行前检查

Codex 先核验 workspace、branch、remote、local HEAD、origin/main、dirty state；回读 AGENTS、当前事实、日志、相关机制和任务文件；判断是否缺真实意图、战略锁定、权限或验证。缺战略锚点时返回 `blocked_strategy_not_locked`。

## Completion Relay

四个结构必须存在：

| 结构 | 作用 |
| --- | --- |
| required_output_inventory | 本轮承诺的每项产物、路径、验证和状态 |
| child_task_graph | 子任务依赖、执行顺序和阻断关系 |
| remaining_work_check | 还有哪些必须完成项，哪些只是后续建议 |
| sync_back_check | 是否需要日志、事实、Project 包、commit、push、remote readback |

局部结果包括一个文件、一个测试、一个表格、一个本地包、一个 probe。它们是 evidence，不是 completed。只要 required_output_inventory 或 sync_back_check 有阻断性缺口，就不得 completed。

## 五层完成态

| 层 | 能证明 | 不能证明 |
| --- | --- | --- |
| technical_validation | 文件、格式、命令、测试通过 | 内容、业务、合规正确 |
| content_validation | 内容与已锁目标一致 | 用户已接受 |
| human_review | 用户或专业主体复审 | 长期稳定 |
| business_observation | 真实交易、履约、反馈 | 普遍可复制 |
| sync_status | commit、push、readback、包路径 | 用户上传 Project 或业务成功 |

## Scenario 4

Codex：“文件已创建、测试通过。”

正确处理：ChatGPT 检查 Completion Relay 和多层完成态。文件和测试只是 technical_validation。还要看内容是否满足目标、是否有 remaining_work、是否需要 Git/日志/Project 包回写、是否有人审或业务证据。不能直接写 completed。

## 最终回报模板

```text
codex_final_output:
  status:
  files_read:
  files_changed:
  required_output_inventory:
  child_task_graph:
  remaining_work_check:
  sync_back_check:
  validation:
  completion_state:
    technical:
    content:
    human:
    business:
    sync:
  git:
  blocked_reason:
  next_safe_action:
```
