"""
用途：
暴露应用服务层模块，包括数据治理、风险路由与业务核心候选服务。

上游：
CLI、Local API、测试和工作流通过这里导入具体服务。

下游：
服务层编排仓库、导入管线与审计，不直接暴露 SQL。

边界：
这里只作为应用服务命名空间，不持有全局状态。
"""

from medical_tourism_os.services.business_core import (
    DemandRadar,
    HumanReviewCoordinator,
    LeadScorer,
    ProductCatalog,
    ProductMatcher,
    build_anonymous_lead,
)
from medical_tourism_os.services.content_interaction import (
    CommentIntake,
    ContentFactory,
    ContentIntelligence,
    DirectMessageIntake,
    PublishingQueue,
)
from medical_tourism_os.services.data_governance import DataGovernanceService, ReviewGateError
from medical_tourism_os.services.risk_router import RiskRouter

__all__ = [
    "CommentIntake",
    "ContentFactory",
    "ContentIntelligence",
    "DataGovernanceService",
    "DemandRadar",
    "DirectMessageIntake",
    "HumanReviewCoordinator",
    "LeadScorer",
    "ProductCatalog",
    "ProductMatcher",
    "PublishingQueue",
    "ReviewGateError",
    "RiskRouter",
    "build_anonymous_lead",
]
