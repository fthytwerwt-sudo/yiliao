# Codex 执行单与权限边界

执行单必须包含 Goal、Context、Current State、Locked Anchors、Constraints、Impact Check、Allowed/Forbidden Changes、Must Read、Implementation Design、Steps、Done When、Blocked If、Validation、Sync Back 和 Final Output。

Codex 读取、结构化、写文件、验证、记录和 Git 收尾；不替用户/ChatGPT 决定战略，也不执行未授权外部动作。

缺关键战略锚点时，Codex 返回 blocked_strategy_not_locked。
