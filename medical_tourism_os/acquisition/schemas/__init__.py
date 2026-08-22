"""暴露 Acquisition 跨层输入、结果、回复引用与反馈合同。"""

from medical_tourism_os.acquisition.schemas.contracts import (
    ContactExtractionResult,
    DirectorySearchResult,
    EmailSendResult,
    FeedbackOutcome,
    FeedbackRecord,
    ProspectDiscoveryResult,
    ProspectScoreDimensions,
    ReplyIntakeRecord,
)

__all__ = [
    "ContactExtractionResult",
    "DirectorySearchResult",
    "EmailSendResult",
    "FeedbackOutcome",
    "FeedbackRecord",
    "ProspectDiscoveryResult",
    "ProspectScoreDimensions",
    "ReplyIntakeRecord",
]
