# 上传说明

本目录是成都国际医疗旅游项目的 ChatGPT Project 协作机制同步包 v2。

它替换上一版语义不完整的短摘要包。上一版已标记为 `DEPRECATED_SEMANTICALLY_INCOMPLETE_DO_NOT_UPLOAD`，不要上传。

## 上传范围

将本目录下 10 个机制文件上传到 ChatGPT Project。`01_Project总控指令_PROJECT_INSTRUCTIONS.md` 的正文可粘贴进 Project Instructions；其余文件作为 Project 资料上传。

## 文件清单

| 文件 | 负责机制 |
| --- | --- |
| 01_Project总控指令_PROJECT_INSTRUCTIONS.md | Project 启动行为、读取路由、状态边界 |
| 02_用户_ChatGPT_Codex完整协作协议.md | 用户、ChatGPT、Codex、外部研究和专业主体权力链 |
| 03_判断系统_真实意图_目标_边界_验收_停止线.md | 真实意图、目标合同、验收和停止线 |
| 04_Implementation_Design_任务路由_No_Guess.md | 六层需求、Implementation Design、State Action Router、No-Guess |
| 05_Codex执行合同_Completion_Relay_完成态.md | Codex 执行单、Completion Relay、五层完成态 |
| 06_失败反馈_Self_Repair_No_Degrade.md | 用户负反馈、自修审计、禁止降级完成 |
| 07_Data_Goal_Anchor_现实验证与反馈.md | 单主变量、现实反馈、验证指标 |
| 08_外部资料_Perplexity_事实裁决_Reference桥接.md | 外部研究、来源、事实分类、参考契约 |
| 09_Project_GitHub_本地_Obsidian_同步与接手.md | 四层分工、新会话、Git/日志/Project 同步 |
| 10_医疗项目特殊协作与安全边界.md | 医疗、隐私、外部动作、专业责任红线 |

## 重要边界

本包只保存协作机制，不保存当前业务事实。当前市场、产品、价格、客户、渠道、商业模型、供应商、Go/No-Go、验证顺序和 latest 状态都必须回读 GitHub main。

本地包存在只说明 `package_generated=true`。用户是否已上传到 Project UI、Project UI 是否可用，必须单独确认。

## 使用方式

复杂任务先读 `03` 和 `04`。Codex 执行前读 `05`。用户反馈不对读 `06`。外部研究读 `08`。同步、接手或当前状态冲突读 `09`。医疗、隐私、外部动作读 `10`。
