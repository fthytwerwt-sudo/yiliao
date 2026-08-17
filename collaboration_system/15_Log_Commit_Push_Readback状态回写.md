# Log、Commit、Push、Readback 状态回写

## 解决什么问题

这个机制解决“做过了，但下次谁也不知道；本地有了，但远端没有；Project 包生成了，但用户没上传；日志还是旧状态”。凡是会影响下一次新会话判断的结果，都必须留下可回读链条。

## 什么时候触发

- 本轮修改了仓库文件。
- 当前事实、机制、日志、Project 包路径或决策记录发生变化。
- 用户要求 GitHub 同步、Project 包同步或最终交付。
- 要报告 completed、formal_synced 或 remote readback。

## 状态定义

| 状态 | 含义 | 不代表 |
| --- | --- | --- |
| local_only | 本地文件已变更 | GitHub 已知 |
| committed | 本地 commit 已创建 | 远端 main 已更新 |
| pushed | push 已尝试并成功 | remote HEAD 已回读 |
| remote_head_verified | origin/main 与 local HEAD 一致 | 用户/业务/Project UI 已验收 |
| package_generated | 本地/仓库中有静态包 | 用户已上传 |
| user_uploaded_to_project_ui | 用户或界面证据显示已上传 | GitHub 被 Project 自动覆盖 |

## Git 收尾流程

1. `git status --short --branch` 确认范围。
2. 只暂存本轮相关路径，避免无关 dirty 混入。
3. 运行测试、链接检查、敏感词/密钥检查和语义检查。
4. 使用 Lore commit message 记录为什么改。
5. push 到 `main`。
6. `git fetch` 后比对 local HEAD 与 `origin/main`。
7. 在最终报告里分开说明 Git 同步、用户上传、业务状态。

## 日志职责

| 文件 | 用途 |
| --- | --- |
| `logs/latest.md` | 最近一次已确认动态、当前安全动作、未确认项 |
| `logs/current_target.md` | 当前唯一目标；战略未锁时仍是锁定最小验证闭环 |
| `logs/change_log.md` | 结构和机制变化历史 |
| `project_facts/04_正式决策记录.md` | 带 provenance 的正式 DECISION |
| `local_path_index.md` | 本地路径、Project 包、上传/UI 状态边界 |

## Blocked 条件

- Git 无权限、网络失败或 remote readback 不一致。
- 暂存范围无法与用户改动区分。
- 发现密钥、患者资料、私人授权或高风险数据。
- 需要用户上传 Project UI 或业务验收，但没有证据。

## 医疗项目现实示例

本轮如果生成 v2 Project 包并 push 成功，只能说 GitHub main 已包含新包。`user_uploaded_to_project_ui` 和 `project_ui_verified` 仍必须保持 unknown，除非用户或界面证据确认。

## 可执行模板

```text
sync_back_check:
  files_changed:
  tests:
  secret_scan:
  logs_updated:
  local_path_index_updated:
  package_generated:
  user_uploaded_to_project_ui:
  project_ui_verified:
  git_commit:
  git_push:
  remote_readback:
  status_boundary:
```
