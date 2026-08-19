"""
用途：
暴露安全导出能力。

上游：
services.data_governance 与未来 dry-run 同步能力调用这里生成对外安全数据。

下游：
返回纯 Python 字典列表，不直接联网、不写文件。

边界：
这里只导出已批准的 canonical fact，并剥离内部 provenance/source 等治理细节。
"""

