# Completion Relay Gate：做到底机制

完成不是“写完一个文件”。每项任务必须检查：

1. required_output_inventory 是否齐全。
2. 依赖任务和必要输入是否完成。
3. 是否还有阻断性的 remaining_work。
4. 是否进行了相应验证。
5. 长期事实、日志、静态包和 Git 是否需要 sync_back。
6. 最终回报是否区分技术、内容、人工、业务与同步状态。

## 不允许的降级

- 局部 probe 冒充完整交付。
- 本地文件冒充远端同步。
- commit 冒充 push/readback。
- 技术通过冒充内容、人审或业务通过。
- 候选方案冒充正式战略。

若存在未完成的必要接力，状态应为 continue、blocked 或 partial，不得写 complete。
