# Obsidian 机制迁移审计

源目录：/Users/fan/Documents/Obsidian Vault/AI协作机制库_AI_collaboration_system。

读取日期：2026-08-18。源文件总数：31。所有下列 Markdown 已完整读取；Obsidian 保持只读且未修改。

迁移状态仅使用 migrated、adapted、not_applicable_with_reason、superseded。落点是本仓库的 canonical 机制文件；不迁移任何视频、路径、媒体、模型、RAG 状态、业务指标或完成结论。

| Obsidian 源文件 | 是否完整读取 | 核心机制 | 医疗项目落点 | 迁移状态 | 未迁移原因 |
| --- | --- | --- | --- | --- | --- |
| 00_总说明_如何使用这套机制.md | yes | 先判断后执行、机制不含事实 | 00、01、02、04、07 | migrated | 不适用部分已抽象 |
| 01_我的AI分工模型_GPT_Codex_Perplexity.md | yes | 工具角色与权限 | 01、13、14 | adapted | 移除旧工具事实 |
| 02_P0-P1-P2判断优先级_priority_anchor.md | yes | P0/P1/P2 冲突优先级 | 05 | migrated | 无 |
| 03_真实意图澄清闸门_true_intent_gate.md | yes | 真实意图前置 | 02 | migrated | 无 |
| 04_六层需求确认与实现设计闸门_six_layer_implementation_gate.md | yes | 六层与设计闸门 | 04 | adapted | 移除视频实例 |
| 05_Codex执行单标准模板_codex_prompt_template.md | yes | Codex 任务合同 | 07 | adapted | 路径改为医疗项目 |
| 06_方向型输入到可执行机制_direction_to_execution.md | yes | 方向到执行契约 | 02、04、07 | adapted | 不保留旧任务类型 |
| 07_外部资料保真提取与执行桥接_external_material_bridge.md | yes | 外部资料保真与桥接 | 13 | adapted | 不复制第三方素材规则细节 |
| 08_原感稿锁定与执行桥接_original_feel_bridge.md | yes | 原话/原感与执行分层 | 03、13 | adapted | 泛化为用户输入保护 |
| 09_失败后路线重判机制_route_replanning.md | yes | 失败分层回退 | 10 | adapted | 无 |
| 10_输出状态与完成度硬规则_output_status_rules.md | yes | 状态词与完成边界 | 09、11、15 | adapted | 无 |
| 11_跨项目迁移使用说明_cross_project_migration.md | yes | 迁移机制不迁移事实 | 14、99 | adapted | 无 |
| 12_常用Codex执行单模板库_codex_templates.md | yes | 常用任务模板 | 07 | adapted | 仅保留通用字段 |
| 99_索引_Index.md | yes | 机制导航 | 00、17 | adapted | 不复制 Obsidian 链接 |
| AI项目协作操作系统_视频工厂提炼版/00_总览_一套项目为什么要分成Project_GitHub_本地_Obsidian.md | yes | 四层闭环 | 00、14 | adapted | 移除项目实例 |
| AI项目协作操作系统_视频工厂提炼版/01_四层物理架构_Project_GitHub_本地执行_Obsidian.md | yes | 信息物理分层 | 14 | adapted | 移除运行环境细节 |
| AI项目协作操作系统_视频工厂提炼版/02_AGENTS与新会话接手机制.md | yes | 接手顺序与入口 | 17、AGENTS.md | adapted | 移除旧路径 |
| AI项目协作操作系统_视频工厂提炼版/03_用户_ChatGPT_Codex_DeepSeek_Perplexity_Work_RAG角色分工.md | yes | 多角色分工 | 01、13、14 | adapted | 移除 DeepSeek/RAG 默认化 |
| AI项目协作操作系统_视频工厂提炼版/04_事实源优先级与冲突裁决.md | yes | 事实裁决 | 05 | adapted | 移除旧仓库实例 |
| AI项目协作操作系统_视频工厂提炼版/05_任务路由_从问题到执行单.md | yes | 路由、状态动作 | 06、07 | adapted | 移除业务流名称 |
| AI项目协作操作系统_视频工厂提炼版/06_工程线协作_L0到L3.md | yes | 分层执行与升级 | 04、07、08 | adapted | 移除视频工程阶段 |
| AI项目协作操作系统_视频工厂提炼版/07_Reference参考如何变成可执行契约.md | yes | Reference 契约 | 13 | adapted | 不复制参考内容 |
| AI项目协作操作系统_视频工厂提炼版/08_Codex执行单_锚点_完成标准_阻断_失败路由.md | yes | 锚点、阻断与收尾 | 03、07、08 | adapted | 无 |
| AI项目协作操作系统_视频工厂提炼版/09_双层完成态_技术通过不等于内容通过.md | yes | 多层完成态 | 09、11 | adapted | 扩展为五层 |
| AI项目协作操作系统_视频工厂提炼版/10_日志_分支_Commit_Push_同步包_状态回写.md | yes | 日志/Git/同步 | 15、16 | adapted | 移除旧分支状态 |
| AI项目协作操作系统_视频工厂提炼版/11_GPT_Project静态资料与GitHub动态事实同步.md | yes | Project 静态包边界 | 14、16 | adapted | 去除动态事实包 |
| AI项目协作操作系统_视频工厂提炼版/12_失败反馈与自修审计机制.md | yes | 自修审计 | 10 | adapted | 无 |
| AI项目协作操作系统_视频工厂提炼版/13_数据目标锚点_从业务目标到下一轮唯一变量.md | yes | 数据锚点与单变量 | 12 | adapted | 移除视频指标 |
| AI项目协作操作系统_视频工厂提炼版/14_新项目如何平移这套协作机制_初始化模板.md | yes | 新项目初始化 | 00、14、17、99 | adapted | 不复制旧目录 |
| AI项目协作操作系统_视频工厂提炼版/15_常见误区与反例.md | yes | 反例与反漂移 | 10、11 | adapted | 移除视频案例 |
| AI项目协作操作系统_视频工厂提炼版/16_一张图看懂完整信息流与执行流.md | yes | 完整信息/执行流 | 00、14、15 | adapted | 移除视频流程节点 |

迁移统计：migrated 3；adapted 28；not_applicable_with_reason 0；superseded 0。

验收：每个源文件都有读取记录、核心机制、医疗项目落点和明确迁移状态；源业务事实未被迁入。
