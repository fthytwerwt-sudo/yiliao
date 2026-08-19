# 学习闭环与本地接口说明

更新时间：2026-08-19。

## 作用

这一组模块补上了当前系统开发的 Phase 5–7：

- `services/learning_loop.py`
  负责 Metrics（指标记录）、Experiment（单主变量实验）、ExperimentReview（实验复盘）、
  WeeklyReview（周复盘）和 DecisionCandidate（候选判断）。
- `workflows/weekly_review.py`
  提供 `LearningLoop` workflow 入口，给 CLI、本地 API 和测试统一调用。
- `interfaces/cli.py`
  提供离线 CLI，包括：
  `system init`、`research import`、`facts list/review`、`demand list`、
  `products list`、`content generate`、`lead score`、`risk check`、
  `experiment create/review`、`weekly-review generate`、
  `decision candidate`、`sync github --dry-run`。
- `interfaces/local_api.py`
  提供只读、loopback-only 的本地接口应用对象：既支持 `handle()` 直接调试，
  也支持 `create_server()` / `serve_forever()` 启动真实本地 HTTP server。
- `workflows/e2e_scenario.py`
  负责 14 阶段 synthetic E2E，验证：
  Research → Fact → Demand → Product → Content → Comment/DM → Risk → Lead → Match
  → Metrics → Experiment → Weekly Review → Decision Candidate → GitHub Dry Run。

## 当前技术状态

- `external_execution_allowed = false`
- `adapters_enabled = false`
- Local API 只允许绑定 `127.0.0.1`
- GitHub sync 永远是 `dry_run = true`
- Decision Candidate 的 `status` 固定为 `candidate`
- `business_validation_completed` 固定为 `false`
- Local API server 默认不自动启动，只有显式调用 `create_server()` / `serve_forever()` 才监听本地端口

## 明确边界

- 这里的 Learning Loop 只处理 synthetic / strategy-agnostic 运营学习对象。
- 不写真实国家、真实平台路线、真实医院、真实价格、真实客户资料。
- 不调用外部 API，不自动发布，不自动 DM，不自动同步现实系统。
- 即使技术测试全部通过，也**不代表**业务战略已经锁定。
- 即使本地 E2E 可跑完，也**不代表**市场验证、供给验证、合规验证或业务闭环完成。

## 技术验收与业务验收的区别

- 技术验收：
  只说明代码、CLI、本地 API、synthetic workflow、测试和 dry-run 合同都成立。
- 业务验收：
  仍需要用户与 ChatGPT 锁定路线、验证对象、观察窗口、真实事实与人工闸门。

当前仓库完成的是前者，不是后者。
