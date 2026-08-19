"""
用途：
在任何业务核心动作前执行文本级高风险路由，优先阻断 PHI、临床、支付、法律等输入。

上游：
inbound workflow、未来 API 和测试会先把用户自由文本送到这里。

下游：
返回 `RiskRouteDecision` 给工作流、权限和审计；只输出脱敏摘要，不输出原文。

边界：
这里不诊断、不治疗、不保存患者文本，也不把高风险原文写入 CRM、审计详情或匹配结果。
"""

from __future__ import annotations

import re
from typing import Iterable, List, Pattern, Tuple

from medical_tourism_os.domain.entities import RiskRouteDecision


class RiskRouter:
    """
    作用：
    用规则优先的 fail-closed 方式判定高风险文本。

    输入：
    任意自由文本。

    输出：
    `RiskRouteDecision`，包含 blocked/category/action/safe_summary。

    关键边界：
    一旦命中高风险类别，必须立即 `fail_closed`，并且只返回脱敏摘要。
    """

    def __init__(self) -> None:
        # 规则按高风险优先顺序排列；一旦命中就立即阻断，避免后续流程继续消费原文。
        # emergency 放在 treatment / medication 之前，是因为真实紧急情形的第一动作必须是停止业务流转，
        # 而不是继续解析它想问治疗还是用药；只要出现紧急信号，就要先进入 fail-closed。
        self._rules: Tuple[Tuple[str, Tuple[Pattern[str], ...]], ...] = (
            (
                "PHI",
                self._compile(
                    (
                        r"\bpatient\b",
                        r"\brecord\b",
                        r"\bpassport\b",
                        r"\bname\b",
                        r"身份证",
                        r"护照",
                        r"病历",
                    )
                ),
            ),
            ("diagnosis", self._compile((r"\bdiagnos", r"\bcondition\b", r"\bwhat disease\b"))),
            ("emergency", self._compile((r"\bemergency\b", r"\burgent\b", r"\bimmediately\b", r"紧急", r"立刻"))),
            ("treatment", self._compile((r"\btreatment\b", r"\bprocedure\b", r"\bchoose care\b"))),
            ("medication", self._compile((r"\bmedication\b", r"\bmedicine\b", r"\bdrug\b"))),
            ("legal", self._compile((r"\blegal\b", r"\blaw\b", r"\bconclusion\b"))),
            ("visa", self._compile((r"\bvisa\b", r"\bimmigration\b", r"\bentry permit\b"))),
            ("payment", self._compile((r"\bpayment\b", r"\bpay now\b", r"\bcard\b", r"\bwire\b"))),
            (
                "privacy",
                self._compile(
                    (
                        r"\bprivate details\b",
                        r"\bshare details\b",
                        r"\bconfidential\b",
                        r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
                        r"\+?\d[\d\s-]{7,}\d",
                        r"\bemail\b",
                        r"\bphone\b",
                        r"\bmobile\b",
                        r"\btelegram\b",
                        r"\bline(?:\s+id)?\b",
                        r"\bqq\b",
                        r"\bwechat\b",
                        r"\bwhatsapp\b",
                        r"微信",
                        r"邮箱",
                        r"电话",
                        r"手机",
                    )
                ),
            ),
            ("guarantee", self._compile((r"\bguarantee\b", r"\bpromise result\b", r"\bassure outcome\b"))),
            ("minor", self._compile((r"\bminor\b", r"\bchild\b", r"\bunderage\b"))),
        )

    def route(self, text: str) -> RiskRouteDecision:
        """
        作用：
        对单段文本执行高风险路由。

        输入：
        自由文本。

        输出：
        `RiskRouteDecision`。

        关键边界：
        结果里的 `safe_summary` 只保留长度、命中类别和命中项数量，不回传原文。
        """

        normalized = " ".join(text.strip().lower().split())
        for category, patterns in self._rules:
            matched_terms = self._matched_terms(normalized, patterns)
            if matched_terms:
                return RiskRouteDecision(
                    blocked=True,
                    category=category,
                    action="fail_closed",
                    safe_summary={
                        "text_length": len(normalized),
                        "matched_category": category,
                        "matched_term_count": len(matched_terms),
                    },
                    matched_terms=matched_terms,
                )
        return RiskRouteDecision(
            blocked=False,
            category="allow",
            action="allow",
            safe_summary={
                "text_length": len(normalized),
                "matched_category": "allow",
                "matched_term_count": 0,
            },
            matched_terms=(),
        )

    def _compile(self, expressions: Iterable[str]) -> Tuple[Pattern[str], ...]:
        return tuple(re.compile(expression, re.IGNORECASE) for expression in expressions)

    def _matched_terms(self, normalized: str, patterns: Iterable[Pattern[str]]) -> tuple[str, ...]:
        hits: List[str] = []
        for pattern in patterns:
            match = pattern.search(normalized)
            if match:
                # 这里仅返回命中的短 token，不返回整段文本，避免高风险原文被带出。
                hits.append(match.group(0))
        return tuple(hits)
