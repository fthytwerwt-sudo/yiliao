# ADR-0001：Deep Immutable 深度不可变审计与记录合同

## Status

Accepted（2026-08-20）。

## Context

Phase 1 的四次独立审查逐步确认：字段 allowlist、闭集代码与顶层 `MappingProxyType` 都不足以保证审计安全。`AuditEvent.to_dict()` 的嵌套导出值、`StoredRecord.new()` 的浅拷贝、`StoredRecord.payload` 的公开可变 `dict`、以及直接构造含嵌套对象的 `AuditEvent`，都能把调用方植入的敏感字符串带入 SQLite。

这不是再补一个敏感关键词或正则能够解决的问题。根因是领域对象没有统一定义“创建后不可变、导出后不反向污染、序列化只读取内部安全快照”的结构合同。

## Decision Drivers

- 审计必须只保存最小、安全、可证明的操作证据。
- 领域记录需避免调用方持有的可变 JSON 别名在创建后污染持久化结果。
- Storage Port 保持业务无关，不能通过识别审计表来承担审计验证职责。
- Python 3.9 标准库为基础；不得为深拷贝/不可变性引入依赖。
- 未来 Business Config 仍必须在自己的入口校验，不能把 Storage 当通用敏感数据过滤器。

## Considered Options

### Option 1：统一深层不可变 JSON 领域合同（采用）

创建 `domain/immutability.py`：只接受 JSON 原子值、mapping 与 list/tuple；递归复制并冻结 mapping 为 `MappingProxyType`、sequence 为 tuple。提供 `to_mutable_json()`，每次导出新的递归普通 JSON 结构。

`AuditEvent` 和 `StoredRecord` 都在 `__post_init__` 使用该合同；它们的 `to_dict()` 只从内部冻结快照导出。审计字段闭集验证也移到 `AuditEvent` 的创建路径，确保 Logger 不是唯一安全入口。

### Option 2：继续在 AuditLogger 中修补过滤规则（拒绝）

它无法处理 return object、`to_dict()` 和 generic Storage 的别名传播；已经在三轮修复后反复证明不够。

### Option 3：让 SqliteStore 识别并清洗 AuditEvent（拒绝）

这会把领域安全策略耦合进通用 Storage，既不能保护内存中的对象，也使未来 PostgreSQL 实现重复业务/审计规则。

## Decision

采用 Option 1。新增通用、递归 JSON freeze/thaw 工具，并让：

1. `AuditEvent` 直接验证 action、outcome 和 details 的字段级闭集，然后把 details 深层冻结。
2. `StoredRecord` 在所有构造/回读路径上深层冻结 `payload`，不保留任何调用方容器引用。
3. 所有 `to_dict()` 返回深拷贝的 JSON-compatible 新对象；修改它们不会改变领域对象、后续 Storage 写入或已写入日志。
4. SQLite 只序列化 `StoredRecord.to_dict()` 的快照，而不是读取公开可变内部容器。

## Consequences

### Positive

- Audit 安全不变量可跨 Logger、return object、serialization 与 SQLite 生效。
- `StoredRecord` 的不可变承诺与运行时行为一致，避免通用领域对象出现意外 alias。
- 同一工具将可复用于未来已审核 Business Config 的不可变版本。

### Negative

- 调用者不能在创建后原地编辑记录；必须构造新领域对象。
- 仅支持 JSON-compatible payload；不支持任意 Python 对象、set 或自定义类。
- 需要为深层 mutation、导出 alias 与回读路径增加测试。

## Implementation Notes

- 执行前先添加失败测试：修改输入 payload、事件 details、导出 `to_dict`、record payload、嵌套 list/mapping，并检查 SQLite 回读。
- 字段级 audit allowlist 不放在 Logger 私有函数中，避免直接构造 `AuditEvent` 绕过验证。
- 不把这项技术安全更正写成商业、医疗、隐私合规或真实业务验证完成。

## Related Decisions

- `docs/plans/2026-08-20_General-AI-Business-Operating-System-V1_设计.md`：V1 的 audit allowlist 与 Storage Port 边界。
- `docs/reviews/phase-01-foundation-attempt-01-failed.md` 至 `attempt-04-failed.md`：触发此决定的独立审查证据。
