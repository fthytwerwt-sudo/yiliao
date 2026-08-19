"""
用途：
提供数据治理阶段可复用的合成研究输入。

上游：
tests.test_data_governance 与本地调试服务读取这里的 fixture。

下游：
把稳定的 `TEST_*` 载荷交给导入治理服务。

边界：
这里只描述模拟输入，不生成 canonical fact，不表达任何现实业务决策。
"""

from __future__ import annotations


SYNTHETIC_RESEARCH_RECORD = {
    "claim": "TEST_MARKET_A has an unresolved access question",
    "source_date": "2026-08-19",
    "scope": "synthetic fixture",
    "provenance": "fixture:TEST_RESEARCH_001",
}
