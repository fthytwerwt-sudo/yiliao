# General AI Agent Operating System V1 架构图

```text
Application Plugins（业务插件：未来 medical_tourism 等）
                         |
AI Capability Layer（Research / Content / Lead / Sales / CRM / Data / Evaluation）
                         |
Core Infrastructure（general_ai_business_os）
 Model Gateway | Agent Runtime | Workflow | Tool Registry
 Memory/Context | Permission/Audit | Secret references | System Config
                         |
External Adapters（Provider/Search/CRM/Social/Email/Crawler）
                         |
                 default: Mock / disabled
```

Core 不保存市场、客户、产品、价格、医院、渠道或业务事实。业务配置只可由 Plugin 注入；真实 Adapter 仍需独立权限、密钥 reference 和人工闸门。
