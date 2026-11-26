"""Counter rig evidence intake only: rotation-only reach bound, no authored path."""
import contextlib,io,runpy,sys,json,hashlib,struct
from pathlib import Path
import numpy as np
checker,root,raw,project,stockpoint=map(Path,sys.argv[1:]); argv=sys.argv[:]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(checker)=="bac196184a601ef867b58baf81f9018949ca2cc46d7b2faf3f828d4ff87b8864"
assert sha(stockpoint)=="f8d9c66fc62e03d33bb0c991f06aa2cd915eb7bd0f1a4a45b36473f84c2a3a41"
for f,h in {"layout.json":"e3fc7eb561ae7288d4dc77ffc47b05cac924e8bb2dc2b99ec789a33d430f4458","opening.gd":"d1a8d6901a8d52a5c5084f19fe429c376800189c46dbeaea9a4012c7a72c59c1","previews/integrated_opening.gd":"29fc86cd076f98169e730bf59aacb63b25b4c28aef4326459679324169e3eba9"}.items():
 assert sha(project/f)==h
sys.argv=[str(checker),str(root),str(raw)]
with contextlib.redirect_stdout(io.StringIO()): w=runpy.run_path(str(checker))
sys.argv=argv
asset=project/"assets/characters/Character1.glb"; assert sha(asset)=="95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099"
b=asset.read_bytes();n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]); rawbin=b[28+n:]
def read(i):
 a=d['accessors'][i];v=d['bufferViews'][a['bufferView']]
 assert a['componentType']==5126 and 'byteStride' not in v
 width={'SCALAR':1,'VEC3':3}[a['type']]
 return np.frombuffer(rawbin,dtype='<f4',count=width*a['count'],offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width).astype(float)
pr=d['meshes'][0]['primitives'][0]; verts=read(pr['attributes']['POSITION'])
nodes=d['nodes']; byname={v['name']: i for i,v in enumerate(nodes)}; parent={c:i for i,v in enumerate(nodes) for c in v.get('children',[])}
assert len(d['skins'][0]['joints'])==66
height=json.loads((project/'layout.json').read_text())['actor_height']; fit=height/np.ptp(verts[:,1])
base=lambda i:np.array(nodes[i].get('translation',[0,0,0]))
def to_spine(n):
 i=byname[n]; a=[]
 while nodes[i]['name']!='Spine02':
  a.append(i);i=parent[i]
 return a
inside=w['got'][0]['measurements']
head,err=w['infer'](np.array([inside['Head:'+name]['straight_pivot_distance_m'] for name in w['marker_names']]),1)
assert err<1e-6
old=json.loads(stockpoint.read_text()); target=np.array(old['selected']['point'])
def bound(ids,clip=None):
 maximum={}
 for i in ids:
  v=base(i)
  scale=np.array(nodes[i].get('scale',[1,1,1]));assert np.array_equal(scale,np.ones(3))
  if clip:
   for c in clip['channels']:
    t=c['target']
    if t['node']!=i: continue
    if t['path']=='scale':raise RuntimeError('scaled path')
    if t['path']=='translation':
     s=clip['samplers'][c['sampler']]; assert s.get('interpolation','LINEAR') in ('LINEAR','STEP')
     v=read(s['output'])
  maximum[nodes[i]['name']]=float(fit*np.max(np.linalg.norm(np.atleast_2d(v),axis=1)))
 return maximum
out={}
for side in ('L','R'):
 path=to_spine(side+'_Hand')
 assert [nodes[i]['name'] for i in path]==[side+'_Hand',side+'_Forearm',side+'_Upperarm',side+'_Clavicle']
 chain=to_spine('Head')+path
 seg=bound(chain); arm=path[:2]; idle=next(x for x in d['animations'] if x['name'].endswith(':idle'))
 fixed=sum(seg.values()); maximum=sum(bound(chain,idle).values()); dist=float(np.linalg.norm(head-target))
 wrist,err2=w['infer'](np.array([inside[side+'_Hand:'+name]['straight_pivot_distance_m'] for name in w['marker_names']]),1)
 assert err2<1e-6
 rest_arm=sum(bound(arm).values())
 rest_clav=sum(bound(path[:3]).values())
 delta=float(np.linalg.norm(target-wrist))
 # Both current and target wrists must be in the same fixed-joint ball;
 # pair separation cannot exceed its diameter, irrespective of paths.
 out[side]=dict(frozen_shoulder_wrist_to_target_distance_m=delta, frozen_shoulder_wrist_travel_diameter_cap_m=2*rest_arm, minimum_excess_beyond_fixed_shoulder_diameter_m=delta-2*rest_arm, frozen_clavicle_origin_wrist_travel_diameter_cap_m=2*rest_clav, excess_beyond_fixed_clavicle_origin_diameter_cap_m=delta-2*rest_clav, shoulder_to_elbow_plus_elbow_to_wrist_rest_m=rest_arm,nominal_head_to_wrist_path_cap_m=fixed,stored_idle_key_bound_head_to_wrist_cap_m=maximum,nearest_point_head_distance_m=dist,threshold_over_nominal_conservative_cap_m=dist-fixed,segment_lengths_m=seg)
print(json.dumps(dict(disposition='HOLD: no approved arm contact rig or body move; no path authored',actor_file_sha=sha(asset),stock_fit_uniform_scale=fit,rest_skin_height_pinned_m=height,exact_presentation_target=target.tolist(),exact_board_component_triangle_total=old['board_component_triangles'],near_lip_z_bound_m=old['board_component_far_z_m'],head_fit_error_m=err,stored_clips=[x['name'] for x in d['animations']],native_measurement_is_existing_idle_only=True,rotation_bound_same_head_point_only=True,wrist_not_fingertip=True,no_contact_rig=True,arms=out),indent=2))
