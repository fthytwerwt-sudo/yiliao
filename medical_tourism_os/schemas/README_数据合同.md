# Phase 1 数据合同说明

## 作用

这份文档描述 `medical_tourism_os` 在 Phase 1 暴露的最小结构化数据合同，供后续导入、服务、接口和人工复核流程复用。

## 事实记录 `FactRecord`

字段：

- `id`：系统生成的稳定 ID，例如 `fact_<uuid>`。
- `claim`：待审事实文本。
- `source`：来源标识，例如 synthetic fixture URI。
- `source_date`：来源日期字符串。
- `scope`：记录适用范围说明。
- `classification`：当前分类，Phase 1 至少支持 `FACT_CANDIDATE` 与 `CANONICAL_FACT`。
- `confidence`：可信度描述；新候选默认 `unreviewed`。
- `freshness`：时效状态；新候选默认 `unknown`。
- `conflict_status`：冲突状态；新候选默认 `unchecked`。
- `review_status`：人工复核状态；新候选默认 `PENDING`。
- `reviewed_by`：人工复核人；未复核时为空。
- `created_at` / `updated_at`：UTC ISO 时间字符串。
- `provenance`：来源证明引用。

## 权限合同

- `SystemConfig.default()` 必须返回：
  - `external_execution_allowed = false`
  - `adapters_enabled = false`
  - `storage_backend = "sqlite"`

- `PermissionPolicy` 必须 deny-by-default：
  - 未开启外部执行时拒绝并返回 `external_execution_disabled`
  - 即使未来外部执行开启，仍需同时满足 adapter 已启用且未被风险模块阻断

## 审计合同

- 审计事件以 JSONL 逐行写入。
- 含有以下关键词的字段值必须脱敏：`patient`、`health`、`token`、`secret`、`payment`、`phi`、`clinical`、`medical`。
- 脱敏值统一写为 `[REDACTED]`。

## Adapter 合同

- `MockAdapter` 关闭时返回：
  - `dry_run = true`
  - `executed = false`
  - `reason = "adapter_disabled"`

- Phase 1 不允许真实外部副作用；即使启用 Mock，也只是本地 mock 完成态。
