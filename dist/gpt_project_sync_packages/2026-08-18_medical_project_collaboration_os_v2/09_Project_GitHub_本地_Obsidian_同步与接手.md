# Project、GitHub、本地、Obsidian：同步与接手

## 解决什么问题

这份机制让新 ChatGPT 知道：Project 包、GitHub main、本地执行目录和 Obsidian 各自是什么，不能互相冒充。

## 四层职责

| 层 | 保存什么 | 不保存什么 |
| --- | --- | --- |
| ChatGPT Project | 项目指令、协作机制静态包、聊天上下文 | 动态事实、密钥、患者资料、每条日志 |
| GitHub main | 当前事实、正式决策、机制、状态、日志、测试 | 未授权敏感资料、本地缓存 |
| 本地执行目录 | 当前机器的运行现场、临时产物、工具环境 | 自动跨会话事实 |
| Obsidian | 可迁移机制、判断路径、案例、反例 | 当前项目动态状态 |

## 新会话接手

涉及当前项目状态时，读取：

1. GitHub main 的 `AGENTS.md`。
2. `collaboration_system/00_总览_用户到现实反馈的完整闭环.md`。
3. `project_facts/00`、`01`、`02`、`03`。
4. `logs/latest.md` 与 `logs/current_target.md`。
5. 当前任务对应文件。

Project 包能告诉你“怎么协作”，不能告诉你当前业务事实是否已改变。

## 冲突处理

如果 Project 包、聊天记忆、外部研究和 GitHub main 冲突，先按 GitHub main 裁决当前事实；用户本轮输入可以指导本轮讨论，但要成为长期事实仍需写回 GitHub。Obsidian 只提供机制和案例，不覆盖医疗项目当前状态。本地文件只有当次本机验证意义，需要长期继承时必须进入日志或事实文件。

## Git / Log / Readback

仓库写入完成至少要求：只暂存本轮路径、验证、secret scan、Lore commit、push、fetch/readback、比对 local HEAD 与 origin/main。Git 同步不证明 Project UI 已上传、用户已验收或业务已成立。

## Project 包三状态

```text
package_generated:
user_uploaded_to_project_ui:
project_ui_verified:
```

文件存在只证明第一项。第二项和第三项必须由用户或界面证据确认。

## Scenario 6

明天用户把美国改英国。

正确处理：Project 包不需要改，因为它不保存当前首发市场。可能需要改的是 GitHub 项目事实或正式决策记录，前提是用户与 ChatGPT 真的锁定了该改变。若只是讨论候选，仍保持 candidate / pending_decision。

## 常见反例

- 本地包存在，就说 Project 已更新。
- Project 旧资料和 GitHub main 冲突时，按 Project 执行当前事实。
- Obsidian 中旧案例详细，就覆盖医疗项目状态。
- 任务分支 push，就说新会话默认知道。

## 可执行模板

```text
sync_and_takeover:
  package_generated:
  user_uploaded_to_project_ui:
  project_ui_verified:
  github_main_head:
  local_head:
  remote_readback:
  current_fact_source:
  conflict:
  write_back_required:
  blocked_if:
```
