from pathlib import Path
import numpy as np,json,hashlib,subprocess,runpy
from scipy.linalg import polar
from scipy.spatial.transform import Rotation
from scipy.spatial.transform import Slerp
B=Path(__file__).resolve().parent.parent
def get(n,h):
 p=B/n;assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
 return json.loads((p/('native-result.json' if (p/'native-result.json').exists() else 'result.json')).read_bytes())
r=get('hvn-l1-wood-paid-handoff-path-v1','fefeadd4dd25f70da48ef1a313f5c9341455fbe94aaf634472bc6bf2afa60477')
m=get('hvn-l1-wood-paid-two-piece-candidate-v1','2dbde03441fe996bab357c37291ee9cbe229bf7a4fbdaf0885313f90cac2c8f5')
a=get('hvn-l1-wood-paid-carry-capture-v1','af819aeb459d6835f43f1f5f015d78abc6916a561b3c3cd7190dfe08eb6a1b98')
e=get('hvn-l1-wood-storage-near-row-v1','b8f6061ab8f7b685beda4629ade265407b7bd5e5dfc649b2197a9b902b8767d6')
raw=B/'havenline-rendered-wood-ab-verified/project/assets/studio/starter_ground_wood_lod.glb'
tri,_=runpy.run_path(str(B/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](raw)
v=np.unique(tri.reshape(-1,3),axis=0); assert len(v)==834
start=m['samples'][0]; a0=a['native']; root=np.array(start['actor_world']); M=np.array(a0['carry_root_world']['basis_cols']).T
assert a0['tick']==start['tick']==1277 and start['actor_world']==a0['actor_world']['origin']
assert abs(start['actor_yaw']-np.arctan2(M[0,2],M[2,2]))<1e-6
cap=a0['actor_collisions'][0]; assert np.allclose(M,np.array(cap['world']['basis_cols']).T)
c=np.array(cap['world']['origin']); rr=cap['radius']; ht=cap['height']
assert abs(M[1,1]-1)<1e-9
def xz(o):return o[..., [0,2]]
def gap(lo,hi,otherlo,otherhi):return np.max(np.maximum(otherlo-hi,lo-otherhi),axis=-1)
leaves=[]
signs=np.array([[i,j,k] for i in [-1,1] for j in [-1,1] for k in [-1,1]])
for gate in a0['gates']:
 assert gate['target_open']==(gate['gate_id']=='gate-south')
 assert np.isclose(gate['angle'],np.pi/2 if gate['target_open'] else 0)
 for box in gate['leaf_boxes']:
  assert box['layer']==1
  T=np.array(box['shape_world']['basis_cols']); pp=np.array(box['shape_world']['origin'])
  x=xz((signs*np.array(box['size'])/2)@T+pp); leaves.append((x.min(0),x.max(0)))
pick=[]; park=[]
for i,o in enumerate(r['motion']):
 p=np.array(o['origin_keys_m']); assert np.max(abs(p[0]-(M@np.array(start['stock_on_real_actor'][i]['local'])+root)))<1e-6
 assert np.array_equal(p[3],e['detached_log_transforms'][i]['t_source_to_source_world'])
 R=np.array(o['rest_basis_rows']);assert np.array_equal(R,e['detached_log_transforms'][i]['R_source_to_source_world'])
 pick.append(v@M.T+p[0]);park.append(v@R.T+p[-1])
camR=np.array([11.,0,-7.]); camR/=np.linalg.norm(camR)
camB=np.array([7.,11,11]);camB/=np.linalg.norm(camB);camU=np.cross(camB,camR)
lens=np.stack([camR,camU])*720/13
report=[]
for i,o in enumerate(r['motion']):
 p=np.array(o['origin_keys_m']); ts=np.array(o['times_s']); R=np.array(o['rest_basis_rows']); delta=np.diff(p,axis=0); duration=ts[-1]-ts[0]
 q0,s0=polar(M);q1,s1=polar(R); SL=Slerp([0,1],Rotation.from_matrix(np.stack([q0,q1])))
 obs=[]; rad=[]
 for k in range(3):
  u=np.linspace(0,1,129);f=3*u*u-2*u*u*u
  O=p[k]+f[:,None]*delta[k]
  if k==1:
   for x in [s0,s1]:assert np.linalg.norm(x,2)<=max(1,np.linalg.norm(M,2))+1e-10
   matrices=SL(f).as_matrix()@(s0+f[:,None,None]*(s1-s0))
  else: matrices=np.repeat((M if k==0 else R)[None,:,:],len(f),axis=0)
  w=np.einsum('nab,vb->nva',matrices,v)+O[:,None,:]
  min_leaf=min(float(min(gap(xz(w).min(1),xz(w).max(1),lo,hi))) for lo,hi in leaves); assert min_leaf>0; obs.append(min_leaf)
  # True vertical capsule is segment capped by sphere. Independent vertex distances are cross-check, not whole-triangle certificate.
  caphalf=ht/2-rr; to=w-c; to[:,:,1]-=np.clip(to[:,:,1],-caphalf,caphalf)
  rad.append(float(np.linalg.norm(to,axis=2).min()-rr)); assert rad[-1]>0
  other=pick[1] if i==0 else park[0]
  if k==0 and i==0:
   z=(w-root)@np.linalg.inv(M).T; zother=(other-root)@np.linalg.inv(M).T
  else:z=w;zother=other
  assert min(gap(z.min(1),z.max(1),zother.min(0),zother.max(0)))>.001
 # Smoothstep speeds are true segment speeds, not inferred physically from the reference.
 peak=1.5*np.linalg.norm(delta,axis=1)/np.diff(ts);assert np.allclose(peak,o['peak_translation_m_s'])
 report.append(dict(duration_s=duration,path_m=float(np.linalg.norm(delta,axis=1).sum()),
  average_path_m_s=float(np.linalg.norm(delta,axis=1).sum()/duration),
  min_possible_peak_for_this_path_and_easing_m_s=float(1.5*np.linalg.norm(delta,axis=1).sum()/duration),
  chosen_peak_m_s=float(peak.max()), max_screen_peak_px_per_60hz_frame=float(np.max(1.5*np.linalg.norm(delta@lens.T,axis=1)/np.diff(ts)/60)),
  minimum_sampled_actual_leaf_aabb_gap_m=min(obs), minimum_sampled_capsule_vertex_gap_m=min(rad)))
assert r['motion'][0]['times_s'][-1]<r['motion'][1]['times_s'][0]
print(json.dumps(dict(reviewed_static_continuous_envelope=True,independent_dense_checks_per_segment=129,gate_matrices_four_layer1=True,xyz_scale_residue=float(np.linalg.norm(M.T@M-np.eye(3),2)),motions=report,needs_actual_same_camera_motion_review=True),indent=2))
