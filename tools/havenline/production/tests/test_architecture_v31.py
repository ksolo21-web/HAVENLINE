from __future__ import annotations
import pathlib,sys,unittest
HERE=pathlib.Path(__file__).resolve();PROD=HERE.parents[1];sys.path.insert(0,str(PROD))
from architecture_v31 import validate as validate_v31
from flake_intelligence import classify_records
from pipeline_telemetry import summarize,validate as validate_telemetry
from ci_toolchain_lock import validate as validate_toolchain,validate_workflow_action_pins,load as load_toolchain
from evidence_retention import validate_manifest,validate_policy as validate_retention
from runtime_dependency_learning import learned_impact,validate as validate_runtime
from task_state_snapshot import snapshot,validate as validate_snapshot
from mutation_canary import run_canaries
from proof_invalidation import invalidate_contract,validate_policy as validate_invalidation
from gate_fingerprint import validate_policy as validate_fingerprint

class ArchitectureV31Tests(unittest.TestCase):
    def test_flake_history_never_waives_mandatory_gate(self):
        rows=[{'source_sha':'a'*40,'gate_id':'C5','test_id':'pose','environment_fingerprint':'env','result':x} for x in ('PASS','FAIL','PASS')]
        r=classify_records(rows,'a'*40,'C5','pose','env',3);self.assertEqual(r['classification'],'FLAKY');self.assertTrue(r['mandatory_gate_still_required']);self.assertFalse(r['repair_authorized'])
    def test_pipeline_telemetry_is_valid_and_does_not_drive_thresholds(self):
        self.assertTrue(validate_telemetry()['passed']);self.assertEqual(summarize()['records'],0)
    def test_irreplaceable_evidence_requires_persistent_locator(self):
        self.assertTrue(validate_retention()['passed']);bad={'task_id':'T68','accepted_source':'a'*40,'retention_class':'irreplaceable','records':[{'kind':'physical','sha256':'b'*64,'locator':'','reproducible':False}],'regeneration_contract':'not exact'};self.assertFalse(validate_manifest(bad)['passed'])
    def test_runtime_dependency_learning_is_additive_only(self):
        data={'schema_version':1,'policy':{'minimum_observations_for_enforcement':3,'minimum_distinct_sources':2,'learned_edges_are_additive_only':True,'static_mandatory_coverage_may_be_removed_automatically':False},'edges':[{'path_pattern':'HavenlineGodot/scripts/foo.gd','affected_task':'T10','suites':['test_t10'],'observation_count':4,'distinct_sources':2}]};r=learned_impact(['HavenlineGodot/scripts/foo.gd'],data);self.assertEqual(r['coverage_mode'],'ADDITIVE_ONLY');self.assertIn('test_t10',r['required_suites']);self.assertTrue(validate_runtime()['passed'])
    def test_task_snapshot_remains_derived(self):
        r=snapshot('T10');self.assertTrue(validate_snapshot(r)['passed']);self.assertTrue(r['snapshot_is_derived_not_authority'])
    def test_t09_snapshot_includes_produced_contract(self):
        r=snapshot('T09');self.assertTrue(validate_snapshot(r)['passed']);self.assertIn('harvest_resource_identity',r['contracts']['produces'])
    def test_mutation_canaries_all_reject_bad_inputs(self):
        r=run_canaries();self.assertTrue(r['passed'],r['errors']);self.assertTrue(all(x['rejected'] for x in r['results']))
    def test_transitive_invalidation_blocks_reuse_without_auto_revocation(self):
        self.assertTrue(validate_invalidation()['passed']);r=invalidate_contract('persistence_schema');self.assertTrue(r['proof_reuse_blocked']);self.assertFalse(r['automatic_approval_revocation']);self.assertIn('T14',r['invalidated_tasks']);self.assertIn('T15',r['invalidated_tasks']);self.assertIn('T70',r['invalidated_tasks']);self.assertIn('save_matrix',r['invalidated_gates'])
    def test_contract_override_ids_match_registry(self):
        r=validate_invalidation();self.assertTrue(r['passed'],r['errors']);self.assertGreaterEqual(r['contract_override_count'],10)
    def test_ci_action_and_toolchain_lock_is_valid(self):
        r=validate_toolchain();self.assertTrue(r['passed'],r['errors']);self.assertGreaterEqual(r['critical_workflow_count'],8)
    def test_ci_lock_rejects_mutable_subpath_action(self):
        pins=load_toolchain()['action_pins']
        bad=validate_workflow_action_pins('- uses: actions/cache/restore@v4\n',pins,'fixture.yml')
        self.assertTrue(bad)
        self.assertIn('actions/cache/restore',bad[0])
        exact=pins['actions/cache']
        good=validate_workflow_action_pins(f'- uses: actions/cache/restore@{exact}\n- uses: actions/cache/save@{exact}\n',pins,'fixture.yml')
        self.assertEqual(good,[])
    def test_environment_sensitive_gate_policy_remains_safe(self):
        r=validate_fingerprint();self.assertTrue(r['passed'],r['errors'])
    def test_complete_v31_validation_passes(self):
        r=validate_v31();self.assertTrue(r['passed'],r['errors']);self.assertEqual(r['task_count'],62);self.assertEqual(r['snapshot_count'],62)
if __name__=='__main__':unittest.main(verbosity=2)
