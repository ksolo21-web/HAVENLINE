#!/usr/bin/env python3
"""Read-only validation of the documentation crosswalk; never a gameplay gate."""
import hashlib, json, re, subprocess, unicodedata
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
BASE='bbc9c57b24d21765c8c65985d4bafd858dcaf652'
ART='a868ae89cdf2f120b478aa0a48fff35e09cc465c'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True)
for required_commit in (BASE,ART):
 if subprocess.run(['git','cat-file','-e',required_commit+'^{commit}'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
  raise SystemExit('Missing immutable source object. Run this read-only remote fetch, then rerun validation: git fetch --filter=blob:none origin '+required_commit)
def read(name):return json.loads((HERE/name).read_text())
def tree(ref):
 out={}
 for line in git('ls-tree','-r',ref).splitlines():
  meta,path=line.split('\t',1);mode,typ,sha=meta.split();out[path]={'mode':mode,'type':typ,'sha':sha}
 return out
checks=[]
def check(name,ok,details):checks.append({'check':name,'passed':bool(ok),'details':details})
matrix=read('TASK_REFERENCE_MATRIX_T01_T80.json');rows=matrix['rows']
graph=json.loads((ROOT/'Docs/Production/DEPENDENCY_GRAPH.json').read_text())
render=read('RENDER_SOURCE_REGISTER.json');refs=read('REFERENCE_EVIDENCE.json')
check('80 unique requested IDs',[r['task_id'] for r in rows]==[f'T{i:02}' for i in range(1,81)],len(rows))
check('70 authentic names and dependencies unchanged',all(r['name']==graph['tasks'][r['task_id']]['name'] and r['dependencies']==graph['tasks'][r['task_id']]['dependencies'] for r in rows[:70]),'Compared to preserved DEPENDENCY_GRAPH.json')
check('10 missing-source rows not invented',all(r['definition_status']=='SOURCE_NOT_FOUND' and r['name'] is None and r['dependencies'] is None for r in rows[70:]),'T71-T80')
check('every task has proof and next action',all(r['acceptance_checks'] and r['next_action'] and r['planning_responsibility'] for r in rows),'80 rows')
ids={a['id'] for a in render['archives']};sids={s['id'] for s in refs['reference_acceptance_scenarios']}
check('all archive/scenario references resolve',all(set(r['render_archive_ids'])<=ids and set(r['reference_scenario_ids'])<=sids for r in rows),{'archives':len(ids),'scenarios':len(sids)})
check('runtime scores remain unassessed',all(r['runtime_match_score'] is None for r in rows),'No game-wide pass invented')
check('mandatory motion critics included',all('C5' in next(r for r in rows if r['task_id']==t)['required_critics_union'] for t in ['T09','T16','T19','T21','T23']),'C5 union')
check('unestablished region art remains explicit',all(next(r for r in rows if r['task_id']==t).get('dedicated_region_render_coverage')=='NOT_ESTABLISHED_IN_AUDITED_ARCHIVES' for t in ['T46','T47','T48','T49','T52']),'No fabricated complete regional render sets')
match=read('MATCH_ACCEPTANCE.json')
check('score rules preserve stronger gates',match['ordinary_critic_floor']==9.5 and match['requested_match_attainment']['minimum_each_applicable_reference_comparison_dimension']==9.9 and match['stricter_locked_dimensions']['reference_fidelity']==10 and match['stricter_locked_dimensions']['visual_language']==10,'9.5 / 9.9 / exact10 remain distinct')
base_tree=tree(BASE);art_tree=tree(ART)
images=[i for a in render['archives'] for i in a['selected_images']]
bad_art=[]
for a in render['archives']:
 if art_tree.get(a['manifest_path'],{}).get('sha')!=a['manifest_blob_at_pin']:bad_art.append(a['manifest_path'])
 for i in a['selected_images']:
  if art_tree.get(i['path'],{}).get('sha')!=i['git_blob_sha']:bad_art.append(i['path'])
check('all pinned render manifests/images exist with exact Git blobs',not bad_art,{'manifests':len(render['archives']),'selected_records':len(images),'bad_paths':bad_art})
paths={i['path']:i for i in images}
shorts=[i for r in rows for i in r.get('selected_render_starting_points',[])]
check('task-specific exact-image bindings match register',all(i['path'] in paths and i['git_blob_sha']==paths[i['path']]['git_blob_sha'] and i['sha256']==paths[i['path']]['sha256'] for i in shorts),len(shorts))
check('recorded inspection scope is honest',refs['fresh_visual_review']['contact_sheets_inspected_count']==19 and refs['full_playback_claimed'] is False and refs['audio_listening_claimed'] is False,'19 contact sheets, no full playback/listening claim')
plan=ROOT/'Docs/Production/HAVENLINE_BUILD_PLAN_V2.md';old=git('show',f'{BASE}:{plan.relative_to(ROOT)}');new=plan.read_text()
def task_columns(text):return {m.group(1):m.group(2).split('|')[:2] for m in re.finditer(r'^\| (T\d\d) \| (.*)$',text,re.M)}
check('original task table definitions/statuses retained',task_columns(old)==task_columns(new),'Only research-link column added')
oldaudio=old.split('## T54 — Music, sound effects and event coverage',1)[1].split('## Wave checkpoint',1)[0]
newaudio=new.split('## T54 — Music, sound effects and event coverage',1)[1].split('## Wave checkpoint',1)[0]
check('existing T54 coverage unchanged',oldaudio==newaudio,'Exact text comparison')
check('no operational workflows in base',not any(p.startswith('.github/') for p in base_tree),'Consolidation workflow boundary retained')
changed=git('diff','--name-only',BASE).splitlines()+git('ls-files','--others','--exclude-standard').splitlines()
allowed=['README.md','REPOSITORY_INDEX.md','BUILD_GAME.md','Docs/Production/HAVENLINE_BUILD_PLAN_V2.md','Docs/Production/TASK_PLAN_REFRESH_2026-11-27.md']
check('only authorized documentation paths changed',all(p in allowed or p.startswith('Docs/Production/ReferenceRefresh/2026-11-27/') for p in changed),changed)
check('all protected tracked files remain byte-identical',not any(p not in allowed and not p.startswith('Docs/Production/ReferenceRefresh/2026-11-27/') for p in git('diff','--name-only',BASE).splitlines()),'Runtime, workflows, assets, dependency/status registries and historical archive untouched')

def anchor(text):
 text=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',text)
 text=text.replace('`','').replace('*','').strip().lower()
 return ''.join(c for c in text if c in '-_ ' or unicodedata.category(c)[0] in 'LN').replace(' ','-')
def anchors(p):return {anchor(m.group(1)) for m in re.finditer(r'^#{1,6} (.+?)\s*$',p.read_text(),re.M)}
mds=[ROOT/p for p in changed if p.endswith('.md') and (ROOT/p).exists()]
badlinks=[];relative_count=0;checked_anchors=0
for p in mds:
 for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  if target.startswith(('https://','http://','mailto:')):continue
  filepart,sep,frag=target.partition('#');dest=(p.parent/filepart).resolve() if filepart else p
  try:rel=dest.relative_to(ROOT).as_posix()
  except ValueError:badlinks.append({'file':str(p.relative_to(ROOT)),'target':target,'why':'outside repo'});continue
  relative_count+=1
  known=dest.exists() or rel in base_tree or any(x.startswith(rel.rstrip('/')+'/') for x in base_tree)
  if not known:badlinks.append({'file':str(p.relative_to(ROOT)),'target':target,'why':'missing'});continue
  if frag and dest.exists() and dest.is_file() and dest.suffix=='.md':
   checked_anchors+=1
   if frag not in anchors(dest):badlinks.append({'file':str(p.relative_to(ROOT)),'target':target,'why':'anchor missing'})
check('relative Markdown links and available anchors resolve',not badlinks,{'relative_links':relative_count,'anchors':checked_anchors,'errors':badlinks})
protected=[p for p in base_tree if p not in allowed]
report={'scope':'Documentation validation only; not game tests or visual acceptance','base_main_sha':BASE,'art_pin':ART,'checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'protected_base_paths':len(protected),'checks':checks}
(HERE/'VALIDATION.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(report,indent=2,ensure_ascii=False))
raise SystemExit(0 if all(c['passed'] for c in checks) else 1)
