import pathlib
import sys
import unittest
from unittest.mock import patch

HERE=pathlib.Path(__file__).resolve()
PROD=HERE.parents[1]
sys.path.insert(0,str(PROD))

from workstream import candidate_reconcile_assessment


class CandidateReconcileTests(unittest.TestCase):
    def test_post_integration_repair_uses_shared_branch_point_not_historical_assignment_base(self):
        scope={
            "registry_base":"historical-assignment",
            "branch_point":"current-integration",
            "changed_files":["tools/havenline/task09/motion_capture.py"],
            "reason":"shared integration/governance prefix excluded",
        }
        drift={
            "base":"current-integration",
            "integration_head":"current-integration",
            "changed_files":[],
            "governance_only":True,
            "requires_reconcile":False,
            "reason":"no integration drift",
        }
        with patch("workstream.candidate_scope_assessment",return_value=scope) as scope_call, \
             patch("workstream.integration_drift_assessment",return_value=drift.copy()) as drift_call:
            actual_scope,actual_drift=candidate_reconcile_assessment(
                "historical-assignment","repair-head","current-integration"
            )
        scope_call.assert_called_once_with("historical-assignment","repair-head","current-integration")
        drift_call.assert_called_once_with("current-integration","current-integration")
        self.assertEqual(actual_scope,scope)
        self.assertFalse(actual_drift["requires_reconcile"])
        self.assertEqual(actual_drift["registry_base"],"historical-assignment")
        self.assertEqual(actual_drift["candidate_branch_point"],"current-integration")

    def test_real_drift_after_shared_branch_point_still_requires_reconcile(self):
        scope={
            "registry_base":"historical-assignment",
            "branch_point":"shared-point",
            "changed_files":["HavenlineGodot/scripts/example.gd"],
            "reason":"shared integration/governance prefix excluded",
        }
        drift={
            "base":"shared-point",
            "integration_head":"newer-integration",
            "changed_files":["HavenlineGodot/scripts/other-runtime.gd"],
            "governance_only":False,
            "requires_reconcile":True,
            "reason":"production/runtime integration drift requires reconciliation",
        }
        with patch("workstream.candidate_scope_assessment",return_value=scope), \
             patch("workstream.integration_drift_assessment",return_value=drift.copy()) as drift_call:
            _,actual_drift=candidate_reconcile_assessment(
                "historical-assignment","candidate","newer-integration"
            )
        drift_call.assert_called_once_with("shared-point","newer-integration")
        self.assertTrue(actual_drift["requires_reconcile"])
        self.assertEqual(actual_drift["candidate_branch_point"],"shared-point")


if __name__=="__main__":
    unittest.main(verbosity=2)
