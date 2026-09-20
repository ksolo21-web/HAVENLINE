#!/usr/bin/env python3
"""Independent bounded review of one exact T10 reconciliation delta.
This reviews preparation only; it cannot approve T10 or authorize itself.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, pathlib, subprocess, time, urllib.request, urllib.error, zipfile
from review_shadow_json_syntax import review_grammar
SOURCE='2842845c4e4a9866d3bf7bb62a1beeabf58199c2'
TREE='4bb22da383e88b44333c30f1f0b7e693e1d0792e'
BASE='f85e2b94cd77676e44f374f8577d079f0d2f6070'
CANARY='31f08a6830dcb55855f5c7ef2a54ddb773e99b97'
PREP_SHA='70ffd9bb63a1a1f8ef4592002d33dd09d387525d870105045ff14eab373e13ac'
VIEW='HavenlineGodot/scripts/world_transform_view.gd'
VIEW_HASH='fc35ebc4bc59dd41e165f6eb8d091ed274c1f02a5fe48e56cf8c9d15b8970b75'
DIMENSIONS={
 'assertions':['assertion_accuracy','behavior_preservation','coverage','regression_safety','source_binding'],
 'authority':['contract_correctness','authority_separation','threshold_preservation','historical_preservation','source_binding'],
 'evidence':['measurement_integrity','complete_domain_coverage','source_binding','failure_preservation','scope_preservation'],
}
INPUT_LIMIT=4096
OUTPUT_LIMIT=1000

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,value):
 path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def git(*args):return subprocess.check_output(['git',*args])
def source(path,ref=SOURCE):return git('show',ref+':'+path).decode('utf-8')
def diff(paths,ref=BASE):return git('diff','--unified=0',ref,SOURCE,'--',*paths).decode('utf-8')
def strict_json(text):
 def pairs(rows):
  out={}
  for k,v in rows:
   if k in out:raise ValueError('duplicate JSON key: '+k)
   out[k]=v
  return out
 def invalid(v):raise ValueError('nonfinite JSON: '+v)
 return json.loads(text,object_pairs_hook=pairs,parse_constant=invalid)

def validate(row,dims):
 errors=[]
 if not isinstance(row,dict):return ['not an object']
 if set(row)!={'observations','defects','coverage_complete','confidence','scores'}:errors.append('fields mismatch')
 for field,lo,hi in [('observations',3,3),('defects',0,5)]:
  vals=row.get(field)
  if not isinstance(vals,list) or not lo<=len(vals)<=hi or any(not isinstance(s,str) or not s.strip() or len(s)>220 or s.rstrip()[-1:] not in '.!?' for s in vals):errors.append(field+' malformed or incomplete')
 if row.get('coverage_complete') is not True:errors.append('incomplete coverage')
 if row.get('confidence') not in ('medium','high'):errors.append('insufficient confidence')
 if row.get('defects'):errors.append('unresolved defects')
 scores=row.get('scores')
 if not isinstance(scores,dict) or set(scores)!=set(dims):errors.append('dimension set mismatch')
 else:
  for key,v in scores.items():
   if type(v) not in (int,float) or not math.isfinite(v) or not 9.0<v<=10:errors.append(key+': not strictly above 9 unrounded')
 return errors

def schema(dims):
 item={'type':'string','maxLength':220,'minLength':1,'pattern':'^.{0,219}[.!?]$'}
 return {'type':'object','properties':{'observations':{'type':'array','items':item,'minItems':3,'maxItems':3},'defects':{'type':'array','items':item,'maxItems':5},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':{d:{'type':'number','minimum':0,'maximum':10} for d in dims},'required':dims,'additionalProperties':False}},'required':['observations','defects','coverage_complete','confidence','scores'],'additionalProperties':False}

def semantic_delta(before,after,path=""):
 rows=[]
 if type(before) is not type(after) or not isinstance(before,(dict,list)):
  if before!=after:rows.append({'path':path,'before':before,'after':after})
 elif isinstance(before,dict):
  for k in sorted(set(before)|set(after)):
   if k not in before:rows.append({'path':path+'/'+k,'added':after[k]})
   elif k not in after:rows.append({'path':path+'/'+k,'removed':before[k]})
   else:rows.extend(semantic_delta(before[k],after[k],path+'/'+k))
 else:
  for i in range(max(len(before),len(after))):
   if i>=len(before):rows.append({'path':path+'/'+str(i),'added':after[i]})
   elif i>=len(after):rows.append({'path':path+'/'+str(i),'removed':before[i]})
   else:rows.extend(semantic_delta(before[i],after[i],path+'/'+str(i)))
 return rows

def preparation(archive):
 raw=pathlib.Path(archive).read_bytes()
 if sha(raw)!=PREP_SHA:raise ValueError('preparation artifact differs')
 with zipfile.ZipFile(archive) as z:
  d={p:strict_json(z.read(p).decode()) for p in ['tooling-tests.json','engine-tests.json','source/prepared-source.json','source-reviews/source-reviews-complete.json']}
  for k in ['tooling-tests.json','engine-tests.json']:
   if d[k]['source']!=SOURCE or d[k]['passed'] is not True:raise ValueError('preparation not passed for exact source')
  for row in d['tooling-tests.json']['rows']:
   fn=row['suite']+'-tests.log'
   if sha(z.read(fn))!=row['log_sha256'] or row['exit_code']!=0:raise ValueError('tooling log mismatch')
  prior=d['source-reviews/source-reviews-complete.json']
  if prior['source']!=BASE or prior['passed'] is not True or prior['required_groups']!=['state','shadow','solver','projection','governance']:raise ValueError('preliminary review identity mismatch')
 return d

def packet(group,archive):
 prep=preparation(archive)
 if git('rev-parse',SOURCE+'^{tree}').decode().strip()!=TREE:raise ValueError('source tree mismatch')
 if sha(source(VIEW).encode())!=VIEW_HASH or source(VIEW)!=source(VIEW,BASE):raise ValueError('product changed')
 for p in ['Docs/Production/CRITIC_MATRIX.json','Docs/Production/CRITIC_EXECUTION.json','Docs/Production/task-gates.json','tools/havenline/production/critic_runtime_lock.json','tools/havenline/production/verify_python_repair_bindings.py']:
  if source(p)!=source(p,BASE):raise ValueError('protected acceptance contract changed')
 common={'source':SOURCE,'tree':TREE,'reviewed_baseline':BASE,'unchanged_product_sha256':VIEW_HASH,'preparation_artifact':10608518512,'preparation_sha256':PREP_SHA,'prior_reviews':{'groups':5,'minimum':prep['source-reviews/source-reviews-complete.json']['lowest_score'],'scope':'unchanged preliminary source only, not final six gameplay critics'},'tests':{'domain':239,'integration':135,'production':330,'task10_tools':136},'mandatory_acceptance_preserved':'C1/C2/C3/C4/C6/C7 all dimensions >9.0 unrounded, G1-G14, impacted regression, no unresolved mandatory defects, fresh integrated source closeout; none approved by this preparation review.'}
 if group=='assertions':
  paths=['HavenlineGodot/tests/test_task10_world_transform.gd','HavenlineGodot/tests/test_task10_integration.gd']
  view=source(VIEW);start=view.index('static func contract()');end=view.index('\nfunc ',start)
  detail={'complete_changed_test_lines':diff(paths),'exact_current_view_contract':view[start:end],'unchanged_view_behavior':'Text readability now belongs to logical viewport pixels; world mesh geometry is not multiplied by the readability setting. Verify the assertions against the exact supplied contract and unchanged reviewed source, not against stale scalar assumptions.'}
 elif group=='authority':
  paths=['Docs/Production/T10/C0_ROOT_CAUSE.json','Docs/Production/T10/REPAIR_PLAN.json','Docs/Production/T10/C0R_REPAIR_SUFFICIENCY.json','Docs/Production/ChangeRequests/T10-c0r-structured-mechanism-detection.json','tools/havenline/production/validate_architecture_v32_t10.py']
  c0=source(paths[0]);plan=strict_json(source(paths[1]));c0r=strict_json(source(paths[2]));auth=source(paths[3]);arch=source(paths[4])
  checks={'plan_c0_hash':plan['c0_report_sha256']==sha(c0.encode()),'c0r_c0_hash':c0r['input_bindings']['c0_sha256']==sha(c0.encode()),'c0r_plan_hash':c0r['input_bindings']['plan_sha256']==sha(source(paths[1]).encode()),'auth_matches_source':strict_json(auth)['source_sha256']==sha(source('tools/havenline/production/repair_sufficiency_critic.py').encode()),'architecture_exact_auth_digest':('C0R_MACHINE_PROSE_REQUEST_SHA256 = "'+sha(auth.encode())+'"') in arch}
  if not all(checks.values()):raise ValueError('authorization binding inconsistency')
  changes={'all_changed_json_values':{p:semantic_delta(strict_json(source(p,BASE)),strict_json(source(p))) for p in paths[:-1]},'complete_python_delta':diff([paths[-1]])}
  # Inherited path strings are unchanged canonical history, not executable repairs.
  detail={'complete_delta':changes,'executed_exact_binding_checks':checks,'publication_boundary':'No new canonical source review record has yet been installed. An independent accepted delta record plus all four cumulative Python before/after bindings must be published at a fresh canonical H, then exact P parents [R,H] must pass the unchanged owner verifier. This packet itself cannot install, approve or waive that step.'}
 else:
  paths=['tools/havenline/task10/run_screen_pixel_canary.py','tools/havenline/task10/verify_screen_pixel_clearance.py','HavenlineGodot/tests/capture_task10_world_transform.gd','tools/havenline/task10/preflight_feedback_layout.gd']
  unchanged={p:{'matches_canonical_reviewed_canary':source(p)==source(p,CANARY),'sha256':sha(source(p).encode())} for p in paths[1:]}
  if not all(v['matches_canonical_reviewed_canary'] for v in unchanged.values()):raise ValueError('capture/verifier changed since independently reviewed canary')
  detail={'reviewed_runner_before_sha256':sha(source(paths[0],CANARY).encode()),'complete_after_runner':source(paths[0]),'unchanged_source_bindings':unchanged,'prior_source_review':'Canonical authorization d30448ba5e5807b2b269d62491262b9365dd25f0 binds the unchanged capture/verifier/preflight at source31f08a; this new runner adds full684 profile coverage, not relaxed thresholds. Raw failures remain retained. Fresh full candidate renders and critics are still required.'}
 data={'identity':common,'review_evidence':detail,'source_hashes':{p:sha(source(p).encode()) for p in paths}}
 prompt=f'Independent non-voting T10 closeout preparation delta review. Group {group}. Review only the exact delta and its supplied established dependencies. Preserve every genuine source-bound defect; do not force a passing score. An already established unchanged function is not missing merely because its full body is in the identified baseline. Every dimension must be scored 0-10 with pass strictly >9.0 unrounded and zero unresolved defects. Report evidence/tool issues separately from gameplay. Required dimensions: '+','.join(DIMENSIONS[group])+'. Return exactly three short, complete observations, concrete defects (or []), coverage_complete, confidence and all scores.\n'+json.dumps(data,ensure_ascii=False,separators=(',',':'))
 return prompt,data

def post(endpoint,body,out,name,timeout=30):
 raw=json.dumps(body,ensure_ascii=False,allow_nan=False).encode();(out/(name+'-request.json')).write_bytes(raw)
 req=urllib.request.Request('http://127.0.0.1:8080'+endpoint,data=raw,headers={'Content-Type':'application/json'},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=timeout) as f:result=f.read()
 except urllib.error.HTTPError as exc:(out/(name+'-error.txt')).write_bytes(exc.read());raise
 (out/(name+'-response.json')).write_bytes(result);return strict_json(result.decode())

def run(group,archive,out):
 out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=False);proc=None;log=None
 result={'source':SOURCE,'tree':TREE,'group':group,'non_voting':True,'task_approved':False,'passed':False}
 try:
  if os.environ.get('HAVENLINE_INDEPENDENT_REVIEW_JOB')!='1':raise ValueError('separate review job required')
  prompt,data=packet(group,archive);write(out/'packet.json',data)
  config=strict_json(source('Docs/Production/CRITIC_EXECUTION.json'))['local_independent_runtime'];cache=pathlib.Path(os.path.expanduser(config['cache_path']));m=strict_json((cache/'manifest.json').read_text())
  for k,v in [('publisher',config['provider']),('base_model',config['base_model']),('revision',config['model_revision']),('runtime_release','b10809')]:
   if m.get(k)!=v:raise ValueError('runtime mismatch '+k)
  for item in m['files']:
   h=hashlib.sha256()
   with (cache/item['filename']).open('rb') as f:
    for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
   if h.hexdigest()!=item['sha256']:raise ValueError('model/runtime bytes mismatch')
  servers=list((cache/'runtime').rglob('llama-server'));assert len(servers)==1;server=servers[0];env=dict(os.environ,LD_LIBRARY_PATH=str(server.parent)+':'+os.environ.get('LD_LIBRARY_PATH',''))
  cmd=[str(server),'-m',str(cache/m['model_file']),'--mmproj',str(cache/m['projector_file']),'--host','127.0.0.1','--port','8080','-c','12288','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-min-tokens','768','--image-max-tokens','2048']
  write(out/'runtime.json',{'manifest':m,'command':cmd,'run':os.environ.get('GITHUB_RUN_ID'),'workflow_source':os.environ.get('GITHUB_SHA')})
  log=(out/'runtime.log').open('w');proc=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
  for _ in range(180):
   if proc.poll() is not None:raise RuntimeError('runtime exited')
   try:
    with urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3) as f:
     if json.load(f).get('status')=='ok':break
   except Exception:pass
   time.sleep(2)
  else:raise RuntimeError('runtime not ready')
  formatted=post('/apply-template',{'messages':[{'role':'user','content':[{'type':'text','text':prompt}]}],'chat_template_kwargs':{'enable_thinking':False}},out,'template')['prompt']
  tokens=post('/tokenize',{'content':formatted,'add_special':True,'parse_special':True},out,'tokenizer')['tokens']
  if len(tokens)+128>INPUT_LIMIT:raise ValueError('input budget exceeded: '+str(len(tokens)))
  grammar=review_grammar(schema(DIMENSIONS[group]));body={'prompt':formatted,'n_predict':OUTPUT_LIMIT,'temperature':0.2,'top_p':0.9,'seed':20260920,'grammar':grammar,'cache_prompt':False,'stream':False}
  reply=post('/completion',body,out,'review',1200)
  if reply.get('stop') is not True or reply.get('truncated') is not False or reply.get('stop_type') not in ('eos','word'):raise ValueError('incomplete model output')
  if reply.get('generation_settings',{}).get('grammar')!=grammar:raise ValueError('grammar not applied exactly')
  if type(reply.get('tokens_evaluated'))!=int or not 0<reply['tokens_evaluated']<=INPUT_LIMIT:raise ValueError('token usage missing or exceeds budget')
  review=strict_json(reply['content']);errors=validate(review,DIMENSIONS[group])
  result.update(review=review,errors=errors,passed=not errors,source_hashes=data['source_hashes'],provider=m['publisher'],model=m['base_model'],model_revision=m['revision'],runtime_release=m['runtime_release'],input_sha256=sha(prompt.encode()),raw_sha256=sha((out/'review-response.json').read_bytes()),actual_input_tokens=reply['tokens_evaluated'],run_id=os.environ.get('GITHUB_RUN_ID'))
 except Exception as exc:result.update(fatal_error=type(exc).__name__+': '+str(exc),failure_layer='NONVOTING_REVIEW_TOOL_OR_SOURCE_DELTA',passed=False)
 finally:
  if proc is not None:
   proc.terminate()
   try:proc.wait(timeout=10)
   except subprocess.TimeoutExpired:proc.kill();proc.wait()
  if log:log.close()
  write(out/'result.json',result);print(json.dumps(result,ensure_ascii=False))
 return 0 if result['passed'] else 1

def aggregate(inputs,out):
 rows={};errors=[]
 for name,dims in DIMENSIONS.items():
  matches=list(pathlib.Path(inputs).glob('**/'+name+'/result.json'))
  if len(matches)!=1:errors.append(name+': missing/duplicate result');continue
  folder=matches[0].parent;row=strict_json(matches[0].read_text());rows[name]=row
  if row.get('source')!=SOURCE or row.get('tree')!=TREE or row.get('group')!=name or row.get('passed') is not True or row.get('task_approved') is not False or row.get('non_voting') is not True:errors.append(name+': identity/status failure')
  errors.extend(name+': '+e for e in validate(row.get('review'),dims))
  raw=(folder/'review-response.json').read_bytes();reply=strict_json(raw.decode())
  if sha(raw)!=row.get('raw_sha256') or strict_json(reply['content'])!=row.get('review') or reply.get('stop') is not True or reply.get('truncated') is not False or reply.get('stop_type') not in ('eos','word'):errors.append(name+': original raw mismatch/incomplete')
  if row.get('run_id')!=os.environ.get('GITHUB_RUN_ID'):errors.append(name+': wrong origin run')
  cfg=strict_json(source('Docs/Production/CRITIC_EXECUTION.json'))['local_independent_runtime']
  for key,value in [('provider',cfg['provider']),('model',cfg['base_model']),('model_revision',cfg['model_revision']),('runtime_release','b10809')]:
   if row.get(key)!=value:errors.append(name+': runtime identity mismatch '+key)
  for path,expected in row.get('source_hashes',{}).items():
   if sha(source(path).encode())!=expected:errors.append(name+': source binding mismatch '+path)
 result={'source':SOURCE,'tree':TREE,'groups':rows,'required_groups':list(DIMENSIONS),'errors':errors,'passed':not errors,'lowest_score':min((v for row in rows.values() for v in row.get('review',{}).get('scores',{}).values()),default=0),'non_voting':True,'task_approved':False,'qualification':'Independent reconciliation delta reviews only. Canonical source authorization and final six gameplay critics remain separate mandatory gates.'}
 write(pathlib.Path(out)/'owner-delta-reviews.json',result);print(json.dumps(result));return 0 if not errors else 1

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',choices=list(DIMENSIONS));p.add_argument('--preparation');p.add_argument('--out',required=True);p.add_argument('--packet-only',action='store_true');p.add_argument('--aggregate');a=p.parse_args()
 if a.aggregate:raise SystemExit(aggregate(a.aggregate,a.out))
 if not a.group or not a.preparation:p.error('--group and --preparation required')
 if a.packet_only:
  prompt,data=packet(a.group,a.preparation);write(pathlib.Path(a.out)/'packet.json',data);print(a.group,len(prompt));raise SystemExit(0)
 raise SystemExit(run(a.group,a.preparation,a.out))
