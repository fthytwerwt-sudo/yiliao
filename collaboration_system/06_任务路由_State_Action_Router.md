# 任务路由与 State Action Router

## 先做 route_decision

每个任务先回答：

- task_type：判断、研究、机制、候选设计、已锁定执行、复盘、同步或只读审计。
- current_state：当前项目/任务状态。
- responsibility_layer：用户、ChatGPT、Codex、外部研究或专业主体。
- allowed_changes、forbidden_changes、must_read、blocked_if。

## State Action Router

| 当前状态 | 允许最小动作 | 禁止动作 |
| --- | --- | --- |
| strategy_definition_pending | 比较候选、收集事实、设计最小验证闭环 | 选定市场/产品/价格/验证顺序 |
| blocked_strategy_not_locked | 输出未决策项和需要用户/ChatGPT 判断的问题 | 用研究建议启动执行 |
| implementation_design_locked | Codex 在限定范围执行和验证 | 改变 locked anchors |
| evidence_pending | 收集可核验证据或停在准备层 | 将预测写成结果 |
| self_repair_required | 定位失败层并最小修复 | 只重试或扩展范围 |
| formal_sync_pending | Git 收尾与远端回读 | 声称跨会话已同步 |

状态动作不是商业决策器；它只规定在给定状态下谁能做哪一类动作。
