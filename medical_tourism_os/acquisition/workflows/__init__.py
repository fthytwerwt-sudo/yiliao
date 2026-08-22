"""暴露潜客发现与人工审核触达两个 Acquisition Workflow。"""

from medical_tourism_os.acquisition.workflows.discovery import ProspectDiscoveryWorkflow
from medical_tourism_os.acquisition.workflows.outreach import OutreachWorkflow

__all__ = ["OutreachWorkflow", "ProspectDiscoveryWorkflow"]
