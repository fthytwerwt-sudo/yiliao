# 变更日志

历史条目记录的是当时的文件结构，不是当前战略事实。当前战略状态以 project_facts/01-04 和 project_state 为准。

| 日期 | 变更范围 | 变化摘要 | 事实状态影响 | 复核 / 同步状态 |
| --- | --- | --- | --- | --- |
| 2026-08-17 | 项目初始化 | 建立项目事实、执行规则、运营模板、复盘结构和静态包生成入口 | 建立 pre_validation 基线；不增加任何供应商、客户或合规已证实事实 | local_only，待 Git commit/push/readback |
| 2026-08-17 | ChatGPT Project 静态包 | 生成 9 文件项目理解包，来源为 aef28ea51e80705a8ab9a8d39cae09e25c4b6e38 | 不改变动态事实；用户上传/生效仍为 UNKNOWN | local commit pending push |
| 2026-08-17 | 初始 GitHub 同步 | main 已推送并回读 d145e4e3a9a9fcc567c4bd1628207bea2d8c4aa3 | 当前项目事实可作为远端基线；本条状态更新仍需单独同步 | prior remote readback confirmed |
| 2026-08-18 | 协作机制级重构 | 研究候选、动态事实、候选剧本与长期协作机制重新分层 | 撤回先前由研究直接升级的战略语义；当前进入 strategy_definition_pending | 待本轮验证与同步 |

记录原则：

- 机制/结构变化写入此处；真实业务观测写入 review_loop。
- 任何更改 current facts 的变更必须同时说明依据、事实标签和是否更新 project_state。
- 不记录患者身份、健康信息、凭据或未授权谈判正文。
