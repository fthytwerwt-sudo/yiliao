"""
用途：
编排 Business Config 从本地文件导入、结构校验、pending 持久化到具名人工审核的最小治理流程。

上游：
CLI、Local API 或离线工具提供一个本地配置包目录和审核者代码。

下游：
Registry 只在 confirmed+approved 后向未来 Agent 注入配置版本。

边界：
Pipeline 不裁决市场、产品、价格或真实性；Research 等状态不能由它自动晋升为 confirmed fact。
"""

from __future__ import annotations

import re
from pathlib import Path

from general_ai_business_os.business_config.contracts import (
    BusinessConfigPackage,
    ConfigClassification,
    ConfigClassificationError,
    ConfigDuplicateVersionError,
    ConfigReviewStatus,
    ConfigValidationError,
)
from general_ai_business_os.business_config.loader import BusinessConfigLoader
from general_ai_business_os.business_config.registry import BusinessConfigRegistry
from general_ai_business_os.business_config.validator import BusinessConfigValidator
from general_ai_business_os.storage.contracts import StoragePort


_SAFE_REVIEWER = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")


class BusinessConfigPipeline:
    """配置导入与审核门；通过组合 Loader/Validator/Registry 保持职责单一。"""

    def __init__(self, store: StoragePort) -> None:
        self._loader = BusinessConfigLoader()
        self._validator = BusinessConfigValidator()
        self._registry = BusinessConfigRegistry(store)

    def import_package(self, package_path: Path) -> BusinessConfigPackage:
        """读取并持久化一个 pending package；重复版本必须显式处理，不能静默覆盖。"""

        manifest_payload, documents = self._loader.load(package_path)
        package = self._validator.validate(manifest_payload, documents)
        if self._registry.exists(package.manifest.business_id, package.manifest.config_version):
            raise ConfigDuplicateVersionError("config_version_already_exists")
        self._registry.save(package)
        return package

    def approve(self, business_id: str, config_version: str, *, reviewer: str) -> BusinessConfigPackage:
        """
        执行具名人工审核的技术记录。

        关键边界：
        只有上游已经被事实裁决为 CONFIRMED_FACT 的 package 可被标记 APPROVED；该检查
        不代表 Pipeline 自己裁决了事实，只是拒绝绕过外部事实裁决 gate。
        """

        if not isinstance(reviewer, str) or not _SAFE_REVIEWER.fullmatch(reviewer):
            raise ConfigValidationError("config_reviewer_invalid")
        package = self._registry.get(business_id, config_version)
        if package.manifest.classification != ConfigClassification.CONFIRMED_FACT:
            raise ConfigClassificationError("config_classification_not_confirmed")
        if package.manifest.review_status != ConfigReviewStatus.PENDING:
            raise ConfigValidationError("config_review_not_pending")
        approved = package.approved(reviewer)
        self._registry.save(approved)
        return approved
