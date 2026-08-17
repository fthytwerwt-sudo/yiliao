# 本地原始资料与工作区索引

用途：定位本机已验证存在的原始资料，不将原始资料复制进 Git。路径存在不等于其中每项事实已被外部独立复核。

最后路径核验：2026-08-17。

## 正式本地工作区

- 工作区：/Users/fan/Documents/医疗/yiliao
- 远端：https://github.com/fthytwerwt-sudo/yiliao.git
- 预期正式分支：main

## 基础市场报告

| 定位 | 本机路径 | SHA-256 | 文件规模 / 修改时间 | Git 处理 |
| --- | --- | --- | --- | --- |
| 早期研究 / 历史基线 | /Users/fan/Desktop/医疗/《成都国际医疗旅游项目市场调研报告.docx》 | 69b2bb67b9b00b7df86eca79a88590337fe12626a988ce2a7d6e56a0be5ccfd0 | 246752 bytes / 2026-08-09T00:58:17+0800 | 不提交 |
| 当前业务基线 v3 | /Users/fan/Desktop/医疗/《成都国际医疗旅游项目市场调研报告_v3.docx》 | 43e8a8e2011b89be72483d5633c497f7f909a1a16256ab653478a7af3074da21 | 116011 bytes / 2026-08-09T22:14:53+0800 | 不提交 |

版本裁决见 references/01_两份市场报告版本差异与裁决.md。两份 DOCX 的 XML 文字/表格结构可完整读取；本机 LibreOffice PNG 渲染发生大面积中文 glyph 缺失，不能将其当作原件视觉 QA 通过，需在 WPS/Word 等具备原字体的查看器中复核布局。任何路径、哈希或内容变化后，需重新核验并更新本索引。

## 只读协作机制来源

- 机制库根目录：/Users/fan/Documents/Obsidian Vault/AI协作机制库_AI_collaboration_system
- 本轮完整读取目录：/Users/fan/Documents/Obsidian Vault/AI协作机制库_AI_collaboration_system/AI项目协作操作系统_视频工厂提炼版
- 同时读取的索引/迁移规则：99_索引_Index.md、11_跨项目迁移使用说明_cross_project_migration.md、00_总说明_如何使用这套机制.md

本轮只迁移协作机制。不得从上述目录复制视频工厂的业务路径、指标、状态、素材、RAG/模型约定或完成结论。

## 不应记录在本索引或仓库中的内容

- 患者姓名、联系方式、健康信息、病历、支付详情、录音录像。
- API Key、Token、Cookie、登录凭据、私人授权书。
- 未获用户确认可公开的医院/旅行伙伴谈判材料。

若未来需要记录敏感操作，只在获授权的合规系统中保存最小必要信息；仓库内只保留匿名化的指标、状态和证据引用。
