# 新会话接手与 AGENTS 机制

## 解决什么问题

AGENTS.md 是新会话的最短入口。它不替代协作机制全文，也不替代项目事实；它告诉新执行者先读什么、哪些不能猜、战略未锁时如何 blocked、怎样收尾。

## 新会话读取顺序

1. `AGENTS.md`。
2. `collaboration_system/00_总览_用户到现实反馈的完整闭环.md`。
3. `project_facts/00_项目身份.md`、`01_当前已确认事实.md`、`02_当前状态_project_state.yaml`、`03_当前未决策事项.md`。
4. `logs/latest.md` 与 `logs/current_target.md`。
5. 当前任务对应的 `collaboration_system`、`research_baselines` 或 `candidate_playbooks` 文件。

## 接手后必须判断

```text
project_identity:
current_branch:
local_head:
origin_main:
dirty_state:
current_stage:
strategy_locked:
task_type:
must_read:
allowed_changes:
forbidden_changes:
blocked_if:
```

## 默认状态

当前项目是 `strategy_definition_pending`。尚无由用户与 ChatGPT 正式锁定的市场、客户、产品、商业模式、价格、验证顺序、正式门槛或 Go/No-Go。新会话不能把研究候选恢复为旧战略。

## Blocked 条件

- 无法确认项目身份或主读取分支。
- 未读 AGENTS 和当前事实就准备写入。
- 任务要求战略执行但 strategy_locked=false。
- 当前事实和 Project 包冲突但未裁决。
- 缺 Implementation Design、授权、验证或同步要求。

## 医疗项目现实示例

如果新会话只拿到 Project 包，它可以知道怎样协作，但不知道当前最新事实。涉及当前市场、候选、决策和日志时，必须回 GitHub main。若 GitHub 显示战略未锁，新会话应返回 `blocked_strategy_not_locked`，而不是根据 Project 包或旧聊天选择路线。

## 可执行模板

```text
new_session_takeover:
  read_agents:
  read_collaboration_overview:
  read_project_facts:
  read_logs:
  task_specific_sources:
  current_state:
  route_decision:
  execution_allowed:
  blocked_reason:
```
