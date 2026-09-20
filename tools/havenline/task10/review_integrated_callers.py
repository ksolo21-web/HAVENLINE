#!/usr/bin/env python3
"""Independent source-delta review of exact integrated repair callers."""
import argparse,ast,hashlib,json,pathlib,subprocess
import review_closeout_delta as r
r.SOURCE='06232b7c0e4cf8662f9b94d51bc93aa125fe2f20'
r.TREE='50d50cf0cbf45eb2d8f38590b91821d97cc83e1e'
r.BASE='2842845c4e4a9866d3bf7bb62a1beeabf58199c2'
r.DIMENSIONS={'callers':['execution_correctness','authority_separation','regression_scope','threshold_preservation','source_binding']}

def current(path):return r.source(path,r.SOURCE)

def named_python(text,name):
 tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
 if len(nodes)!=1:raise ValueError('ambiguous dependency')
 return ast.get_source_segment(text,nodes[0])

def packet(group,proof):
 if group!='callers':raise ValueError('wrong review group')
 p=pathlib.Path(proof);checks=json.loads(p.read_text())
 if checks.get('source')!=r.SOURCE or checks.get('passed') is not True:raise ValueError('exact source preflight incomplete')
 if r.git('rev-parse',r.SOURCE+'^{tree}').decode().strip()!=r.TREE:raise ValueError('source tree changed')
 paths=r.git('diff','--name-only',r.BASE,r.SOURCE).decode().splitlines()
 if len(paths)!=7 or any(x.startswith('HavenlineGodot/') for x in paths):raise ValueError('unexpected source delta')
 for path in ['HavenlineGodot/scripts/world_transform_view.gd','tools/havenline/production/verify_python_repair_bindings.py','Docs/Production/CRITIC_MATRIX.json','Docs/Production/CRITIC_EXECUTION.json','Docs/Production/task-gates.json','tools/havenline/task10/benchmark_supervisor.py','tools/havenline/task10/benchmark_world_transform.gd']:
  if current(path)!=r.source(path,r.BASE):raise ValueError('protected implementation changed')
 callers=[]
 for name,build in [('isolated','built-pending-dependency'),('world-transformation','first-builder-milestone')]:
  path='.github/workflows/havenline-task10-'+name+'.yml';text=current(path)
  guard=next(s.strip() for s in text.splitlines() if "assert next(x['status']" in s)
  commands=[s.strip() for s in text.splitlines() if 'validate_integration_scope.py --base "$' in s or 'then integration=$(git rev-parse' in s]
  gate=text.split('  repair-sufficiency:',1)[1].split('\n  '+build+':',1)[0]
  if 'builder_repair_gate.py' not in gate or 'needs: repair-sufficiency' not in text.split('\n  '+build+':',1)[1][:300]:raise ValueError('source admission dependency removed')
  allowed=ast.literal_eval(guard.rsplit(' in ',1)[1]);expected={'INTEGRATION_READY','INTEGRATING','UNDER_REVIEW','FIX_REQUIRED'}
  if set(allowed)!=expected:raise ValueError('state acceptance expanded beyond bounded repair')
  callers.append({'path':path,'current_integrated_state_guard':guard,'current_integrated_baseline_commands':commands,'exact_source_gate_remains_direct_prerequisite':True,'accepted_states':allowed,'APPROVED_and_LOCKED_are_rejected':True})
 verifier=current('tools/havenline/production/verify_python_repair_bindings.py')
 auth_path='Docs/Production/ChangeRequests/T10-benchmark-liveness-contract.json';auth=json.loads(current(auth_path));binding=[]
 for path,expected in auth['implementation_sha256'].items():
  actual=r.sha(current(path).encode())
  if expected!=actual:raise ValueError('authorization implementation hash mismatch')
  binding.append({'path':path,'actual_and_expected_sha256':actual,'matches':True})
 arch_path='tools/havenline/production/validate_architecture_v32_t10.py';arch=current(arch_path);auth_hash=r.sha(current(auth_path).encode())
 declaration=next(s for s in arch.splitlines() if s.startswith('BENCHMARK_LIVENESS_REQUEST_SHA256 ='))
 if auth_hash not in declaration:raise ValueError('architecture authorization pin differs')
 plan=json.loads(current('Docs/Production/T10/REPAIR_PLAN.json'));c0r=json.loads(current('Docs/Production/T10/C0R_REPAIR_SUFFICIENCY.json'))
 if c0r['input_bindings']['plan_sha256']!=r.sha(current('Docs/Production/T10/REPAIR_PLAN.json').encode()) or c0r['passed'] is not True:raise ValueError('C0R binding invalid')
 op=next(g for g in plan['repair_sufficiency']['repair_groups'] if g['group_id']=='c0r-source-bound-admission')['repair_operations'][-1]
 data={'source':r.SOURCE,'tree':r.TREE,'baseline':r.BASE,'source_hashes':{p:r.sha(r.source(p).encode()) for p in paths},'exact_source_tests':checks,'current_callers':callers,'complete_unchanged_owner_DAG_rule':named_python(verifier,'promotion_dag_errors'),'complete_unchanged_authority_context_rule':named_python(verifier,'authority_context'),'hash_rebindings':binding,'current_architecture_digest_declaration':declaration,'current_declared_contract_operation':op,'complete_added_workflow_tests':current('tools/havenline/task10/tests/test_task10_workflows.py').split('class IntegratedRepairCallerTests',1)[1],'quality_boundary':'FIX_REQUIRED only permits verification of the exact already-source-admitted integrated repair. It does not mark quality approved. The complete six critic suite, G1-G14, regression and fresh integrated closeout still block approval. Source publication itself is not authorized by this non-voting review.','unchanged':{'gameplay':True,'critic_matrix_and_thresholds':True,'benchmark_code_and_budgets':True,'external_owner_verifier':True},'task_approved':False}
 prompt='Independently review this exact proposed T10 workflow-call and hash-binding delta. The existing owner protocol requires promotion parents [R,H], so H is the second parent, while the first parent R already contains the repair. Assess whether the CURRENT callers below preserve that baseline and allow verification without granting approval. Review all supplied changes and complete dependency contracts; report every genuine defect, not the fact that later approval has not happened yet. Required dimensions: '+','.join(r.DIMENSIONS[group])+'. Scores 0-10, pass strictly >9.0 unrounded in every dimension with zero unresolved defects. Return exactly three short complete observations, concrete defects or [], coverage_complete, confidence and every score.\n'+json.dumps(data,ensure_ascii=False,separators=(',',':'))
 return prompt,data

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--proof',required=True);p.add_argument('--out',required=True);a=p.parse_args();r.packet=packet;raise SystemExit(r.run('callers',a.proof,a.out))
