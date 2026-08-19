# 脚本目录说明

当前阶段不放任何**依赖未锁定业务战略的业务自动化脚本**。

这是 `DEC-ENG-001` 对旧规则的精化：业务战略仍为 `strategy_definition_pending`，但允许建设 `strategy-agnostic system infrastructure`（战略无关系统基础设施）。该许可不代表项目已选择市场、客户、产品、价格、医院、渠道、商业模式或 Go / No-Go。

## 当前禁止

- 依赖未锁业务战略的自动化。
- 自动营销、自动发布、自动 DM、自动医院外联。
- 患者管理、真实患者记录、自动支付或真实收款。
- 自动医疗判断、诊断、治疗建议或疗效/签证/合规保证。
- 把 Research（研究输入）或 AI 输出自动升级为 Confirmed Fact（已确认事实）或 Decision（正式决策）。
- 未经单独用户授权的真实外部 adapter（适配器）调用。

## 当前允许

- `strategy-agnostic system infrastructure`（战略无关系统基础设施）。
- `domain models`（领域模型）、`storage abstraction`（存储抽象层）和 `workflow interfaces`（流程接口）。
- `data cleaning pipeline`（数据清洗管线）、`synthetic fixtures`（模拟测试数据）和 `Mock adapters`（模拟适配器）。
- `local API`（本地接口）、CLI（命令行工具）、本地 Admin / Debug 页面。
- `audit system`（审计系统）、`permission system`（权限系统）、数据库迁移、导入导出和 `automated tests`（自动测试）。

真实外部动作继续默认关闭。任何新系统代码必须通过 `AGENTS.md`、`collaboration_system/18_医疗项目特殊安全与专业责任边界.md` 和 `project_facts/07_合规与责任边界.md` 的边界检查；无论何时，模拟运行都不得产生现实副作用。
