#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from flake_intelligence import classify_records
from evidence_retention import validate_manifest
from contract_compatibility import evaluate_change
from gate_fingerprint import load_json as gf_load, POLICY as GF_POLICY
from preactivation_feasibility import resolve_capabilities
from failure_intelligence import query
from task_state_snapshot import snapshot,validate as validate_snapshot
ROOT=Path(__file__).resolve().parents[3];MATRIX=ROOT/'Docs/Production/MUTATION_CANARY_MATRIX.json'

def run_canaries():
    results=[]
    flake=classify_records([
      {'source_sha':'a'*40,'gate_id':'g','test_id':'t','environment_fingerprint':'e','result':'PASS'},
      {'source_sha':'a'*40,'gate_id':'g','test_id':'t','environment_fingerprint':'e','result':'FAIL'},
      {'source_sha':'a'*40,'gate_id':'g','test_id':'t','environment_fingerprint':'e','result':'PASS'}], 'a'*40,'g','t','e',3)
    results.append({'id':'CANARY-FLAKE-WAIVER','rejected':flake['classification']=='FLAKY' and flake['mandatory_gate_still_required'] and not flake['repair_authorized']})
    bad_manifest={'task_id':'T68','accepted_source':'a'*40,'retention_class':'irreplaceable','records':[{'kind':'physical','sha256':'b'*64,'locator':'','reproducible':False}],'regeneration_contract':'not exactly reproducible'}
    results.append({'id':'CANARY-RETENTION-LOCATOR','rejected':not validate_manifest(bad_manifest)['passed']})
    bad_contract={'contract_id':'persistence_schema','from_version':1,'to_version':2,'change_kind':'breaking','consumer_revalidation':[]}
    results.append({'id':'CANARY-CONTRACT-BREAK','rejected':not evaluate_change(bad_contract)['passed']})
    policy=gf_load(GF_POLICY);fresh=all(policy['gates'][g]['reuse']=='exact_source_required' for g in ('physical_device','critic_review','integration','post_integration_regression','closeout','release_manifest'))
    results.append({'id':'CANARY-PROOF-FRESH','rejected':fresh})
    cap=resolve_capabilities('T68');results.append({'id':'CANARY-CAPABILITY-UNKNOWN','rejected':not cap['runtime_activation_allowed'] and cap['capabilities']['physical_phone_4k60']['state']=='UNVERIFIED'})
    hist=query('T24','C5','pixel RMSE pose identity mismatch');advisory=bool(hist.get('matches')) and all(m.get('advisory_only') for m in hist['matches']);results.append({'id':'CANARY-HISTORY-AUTHORITY','rejected':advisory})
    state=snapshot('T10');results.append({'id':'CANARY-TASK-STATE-AUTHORITY','rejected':validate_snapshot(state)['passed'] and state['snapshot_is_derived_not_authority'] and state['lifecycle_status']=='LOCKED' and 'lifecycle_status_LOCKED' in state['blockers'] and 'ownership_not_assigned' in state['blockers']})
    matrix=json.loads(MATRIX.read_text());expected={x['id'] for x in matrix['canaries']};actual={x['id'] for x in results};errors=[]
    if actual!=expected:errors.append(f'canary coverage mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}')
    errors += [r['id']+' failed to reject mutation' for r in results if not r['rejected']]
    if matrix.get('shipping_runtime_mutation_allowed') is not False or matrix.get('player_save_mutation_allowed') is not False:errors.append('mutation canaries must remain synthetic/non-shipping')
    return {'passed':not errors,'results':results,'errors':errors}
if __name__=='__main__':
    r=run_canaries();print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 2)
