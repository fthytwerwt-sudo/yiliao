# Completion Relay Gate：做到底机制

## 解决什么问题

Completion Relay Gate 防止“做了一个局部结果，就提前宣布完成”。它把交付拆成清单、任务树、剩余工作、验证和同步回写。尤其在多文件机制迁移、Project 包生成、Git 收尾和医疗项目边界里，文件存在只是开始，不是完成。

## 什么时候触发

- 任务包含多个产物、多个目录、多次验证或 Git 同步。
- 用户要求“做到底”“别停在半成品”。
- Codex 汇报“文件已创建、测试通过”。
- 要判断 completed、partial、continue 或 blocked。
- 结果要被下个 ChatGPT、Project 或 GitHub 继续使用。

## 什么小任务不用启动完整闸门

单个只读命令、一个文件的无语义格式修正、路径是否存在检查，可以用轻量收尾。但只要结果会改变长期事实、同步包、日志或用户验收，就必须启动。

## 四个结构

| 结构 | 必须回答 |
| --- | --- |
| required_output_inventory | 本轮承诺的每项输出、路径、验证、状态 |
| child_task_graph | 子任务依赖、顺序、谁负责、哪项阻断后续 |
| remaining_work_check | 还有哪些必须完成项、哪些只是后续建议 |
| sync_back_check | 是否需要日志、事实、Project 包、commit、push、remote readback |

## 什么叫局部结果

局部结果包括：一个文件已写、一个测试通过、一个本地包存在、一个候选清单完成、一个 research table 完成、一个 probe 成功。它们可以作为 evidence，但不得 completed，除非执行单原本只要求这个局部结果，并且 Done When 明确如此。

## 不得 completed 的情况

- required_output_inventory 还有必交付项未完成。
- child_task_graph 有下游依赖未执行。
- remaining_work_check 显示仍有阻断项。
- sync_back_check 需要 Git 或 Project 包更新但未做。
- 技术验证通过但内容、人工、业务或同步状态未区分。
- 降级方案未获用户批准。

## 检查漏项的方法

1. 回到执行单的 Done When，逐项打勾。
2. 查 `git status --short`，确认无关 dirty 未混入。
3. 查测试/验证命令真实输出。
4. 查涉及的索引、日志、路径是否需要更新。
5. 查 Project 包是否只是本地生成，用户上传/UI 生效是否仍 unknown。
6. 查最终回报是否明确 remaining_work。

## 失败后回哪一层

缺产物回 Workflow；缺路线回 Implementation Design；缺事实回 Fact Arbitration；缺验收回 Acceptance；缺 Git 或包同步回 Sync；用户说“不对”回 Self Repair；原目标达不到回 No Degrade。

## 医疗项目现实示例

Codex 说“我创建了医院候选表，并且 Markdown 测试通过”。Completion Relay 应继续检查：是否有来源、日期、范围；是否只是公开资料候选；是否未对外联系；是否未写成 confirmed supplier；是否需要更新研究基线或日志；是否需要用户决定下一步。只有都满足，才能说“本轮只读候选整理完成”。

## 最终报告格式

```text
completion_relay:
  required_output_inventory:
    - item:
      path:
      status:
      evidence:
  child_task_graph:
    - task:
      depends_on:
      status:
  remaining_work_check:
    blocking_remaining:
    non_blocking_followups:
  sync_back_check:
    logs:
    project_facts:
    project_package:
    git_commit:
    git_push:
    remote_readback:
  final_status:
  why_not_more:
```
