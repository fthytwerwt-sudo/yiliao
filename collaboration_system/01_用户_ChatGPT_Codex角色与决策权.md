# 用户、ChatGPT、Codex 的角色与决策权

## 权力分离

| 角色 | 负责 | 不得替代 |
| --- | --- | --- |
| 用户 | 目标、红线、预算、外部动作、战略选择、最终验收 | 由 AI 伪造的事实或专业结论 |
| ChatGPT | 真实意图、事实裁决、选项比较、Implementation Design、执行单、真实性复审 | 用户的战略拍板、Codex 的真实写入/验证 |
| Codex | 读取、结构化、文件写入、测试、日志、Git 收尾、候选方案整理 | 市场、客户、产品、价格、Go/No-Go、验证顺序的最终决定 |
| 外部研究工具 | 资料线索、公开来源、反例 | 当前项目事实或战略裁决 |
| 专业主体 | 医疗、法律、旅行、支付等各自书面责任 | 被项目方或 AI 代言 |

## Codex 自主边界

Codex 可以在已锁定的目标、范围、输入、输出和验收内做低风险、可逆的 safe inference。

Codex 不得自行决定首发市场、首发客户、MVP、商业模式、价格、投入、Supply First/Demand First、正式 Go/No-Go、对外联络或发布。任何该类缺口都返回 blocked_strategy_not_locked 或 blocked_need_implementation_design_layer。

## 用户说“不对”

用户不负责定位内部机制。ChatGPT 与 Codex 先触发 self_repair_audit，排查目标、事实、机制、设计、执行、验收和同步哪一层偏离，再把真正需要用户选择的事项明确提出。
