#!/usr/bin/env python3
"""Repair review presentation only; preserve exact source, raw scores and gates."""
from __future__ import annotations
import argparse,json,os,pathlib,re,zipfile
import review_closeout_delta as r
ORIGINAL_PACKET=r.packet
EVIDENCE_SHA='c008da1691ce1c285f24188d4ba7d33a3d8ad7a15d3fbe9e36d260321cca17a2'
EVIDENCE_RUN='35527195052'
CANONICAL='0b61aa5bd6a9e9cb3662412f9d0a7003d2bd5f00'

def function(text,name):
 lines=text.splitlines(keepends=True);starts=[i for i,s in enumerate(lines) if re.match(r'^(?:static )?func '+re.escape(name)+r'\(',s)]
 if len(starts)!=1:raise ValueError('ambiguous function '+name)
 begin=starts[0];end=next((i for i in range(begin+1,len(lines)) if re.match(r'^(?:static )?func ',lines[i])),len(lines))
 return {'function':name,'current_lines':[begin+1,end],'complete_body':''.join(lines[begin:end])}

def assertions(before,after):
 old=set(before.splitlines());rows=[]
 for i,line in enumerate(after.splitlines(),1):
  if line not in old and line.lstrip().startswith('check('):
   match=re.match(r'\s*check\("([^"\\]*(?:\\.[^"\\]*)*)"',line)
   if not match:raise ValueError('unsupported assertion')
   rows.append({'current_line':i,'name':match.group(1),'current_statement':line.strip()})
 return rows

def packet(group,archive):
 _,original=ORIGINAL_PACKET(group,archive);prep=r.preparation(archive)
 if group=='assertions':
  current=[]
  with zipfile.ZipFile(archive) as z:
   for path,digest in original['source_hashes'].items():
    report=[r.strict_json(s) for s in z.read(pathlib.Path(path).stem+'.log').decode().splitlines() if s.startswith('{')][-1]
    if report['passed'] is not True or report['failures']:raise ValueError('source engine suite failed')
    rows=assertions(r.source(path,r.BASE),r.source(path))
    for row in rows:
     found=[x for x in report['checks'] if x['name']==row['name']]
     if len(found)!=1 or found[0]['passed'] is not True:raise ValueError('exact assertion result missing')
     row['executed_result']='PASS; exact check name matched once in pinned-engine log'
    current.append({'path':path,'sha256':digest,'all_changed_current_assertions':rows})
  evidence={'current_assertions':current,'complete_existing_functions':[function(r.source(r.VIEW),n) for n in ['configure_readability','screen_delta_to_label_offset','_readable_reasons','feedback_text']],'current_view_contract':original['review_evidence']['exact_current_view_contract']}
  context='Only CURRENT assertions are shown, not a unified diff. Removed historical lines are not current tests. An added test may exercise an existing implementation; no code change is required merely to add coverage.'
 elif group=='authority':
  changes=original['review_evidence']['complete_delta']['all_changed_json_values'];values={p:json.loads(r.source(p)) for p in changes}
  cp='Docs/Production/T10/C0_ROOT_CAUSE.json';pp='Docs/Production/T10/REPAIR_PLAN.json';ap='Docs/Production/ChangeRequests/T10-c0r-structured-mechanism-detection.json'
  c0=values[cp];plan=values[pp];c0r=values['Docs/Production/T10/C0R_REPAIR_SUFFICIENCY.json'];history=c0['pre_final_reconciliation']
  if history['frozen_source']!=r.BASE or prep['engine-tests.json']['source']!=r.SOURCE:raise ValueError('source chronology mismatch')
  bindings=[]
  for consumer,target,expected in [('plan.c0_report_sha256',cp,plan['c0_report_sha256']),('c0r.c0_sha256',cp,c0r['input_bindings']['c0_sha256']),('c0r.plan_sha256',pp,c0r['input_bindings']['plan_sha256']),('authorization.source_sha256','tools/havenline/production/repair_sufficiency_critic.py',values[ap]['source_sha256'])]:
   actual=r.sha(r.source(target).encode())
   if actual!=expected:raise ValueError('current digest mismatch '+consumer)
   bindings.append({'consumer':consumer,'target':target,'current_actual_and_expected_digest':actual,'equality_test':True})
  arch='tools/havenline/production/validate_architecture_v32_t10.py';after=r.source(arch).splitlines(keepends=True);before=r.source(arch,r.BASE).splitlines(keepends=True)
  if len(after)!=len(before) or [i for i,(a,b) in enumerate(zip(before,after)) if a!=b]!=[78]:raise ValueError('unexpected executable delta')
  declaration=after[78].strip();usage=''.join(after[221:239]);digest=r.sha(r.source(ap).encode())
  if digest not in declaration or 'hashlib.sha256(machine_request_bytes).hexdigest()!=C0R_MACHINE_PROSE_REQUEST_SHA256' not in usage:raise ValueError('exact unchanged digest comparator missing')
  forward=[];inherited=[]
  for file,rows in changes.items():
   for row in rows:
    if row['path'].startswith('/inherited_noncausal_files/'):
     path=row['added']
     if r.source(path)!=r.source(path,CANONICAL):raise ValueError('canonical history bytes changed')
     inherited.append(path);continue
    if row['path']=='/pre_final_reconciliation':continue
    forward.append({'file':file,'field':row['path'],'current_value':row.get('after',row.get('added'))})
  evidence={'sole_changed_executable_statement':declaration,'unchanged_strict_digest_comparator':usage,'executed_current_bindings':bindings,'all_other_current_metadata_changes':forward,'historical_metadata':{'recorded_previous_source':history['frozen_source'],'purpose':'Preserve the previous failed run and causal repair, NOT a current-source verdict','current_source_engine_results':prep['engine-tests.json'],'inherited_paths_count':len(inherited),'inherited_path_manifest_sha256':r.sha(json.dumps(inherited).encode()),'all_exact_canonical_bytes_verified':True},'publication_boundary':'Canonical publication is still pending and blocked. This review assesses the proposed source BEFORE admission. The unchanged external owner verifier and all final gameplay critics remain mandatory.'}
  original['verified_inherited_paths']=inherited
  context='This is PRE-ADMISSION correctness review, not certification of already completed publication. Compare stored digests to actual named CURRENT file bytes, not old-versus-new versions. Historical failures are retained audit records, not current test outcomes.'
 else:raise ValueError('only the two rejected packets may be rerun')
 data={'source':r.SOURCE,'tree':r.TREE,'reviewed_baseline':r.BASE,'product_sha256':r.VIEW_HASH,'source_hashes':original['source_hashes'],'evidence':evidence,'task_approved':False}
 prompt=f'Independent non-voting T10 preparation delta review: {group}. '+context+' Review every supplied change against its complete source dependencies and real engine evidence. Preserve genuine defects; do not force a pass. Required dimensions: '+','.join(r.DIMENSIONS[group])+'. Score 0-10; all must be >9.0 unrounded with no unresolved defect to pass. Return exactly three short complete ordinary sentences as observations, preferably under 100 characters; concrete defects or [], coverage_complete, confidence, and every score.\n'+json.dumps(data,ensure_ascii=False,separators=(',',':'))
 if group=='authority':
  prompt=prompt.replace('Docs/Production/','DP/').replace('tools/havenline/','TH/').replace('/repair_sufficiency/repair_groups/20/','/governance_group/')
  prompt+='\nPath aliases: DP/ = Docs/Production/; TH/ = tools/havenline/; /governance_group/ = /repair_sufficiency/repair_groups/20/.'
 return prompt,data

def validate_original(folder,name,origin):
 row=r.strict_json((folder/'result.json').read_text());raw=(folder/'review-response.json').read_bytes();reply=r.strict_json(raw.decode())
 if row.get('source')!=r.SOURCE or row.get('tree')!=r.TREE or row.get('group')!=name or row.get('passed') is not True or row.get('non_voting') is not True or row.get('task_approved') is not False:raise ValueError('review identity/status mismatch')
 errors=r.validate(row.get('review'),r.DIMENSIONS[name])
 if errors:raise ValueError('review remains failed: '+repr(errors))
 if r.sha(raw)!=row.get('raw_sha256') or r.strict_json(reply['content'])!=row['review'] or reply.get('stop') is not True or reply.get('truncated') is not False or reply.get('stop_type') not in ('eos','word'):raise ValueError('original raw altered/incomplete')
 if str(row.get('run_id'))!=str(origin):raise ValueError('origin run mismatch')
 config=r.strict_json(r.source('Docs/Production/CRITIC_EXECUTION.json'))['local_independent_runtime']
 for k,v in [('provider',config['provider']),('model',config['base_model']),('model_revision',config['model_revision']),('runtime_release','b10809')]:
  if row.get(k)!=v:raise ValueError('runtime mismatch')
 for path,expected in row['source_hashes'].items():
  if r.sha(r.source(path).encode())!=expected:raise ValueError('source bytes changed')
 return row

def aggregate(inputs,archive,out):
 inputs=pathlib.Path(inputs);out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True);rows={};errors=[]
 try:
  if r.sha(pathlib.Path(archive).read_bytes())!=EVIDENCE_SHA:raise ValueError('retained evidence archive changed')
  retained=out/'retained-evidence'
  with zipfile.ZipFile(archive) as z:
   if len(z.namelist())!=len(set(z.namelist())) or any(pathlib.PurePosixPath(p).is_absolute() or '..' in pathlib.PurePosixPath(p).parts for p in z.namelist()):raise ValueError('unsafe archive')
   z.extractall(retained)
  rows['evidence']=validate_original(retained/'evidence','evidence',EVIDENCE_RUN)
  for name in ['assertions','authority']:
   matches=list(inputs.glob('**/'+name+'/result.json'))
   if len(matches)!=1:raise ValueError('missing/duplicate review '+name)
   rows[name]=validate_original(matches[0].parent,name,os.environ['GITHUB_RUN_ID'])
 except Exception as exc:errors.append(type(exc).__name__+': '+str(exc))
 result={'source':r.SOURCE,'tree':r.TREE,'groups':rows,'required_groups':list(r.DIMENSIONS),'errors':errors,'passed':not errors and len(rows)==3,'lowest_score':min((v for row in rows.values() for v in row['review']['scores'].values()),default=0),'non_voting':True,'task_approved':False,'retained_evidence':{'run':EVIDENCE_RUN,'artifact':10610506963,'archive_sha256':EVIDENCE_SHA},'qualification':'Source preparation review only; canonical authority, all six final critics, G1-G14 and integrated-source closeout are not waived.'}
 r.write(out/'owner-delta-reviews.json',result);print(json.dumps(result));return 0 if result['passed'] else 1

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',choices=['assertions','authority']);p.add_argument('--preparation');p.add_argument('--out',required=True);p.add_argument('--packet-only',action='store_true');p.add_argument('--aggregate');p.add_argument('--retained');a=p.parse_args()
 if a.aggregate:raise SystemExit(aggregate(a.aggregate,a.retained,a.out))
 if not a.group or not a.preparation:p.error('--group and --preparation required')
 r.packet=packet
 if a.packet_only:
  text,data=packet(a.group,a.preparation);r.write(pathlib.Path(a.out)/'packet.json',data);print(a.group,len(text));raise SystemExit(0)
 raise SystemExit(r.run(a.group,a.preparation,a.out))
