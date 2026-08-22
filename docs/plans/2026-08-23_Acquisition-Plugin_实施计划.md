# Acquisition Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在医疗旅游业务层建立独立、离线、Mock-only 的 Business Prospect 获客插件。

**Architecture:** 使用纯 Python dataclass/Enum/Protocol 分隔 domain、schemas、interfaces、services、workflows 和 adapters；所有外部边界返回显式 `dry_run/executed`。插件不修改 General AI Core，也不复用 Consumer Lead 或 LeadScorer。

**Tech Stack:** Python 3.9 标准库、`dataclasses`、`enum`、`typing.Protocol`、`unittest`、JSON manifest。

---

### Task 1: 锁定 Acquisition 数据合同

**Files:**
- Create: `tests/test_acquisition_plugin.py`
- Create: `medical_tourism_os/acquisition/domain/models.py`
- Create: `medical_tourism_os/acquisition/schemas/contracts.py`

1. 先写领域对象、评分维度和 Adapter 结果的失败测试。
2. 运行：`PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_acquisition_plugin -v`；预期因模块缺失失败。
3. 实现最小 immutable dataclass、enum 和输入校验。
4. 重跑目标测试；预期通过本任务用例。

### Task 2: 实现接口、分类与评分

**Files:**
- Create: `medical_tourism_os/acquisition/interfaces/providers.py`
- Create: `medical_tourism_os/acquisition/services/core.py`
- Modify: `tests/test_acquisition_plugin.py`

1. 先写 `DirectoryProvider` / `ContactExtractor` / `EmailProvider` 合同及分类、五维评分测试。
2. 运行目标测试并确认失败原因是实现缺失。
3. 实现 Protocol、`BusinessClassifier` 和 `ProspectScorer`。
4. 重跑并确认分数、priority、reason_codes、queue status 均通过。

### Task 3: 实现草稿和 Mock Adapter

**Files:**
- Create: `medical_tourism_os/acquisition/adapters/mock.py`
- Modify: `medical_tourism_os/acquisition/services/core.py`
- Modify: `tests/test_acquisition_plugin.py`

1. 先写 OutreachDraft 内容和 Mock 零外部动作测试。
2. 运行目标测试并确认 RED。
3. 实现 `OutreachGenerator`、`MockDirectoryProvider`、`MockEmailProvider`。
4. 重跑并断言两个 Adapter 均为 `dry_run=true/executed=false`。

### Task 4: 实现两个 Workflow 与 Plugin Manifest

**Files:**
- Create: `medical_tourism_os/acquisition/workflows/discovery.py`
- Create: `medical_tourism_os/acquisition/workflows/outreach.py`
- Create: `medical_tourism_os/acquisition/plugin.json`
- Create/Modify: 各层 `__init__.py`
- Modify: `tests/test_acquisition_plugin.py`

1. 先写 discovery、具名人工复核、发送队列、回复引用与反馈测试。
2. 运行目标测试并确认 RED。
3. 实现最小 workflow 状态机和 manifest-only plugin descriptor。
4. 重跑并确认未审核发送被阻断、审核后仍只 dry-run。

### Task 5: 全量验证与收尾

**Files:**
- Verify: `general_ai_business_os/**/*.py`
- Verify: `medical_tourism_os/services/business_core.py`
- Verify: `tests/`

1. 运行目标测试：`PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest tests.test_acquisition_plugin -v`。
2. 运行全量测试：`PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -v`。
3. 运行编译：`PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m compileall -q general_ai_business_os medical_tourism_os tests`。
4. 运行 `git diff --check`、Core 业务语义扫描、真实 API/网络/secret 扫描和 `git status`。
5. 只暂存本轮路径，按 Lore protocol 提交、push `main`，并回读 `origin/main`。
