"""
用途：
暴露 Phase 3 的工作流入口。

上游：
测试、CLI 和未来接口层从这里导入 inbound workflow。

下游：
`core.py` 提供具体编排逻辑。

边界：
工作流层只编排现有服务，不直接实现医疗判断或外部副作用。
"""

from medical_tourism_os.workflows.core import InboundWorkflow

__all__ = ["InboundWorkflow"]
