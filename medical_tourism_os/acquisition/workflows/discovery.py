"""
用途：
编排市场关键词、目录 Provider、企业分类、可选联系方式提取和独立 Prospect 评分。

上游：
本地测试或未来受控接口传入 market、keywords 和证据化五维评分。

下游：
输出 ProspectDiscoveryResult，供人工 review / outreach / hold 队列消费。

边界：
没有评分证据时自动使用全零维度并 hold；不调用 Consumer Lead，不推断真实合作概率。
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

from medical_tourism_os.acquisition.interfaces import ContactExtractor, DirectoryProvider
from medical_tourism_os.acquisition.schemas import (
    ContactExtractionResult,
    DirectorySearchResult,
    ProspectDiscoveryResult,
    ProspectScoreDimensions,
)
from medical_tourism_os.acquisition.services import BusinessClassifier, ProspectScorer


class ProspectDiscoveryWorkflow:
    """把企业发现、分类和 B2B 评分串成单一可测试流程。"""

    def __init__(
        self,
        *,
        directory_provider: DirectoryProvider,
        classifier: BusinessClassifier,
        scorer: ProspectScorer,
        contact_extractor: Optional[ContactExtractor] = None,
    ) -> None:
        if getattr(directory_provider, "mock_only", False) is not True:
            raise ValueError("mock_directory_provider_required")
        # V1 不配置真实网站 extractor；可选测试实现也必须显式声明 mock-only。
        if contact_extractor is not None and getattr(contact_extractor, "mock_only", False) is not True:
            raise ValueError("mock_contact_extractor_required")
        self.directory_provider = directory_provider
        self.classifier = classifier
        self.scorer = scorer
        self.contact_extractor = contact_extractor

    def run(
        self,
        *,
        market: str,
        keywords: Sequence[str],
        score_dimensions_by_entity: Optional[Mapping[str, ProspectScoreDimensions]] = None,
    ) -> ProspectDiscoveryResult:
        """
        运行一次发现流程并返回各阶段显式对象。

        关键边界：维度映射缺失不是自动猜分的理由；对应 Prospect 必须进入 hold。
        """

        directory_result = self.directory_provider.search(market=market, keywords=keywords)
        if (
            not isinstance(directory_result, DirectorySearchResult)
            or not directory_result.dry_run
            or directory_result.executed
        ):
            raise RuntimeError("external_directory_execution_forbidden")
        dimensions_by_entity = score_dimensions_by_entity or {}
        entities = []
        prospects = []
        contact_results_by_entity = {}
        for discovered in directory_result.entities:
            classified = self.classifier.classify(discovered)
            entities.append(classified)
            dimensions = dimensions_by_entity.get(classified.id, ProspectScoreDimensions.empty())
            prospects.append(self.scorer.score(classified.id, dimensions))
            if self.contact_extractor is not None:
                extraction = self.contact_extractor.extract(entity=classified)
                if (
                    not isinstance(extraction, ContactExtractionResult)
                    or not extraction.dry_run
                    or extraction.executed
                ):
                    raise RuntimeError("external_contact_extraction_forbidden")
                contact_results_by_entity[classified.id] = extraction
            else:
                contact_results_by_entity[classified.id] = ContactExtractionResult(
                    contacts=(),
                    dry_run=True,
                    executed=False,
                    status="contact_extractor_not_configured",
                )
        return ProspectDiscoveryResult(
            directory_result=directory_result,
            entities=tuple(entities),
            prospects=tuple(prospects),
            contact_results_by_entity=contact_results_by_entity,
        )
