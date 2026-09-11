#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[3]
CLI=ROOT/'tools/havenline/production/production_cli.py'

def run(*args,ok=True):
 p=subprocess.run(['python3',str(CLI),*args],cwd=ROOT,text=True,capture_output=True)
 if ok and p.returncode!=0:raise AssertionError((args,p.stdout,p.stderr))
 if not ok and p.returncode==0:raise AssertionError(('expected failure',args,p.stdout))
 return p

checks=[]
def check(name,fn):
 fn();checks.append(name)

check('registry validates',lambda:run('validate-registry'))
check('T03 owned path allowed',lambda:run('validate-candidate','T03','HavenlineGodot/scripts/camp_boundary.gd'))
check('T03 approved river authority rejected',lambda:run('validate-candidate','T03','HavenlineGodot/scripts/river_geometry.gd',ok=False))
check('future worker shared integration path rejected',lambda:run('validate-candidate','T04','HavenlineGodot/scripts/main.gd',ok=False))
p=run('impact','HavenlineGodot/scripts/river_geometry.gd');assert json.loads(p.stdout)['impacted_tasks']==['T02','T03'];checks.append('impact maps river to T02/T03')
p=run('regression-plan','HavenlineGodot/scripts/reference_forest.gd');d=json.loads(p.stdout);assert 'test_reference_forest' in d['required_suites'] and 'test_task02_river' in d['required_suites'] and 'test_task03_boundary' in d['required_suites'];checks.append('impact regression includes all affected prior tasks')
with tempfile.TemporaryDirectory() as td:
 packet=Path(td)/'T04.md';run('task-packet','T04','--output',str(packet));s=packet.read_text();assert 'havenline/T04-camera' not in s or 'T04' in s;assert 'Base integration commit:' in s;checks.append('task packet generated with base commit')
 p=run('capture-plan','T06','--motion');d=json.loads(p.stdout);assert 'realtime_cycle' in d['deterministic_required_states'] and 'native_3840x2160_scale1_if_applicable' in d['deterministic_required_states'];checks.append('motion/capture plan complete')
 p=run('save-matrix','T14');assert 'interrupted_save' in json.loads(p.stdout)['cases'];checks.append('save matrix includes interrupted save')
 p=run('device-matrix','T07');assert 'foldable_inner_landscape' in json.loads(p.stdout)['classes'];checks.append('device matrix includes foldable')
 good={'gates':{**{f'G{i}':True for i in range(1,15)},'G9':'NOT_APPLICABLE','G10':'NOT_APPLICABLE','G11':'NOT_APPLICABLE'},'hashes_valid':True,'evidence_current':True,'unresolved_mandatory_defects':[],'critic_reviews':[{'critic_id':'C1','independent':True,'mandatory_dimensions':{'a':9.01,'b':10.0},'unresolved_defects':[]}]}
 # restore NA fields after dict expansion
 good['gates']['G9']='NOT_APPLICABLE';good['gates']['G10']='NOT_APPLICABLE';good['gates']['G11']='NOT_APPLICABLE'
 gp=Path(td)/'good.json';gp.write_text(json.dumps(good));run('closure',str(gp));checks.append('closure accepts strict >9')
 bad=json.loads(json.dumps(good));bad['critic_reviews'][0]['mandatory_dimensions']['a']=9.0;bp=Path(td)/'bad.json';bp.write_text(json.dumps(bad));run('closure',str(bp),ok=False);checks.append('closure rejects exactly 9.0')
 print(json.dumps({'passed':True,'checks':checks,'count':len(checks)},indent=2))
