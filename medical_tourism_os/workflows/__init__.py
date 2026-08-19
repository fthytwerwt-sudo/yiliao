"""
用途：
暴露 workflow 包的最小稳定入口。

上游：
现有 Phase 3 模块通过 `medical_tourism_os.workflows.core` 访问 inbound workflow。

下游：
更高阶段的 workflow 直接从各自模块导入，避免包初始化时出现循环依赖。

边界：
这里保持轻量，不在包初始化阶段触发更深层的 service / workflow 互相加载。
"""

from medical_tourism_os.workflows.core import InboundWorkflow

__all__ = ["InboundWorkflow"]
