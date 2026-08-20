"""端到端验证通用 Agent OS 的本地 Mock 闭环。"""
import unittest
from general_ai_business_os.synthetic_e2e import run_test_business
class SyntheticAgentOsE2ETests(unittest.TestCase):
    def test_test_business_runs_without_external_action_or_business_validation(self):
        result = run_test_business()
        self.assertEqual(0, result.external_actions_attempted)
        self.assertFalse(result.business_validation_completed)
        self.assertEqual("Feedback", result.stages[-1])
