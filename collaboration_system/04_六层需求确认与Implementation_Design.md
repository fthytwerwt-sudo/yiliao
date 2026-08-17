# 六层需求确认与 Implementation Design

## 解决什么问题

六层需求确认解决“目标写了、步骤写了，但实现路线没人锁”的问题。没有这一层，Codex 会在执行阶段自己猜核心路线，最后可能技术上做了很多，语义上却偏离用户真实目标。

## 什么时候触发

- 复杂任务、机制迁移、同步包生成、外部研究桥接、数据验证设计、候选路线比较。
- 用户反馈“不对”“怪”“不完整”“不是我要的”。
- 旧规则和新目标冲突。
- 需要 Codex 改文件，但 primary_route、fallback、能力边界、probe、验收或 blocked 条件不清。

## 什么时候不触发

单一、低风险、已锁定的格式修正或只读命令检查，可以直接进入执行合同，但最终仍要做 Completion Relay。

## 六层结构

```text
1 Goal
2 Mechanism
3 Implementation Design
4 Workflow
5 Acceptance
6 Feedback
```

| 层 | 必须回答 | 缺失后果 |
| --- | --- | --- |
| 1 Goal | 本轮真正目标、本轮不做什么、阶段目标还是最终目标 | 执行会替用户扩大目标 |
| 2 Mechanism | 何时触发、何时禁止、何时降级、哪些能力待验证 | 旧机制会覆盖新任务 |
| 3 Implementation Design | 路线、fallback、能力状态、probe、输入输出、Codex 自主边界 | Codex 会猜核心路线 |
| 4 Workflow | 谁判断、谁执行、执行顺序、检查点、是否需要用户回审 | 子任务会断链 |
| 5 Acceptance | 技术、内容、人工、业务、同步的成功/失败 | 技术通过会冒充完成 |
| 6 Feedback | 失败后回目标、机制、设计、流程、执行、权限还是验收 | 只会重复 retry |

## Implementation Design 最低字段

```text
primary_route:
fallback_route:
capability_status:
  confirmed:
  partially_true:
  pending_validation:
probe_required:
inputs:
outputs:
dependencies:
allowed_codex_autonomy:
forbidden_codex_guessing:
done_when:
blocked_if:
```

其中 `primary_route` 必须由用户与 ChatGPT 锁定或明确标为 candidate_route。战略未锁定时，Codex 不得把 candidate_route 改成 active_route。

## 角色和权限

ChatGPT 负责补齐六层、提出路线与反方风险、决定是否可下发。用户负责目标、授权、预算、红线和最终商业拍板。Codex 只执行已锁定的 Implementation Design，并报告能力缺口。

## 默认动作

- 缺 Goal：回真实意图。
- 缺 Mechanism：补触发/禁止/降级/blocked。
- 缺 Implementation Design：输出 `blocked_need_implementation_design_layer`。
- 缺 Workflow：先写任务树。
- 缺 Acceptance：不执行或只做内部诊断。
- 缺 Feedback：补失败路由后再执行。

## 医疗项目现实示例

如果以后决定验证需求，不能只说：去找美国客户。

必须先设计：

- 去哪里找：公开社群、转介绍、医生网络、海外华人机构还是广告。
- 用什么最小 offer：访谈、咨询预约、健康管理说明、预审问卷还是报价。
- 是否收钱：不收、意向金、订金或仅验证问题严重性。
- 是否需要落地页：如果需要，落地页验证什么，不验证什么。
- 什么证明 Demand：合格回复、预约、付费、转介绍、到院。
- 什么只是“说感兴趣”：点赞、收藏、泛泛回复、朋友觉得可以。

未锁这些之前，Codex 不能自行开始“获客执行”。

## 常见误用 / 反例

- 用更长 prompt 代替路线设计。
- 只有 primary_route，没有 fallback 和 blocked_if。
- 让 Codex 边执行边决定是否换市场、渠道或价格。
- 做了技术 probe，就说商业能力成立。

## 可执行模板

```text
six_layer_gate:
  1_goal:
    real_goal:
    not_this_round:
  2_mechanism:
    trigger:
    non_trigger:
    downgrade:
    blocked:
  3_implementation_design:
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
  4_workflow:
    steps:
    owners:
    checkpoints:
  5_acceptance:
    technical:
    content:
    human:
    business:
    sync:
  6_feedback:
    if_goal_wrong:
    if_route_wrong:
    if_execution_wrong:
    if_validation_missing:
```
