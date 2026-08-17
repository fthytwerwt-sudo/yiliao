# Implementation Design、任务路由与 No-Guess

## 解决什么问题

复杂任务不能只有目标和步骤。必须先回答任务类型、当前状态、谁负责、哪条路线、fallback、能力边界、probe、验收和 blocked 条件。否则 Codex 会在执行中猜核心路线。

## 六层需求

```text
1 Goal
2 Mechanism
3 Implementation Design
4 Workflow
5 Acceptance
6 Feedback
```

| 层 | 必须回答 |
| --- | --- |
| Goal | 本轮真正目标、本轮不做什么 |
| Mechanism | 触发、禁止、降级、blocked |
| Implementation Design | primary_route、fallback_route、capability_status、probe_required、inputs、outputs、dependencies、allowed_codex_autonomy、forbidden_codex_guessing、done_when、blocked_if |
| Workflow | 步骤、责任人、检查点 |
| Acceptance | 技术、内容、人工、业务、同步成功/失败 |
| Feedback | 失败回目标、机制、路线、执行、权限还是验收 |

## route_decision

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

## State Action Router

| 状态 | 允许动作 | 禁止动作 |
| --- | --- | --- |
| strategy_definition_pending | 比较候选、收集事实、设计最小验证闭环 | 选定市场/产品/价格/验证顺序 |
| blocked_strategy_not_locked | 输出未决策项和判断问题 | 用研究建议启动执行 |
| implementation_design_locked | Codex 在限定范围执行 | 改 locked anchors |
| evidence_pending | 收集可核验证据 | 把预测写成结果 |
| self_repair_required | 定位 fault layer 并最小修复 | 只 retry 或扩大范围 |
| formal_sync_pending | Git/日志/包路径回写 | 未回读就说同步完成 |

## No-Guess

Codex 可推断：唯一匹配路径、低风险格式、等价验证命令、结构化字段补齐。

Codex 不可猜：战略、市场、产品、客户、价格、商业模型、医院合作、医疗/法律结论、外部授权、发布、收款、完成态、人审、业务结果。

## 医疗项目示例

如果以后决定验证需求，不能只说“去找美国客户”。必须先设计：去哪里找、用什么最小 offer、是否收钱、是否需要落地页、什么证明 Demand、什么只是“说感兴趣”。未锁这些，Codex 不得启动获客执行。

## 可执行模板

```text
implementation_design:
  primary_route:
  fallback_route:
  capability_status:
  probe_required:
  inputs:
  outputs:
  dependencies:
  allowed_codex_autonomy:
  forbidden_codex_guessing:
  done_when:
  blocked_if:
```
