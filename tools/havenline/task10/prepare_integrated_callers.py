#!/usr/bin/env python3
"""Reproduce a bounded, unapproved integration-caller review source."""
import argparse,hashlib,json,os,pathlib,re,subprocess
BASE='2842845c4e4a9866d3bf7bb62a1beeabf58199c2'
SOURCE='06232b7c0e4cf8662f9b94d51bc93aa125fe2f20'
TREE='50d50cf0cbf45eb2d8f38590b91821d97cc83e1e'
DATE='2026-09-20T18:19:13Z'
MESSAGE='T10: reconcile integrated repair callers with exact authority-parent semantics\n\nKeep gameplay and all acceptance thresholds unchanged. Integrated FIX_REQUIRED is validation-only behind the exact C0R and owner-source gates. Scope and regression compare P to authority parent H, not already-reviewed R, for required ordered [R,H] promotions. Bind the affected workflow/test hashes without changing benchmark code, budgets or samples. This is an unapproved source for independent review; T11 stays locked.\n'
TEST_ADDITION='\n\nclass IntegratedRepairCallerTests(unittest.TestCase):\n    def test_repair_capture_is_not_an_approval_transition(self):\n        import ast\n        for name in (\'isolated\',\'world-transformation\'):\n            text=(WORKFLOWS/(\'havenline-task10-\'+name+\'.yml\')).read_text()\n            lines=[x for x in text.splitlines() if "assert next(x[\'status\']" in x]\n            self.assertEqual(1,len(lines))\n            allowed=ast.literal_eval(lines[0].rsplit(\' in \',1)[1])\n            self.assertEqual({\'INTEGRATION_READY\',\'INTEGRATING\',\'UNDER_REVIEW\',\'FIX_REQUIRED\'},set(allowed))\n            for rejected in (\'APPROVED\',\'LOCKED\',\'PREPARED\',\'ASSIGNED\',\'BLOCKED\',\'unknown\'):\n                self.assertNotIn(rejected,allowed)\n            build=\'built-pending-dependency\' if name==\'isolated\' else \'first-builder-milestone\'\n            prefix=text.split(\'  repair-sufficiency:\',1)[1].split(\'\\n  \'+build+\':\',1)[0]\n            self.assertIn(\'builder_repair_gate.py\',prefix)\n            self.assertIn(\'needs: repair-sufficiency\',text.split(\'\\n  \'+build+\':\',1)[1][:300])\n\n    def test_integrated_scope_uses_authority_parent_not_reviewed_parent(self):\n        for name,variable in [(\'isolated\',\'GITHUB_SHA\'),(\'world-transformation\',\'CANDIDATE\')]:\n            text=(WORKFLOWS/(\'havenline-task10-\'+name+\'.yml\')).read_text()\n            self.assertIn(\'validate_integration_scope.py --base "$\'+variable+\'^2"\',text)\n            self.assertNotIn(\'validate_integration_scope.py --base "$\'+variable+\'^"\',text)\n\n    def test_integrated_regression_uses_exact_authority_parent(self):\n        text=(WORKFLOWS/\'havenline-task10-world-transformation.yml\').read_text()\n        self.assertIn(\'if [ "$GITHUB_SHA" = "$integration" ]; then integration=$(git rev-parse "$GITHUB_SHA^2"); fi\',text)\n        self.assertNotIn(\'git rev-parse "$GITHUB_SHA^"\',text)\n\n    def test_real_review_merge_exposes_first_parent_regression_blind_spot(self):\n        import subprocess\n        source=\'2842845c4e4a9866d3bf7bb62a1beeabf58199c2\'\n        def changed(parent):\n            return set(subprocess.check_output([\'git\',\'diff\',\'--name-only\',source+parent,source],cwd=ROOT,text=True).splitlines())\n        path=\'HavenlineGodot/scripts/world_transform_view.gd\'\n        self.assertNotIn(path,changed(\'^\'))\n        self.assertIn(path,changed(\'^2\'))\n'

def prepare(repo,out):
 r=pathlib.Path(repo);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
 def git(*args):return subprocess.check_output(['git',*args],cwd=r)
 def sha(p):return hashlib.sha256((r/p).read_bytes()).hexdigest()
 if git('rev-parse','HEAD').decode().strip()!=BASE:raise ValueError('wrong source base')
 for name in ['world-transformation','isolated']:
  p=r/'.github/workflows'/('havenline-task10-'+name+'.yml');s=p.read_text();old="in ['INTEGRATION_READY','INTEGRATING','UNDER_REVIEW']"
  if s.count(old)!=1:raise ValueError('caller state anchor changed')
  s=s.replace(old,"in ['INTEGRATION_READY','INTEGRATING','UNDER_REVIEW','FIX_REQUIRED']").replace('"$CANDIDATE^"','"$CANDIDATE^2"').replace('"$GITHUB_SHA^"','"$GITHUB_SHA^2"');p.write_text(s)
 p=r/'tools/havenline/task10/tests/test_task10_workflows.py';p.write_text(p.read_text()+TEST_ADDITION)
 p=r/'Docs/Production/ChangeRequests/T10-benchmark-liveness-contract.json';d=json.loads(p.read_text())
 for file in ['.github/workflows/havenline-task10-isolated.yml','tools/havenline/task10/tests/test_task10_workflows.py']:d['implementation_sha256'][file]=sha(file)
 d['post_review_caller_delta']={'baseline_source':BASE,'scope':'Workflow invocation metadata and tests only; benchmark supervisor, GDScript, budgets, samples and C6 thresholds unchanged.','repair':'Allow source-verified integrated FIX_REQUIRED capture without approval, and compare scope/regression against authoritative second merge parent H in exact [R,H] promotions.','final_source_review_required':True,'task_approved':False}
 p.write_text(json.dumps(d,indent=2,ensure_ascii=True)+'\n');digest=sha(str(p.relative_to(r)))
 p=r/'tools/havenline/production/validate_architecture_v32_t10.py';s,n=re.subn(r'BENCHMARK_LIVENESS_REQUEST_SHA256 = "[0-9a-f]{64}"',f'BENCHMARK_LIVENESS_REQUEST_SHA256 = "{digest}"',p.read_text());assert n==1;p.write_text(s)
 p=r/'Docs/Production/T10/REPAIR_PLAN.json';plan=json.loads(p.read_text());g=next(x for x in plan['repair_sufficiency']['repair_groups'] if x['group_id']=='c0r-source-bound-admission');op=g['repair_operations'][-1]
 if op['target_symbols']!=['C0R_MACHINE_PROSE_REQUEST_SHA256']:raise ValueError('unexpected operation binding')
 op['target_symbols'].append('BENCHMARK_LIVENESS_REQUEST_SHA256');op['with']='IMPLEMENT_SYMBOLS['+','.join(op['target_symbols'])+']'
 g['causal_mechanism']=';'.join(x['operation_kind']+'['+','.join(x['target_symbols'])+']' for x in g['repair_operations']);g['implementation_diff_contract']['required_added_markers'].append({'kind':'CODE_IDENTIFIER','value':'BENCHMARK_LIVENESS_REQUEST_SHA256'})
 p.write_text(json.dumps(plan,indent=2,ensure_ascii=True)+'\n')
 with (out/'c0r.log').open('w') as log:subprocess.run(['python3','tools/havenline/production/repair_sufficiency_critic.py','--c0','Docs/Production/T10/C0_ROOT_CAUSE.json','--plan','Docs/Production/T10/REPAIR_PLAN.json','--output','Docs/Production/T10/C0R_REPAIR_SUFFICIENCY.json'],cwd=r,stdout=log,stderr=subprocess.STDOUT,check=True)
 paths=git('diff','--name-only').decode().splitlines()
 if len(paths)!=7 or any(p.startswith('HavenlineGodot/') for p in paths):raise ValueError('source scope exceeded')
 subprocess.run(['git','add','--']+paths,cwd=r,check=True);tree=git('write-tree').decode().strip()
 if tree!=TREE:raise ValueError('tree mismatch: '+tree)
 env=dict(os.environ,GIT_AUTHOR_NAME='T10 Review Preparation',GIT_AUTHOR_EMAIL='t10-review@example.invalid',GIT_AUTHOR_DATE=DATE,GIT_COMMITTER_NAME='T10 Review Preparation',GIT_COMMITTER_EMAIL='t10-review@example.invalid',GIT_COMMITTER_DATE=DATE)
 source=subprocess.check_output(['git','commit-tree',tree,'-p',BASE],cwd=r,input=MESSAGE.encode(),env=env).decode().strip()
 if source!=SOURCE:raise ValueError('commit identity mismatch')
 subprocess.run(['git','checkout','--detach',source],cwd=r,check=True)
 result={'source':source,'tree':tree,'base':BASE,'changed_paths':paths,'source_hashes':{p:sha(p) for p in paths},'product_sha256':sha('HavenlineGodot/scripts/world_transform_view.gd'),'task_approved':False,'purpose':'UNAPPROVED_REVIEW_SOURCE'}
 (out/'identity.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--out',required=True);a=p.parse_args();prepare(a.repo,a.out)
