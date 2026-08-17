# Codex 执行单与执行器权限边界

## 解决什么问题

Codex 执行单不是一段更长的“帮我做一下”。它是一份让执行器不需要猜核心决策的合同。它必须让另一个人能检查：本轮要做什么、不做什么、依据什么、能改哪里、缺什么 blocked、怎样验证、怎样同步。

## 什么时候触发

- ChatGPT 准备把任务交给 Codex。
- 任务涉及文件写入、脚本、测试、同步包、日志、Git 或结构化资料。
- 用户输入是方向型，需要转成执行字段。
- Codex 结果会影响下一次新会话的默认事实。

## 执行单必填字段

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

## 字段定义

| 字段 | 必须写清 | 不能偷换 |
| --- | --- | --- |
| Goal | 本轮唯一目标和本轮不做什么 | 不把阶段目标写成最终业务成功 |
| Context | 当前项目事实、研究输入、前序结果 | 不塞无关历史，不用记忆代替回读 |
| Current State | 如 strategy_definition_pending / self_repair_required | 不把候选状态写成 locked |
| Locked Anchors | 已锁目标、范围、事实源、验收、对象 | 不让 Codex 改锚点 |
| Constraints | 权限、外部动作、敏感数据、工具和文件边界 | 不默认允许联网、外联、收款或发布 |
| Impact Check | 影响哪些文件、事实、同步包、日志和风险 | 不把局部改动误写为全局变化 |
| Allowed Changes | 明确可写路径与可改内容 | 不使用 broad scope 或 git add . |
| Forbidden Changes | 禁止路径、状态、事实、战略、外部动作 | 不凭“方便”扩大范围 |
| Must Read | 必须读取的文件、原因和读取状态 | 不靠聊天描述直接改 |
| Implementation Design | primary_route、fallback、probe、能力状态 | 不让执行步骤临时决定路线 |
| Execution Steps | 最小顺序动作 | 不夹带未锁定决策 |
| Done When | 产物、验证、日志、同步和状态边界 | 不用测试通过冒充完成 |
| Blocked If | 缺文件、缺权限、缺设计、事实冲突 | 不继续硬做 |
| Validation | 命令、人工检查、场景检查、回读 | 不报告未运行的验证 |
| Sync Back | 是否改 logs、project_facts、Project 包、Git | 不把本地文件当远端事实 |
| Final Output | 结果、证据、风险、未完成、SHA | 不省略失败项 |

## Codex 执行前检查

1. 核验 workspace、remote、branch、local HEAD、origin/main 和 dirty state。
2. 回读 `AGENTS.md`、本目录相关机制、`project_facts`、`logs` 和任务文件。
3. 检查真实意图、战略锁定、Implementation Design、权限、验收和验证是否完整。
4. 判断任务是否会改变当前项目事实、Project 包或外部现实。
5. 缺关键锚点时输出明确 blocked 状态，不生成“看起来合理”的替代方案。

## 权限边界

Codex 可以：读取、结构化、写文档、写测试、运行本地验证、生成同步包、更新日志、做 Git 收尾、提出候选和缺口。

Codex 不可以：决定战略、首发市场、客户、产品、价格、商业模式、医院合作、医疗/法律结论、是否联系外部主体、是否收款、是否发布、是否 Go/No-Go、是否接受降级完成。

## Blocked 条件

- 缺 `Goal` 或 `本轮不是`。
- 缺 `Allowed Changes` 或 `Forbidden Changes`。
- 缺 `Implementation Design`，返回 `blocked_need_implementation_design_layer`。
- 战略未锁却要求执行战略动作，返回 `blocked_strategy_not_locked`。
- 缺真实意图，返回 `blocked_missing_true_intent_gate`。
- 外部动作、敏感医疗数据或专业责任不清。

## 医疗项目现实示例

若执行单写“整理医院候选”，Codex 可读取公开资料、按字段结构化、标来源和缺口。若执行单写“联系医院谈合作”，Codex 必须 blocked，除非用户明确授权外联、目标、话术、主体、合规边界和记录方式。

## 最终回报模板

```text
status:
task_type:
route_decision:
files_read:
files_changed:
validation:
  commands:
  result:
  failed_items:
completion_boundary:
  technical:
  content:
  human:
  business:
  sync:
git:
  branch:
  commit:
  push:
  remote_readback:
blocked:
blocked_reason:
remaining_work:
next_safe_action:
```
