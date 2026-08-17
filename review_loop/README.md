# 90 天验证复盘系统

本目录是记录真实验证证据的工作表集合，不是预测展示页。

## 使用原则

1. 先记数据窗口、来源、口径和状态，再写结论。
2. 只用匿名 case_id 或聚合数据，绝不写患者身份、健康资料、病历或支付明细。
3. observed、quoted、forecast、unknown 必须分开。
4. 任何假设值不自动推进项目阶段。
5. 每轮只指定一个 primary_variable；避免同时改变客群、价格、渠道、产品和话术。

## 记录顺序

1. supplier_validation：先验证书面供给与 SLA。
2. customer_interview_log：了解目标客户语言、顾虑和边界接受度。
3. experiment_log：记录一个可反驳的实验。
4. funnel_metrics：按时间窗口记录漏斗真实数量。
5. unit_economics：用实际收入、成本、退款和 CAC 计算贡献。
6. incident_and_boundary_log：记录异常、投诉、数据和责任边界事件。
7. 90_day_scorecard：汇总闸门状态，不能替代原始记录。

## 数据成熟度

- not_started：尚无数据。
- collected_unverified：已收集，尚未复核。
- observed_verified：可定位的真实观察。
- insufficient_sample：有少量数据，不足以下结论。
- contradicted：结果反证当前假设。

任何真实外部行动必须先得到用户授权并遵循项目合规边界。
