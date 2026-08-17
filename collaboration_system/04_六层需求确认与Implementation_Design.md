# 六层需求确认与 Implementation Design

复杂任务不能只有目标和步骤。必须确认六层：

1. 目标层：本轮真正目标和不做什么。
2. 机制层：何时触发、禁止、降级和 blocked。
3. Implementation Design：主路线、备选路线、能力状态、probe、Codex 自主范围和禁止猜测。
4. 流程层：执行顺序、输入输出、检查点和责任人。
5. 判断标准层：技术、内容、人工、业务的成功/失败条件。
6. 反馈层：失败应回到目标、机制、设计、流程、执行、权限还是验收。

## Implementation Design 最低字段

- primary_route 与 fallback_route。
- capability_status：confirmed / partially_true / pending_validation。
- probe_required。
- required_inputs 与 required_outputs。
- allowed_codex_autonomy 与 forbidden_codex_guessing。
- validation 与 blocked_if_missing。

战略路线尚未由用户与 ChatGPT 锁定时，primary_route 不得由 Codex 生成；可以记录为 candidate_route，状态为 pending_decision。
