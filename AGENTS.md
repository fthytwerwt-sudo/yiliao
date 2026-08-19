# 成都国际医疗旅游项目：接手与执行契约

## 项目身份

这是一个处于 strategy_definition_pending 的项目。项目已有研究资料，但业务方向、市场、客户、MVP、商业模式、价格、最小闭环、验证顺序、Go/No-Go 尚未由用户与 ChatGPT 正式锁定。

协作机制的 canonical source 是 `collaboration_system/`。ChatGPT Project 使用版必须来自语义完整包 `dist/gpt_project_sync_packages/2026-08-18_medical_project_collaboration_os_v2/`；旧短摘要包已废弃，不得上传或作为执行依据。

GitHub main 是唯一的动态项目事实源。ChatGPT Project 是长期协作机制层；本地是执行现场；Obsidian 是跨项目机制来源。

## 新会话读取顺序

1. AGENTS.md。
2. collaboration_system/00_总览_用户到现实反馈的完整闭环.md。
3. project_facts/00_项目身份.md、01_当前已确认事实.md、02_当前状态_project_state.yaml、03_当前未决策事项.md。
4. logs/latest.md 与 logs/current_target.md。
5. 当前任务对应的 collaboration_system、research_baselines 或 candidate_playbooks 文件。

## 权限

用户决定目标、红线、预算、外部动作、战略和最终验收。ChatGPT 负责真实意图、事实裁决、选项比较、Implementation Design、执行单和复审。Codex 负责读取、结构化、写入、验证、记录和 Git 收尾。

Codex 不得自行决定首发国家、首发用户、MVP、商业模式、定价、是否 Go、验证顺序、Supply First/Demand First、是否扩大投入、是否联系客户/机构或是否发布。未锁定时输出 blocked_strategy_not_locked。

## 事实与研究

project_facts 只保存已确认事实、状态、未决策事项与带 provenance 的正式决策。research_baselines 保存两份报告的版本关系和研究候选。研究输入、外部资料、Project 静态包、聊天记忆和历史归档不能自动改变 current facts。

## Canonical 来源

- 协作机制：collaboration_system/。
- 执行入口：collaboration_system/07_Codex执行单与执行器权限边界.md。
- Project 协作机制包：dist/gpt_project_sync_packages/2026-08-18_medical_project_collaboration_os_v2/。
- 项目事实：project_facts/01_当前已确认事实.md。
- 当前状态：project_facts/02_当前状态_project_state.yaml。
- 未决策事项：project_facts/03_当前未决策事项.md。
- 最新日志：logs/latest.md。
- 研究基线：research_baselines/。

execution_rules 与 references 仅保留兼容入口，不再独立定义机制或事实。

## 外部动作与安全

external_execution_allowed: false。未经用户明确授权，不发送、联系、投放、收款、签约、发布或创建患者记录。不得在仓库、Project 静态包、聊天或日志保存患者/健康/个人资料、密钥、Token、私人授权或未经确认可公开的材料。

医疗、法律、数据、旅行、支付等专业责任见 collaboration_system/18_医疗项目特殊安全与专业责任边界.md。项目方与 AI 不提供诊断、治疗决定、疗效承诺或法律结论。

## 文件命名中英双语规则

以后新建的、由用户需要理解或长期维护的项目文件、目录、文档、配置说明、报告、执行单、数据表定义文件等，默认采用 `English（英文原词） + 中文说明` 的双语命名方式。

目标是让用户仅看文件名或目录名，就知道“这是什么、干什么”。推荐优先采用 `English_中文` 格式，并与现有仓库风格保持一致；不得把代码关键字或工具强制要求的固定文件名翻译掉。

对于生态或工具规定的固定技术文件名，例如 `README.md`、`pyproject.toml`、`package.json`、`.gitignore`、`Dockerfile`、`__init__.py`、框架要求的固定路径或文件名，保持原名，不强行双语重命名。

对于 Python 模块、包、导入路径、API route（接口路由）、数据库 migration（数据库迁移）等会影响代码运行的技术文件名，如果双语或中文会破坏兼容性，则保留合法英文技术名，但必须在同级 README、文件头说明或索引中补充中文用途说明。

不允许为了满足命名规则而破坏 import（导入）、build（构建）、CI（持续集成）、部署、平台约束或第三方工具兼容性。修改旧文件时不要求一次性全仓重命名；只对本轮新增或明确要求调整的文件执行，避免无关的大面积 rename（重命名）。

核心原则：`用户可读性优先，但不得破坏工程兼容性。`

## 代码可审查性与中文注释规则

### 1. 目标

当前用户不是专业程序员。

以后新增或修改代码时，必须保证用户无需逐行理解代码语法，也能快速判断：

- 这个文件是干什么的。
- 这个函数 / 类解决什么问题。
- 输入是什么。
- 输出是什么。
- 最关键的判断逻辑在哪里。
- 为什么采用这条逻辑。
- 什么情况下会 `Blocked（阻断）` / `fail（失败）` / `downgrade（降级）`。
- 哪些地方修改后可能影响其他链路。

注释的目标是“方便审查”，不是“逐行教学”。

### 2. 禁止逐行无意义注释

禁止出现类似：

```python
count += 1  # count 加 1
```

```python
if value is None:  # 如果 value 是空
```

```python
return result  # 返回结果
```

这类注释只是把代码翻译成中文，没有增加判断价值。

默认不要求每一行代码都加注释。

### 3. 必须备注的层级

#### A. 文件级说明

每个核心代码文件开头，必须用简短中文说明：

- 这个文件负责什么。
- 它处于哪条项目链路。
- 上游输入来自哪里。
- 下游输出给谁。
- 它不负责什么。

示例：

```python
"""
用途：
把 content_experiment（内容实验）转换成 generation_spec（统一生成规格）。

上游：
商品事实包、市场研究快照、实验假设。

下游：
generation_spec_compiler（生成规格编译器）。

边界：
这里只生成结构化规格，不调用图片 / 视频 API，也不负责真实发布。
"""
```

#### B. 函数 / 类级说明

只要函数承担真实业务逻辑、状态转换、数据处理或外部调用，必须说明：

- 作用。
- 主要输入。
- 主要输出。
- 关键边界。

简单 `helper（辅助函数）` 不要求机械补长注释。

示例：

```python
def build_generation_spec(experiment):
    """
    作用：
    把已经验证过的 content_experiment（内容实验）转成唯一正式生产订单。

    输入：
    experiment：已通过事实与实验规则校验的内容实验。

    输出：
    generation_spec（统一生成规格）：后续 Prompt、图片、TTS、视频都只能读取它。

    关键边界：
    缺商品事实或实验主指标时不得继续生成。
    """
```

#### C. 关键逻辑块说明

以下位置必须在代码上方写中文备注：

- 业务规则判断。
- 风险阻断。
- 状态转换。
- `fallback（降级替代）`。
- `retry（失败重试）`。
- 数据来源判断。
- 第三方估算 / 官方事实区分。
- 实验变量判断。
- 多平台数据映射。
- 外部 API 调用。
- 不直观的算法 / 正则 / 数据转换。
- 容易被未来维护者误删的逻辑。

注释重点解释：

**为什么这样判断。**

不要只描述：

**代码正在做什么。**

示例：

```python
# 这里必须保留原始平台指标名。
# 原因：Instagram / TikTok 的指标定义可能变化，
# canonical_metric（内部统一指标）只用于内部统一分析，不能覆盖原始事实。
raw_metric_name = record["metric_name"]
canonical_metric = map_metric(raw_metric_name)
```

### 4. 复杂条件必须解释业务含义

出现复杂 `if / elif`、多层状态判断、多个条件组合时，必须在代码前说明这段判断对应的真实业务规则。

示例：

```python
# 只有同时满足：
# 1. 有真实 publication_id（平台内容 ID）
# 2. 有明确 observation_window（观察窗口）
# 3. 数据来源属于第一方账号
# 才允许把这条数据升级为真实发布表现。
if publication_id and observation_window and source_type == "account_first_party":
    ...
```

### 5. 关键字段首次出现必须补中文语义

技术字段本体保持英文。

首次在核心逻辑中使用、且字段语义不直观时，必须补简短中文说明。

例如：

```python
# fact_refs（事实引用）：当前公开内容允许引用的商品事实证据 ID。
fact_refs = spec["fact_refs"]

# change_variable（变化变量）：本轮实验唯一允许变化的主要内容变量。
change_variable = experiment["change_variable"]
```

无需在同一文件后面每次重复解释。

### 6. 外部 API / 模型调用必须说明

任何下列服务的调用附近必须说明：

- TikTok。
- Instagram。
- Amazon。
- DeepSeek。
- 阿里云。
- Kling。
- TTS。
- 图片模型。
- 视频模型。
- 第三方数据服务。

说明内容必须包含：

- 调什么。
- 为什么调。
- 输入来源。
- 返回值用于哪里。
- 失败后怎么办。
- 是否产生费用 / 外部副作用。

### 7. 修改旧代码时的注释规则

不要求为了本规则一次性给整个旧仓库补满注释。

以后修改某个文件时：

- 本轮修改涉及的核心逻辑必须达到本规则。
- 如果修改触碰到附近明显难理解的关键逻辑，应顺手补最小必要注释。
- 不允许借“补注释”大面积重写与当前任务无关的代码。

### 8. 注释语言

默认：中文理解优先。

英文函数名、变量名、字段名、API 名、模型名、技术原词保持原样。

首次出现时使用：

`英文原词 + 中文解释`

例如：

`generation_spec（统一生成规格）`

`provenance（数据来源证明）`

`human_override（人工覆盖记录）`

### 9. 完成标准

代码提交前必须检查：

用户只看：

- 文件头说明。
- 函数说明。
- 关键逻辑块注释。

能否大致知道：

“这段代码在系统里干什么、为什么这么做、改错会影响哪里。”

如果只能逐行读 Python 才能理解核心逻辑，则本轮代码可审查性不合格。

## Git 收尾

只暂存明确路径；验证后使用 Lore commit；push main 并回读 origin/main。commit、push、远端 readback 与用户/专业/业务验收必须分开报告。
