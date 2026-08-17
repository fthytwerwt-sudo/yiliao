# No Degrade：禁止降级完成

## 解决什么问题

No Degrade 防止系统达不到原目标时，偷偷把更低标准的产物改名为完成。降级可以被提出，但必须披露损失、等待有权主体批准，并保持状态边界。

## 什么时候触发

- 原目标做不到、权限不足、能力未验证、资料缺失。
- Codex 产出的是 probe、草案、候选、报告、局部表格或本地包。
- 外部 API、外联、专业主体、人审或业务证据缺失。
- 用户质疑“这是不是在降级交付”。

## 必须写清的字段

```text
original_goal:
why_unavailable:
missing_requirement:
fallback_option:
fallback_loss:
user_approval_required:
status:
```

## 状态规则

| 实际结果 | 正确状态 | 不能写成 |
| --- | --- | --- |
| 内部诊断、probe、技术预览 | internal_diagnostic_only | completed |
| 候选路线、候选事实、候选模板 | candidate / pending_decision | Decision |
| 本地生成但未 push/readback | local_only / sync_pending | formal_synced |
| Project 包本地存在 | package_generated | user_uploaded_to_project_ui |
| 用户或专业主体未复审 | human_review_pending | accepted |
| 外部动作未授权 | blocked_missing_authorization | executed |

## 判断流程

1. 回到 original_goal。
2. 对照 Done When 和 Acceptance。
3. 写出为什么不可达，以及缺什么。
4. 如果有 fallback，说明 fallback_loss。
5. 判断是否需要用户批准。
6. 未批准前状态只能是 blocked、continue、partial、candidate 或 internal_diagnostic_only。

## 医疗项目现实示例

如果目标是“获得医院书面合作意向”，但本轮只整理了公开医院介绍，那么 fallback 是“候选供应侧资料表”，fallback_loss 是没有合作意向、没有报价、没有 SLA、没有外联授权。状态只能是 Research / Fact candidate，不是供应商确认。

## 常见误用 / 反例

- 达不到外联目标，就把公开资料表写成合作完成。
- 没有用户上传 Project，就说 Project 同步完成。
- 没有专业复核，就说医疗合规边界已确认。
- 用户要求语义完整，交付短摘要并说“结构已齐”。

## 可执行模板

```text
no_degrade_completion:
  original_goal:
  achieved:
  why_unavailable:
  missing_requirement:
  fallback_option:
  fallback_loss:
  user_approval_required:
  current_status:
  next_safe_action:
```
