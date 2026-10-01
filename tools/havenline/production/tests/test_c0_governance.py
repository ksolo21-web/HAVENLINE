import pathlib,sys,unittest
HERE=pathlib.Path(__file__).resolve();PROD=HERE.parents[1];ROOT=HERE.parents[4];sys.path.insert(0,str(PROD))
from lib import DOCS,load_json

class C0GovernanceTests(unittest.TestCase):
    def test_c0_is_operational_but_never_an_approval_vote(self):
        c0=load_json(DOCS/'C0_EXECUTION.json');matrix=load_json(DOCS/'CRITIC_MATRIX.json')
        self.assertEqual(c0['critic_id'],'C0');self.assertEqual(c0['status'],'OPERATIONAL')
        self.assertTrue(c0['non_voting']);self.assertFalse(c0['approval_critic'])
        self.assertFalse(c0['may_score_gameplay']);self.assertFalse(c0['may_approve_task']);self.assertFalse(c0['may_lower_C1_C11_thresholds'])
        self.assertEqual(set(matrix['critics']),{f'C{i}' for i in range(1,12)})
        self.assertTrue(all('C0' not in critics for critics in matrix['task_applicability'].values()))

    def test_fix_required_builder_requires_c0_contract(self):
        text=(ROOT/'.github/workflows/havenline-candidate-guard.yml').read_text()
        self.assertIn("env.TASK_STATUS == 'FIX_REQUIRED'",text)
        self.assertIn('C0_ROOT_CAUSE.json',text);self.assertIn('REPAIR_PLAN.json',text)
        self.assertIn('builder_repair_gate.py',text);self.assertIn('repair_base',text)

    def test_c0_workflow_is_diagnostic_only_and_frozen_sha_scoped(self):
        text=(ROOT/'.github/workflows/havenline-c0-root-cause.yml').read_text()
        self.assertIn('cancel-in-progress: false',text)
        self.assertIn('ref: ${{ inputs.failed_candidate }}',text)
        self.assertIn('HAVENLINE_C0_INDEPENDENT_JOB',text)
        self.assertIn('c0_root_cause_advisor.py',text)
        self.assertIn('C0 is diagnostic-only',text)

    def test_builder_standard_requires_finish_running_sha(self):
        text=(DOCS/'BUILDER_REPAIR_STANDARD.md').read_text()
        self.assertIn('finish_running_sha',text)
        self.assertIn('complete known blocker set',text)
        self.assertIn('must_not_change',text)

if __name__=='__main__':unittest.main(verbosity=2)
