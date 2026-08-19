"""
用途：
把内部事实库中的 canonical fact 安全导出为对外可用的最小字段集。

上游：
数据治理服务和未来 GitHub dry-run 读取这里过滤后的事实。

下游：
返回适合 JSON/报告使用的字典列表。

边界：
这里只输出已人工批准的 canonical fact，不泄露 source、provenance 等内部治理字段。
"""

from __future__ import annotations

from typing import Iterable, List, Dict, Any

from medical_tourism_os.domain.entities import FactClassification, FactRecord, ReviewStatus


def export_canonical_facts(records: Iterable[FactRecord]) -> List[Dict[str, Any]]:
    """
    作用：
    导出已批准 canonical fact 的最小安全视图。

    输入：
    任意事实记录集合。

    输出：
    仅含非敏感、非内部治理字段的字典列表。

    关键边界：
    候选、研究、假设、决策候选都不能被导出；否则外部消费者会误把未确认内容当正式事实。
    """

    exported = []
    for record in records:
        if record.classification != FactClassification.CANONICAL_FACT:
            continue
        if record.review_status != ReviewStatus.APPROVED:
            continue
        exported.append(
            {
                "id": record.id,
                "claim": record.claim,
                "source_date": record.source_date,
                "scope": record.scope,
                "classification": record.classification.value,
                "confidence": record.confidence,
                "freshness": record.freshness,
                "conflict_status": record.conflict_status,
                "review_status": record.review_status.value,
                "updated_at": record.updated_at,
            }
        )
    return exported

