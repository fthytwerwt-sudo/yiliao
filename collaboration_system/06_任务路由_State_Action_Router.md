# 任务路由与 State Action Router

## 解决什么问题

任务路由把一句用户输入变成“能不能开始、谁负责、改什么、何时停”。State Action Router 把当前项目状态映射成允许动作和禁止动作。它们防止 Codex 把“帮我看看”“直接做”“同步一下”理解成自己最方便的文件操作。

## 什么时候触发

- 每次准备下发 Codex。
- 用户输入不清楚或带有方向判断。
- 当前状态可能是 strategy_definition_pending、blocked、evidence_pending、self_repair_required 或 formal_sync_pending。
- 任务涉及多文件、多步骤、Project 包、Git 同步或外部资料。

## route_decision 必填字段

```text
task_type:
current_state:
responsibility_layer:
input_signal:
observed_evidence:
fact_source_used:
must_read:
allowed_changes:
forbidden_changes:
implementation_design_required:
selected_action:
done_when:
blocked_if:
sync_back:
execution_permission:
```

## 任务类型

| task_type | 允许动作 | 需要额外检查 |
| --- | --- | --- |
| true_intent_or_strategy_judgment | 候选比较、问题澄清、决策字段 | 不允许 Codex 选战略 |
| mechanism_sync_or_fix | 改协作机制、测试、Project 包 | 语义覆盖和无业务事实泄漏 |
| read_only_research | 提取资料、标来源和缺口 | 研究不得写成事实 |
| implementation_design | 写路线、fallback、probe、验收 | 未锁定路线保持 candidate |
| locked_execution | 按已锁定合同执行 | 不改变 locked anchors |
| self_repair_audit | 分层诊断、最小修复 | 不要求用户排查内部机制 |
| formal_sync | 日志、commit、push、readback、包路径 | 同步不等于用户上传或业务验收 |

## State Action Router

| 当前状态 | 允许最小动作 | 禁止动作 |
| --- | --- | --- |
| strategy_definition_pending | 比较候选、收集事实、设计最小验证闭环 | 选定市场/产品/价格/验证顺序 |
| blocked_strategy_not_locked | 输出未决策项、证据缺口和需要用户/ChatGPT 判断的问题 | 用研究建议启动执行 |
| implementation_design_locked | Codex 在限定范围执行和验证 | 改变 locked anchors |
| evidence_pending | 收集可核验证据或停在准备层 | 将预测写成结果 |
| self_repair_required | 定位 fault layer 并最小修复 | 只 retry 或扩展范围 |
| formal_sync_pending | Git 收尾、日志回写、远端 readback | 声称跨会话已同步但未回读 |

## 默认动作

先做 route_decision，再决定是否需要六层确认、Implementation Design、Reference Bridge、Completion Relay 或 Self Repair。路由清楚不等于可以执行；它只是决定下一张闸门。

## Blocked 条件

- project_route 未识别。
- must_read 文件无法读取。
- allowed_changes / forbidden_changes 缺失。
- 当前状态禁止该动作。
- 任务需要用户或专业主体授权但未授权。
- 研究、事实、决策混在一起无法裁决。

## 医疗项目现实示例

用户说“直接让 Codex 开始找医院”。路由不能是 locked_execution。它更可能是 `true_intent_or_strategy_judgment` 或 `implementation_design`：先判断找医院验证什么、是否允许外联、需要公开资料还是真实沟通、成功证据是什么。未授权外联时，Codex 只能做只读公开资料候选或 blocked。

## 常见误用 / 反例

- route_decision 写了“机制修补”，但实际改了业务事实。
- strategy_definition_pending 下直接生成外联名单和话术。
- formal_sync_pending 下只生成本地包，却说 Project UI 已更新。

## 可执行模板

```text
state_action_router:
  input_signal:
  task_type:
  current_state:
  responsibility_layer:
  observed_evidence:
  fact_source_used:
  trigger_mechanism:
  selected_action:
  allowed_changes:
  forbidden_changes:
  must_read:
  done_when:
  blocked_if:
  feedback_update:
  execution_permission:
```
