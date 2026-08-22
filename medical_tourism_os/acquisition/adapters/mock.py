"""
用途：
提供企业目录与邮件发送的 Mock Adapter，供离线 Workflow 和测试使用。

上游：
测试传入 synthetic BusinessEntity fixture；Outreach Workflow 传入已审草稿和 ContactPoint 引用。

下游：
返回显式 `dry_run=true`、`executed=false` 的 Provider 结果。

边界：
本文件不 import HTTP/SMTP SDK、不读取 API key、不访问网站、不发送邮件；
`executed` 专指现实外部执行，因此 Mock 永远为 false。
"""

from __future__ import annotations

from typing import Iterable, Sequence

from medical_tourism_os.acquisition.domain import BusinessEntity, ContactPoint, OutreachDraft
from medical_tourism_os.acquisition.schemas import DirectorySearchResult, EmailSendResult


class MockDirectoryProvider:
    """只在内存 synthetic fixtures 中过滤企业候选。"""

    mock_only = True

    def __init__(self, *, fixtures: Iterable[BusinessEntity] = ()) -> None:
        self._fixtures = tuple(fixtures)

    def search(self, *, market: str, keywords: Sequence[str]) -> DirectorySearchResult:
        """
        在本地 fixture 中执行确定性匹配。

        关键边界：本地过滤不算现实目录执行，结果固定 executed=false。
        """

        normalized_market = market.strip().casefold()
        normalized_keywords = tuple(
            dict.fromkeys(str(item).strip().casefold() for item in keywords if str(item).strip())
        )
        if not normalized_market:
            raise ValueError("market_required")
        if not normalized_keywords:
            raise ValueError("keywords_required")

        matches = []
        for entity in self._fixtures:
            haystack = " ".join(
                (entity.company_name, entity.category.value, entity.description, entity.location)
            ).casefold()
            if normalized_market in entity.location.casefold() and any(
                keyword in haystack for keyword in normalized_keywords
            ):
                matches.append(entity)
        return DirectorySearchResult(
            entities=tuple(matches),
            dry_run=True,
            executed=False,
            status="mock_directory_only",
        )


class MockEmailProvider:
    """返回未发送结果；类本身不存在任何网络或 SMTP 执行路径。"""

    mock_only = True

    def send(self, *, draft: OutreachDraft, contact: ContactPoint) -> EmailSendResult:
        """
        模拟邮件边界并丢弃可产生外部动作的细节。

        关键边界：只回传 prospect id 和状态，不回传正文或联系方式引用。
        """

        if not isinstance(contact, ContactPoint):
            raise ValueError("contact_point_required")
        return EmailSendResult(
            prospect_id=draft.prospect_id,
            dry_run=True,
            executed=False,
            status="mock_email_not_sent",
            provider_message_id=None,
        )
