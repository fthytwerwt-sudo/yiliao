# Log、Commit、Push、Readback 状态回写

## 日志职责

- logs/latest.md：最近一次已确认动态、待验证和下一安全动作。
- logs/current_target.md：当前唯一工作目标；未锁定战略时是“锁定最小验证闭环”，不是具体执行路线。
- project_facts/04_正式决策记录.md：带 provenance 的正式 DECISION。
- logs/change_log.md：结构/机制和事实变更历史。

## Git 收尾

修改长期项目文件时：检查范围和秘密 → 验证 → 明确暂存 → Lore commit → push main → fetch/readback → 比对 local HEAD 与 origin/main。

只有 readback 成功才可称 formal_synced。Git 同步不证明用户上传 Project、专业批准或业务成功。
