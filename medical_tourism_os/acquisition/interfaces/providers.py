"""
用途：
定义未来目录、公开联系方式提取和邮件 Provider 的可替换 Protocol。

上游：
Workflow 只依赖这些 Protocol，不依赖 Google、Yelp、Gmail 或任何 SDK。

下游：
Mock Adapter 和未来经过单独批准的真实 Adapter 实现这些调用合同。

边界：
接口不保存凭据、不发起网络、不授权外部动作；真实实现还必须增加 Permission/Audit gate。
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from medical_tourism_os.acquisition.domain import BusinessEntity, ContactPoint, OutreachDraft
from medical_tourism_os.acquisition.schemas import (
    ContactExtractionResult,
    DirectorySearchResult,
    EmailSendResult,
)


@runtime_checkable
class DirectoryProvider(Protocol):
    """按市场和关键词返回 BusinessEntity 候选及明确执行状态。"""

    def search(self, *, market: str, keywords: Sequence[str]) -> DirectorySearchResult:
        ...


@runtime_checkable
class ContactExtractor(Protocol):
    """从企业实体提取公开联系方式引用；V1 不提供具体实现。"""

    def extract(self, *, entity: BusinessEntity) -> ContactExtractionResult:
        ...


@runtime_checkable
class EmailProvider(Protocol):
    """定义邮件发送边界；是否允许现实发送由未来独立权限层决定。"""

    def send(self, *, draft: OutreachDraft, contact: ContactPoint) -> EmailSendResult:
        ...
