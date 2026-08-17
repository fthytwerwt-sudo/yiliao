# Project、GitHub、本地与 Obsidian 的物理分层

## 解决什么问题

本机制定义“信息住在哪里”。它防止 Project 静态包、GitHub main、本地文件和 Obsidian 互相冒充。长期项目不能只靠聊天，也不能只靠仓库；四层不是重复备份，而是不同职责的空间。

## 四层职责

| 层 | 保存什么 | 不保存什么 | 事实权 |
| --- | --- | --- | --- |
| ChatGPT Project | 项目指令、协作机制静态包、聊天上下文、少量可重复参考资料 | 实时项目状态、密钥、患者资料、每条日志、所有研究原文 | 协作上下文，不是动态事实 |
| GitHub main | 当前事实、正式决策、机制、状态、日志、索引、测试、轻量证据 | 未授权敏感资料、本地缓存、私人授权、大型临时产物 | 动态项目事实源 |
| 本地执行目录 | 文件现场、依赖环境、临时产物、未提交实验、本机验证 | 自动跨会话事实 | 现场证据，需回写才持久 |
| Obsidian | 可迁移方法、判断路径、案例、反例、模板 | 医疗项目当前动态状态 | 机制源，不是项目状态 |

## 什么时候触发

- 新会话需要接手项目。
- Project 包、GitHub 文件、本地结果或 Obsidian 笔记冲突。
- 本地存在文件，但不确定是否已同步。
- 用户要求刷新 ChatGPT Project。
- 机制迁移需要区分通用行为逻辑和旧项目业务事实。

## 判断流程

1. 当前项目状态先看 GitHub main。
2. 当前本机文件是否存在，必须用本地命令验证。
3. Project 包只说明上传资料的一次静态快照。
4. Obsidian 只提供机制来源和可迁移案例。
5. 若某条信息需要下次新会话默认知道，写回 GitHub main。
6. 若某条机制需要 Project 内新聊天持续使用，生成静态包并让用户上传。

## 冲突裁决

| 冲突 | 裁决 |
| --- | --- |
| Project 静态包 vs GitHub main | GitHub main 胜出 |
| 本地文件存在 vs GitHub 没有 | 本地只是现场，不能自动成为跨会话事实 |
| Obsidian 机制 vs 医疗项目事实 | 机制可参考，当前事实看 GitHub |
| 用户本轮输入 vs 仓库旧状态 | 用户指导本轮；长期改变需回写 |
| 外部研究 vs 项目事实 | 外部研究是候选 |

## 医疗项目现实示例

如果本地 Project 包里有“协作机制 v2”，这只证明 package_generated。它不证明用户已上传到 Project UI，也不证明 Project 新聊天一定已读到。若用户明天把美国候选改成英国候选，Project 包不需要改；变的是 GitHub project_facts 或 decision record，前提是用户与 ChatGPT 正式锁定。

## 常见误用 / 反例

- “聊天里说过”当成 GitHub 已更新。
- “本地包存在”当成 Project UI 已上传。
- “Obsidian 有旧机制案例”当成医疗项目当前事实。
- “研究报告有最新数据”当成项目已决策。

## 可执行模板

```text
physical_layer_check:
  question:
  project_package_state:
  github_main_state:
  local_workspace_state:
  obsidian_mechanism_state:
  conflict:
  authority:
  write_back_needed:
  project_upload_needed:
  user_confirmation_needed:
```
