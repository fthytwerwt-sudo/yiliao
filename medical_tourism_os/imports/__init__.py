"""
用途：
暴露数据导入治理所需的纯 Python 管线组件。

上游：
services.data_governance 读取这里的 Importer、Normalizer、Validator 等组件。

下游：
组件只返回结构化 Python 数据，不直接写数据库或审计。

边界：
这里不做 SQL、不写文件；所有持久化由 repository / audit 层负责。
"""

