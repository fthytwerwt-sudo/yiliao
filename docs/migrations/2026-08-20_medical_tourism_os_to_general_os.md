# medical_tourism_os 到 General OS 迁移记录

## 当前状态

| 字段 | 值 |
| --- | --- |
| 旧入口 | `medical_tourism_os/` |
| 旧入口状态 | retained（保留） |
| 新主架构 | `general_ai_business_os/` |
| 新架构状态 | active_for_new_capabilities（新增能力入口） |
| 当前兼容委托 | none（尚无） |
| 回滚方式 | 删除新包相关提交；旧包与原有测试不受影响 |

## Phase 1 边界

本 Phase 只创建中性基础能力。`general_ai_business_os` 不导入 `medical_tourism_os`，旧包也不在本 Phase 委托新包。这样既能验证隔离，又不会把旧医疗安全语义意外弱化为通用规则。

## 后续迁移准入

每个拟迁移能力必须先满足以下条件：

1. 新包已有真实实现和失败路径测试。
2. 已针对旧入口补充或保留等价回归测试。
3. 有独立 Phase Review 允许继续。
4. 兼容 adapter 的输入/输出和回滚路径已记录。

在全部条件完成前，旧实现继续是唯一有效入口。
