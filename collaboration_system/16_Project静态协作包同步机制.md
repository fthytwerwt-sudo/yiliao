# Project 静态协作包同步机制

## 解决什么问题

Project 静态协作包让一个新的 ChatGPT 即使不知道 Obsidian、不知道视频工厂、不知道此前聊天，也能按本项目协作机制工作。它不是 GitHub 镜像，也不是业务事实包。

## 什么时候触发

- 协作机制、任务路由、事实裁决、执行合同、完成态、自修或医疗边界发生变化。
- 旧 Project 包缺关键机制，导致新 ChatGPT 无法执行。
- 用户明确要求提供 GPT Project 同步包地址。
- Project 包内容和 GitHub canonical collaboration system 明显不一致。

## 允许内容

Project 包只保存长期协作机制：

- 用户、ChatGPT、Codex 的分工和权力链。
- 真实意图闸门、目标/边界/验收/停止线。
- 六层需求确认、Implementation Design、No-Guess Routing。
- Codex 执行合同、Completion Relay、完成态。
- Self Repair、No Degrade、Data Goal Anchor。
- 外部研究桥、Project/GitHub/本地/Obsidian 分层。
- 新会话接手、Git/日志/同步规则、医疗安全边界。

## 禁止内容

不得包含当前首发市场、产品、客户、价格、商业模型、Go Gate、90 天打法、供应商、渠道、latest 业务状态、研究报告摘要、真实指标、患者/个人健康信息、密钥、私人授权或未授权资料。

## 自包含标准

一个新 ChatGPT 只读 Project 包，应能执行：

1. 什么时候先判断而不执行。
2. 怎样识别真实意图。
3. 怎样定义目标、边界、验收和停止线。
4. 怎样做 Implementation Design。
5. 什么时候 blocked。
6. 怎样区分研究、事实候选、事实、推断、假设、决策和未知。
7. 怎样给 Codex 执行单。
8. Codex 什么能决定、什么不能决定。
9. 怎样检查是否真正做完。
10. 用户说“不对”以后怎样自修。
11. 怎样避免降级完成。
12. 怎样处理外部研究和医疗特殊风险。

如果需要知道“当前项目事实”，才回读 GitHub main。

## 版本与废弃

旧包如果只是短摘要，必须标记 `DEPRECATED_SEMANTICALLY_INCOMPLETE_DO_NOT_UPLOAD`。旧业务事实包继续保持 `DEPRECATED_DO_NOT_UPLOAD`。canonical 包路径由 `local_path_index.md` 声明。

## 三个独立状态

```text
package_generated:
user_uploaded_to_project_ui:
project_ui_verified:
```

三者不能互相推断。文件存在不等于用户上传，用户上传不等于 GitHub current facts 改变。

## 医疗项目现实示例

明天用户把美国候选改成英国候选，Project 包不需要改。因为 Project 包保存的是“如何处理候选变更”：它会要求回读 GitHub、做事实裁决、判断是否正式 DECISION、更新 project_facts，而不是保存某个国家是默认答案。

## 可执行模板

```text
project_package_sync:
  package_version:
  canonical_path:
  source_commit:
  contains_only_mechanisms:
  forbidden_business_facts_checked:
  self_contained_scenarios_checked:
  old_package_deprecated:
  package_generated:
  user_uploaded_to_project_ui:
  project_ui_verified:
```
