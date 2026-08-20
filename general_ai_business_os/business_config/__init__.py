"""
用途：
承载可审核、可版本化的 Business Config（业务配置）导入能力。

上游：
JSON/YAML 配置包、CLI 与 Local API 将通过此包进入配置治理流程。

下游：
只有已确认的配置版本会被未来 Media、Lead、Sales、CRM、Knowledge 与 Experiment Agent 读取。

边界：
这里不决定任何市场、客户、产品、价格或商业模式；业务值必须来自带来源和人工审核的输入包。
"""

from general_ai_business_os.business_config.pipeline import BusinessConfigPipeline
from general_ai_business_os.business_config.registry import BusinessConfigRegistry

__all__ = ("BusinessConfigPipeline", "BusinessConfigRegistry")
