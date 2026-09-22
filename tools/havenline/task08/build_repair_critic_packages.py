#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--evidence',required=True);ap.add_argument('--visual',required=True);ap.add_argument('--out-root',required=True);a=ap.parse_args()
 c=a.candidate;e=Path(a.evidence);v=Path(a.visual);out=Path(a.out_root);out.mkdir(parents=True,exist_ok=True)
 tests=load(e/'tests.json');gate=load(e/'capture-gate.json');perf=load(e/'integrated-performance-gate.json');review=load(v/'review-manifest.json')
 assert tests['source']==gate['candidate_commit']==review['candidate_sha']==c
 assert tests['all_passed'] and gate['passed'] and perf['passed'] and review['ready_for_user_visual_review']
 assert review['primitive_findings_count']==0 and review['capture_fps']>=59.9 and review['motion_video_seconds']>=3
 control={'schema_version':1,'task_id':'T08','candidate':c,'source_bound':True,'simulation_authoritative':True,'mutates_inventory':False,'one_primary_joystick':True,'permanent_action_buttons':0,'primitive_feedback_allowed':False,'scope':'T08 visible inventory, carrying and automatic transfer presentation'}
 loop={'schema_version':1,'candidate':c,'functional_suites':tests['suite_count'],'functional_checks':tests['total_checks'],'transfer_directions':gate['transfer_directions'],'route_destinations':gate['route_destinations'],'conservation_held':gate['conservation_held'],'actor_integrity':gate['actor_integrity'],'visual_proof':{'resolution':review['internal_resolution'],'fps':review['capture_fps'],'motion_seconds':review['motion_video_seconds'],'stills_count':review['stills_count']}}
 stills=sorted((v/'stills').glob('*.png'))
 paths={'detail':e/'captures/detail/transfer-three-quarter.png','route0':e/'captures/route-proofs/routes-000.png','route1':e/'captures/route-proofs/routes-443.png','s24':e/'captures/sequence/sequence-024.png','s66':e/'captures/sequence/sequence-066.png','s108':e/'captures/sequence/sequence-108.png','s150':e/'captures/sequence/sequence-150.png'}
 for p in list(paths.values())+stills:
  if not p.is_file():raise SystemExit('missing evidence '+str(p))
 plans={
 'C2':[('authored-transfer-geometry',[(p,'image','geometry_state','Final native-4K authored transfer feedback') for p in stills]+[(paths['detail'],'image','geometry_state','Three-quarter transfer detail'),(paths['route0'],'image','geometry_state','Route start cross-view'),(paths['route1'],'image','geometry_state','Route end cross-view')])],
 'C3':[('physical-transfer-loop',[(paths[k],'image','gameplay_state','Automatic physical transfer-loop state') for k in ('s24','s66','s108','s150')]+[(p,'image','gameplay_state','Final authored destination feedback') for p in stills])],
 'C4':[('transfer-readability',[(p,'image','feedback_state','Final native-4K destination/direction feedback') for p in stills]+[(paths['detail'],'image','gameplay_state','Three-quarter transfer interaction'),(paths['route0'],'image','feedback_state','Route start/direction feedback'),(paths['route1'],'image','feedback_state','Route completion/destination feedback')])]
 }
 for cid,groups in plans.items():
  pkg=out/f'havenline-task08-critic-{cid}';shutil.rmtree(pkg,ignore_errors=True);pkg.mkdir(parents=True)
  (pkg/'control-state.json').write_text(json.dumps(control,indent=2)+'\n');(pkg/'loop-evidence.json').write_text(json.dumps(loop,indent=2)+'\n')
  gs=[]
  for gid,rows in groups:
   items=[]
   for n,(src,kind,cat,desc) in enumerate(rows):
    rel=Path('images')/(f'{n:02d}-'+src.name);dst=pkg/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    items.append({'path':str(Path('critic-input')/rel),'kind':kind,'category':cat,'sha256':digest(dst),'description':desc})
   if cid=='C3':
    items += [
     {'path':str(pkg/'control-state.json'),'kind':'json','category':'control_state','sha256':digest(pkg/'control-state.json'),'description':'T08 control/authority contract'},
     {'path':str(pkg/'loop-evidence.json'),'kind':'json','category':'loop_evidence','sha256':digest(pkg/'loop-evidence.json'),'description':'Exact repaired transfer-loop/conservation proof'}]
   if cid=='C4':
    items.append({'path':str(pkg/'control-state.json'),'kind':'json','category':'gameplay_state','sha256':digest(pkg/'control-state.json'),'description':'T08 gameplay/control context'})
   gs.append({'id':gid,'items':items})
  (pkg/'critic-manifest.json').write_text(json.dumps({'schema_version':1,'task_id':'T08','critic_id':cid,'candidate_commit':c,'groups':gs},indent=2)+'\n')
 print(json.dumps({'passed':True,'task_id':'T08','candidate':c,'critics':['C2','C3','C4'],'checks':tests['total_checks']},indent=2))
if __name__=='__main__':main()
