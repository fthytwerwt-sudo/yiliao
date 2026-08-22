"""
用途：
标识医疗旅游业务层的 Acquisition Plugin（获客插件）并暴露安全描述入口。

上游：
Application Plugin host 或人工审查工具可读取 plugin manifest 和 descriptor。

下游：
domain、interfaces、services、workflows、adapters 与 schemas 组成独立 B2B 获客纵向层。

边界：
这里不注册真实 Provider、不启动网络、不复用 Consumer Lead，也不修改 General AI Core。
"""

from __future__ import annotations

from typing import Dict


def plugin_descriptor() -> Dict[str, object]:
    """返回只描述 Mock 能力的本地 Plugin 信息，不执行任何获客或外部动作。"""

    return {
        "plugin_id": "ACQUISITION",
        "mode": "mock_only",
        "external_execution_allowed": False,
    }


__all__ = ["plugin_descriptor"]
