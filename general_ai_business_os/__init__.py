"""
用途：
提供 General AI Business Operating System V1（通用 AI 商业运营系统）的中性根包。

上游：
CLI、本地 API、测试与未来业务配置包从这里进入通用能力层。

下游：
各领域 Agent、Storage Port、Adapter 与权限策略由子包实现。

边界：
这里不导入 `medical_tourism_os`，也不保存任何业务战略、客户、价格或平台事实。
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
