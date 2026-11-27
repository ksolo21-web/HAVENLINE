#!/usr/bin/env python3
"""Verify preservation and the bounded acceptance-tooling change, not the game."""
from __future__ import annotations
import hashlib,json,pathlib,subprocess,sys

ROOT=pathlib.Path(__file__).resolve().parents[4]
BASE='7180d1315af56228e7629735c2bd50bda3c43596'
PACKAGE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/havenline/production'))
from reference_acceptance import policy_errors,load_json_strict,validate_historical_receipt
from validate_migration import forward_acceptance_errors

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)

def old(relative):
    return git('show',BASE+':'+relative)

def main():
    checks=[]
    def check(name,passed,detail=None):
        checks.append({'name':name,'passed':bool(passed),'detail':detail})
    changed=git('diff','--name-only','--no-renames',BASE).decode().splitlines()
    added=git('ls-files','--others','--exclude-standard').decode().splitlines()
    paths=sorted(set(changed+added))
    allowed_root={'AGENTS.md','README.md','BUILD_GAME.md','REPOSITORY_INDEX.md'}
    allowed_docs={'ANTI_LOOP_ROOT_CAUSE_STANDARD.md','CRITIC_EXECUTION.json','CRITIC_MATRIX.json','DEPENDENCY_GRAPH.json','FINAL_VISUAL_SIGNOFF_TEMPLATE.json','FORWARD_EXECUTION_STANDARD.md','HAVENLINE_BUILD_PLAN_V2.md','PRODUCTION_ARCHITECTURE_V32_STANDARD.md','REFERENCE_STYLE_LOCK.json','REFERENCE_STYLE_LOCK_STANDARD.md','SHIPPING_VISUAL_APPROVAL_POLICY.json','TASK_PACKET_TEMPLATE.md','REFERENCE_ACCEPTANCE_POLICY.json','REFERENCE_ACCEPTANCE_STANDARD.md','EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md'}
    def allowed(path):
        if '__pycache__' in pathlib.PurePosixPath(path).parts or path.endswith('.pyc'):return False
        if path in allowed_root:return True
        if path.startswith('Docs/Production/AcceptanceTightening/2026-11-27/'):return True
        if path.startswith('Docs/Production/') and path.removeprefix('Docs/Production/') in allowed_docs:return True
        if path.startswith('tools/havenline/production/') and path.endswith('.py'):return True
        if path in {'tools/havenline/task10/aggregate_critics.py','tools/havenline/task10/export_closure_records.py','tools/havenline/task10/tests/test_export_closure_records.py'}:return True
        if path in {'tools/havenline/task12/final_candidate_gate.py','tools/havenline/task12/validate_critic_review_records.py','tools/havenline/task12/validator_bundle.py','tools/havenline/task12/tests/test_critic_review_records.py','tools/havenline/task12/tests/test_final_candidate_gate.py'}:return True
        return False
    check('changes_confined_to_approved_policy_and_tooling',all(allowed(p) for p in paths),[p for p in paths if not allowed(p)])
    statuses=git('diff','--name-status','--no-renames',BASE).decode().splitlines()
    check('no_deleted_or_renamed_existing_files',all(row.split('\t',1)[0] in {'A','M'} for row in statuses))
    check('no_runtime_asset_render_or_archive_mutations',not any(p.startswith(('Havenline','Docs/Design/','Docs/RepositoryArchive/')) for p in paths))
    check('historical_workflows_remain_inactive',not (ROOT/'.github').exists() and not any(p.startswith('.github/') for p in paths))
    frozen=git('ls-tree','-r','--name-only',BASE,'--','Docs/Production/ReferenceRefresh/2026-11-27/').decode().splitlines()
    check('frozen_reference_refresh_bytes_preserved',all((ROOT/p).read_bytes()==old(p) for p in frozen),{'files':len(frozen)})
    protected=['WORKSTREAM_REGISTRY.json','PATH_OWNERSHIP.json','task-gates.json','APPROVAL_INVALIDATIONS.json']
    check('lifecycle_ownership_and_invalidation_bytes_preserved',all((ROOT/'Docs/Production'/p).read_bytes()==old('Docs/Production/'+p) for p in protected))
    graph=load_json_strict(ROOT/'Docs/Production/DEPENDENCY_GRAPH.json')
    matrix=load_json_strict(ROOT/'Docs/Production/CRITIC_MATRIX.json')
    check('all_70_task_definitions_dependencies_and_statuses_preserved',graph['tasks']==json.loads(old('Docs/Production/DEPENDENCY_GRAPH.json'))['tasks'] and list(graph['tasks'])==[f'T{i:02d}' for i in range(1,71)])
    old_matrix=json.loads(old('Docs/Production/CRITIC_MATRIX.json'))
    check('historical_critic_task_mapping_and_receipts_preserved',matrix['task_applicability']==old_matrix['task_applicability'] and all(matrix[k]==v for k,v in old_matrix.items() if k.startswith(('completed_','current_'))))
    policy=load_json_strict(ROOT/'Docs/Production/REFERENCE_ACCEPTANCE_POLICY.json')
    execution=load_json_strict(ROOT/'Docs/Production/CRITIC_EXECUTION.json')
    check('current_policy_and_graph_matrix_projections_match',not forward_acceptance_errors(graph,matrix,policy,execution) and not policy_errors(policy))
    receipts=policy['historical_preservation']['receipts']
    results=[validate_historical_receipt(r['task_id'],r['candidate_sha'],r['path']) for r in receipts]
    check('eleven_historical_receipts_hash_verified_and_nonapproving',len({r['path'] for r in receipts})==11 and all(r['passed'] and r['approval_allowed'] is False for r in results),{'unique_receipts':len({r['path'] for r in receipts}),'task_candidate_bindings':len(receipts)})
    for path,key in [('REFERENCE_STYLE_LOCK.json','acceptance'),('REFERENCE_FIDELITY_STANDARD.json','approval_rules'),('SHIPPING_VISUAL_APPROVAL_POLICY.json','whole_game_release')]:
        check('stronger_gate_preserved_'+path,load_json_strict(ROOT/'Docs/Production'/path)[key]==json.loads(old('Docs/Production/'+path))[key])
    c5=load_json_strict(ROOT/'Docs/Production/CRITIC_EXECUTION.json')['critics']['C5']
    check('static_c5_capability_cannot_claim_final_playback',c5.get('automated_final_approval') is False and c5.get('evidence_mode')=='contact_sheets_and_text')
    check('whitespace_diff_clean',subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0)
    report={'schema_version':1,'base_commit':BASE,'validation_kind':'POLICY_TOOLING_SCOPE_AND_PRESERVATION_ONLY','game_approval_allowed':False,'passed':all(c['passed'] for c in checks),'checks_passed':sum(c['passed'] for c in checks),'checks_required':len(checks),'changed_or_new_files':len(paths),'checks':checks}
    (PACKAGE/'SCOPE_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
