# 90 天总分卡

状态日期：2026-08-17。以下表格的初始值都是 not_started / UNKNOWN，不是零结果，也不是预测完成。

| 验证维度 | 90 天门槛 | 当前观测 | 数据成熟度 | 证据位置 | 当前判断 |
| --- | --- | --- | --- | --- | --- |
| 候选机构真实访谈 | 至少 2 家 | 未开始 | not_started | supplier_validation | UNKNOWN |
| 书面 SLA | 至少 1 家 | 未开始 | not_started | supplier_validation | UNKNOWN |
| 外籍流程 + 书面价格 + 双语交付 + 异常/转诊 | 至少 1 组可用证据 | 未开始 | not_started | supplier_validation / operations/03 | UNKNOWN |
| 合格线索 | 至少 40 | 未开始 | not_started | funnel_metrics | UNKNOWN |
| Evaluation | 约 20 | 未开始 | not_started | funnel_metrics | UNKNOWN |
| Formal Quote | 约 10 | 未开始 | not_started | funnel_metrics | UNKNOWN |
| 真实有效订金 | 至少 5 | 未开始 | not_started | funnel_metrics / unit_economics | UNKNOWN |
| 实际成行 | 至少 3 | 未开始 | not_started | funnel_metrics | UNKNOWN |
| 完成交付 | 至少 3 | 未开始 | not_started | funnel_metrics / experiment_log | UNKNOWN |
| P50 付费 CAC | 不高于 USD 900 | 未开始 | not_started | unit_economics | UNKNOWN |
| 成行 CAC | 不高于 USD 1,200 | 未开始 | not_started | unit_economics | UNKNOWN |
| P50 单客贡献 | 大于 USD 600 | 未开始 | not_started | unit_economics | UNKNOWN |
| 重大责任/数据事件 | 0 个未受控事件 | 未开始 | not_started | incident_and_boundary_log | UNKNOWN |

## 本期结论

当前仅能得出：验证系统已建立，尚无真实业务观测。不可将此分卡用于对外宣称项目已通过任何商业/合规闸门。

## 下一次更新规则

每一行只在有来源、日期、口径、匿名化记录和复核人时更新。若发现失败，标记 contradicted 或 Hold/No-Go，而不是删除记录。
