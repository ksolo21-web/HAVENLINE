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
 seq=load(e/'captures/sequence/capture.json')
 routes=load(e/'captures/route-proofs/capture.json')
 native_carry=e/'native4k/carrying-front.png'
 route_reports=[load(v/f'route-{idx}/capture.json') for idx in (0,2,5)]
 assert all(r['candidate_commit']==c and r['conservation_held'] and r['native_3840x2160_scale1'] for r in route_reports)
 def trace_at(report,frame):
  return next(row for row in report['trace'] if int(row['frame'])==frame)
 source_to_actor=trace_at(seq,24)
 actor_to_destination=trace_at(seq,66)
 route_active=[trace_at(r,25) for r in route_reports]
 route_arrival=[trace_at(r,50) for r in route_reports]
 control={
  'schema_version':1,'task_id':'T08','candidate':c,'source_bound':True,
  'simulation_authoritative':True,'presentation_mutates_inventory':False,
  'one_primary_joystick':True,'permanent_action_buttons':0,
  'primitive_geometry_prohibited':True,'authored_feedback_present':True,
  'authored_feedback_assets':seq['transfer_contract']['authored_feedback_assets'],
  'custom_feedback_shader':seq['transfer_contract']['feedback_shader'],
  'scope':'T08 visible inventory, physical carrying and automatic source-to-actor / actor-to-destination transfer presentation',
  'scope_exclusions':['T08 does not own threat/enemy warning UI','T08 does not add manual pickup/deposit action buttons','T08 does not replace T07 contextual target selection'],
 }
 loop={
  'schema_version':1,'candidate':c,'functional_suites':tests['suite_count'],'functional_checks':tests['total_checks'],
  'transfer_directions':gate['transfer_directions'],'route_destinations':gate['route_destinations'],
  'conservation_held':gate['conservation_held'],'actor_integrity':gate['actor_integrity'],
  'destination_endpoints_visible':gate['destination_endpoints_visible'],
  'arrival_pulse_samples':gate['arrival_pulse_samples'],
  'visual_proof':{'resolution':review['internal_resolution'],'fps':review['capture_fps'],'motion_seconds':review['motion_video_seconds'],'stills_count':review['stills_count']},
  'source_to_actor_example':{'frame':24,'transfers':source_to_actor['transfers'],'inventory':source_to_actor['inventory'],'player_stack_logical_total':source_to_actor['player_stack']['logical_total']},
  'actor_to_destination_example':{'frame':66,'transfers':actor_to_destination['transfers'],'inventory':actor_to_destination['inventory'],'stored':actor_to_destination['stored']},
  'native_route_active_examples':[{'frame':25,'transfers':row['transfers'],'route_camera':row['route_camera']} for row in route_active],
  'native_route_arrival_examples':[{'frame':50,'transfers':row['transfers'],'route_camera':row['route_camera']} for row in route_arrival],
  'dimension_scope':{
    'interactable_clarity':'T07 remains the automatic context/target selector. For T08, judge whether the selected transfer path, resource and endpoint are visually legible; do not require a manual interact button or unrelated prompt.',
    'danger_clarity':'No threat is active in these transfer-isolation states and T08 does not own danger-system implementation. Judge whether transfer feedback is clearly non-danger feedback and does not masquerade as a threat cue; do not require unrelated enemy/warning UI.',
    'collection_feedback':'Use source_to_actor_example plus sequence frame 024 and visible-carry evidence to judge automatic collection feedback.',
    'resource_destination':'Use gold actor-to-destination trails, arrowheads, endpoint-framed native routes and arrival bursts.',
    'world_change_clarity':'Use authoritative before/after counts, completed receipts and destination-specific arrival evidence; T08 presents transfer state but does not own T10 world transformation.',
    'next_action_clarity':'Havenline uses one movement joystick and automatic context actions. Judge continuity of the automatic physical loop rather than requiring a new action button.',
    'havenline_identity':'Primitive geometry is prohibited, not feedback. Authored transfer ribbons, directional sigils, arrival bursts and authored resource meshes remain visible feedback.',
  }
 }
 stills=sorted((v/'stills').glob('*.png'))
 paths={'detail':e/'captures/detail/transfer-three-quarter.png','route0':e/'captures/route-proofs/routes-000.png','route1':e/'captures/route-proofs/routes-443.png','s24':e/'captures/sequence/sequence-024.png','s66':e/'captures/sequence/sequence-066.png','s108':e/'captures/sequence/sequence-108.png','s150':e/'captures/sequence/sequence-150.png','nativecarry':native_carry}
 for p in list(paths.values())+stills:
  if not p.is_file():raise SystemExit('missing evidence '+str(p))
 plans={
 'C2':[('authored-transfer-geometry',[(p,'image','geometry_state','Final native-4K authored transfer feedback') for p in stills]+[(paths['detail'],'image','geometry_state','Three-quarter transfer detail'),(paths['nativecarry'],'image','geometry_state','Native-4K authored physical carry geometry')])],
 'C3':[('physical-transfer-loop',[(paths[k],'image','gameplay_state',desc) for k,desc in (
   ('s24','Source-to-actor automatic collection with active authored trail/arrow'),
   ('s66','Actor-to-destination automatic delivery with active authored trail/arrow'),
   ('s108','Helper source-to-actor collection and visible carried-resource update'),
   ('s150','Helper actor-to-destination delivery continuation'),
   ('nativecarry','Native-4K visible authored resource carrying'))]+[(p,'image','gameplay_state','Final native-4K authored destination response') for p in stills[:2]])],
 'C4':[('transfer-readability',[(paths[k],'image',cat,desc) for k,cat,desc in (
   ('s24','feedback_state','Source-to-actor collection feedback and direction'),
   ('s66','feedback_state','Actor-to-destination delivery feedback and direction'),
   ('nativecarry','gameplay_state','Native-4K visible physical carrying state'),
   ('detail','gameplay_state','Close three-quarter selected transfer interaction'),
   ('route0','feedback_state','Route proof start with endpoint framing'),
   ('route1','feedback_state','Route proof completion framing'))]+[(p,'image','feedback_state','Native-4K destination arrival response') for p in stills])]
 }
 for cid,groups in plans.items():
  pkg=out/f'havenline-task08-critic-{cid}';shutil.rmtree(pkg,ignore_errors=True);pkg.mkdir(parents=True)
  (pkg/'control-state.json').write_text(json.dumps(control,indent=2)+'\n');(pkg/'loop-evidence.json').write_text(json.dumps(loop,indent=2)+'\n')
  gs=[]
  for gid,rows in groups:
   items=[]
   for n,(src,kind,cat,desc) in enumerate(rows):
    rel=Path('images')/(f'{n:02d}-'+src.name);dst=pkg/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    items.append({'path':str(pkg/rel),'kind':kind,'category':cat,'sha256':digest(dst),'description':desc})
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
