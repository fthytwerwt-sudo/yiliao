"""
用途：
提供 Phase 5 学习闭环的 workflow 入口，让 CLI、本地 API 与测试通过统一名字访问。

上游：
tests、CLI、local API 和 synthetic E2E 从这里导入 LearningLoop。

下游：
委托 `services.learning_loop` 完成真正的指标与实验逻辑。

边界：
这里只做 workflow 命名层与轻量视图整理，不新增业务战略或外部动作。
"""

from __future__ import annotations

from typing import Dict, Optional

from medical_tourism_os.services.learning_loop import LearningLoopService, WeeklyReview


class LearningLoop(LearningLoopService):
    """
    作用：
    暴露学习闭环的 workflow 入口。

    关键边界：
    workflow 只整理当前学习状态快照，不改变服务层的 candidate-only 约束。
    """

    def export_review_board(self, weekly_review: Optional[WeeklyReview] = None) -> Dict[str, object]:
        """返回给 CLI / 本地 API 使用的只读周复盘面板。"""

        review = weekly_review
        if review is None:
            if not self._weekly_reviews:
                raise ValueError("weekly_review_required")
            review = list(self._weekly_reviews.values())[-1]
        return {
            "weekly_review_id": review.id,
            "primary_variable_candidates": list(review.primary_variable_candidates),
            "evidence": list(review.evidence),
            "counterevidence": list(review.counterevidence),
            "unknowns": list(review.unknowns),
            "risks": list(review.risks),
            "next_variables": list(review.next_variables),
        }
