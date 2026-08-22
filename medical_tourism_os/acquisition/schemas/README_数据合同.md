# Acquisition Plugin 数据合同

## 对象分离

`BusinessEntity` / `Prospect` / `ContactPoint` / `OutreachDraft` 只服务 B2B 合作获客。它们不导入 `AnonymousLead` / `LeadScorer`，也没有 patient、consent 或 intent 字段。

## Adapter 状态

第一版的 `MockDirectoryProvider` 与 `MockEmailProvider` 固定返回：

- `dry_run = true`
- `executed = false`
- 目录状态：`mock_directory_only`
- 邮件状态：`mock_email_not_sent`

这里的 `executed` 专指真实外部 Provider 动作；本地生成 fixture 或结果对象不算真实执行。

## 公开联系方式

`ContactPoint.value_reference` 只能保存 `public_contact_ref_` 加 32 位 hex token 的引用，不能保存原始邮箱或电话，也不能通过给号码加前缀绕过。`verified_at` 为空表示尚未人工核验。

`ProspectDiscoveryResult.contact_results_by_entity` 保留每次 Contact Extractor 的完整 `dry_run`、`executed`、`status` 和 contacts，避免 Workflow 吞掉外部边界审计状态。`ContactExtractionResult` 还会在运行时确认 contacts 全部是 `ContactPoint`，不能用原始字符串绕过类型提示。

## 回复与反馈

Reply Intake 只保存 `reply_ref_*`，不保存邮件正文。除 `no_response_observed` 外，Feedback 必须建立在 send queue 和已记录 Reply Intake 之后，且 evidence refs 必须引用该 Prospect 的 reply reference；它不会自动修改 Prospect 分数、业务事实或正式决策。
