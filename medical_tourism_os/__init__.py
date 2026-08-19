"""
用途：
暴露战略无关医疗旅游运营系统的 Phase 1 公共入口。

上游：
CLI、测试与后续应用服务通过这里导入基础配置和领域对象。

下游：
domain、storage、permissions、audit、adapters 等子模块。

边界：
这里只做稳定导出，不承载业务战略、真实平台逻辑或外部副作用。
"""

from medical_tourism_os.config import SystemConfig
from medical_tourism_os.domain.entities import FactClassification, FactRecord, ReviewStatus

__all__ = [
    "FactClassification",
    "FactRecord",
    "ReviewStatus",
    "SystemConfig",
]

__version__ = "0.1.0"
