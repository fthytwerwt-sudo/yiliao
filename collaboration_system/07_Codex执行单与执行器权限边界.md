# Codex 执行单与执行器权限边界

ChatGPT 下发给 Codex 的执行单必须包含：

Goal、Context、Current State、Locked Anchors、Constraints、Impact Check、Allowed Changes、Forbidden Changes、Must Read、Implementation Design、Execution Steps、Done When、Blocked If、Validation、Sync Back、Final Output。

## Codex 执行前检查

1. 核验 workspace、remote、branch、local HEAD、origin/main 和 dirty state。
2. 回读 AGENTS、canonical collaboration source、project facts、当前日志和任务文件。
3. 判断任务是否缺真实意图、战略锁定、Implementation Design、权限或验证。
4. 缺核心战略锚点时输出 blocked_strategy_not_locked；不得以“候选最合理”作为执行许可。

## 写入权限

Codex 只改执行单允许的路径。外部研究、Project 静态包、候选剧本、模板、真实数据和正式事实的写入权不同；不确定时只读或 blocked。

## 收尾

Codex 负责技术验证、内容一致性检查、日志/事实回写建议、明确暂存、commit、push 和远端 readback。它不把这些技术状态写成用户决策、专业批准或业务成功。
