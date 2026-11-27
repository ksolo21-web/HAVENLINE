#!/usr/bin/env python3
"""Focused acceptance regressions; no game build or live reviewer is invoked."""
from __future__ import annotations
import importlib,io,json,pathlib,sys,time,unittest

ROOT=pathlib.Path(__file__).resolve().parents[4]
PACKAGE=pathlib.Path(__file__).resolve().parent
PRODUCTION=ROOT/'tools/havenline/production'
sys.path.insert(0,str(PRODUCTION))

def run_suite(name,suite,rows,log):
    count=suite.countTestCases();stream=io.StringIO();start=time.monotonic()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    row={'name':name,'tests_run':result.testsRun,'expected_nonzero_tests':count,'passed':count>0 and result.wasSuccessful() and not result.skipped,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'duration_seconds':round(time.monotonic()-start,3)}
    rows.append(row);log.append(name+'\n'+stream.getvalue())
    print(json.dumps(row),flush=True)

def main():
    rows=[];log=[]
    patterns=[
      ('production','test_reference_acceptance.py'),('production','test_specialist_safeguards.py'),
      ('production','test_specialist_critic_runner.py'),('production','test_forward_review_evidence.py'),
      ('production','test_performance_review_transport.py'),
      ('production','test_workstream_status_authority.py'),('production','test_reference_style_lock.py'),
      ('production','test_shipping_visual_gate.py'),('production','test_forward_acceptance_policy.py'),
      ('production','test_repair_sufficiency_critic.py'),('production','test_future_prep_packets.py'),
      ('production','test_t05_completion.py'),('task12','test_critic_review_records.py'),
      ('task12','test_final_candidate_gate.py'),('task10','test_aggregate_critics.py'),
    ]
    for directory,pattern in patterns:
        loader=unittest.TestLoader()
        suite=loader.discover(str(ROOT/'tools/havenline'/directory/'tests'),pattern=pattern)
        run_suite(directory+'/'+pattern,suite,rows,log)
    sys.path.insert(0,str(PRODUCTION/'tests'))
    importlib.import_module('test_architecture_v31')
    names=['test_t09_raw_critic_semantics_are_fail_closed','test_original_confidence_schemas_without_conversion','test_categorical_confidence_does_not_waive_other_raw_gates','test_t09_aggregate_and_defect_ledger_are_fail_closed']
    run_suite('preserved_historical_raw_and_aggregate_semantics',unittest.TestLoader().loadTestsFromNames(['test_architecture_v31.ArchitectureV31Tests.'+name for name in names]),rows,log)
    names=['test_single_visual_dissent_routes_to_adjudication_not_product_failure','test_historical_quorum_never_grants_current_approval','test_two_correlated_visual_defect_votes_still_fail','test_incomplete_reviewer_is_retry_not_a_negative_vote']
    run_suite('legacy_quorum_is_nonapproving',unittest.TestLoader().loadTestsFromNames(['test_critic_loop_regressions.CriticLoopRegressionTests.'+name for name in names]),rows,log)
    sys.path.insert(0,str(ROOT/'tools/havenline/task10/tests'))
    run_suite('historical_export_cannot_authorize_current_approval',unittest.TestLoader().loadTestsFromName('test_export_closure_records.ExportTests.test_canonical_keeps_original_scores_and_confidence'),rows,log)
    report={'schema_version':1,'validation_kind':'FOCUSED_POLICY_AND_TOOLING_REGRESSION_ONLY','passed':all(r['passed'] for r in rows),'groups_passed':sum(r['passed'] for r in rows),'groups_required':len(rows),'tests_run':sum(r['tests_run'] for r in rows),'failures':sum(r['failures'] for r in rows),'errors':sum(r['errors'] for r in rows),'skipped':sum(r['skipped'] for r in rows),'game_approval_allowed':False,'groups':rows,'scope_notes':['Synthetic fixtures test gate behavior; they are not real critic/game approvals.','Media cases use generated local fixture bytes and actual decoding.','T12 cross-record tests isolate bundle identity with an explicit synthetic fixture; the consolidated historical workflow-dependent bundle is not claimed operational.','Legacy architecture/workflow-wide suites are outside this scoped run; no archived workflow is activated.']}
    (PACKAGE/'TEST_RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
    (PACKAGE/'TEST_OUTPUT.txt').write_text('\n\n'.join(log))
    print(json.dumps({k:v for k,v in report.items() if k not in {'groups','scope_notes'}},indent=2),flush=True)
    return 0 if report['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
