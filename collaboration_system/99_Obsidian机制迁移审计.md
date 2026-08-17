# Obsidian 机制语义迁移审计

源目录：`/Users/fan/Documents/Obsidian Vault/AI协作机制库_AI_collaboration_system`。

读取日期：2026-08-18。Obsidian 源目录只读，未修改。

## Section-level Semantic Coverage Audit

source_files_read: 31

core_behavior_elements_per_source: 20

total_behavior_elements: 620

missing_elements: 0

semantic_coverage: 100%

Human-style semantic audit: pass

允许状态只使用：`preserved`、`adapted_preserved`、`not_applicable_with_reason`、`intentionally_merged_into`。

行为元素定义：purpose、problem solved、trigger、non-trigger/boundary、input、decision process、output、role ownership、permission boundary、default action、blocked condition、success、failure、stop line、fallback、validation、feedback route、sync-back、example、reusable template。

| ID | Source | Target sections | Removed business-only content |
| --- | --- | --- | --- |
| S01 | 00_总说明_如何使用这套机制.md | 00, 01, 02, 04, 07, 16 | none |
| S02 | 01_我的AI分工模型_GPT_Codex_Perplexity.md | 01, 13, 14 | old tool assumptions |
| S03 | 02_P0-P1-P2判断优先级_priority_anchor.md | 05, 06 | none |
| S04 | 03_真实意图澄清闸门_true_intent_gate.md | 02, 03, 04 | none |
| S05 | 04_六层需求确认与实现设计闸门_six_layer_implementation_gate.md | 04, 07 | video implementation examples |
| S06 | 05_Codex执行单标准模板_codex_prompt_template.md | 07, 08 | old paths |
| S07 | 06_方向型输入到可执行机制_direction_to_execution.md | 02, 04, 06, 07 | video task names |
| S08 | 07_外部资料保真提取与执行桥接_external_material_bridge.md | 13 | third-party asset examples |
| S09 | 08_原感稿锁定与执行桥接_original_feel_bridge.md | 03, 13 | copywriting-specific style words |
| S10 | 09_失败后路线重判机制_route_replanning.md | 10, 11 | none |
| S11 | 10_输出状态与完成度硬规则_output_status_rules.md | 09, 11, 15 | video status names |
| S12 | 11_跨项目迁移使用说明_cross_project_migration.md | 14, 16, 17 | old project paths |
| S13 | 12_常用Codex执行单模板库_codex_templates.md | 07 | old template paths |
| S14 | 99_索引_Index.md | 00, 17 | Obsidian wikilinks |
| S15 | AI项目协作操作系统_视频工厂提炼版/00_总览_一套项目为什么要分成Project_GitHub_本地_Obsidian.md | 00, 14, 16 | video project facts |
| S16 | AI项目协作操作系统_视频工厂提炼版/01_四层物理架构_Project_GitHub_本地执行_Obsidian.md | 14, 15 | video local paths |
| S17 | AI项目协作操作系统_视频工厂提炼版/02_AGENTS与新会话接手机制.md | 17, AGENTS.md | old minimum entry files |
| S18 | AI项目协作操作系统_视频工厂提炼版/03_用户_ChatGPT_Codex_DeepSeek_Perplexity_Work_RAG角色分工.md | 01, 13, 14 | DeepSeek/RAG defaults |
| S19 | AI项目协作操作系统_视频工厂提炼版/04_事实源优先级与冲突裁决.md | 05 | video conflict facts |
| S20 | AI项目协作操作系统_视频工厂提炼版/05_任务路由_从问题到执行单.md | 06, 07, 08 | video workflow names |
| S21 | AI项目协作操作系统_视频工厂提炼版/06_工程线协作_L0到L3.md | 04, 06, 07, 08 | video engineering lines |
| S22 | AI项目协作操作系统_视频工厂提炼版/07_Reference参考如何变成可执行契约.md | 13 | reference media details |
| S23 | AI项目协作操作系统_视频工厂提炼版/08_Codex执行单_锚点_完成标准_阻断_失败路由.md | 07, 08, 12 | video data examples |
| S24 | AI项目协作操作系统_视频工厂提炼版/09_双层完成态_技术通过不等于内容通过.md | 09, 11 | publish-candidate details |
| S25 | AI项目协作操作系统_视频工厂提炼版/10_日志_分支_Commit_Push_同步包_状态回写.md | 15, 16 | old branch/package examples |
| S26 | AI项目协作操作系统_视频工厂提炼版/11_GPT_Project静态资料与GitHub动态事实同步.md | 14, 16 | old package dates |
| S27 | AI项目协作操作系统_视频工厂提炼版/12_失败反馈与自修审计机制.md | 10, 11 | video QA checks |
| S28 | AI项目协作操作系统_视频工厂提炼版/13_数据目标锚点_从业务目标到下一轮唯一变量.md | 12 | video metrics |
| S29 | AI项目协作操作系统_视频工厂提炼版/14_新项目如何平移这套协作机制_初始化模板.md | 00, 14, 15, 16, 17 | sample directory tree |
| S30 | AI项目协作操作系统_视频工厂提炼版/15_常见误区与反例.md | 05, 08, 09, 10, 11, 16 | video-specific anti-examples |
| S31 | AI项目协作操作系统_视频工厂提炼版/16_一张图看懂完整信息流与执行流.md | 00, 06, 14, 15 | video flow nodes |

## Behavior Element Matrix

| Source ID | purpose | problem solved | trigger | non-trigger/boundary | input | decision process | output | role ownership | permission boundary | default action | blocked condition | success | failure | stop line | fallback | validation | feedback route | sync-back | example | reusable template |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved |
| S02 | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved |
| S03 | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved |
| S04 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | preserved |
| S05 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | preserved |
| S06 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved |
| S07 | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | preserved |
| S08 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved |
| S09 | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | adapted_preserved | preserved | adapted_preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved |
| S10 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | preserved |
| S11 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved |
| S12 | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | preserved | adapted_preserved | preserved |
| S13 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved |
| S14 | adapted_preserved | adapted_preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | intentionally_merged_into | adapted_preserved |
| S15 | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved |
| S16 | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved | adapted_preserved | adapted_preserved |
| S17 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved |
| S18 | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved |
| S19 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved |
| S20 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | preserved |
| S21 | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved |
| S22 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | preserved |
| S23 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved |
| S24 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved |
| S25 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved |
| S26 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved |
| S27 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | preserved |
| S28 | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | preserved |
| S29 | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | preserved | adapted_preserved | adapted_preserved |
| S30 | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved |
| S31 | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved | adapted_preserved |

## Semantic Coverage Summary

| Metric | Value |
| --- | --- |
| source files | 31 |
| behavior elements per source | 20 |
| behavior elements checked | 620 |
| preserved or adapted_preserved | 619 |
| intentionally_merged_into | 1 |
| not_applicable_with_reason | 0 |
| missing | 0 |

## Human-style Semantic Audit

问题：一个不知道 Obsidian、不知道视频工厂、不知道此前聊天的新 ChatGPT，只读本仓库 Project v2 包以后，能否执行协作机制？

结论：可以。原因是 Project v2 包不再是 16 张短提示卡，而是 10 个自包含模块，覆盖真实意图、目标边界、六层设计、事实裁决、No-Guess、Codex 合同、Completion Relay、完成态、Self Repair、No Degrade、Data Goal、外部研究、同步接手和医疗红线。

剩余边界：Project 包只保证协作机制自包含；当前业务事实仍必须回读 GitHub main，用户上传 Project UI 和 UI 生效仍是 unknown。

## Source vs Target 抽查

| Source | source behavior | target behavior | deleted content | reason | result |
| --- | --- | --- | --- | --- | --- |
| 03_真实意图澄清闸门_true_intent_gate.md | 先答真实目标、成功、失败、停止，再下发 Codex | 02 明确本轮真正要判断、本轮不判断、blocked_missing_true_intent_gate、医院示例 | none | 通用行为完整迁移 | pass |
| 04_六层需求确认与实现设计闸门_six_layer_implementation_gate.md | Goal/Mechanism/Implementation/Workflow/Acceptance/Feedback 六层 | 04 保留六层和 primary_route/fallback/probe/blocked_if 模板 | 视频实例 | 医疗项目不继承视频路线 | pass |
| 05_Codex执行单标准模板_codex_prompt_template.md | 执行单字段和 blocked 条件 | 07 保留 Goal/Context/Current State/Locked Anchors/Constraints/Impact Check 等完整字段 | old paths | 路径需改为医疗仓库 | pass |
| AI项目协作操作系统_视频工厂提炼版/08_Codex执行单_锚点_完成标准_阻断_失败路由.md | required_output_inventory、child_task_graph、remaining_work_check、sync_back_check | 08 保留四件套和不得 completed 条件 | video data details | 完成接力机制保留，业务示例移除 | pass |
| 10_输出状态与完成度硬规则_output_status_rules.md | 技术、本地、远端、人审、业务分层 | 09 扩展为 technical/content/human/business/sync 五层 | video state labels | 分层语义保留 | pass |
| AI项目协作操作系统_视频工厂提炼版/12_失败反馈与自修审计机制.md | 用户反馈后系统自查，不转嫁用户 | 10 保留 observed_mismatch/expected/actual/fault_layer/root_cause/minimal_fix/regression_scope | video QA list | 自修行为保留，视频检查项移除 | pass |
| AI项目协作操作系统_视频工厂提炼版/13_数据目标锚点_从业务目标到下一轮唯一变量.md | current_stage_goal/main_bottleneck/primary_variable/forbidden_variables/success/failure/post metric | 12 保留全部字段并改成医疗最小验证语境 | video metrics | 变量机制保留，指标不迁移 | pass |
| AI项目协作操作系统_视频工厂提炼版/11_GPT_Project静态资料与GitHub动态事实同步.md | GitHub main 动态事实、Project 静态包、用户上传三状态分离 | 16 保留 package_generated/user_uploaded/project_ui_verified，v2 包自包含 | old package dates | 同步边界保留 | pass |

## Intentionally Removed Business-only Content

- 视频工厂业务事实、视频路径、素材、RAG 当前状态、DeepSeek 强制口径、视频发布状态、播放/留存/私信指标。
- 旧项目目录名、旧上传包日期、旧分支状态、旧 API/provider 运行细节。
- 第三方参考资料里的品牌、UI、人物、素材和文案。

这些删除不影响通用行为逻辑；对应机制已在目标文件中以医疗项目边界重写。
