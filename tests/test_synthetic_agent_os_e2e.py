"""端到端验证通用 Agent OS 的本地 Mock 闭环。"""
import unittest
from general_ai_business_os.synthetic_e2e import run_test_business
class SyntheticAgentOsE2ETests(unittest.TestCase):
    def test_test_business_records_tool_evaluation_and_feedback_evidence_without_external_action(self):
        """阶段名不能充当闭环证明；E2E 必须返回 Tool、Evaluation 与 Feedback 三类真实工件。"""

        result = run_test_business()

        self.assertFalse(result.external_actions_allowed)
        self.assertEqual(0, result.external_actions_attempted)
        self.assertFalse(result.business_validation_completed)
        self.assertEqual(1, result.tool_execution_count)
        self.assertEqual("COMPLETED", result.tool_evidence[0]["status"])
        self.assertEqual("OBSERVED", result.evaluation.verdict)
        self.assertEqual("RECORDED", result.feedback.status)
        self.assertEqual("TEST_AGENT", result.feedback.agent_id)
