# Codex 执行、验证与 Git 收尾

## 工作区纪律

- 只在 yiliao 的唯一正式本地工作区写入本项目文件。
- 不修改 Obsidian 协作机制库、视频工厂、其他仓库、两份原始 DOCX 或用户其他项目。
- 写入前检查 git status、当前分支、remote 和文件范围。
- 只暂存明确属于本次任务的路径；若出现无关改动，保留且不擅自暂存。

## 变更纪律

- 更新既有事实优先于另建重复文件。
- 每个文件有唯一职责；状态的 canonical 入口是 project_facts/01 与 02。
- 医疗、法律、数据、价格和业务结果不补造。
- 患者资料、个人可识别信息、密钥、Token、私人授权和原始报告不得提交。
- 外部发送、发布、投放、支付、订单、签约默认不执行。

## 验证次序

1. 文件存在和目录结构。
2. Markdown 内部链接、标题和表格基本可读。
3. YAML 可解析。
4. 不含秘密、患者数据或禁止内容。
5. 事实标签、当前阶段、市场和产品在入口文件中一致。
6. 本次任务相关模板是否真正可填写和记录。
7. git diff、git status、明确暂存、commit、push。
8. 远端 main readback、最终 SHA 和远端文件一致性。

## Git 完成态

只有 commit、push 和远端 main readback 均成功，才能把本次仓库状态描述为 formal_synced。普通 Git、gh、远端网页和本地 shell 的认证状态可能不同；不得用其中一个替代另一个。

若 push 遭遇网络传输异常，先进行非破坏性重试/诊断；不得将其直接归因于 Token。若需要 GitHub 官方登录、2FA 或授权，交由用户完成，且绝不在聊天、仓库、Markdown、.env、remote URL 或日志中写入 Token。

## Commit 信息

所有提交遵守仓库的 Lore Commit Protocol：

- 首行说明为什么要做该变更。
- 正文解释约束和取舍。
- 按需要使用 Constraint、Rejected、Confidence、Scope-risk、Directive、Tested、Not-tested 等 Git trailers。

## 收尾回写

完成一项会影响长期项目状态的工作后，至少检查：

- project_facts/01 和 project_state 是否需要更新。
- logs/latest、decision_log、change_log 是否需要回写。
- ChatGPT Project 静态包是否已过期，需要重新生成。
- 远端 main 是否是当前事实源。
