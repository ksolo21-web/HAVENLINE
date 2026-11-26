import contextlib,io,hashlib,sys,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
from support import connected
root=Path(__file__).resolve().parents[1]; p=root/'hvn-l1-clean-character-rerig-v1'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
for d,m in [(root/'hvn-l1-clean-character-contact-feasibility-v1','21bd75670cd7b3ce8e9ddd4525159237f2c675ee1da7b65de4ba461b3ff88ea4'),(root/'hvn-l1-clean-rig-crossing-cause-v1','6554aa931658c2e18da7f9700c59c67283d2704e2501f31b4a35c03e076a4658'),(root/'hvn-l1-clean-character-grounded-first-v1','19c8393eec06d0ea77bf497173c68ca61c046448da68465ee7648ad8cfa45450'),(p,'9b405654e2bcb626a3b97be159fca3e487f6a11bd6bc69a4736f7727d0e0b29f'),(root/'hvn-l1-c1-stock66-contact-first-v1','5894bae40aa1486de7ea979eeabe2c1a0007124afe35c6114a75ca4e2a7d21fd')]:
 assert sha(d/'SHA256SUMS')==m
 for line in (d/'SHA256SUMS').read_text().splitlines():
  h,q=line.split();assert sha(d/q)==h
# Material/scale/camera and authored terrain source custody only. No old bone/pose is reused.
sys.path.append(str(root/'hvn-l1-c1-stock66-contact-first-v1'))
with contextlib.redirect_stdout(io.StringIO()):
 import run as stock
rec=json.loads((p/'result.json').read_text())
out=p/'build-output.LOCAL'
assert {n:sha(out/n) for n in rec['local_payload_hashes']}==rec['local_payload_hashes']
rig=json.loads((out/'rig.LOCAL.json').read_text()); ss=np.load(out/'skin.LOCAL.npz',allow_pickle=False)
N=rig['new_bones']; slots=rig['weighted_slots']
indices=ss['joints']; weights=ss['weights'].astype(float)
V,TR=stock.V,stock.TR
Mh=stock.asset_world;S=Mh[0,0]
assert np.allclose(Mh[:3,:3],S*np.eye(3),atol=1e-7)
world=Mh[:3,3]
assert len(V)==len(indices)==52898 and len(TR)==96001
Weld=stock.weld
rest=V*S+world
B={n:np.asarray(v['global_bind']) for n,v in N.items()}
inv=np.stack([np.linalg.inv(B[k]) for k in slots])
p4=np.column_stack([V,np.ones(len(V))])
roll={'L':(-3.,0.),'R':(4.,-4.)} # world +X sends forward toward -Y
shift={'L':.080,'R':-.080}
def current_point(k):return B[k][:3,3]
def move(r,a,b):return stock.move(r,a,b)
identity=np.eye(3)
def pose_frames(override):
 H={}
 for n,meta in N.items():
  pa=meta['parent'];H[n]=B[n] if pa is None else H[pa]@np.asarray(meta['local_bind'])
  if n in override:H[n]=override[n]
 return H
def skin(H,mat=False):
 M=np.stack([H[n] for n in slots])@inv
 out=sum((M[indices[:,i]]@p4[:,:,None])[:,:3,0]*weights[:,i,None] for i in range(4))*S+world
 return (out,M) if mat else out
def joint_support():
 control={'Pelvis':move(identity,[0,0,0],[0,root_Pelvis_y/S,0])@B['Pelvis']}
 for s in 'LR':
  a0,k0,b0,t0=[current_point(s+n) for n in ('Hip','Shin','Heel','Ball')]
  a=a0+[0,root_Pelvis_y/S,0]
  q=(np.asarray(exact['anchor_solve'][s]['authored_ankle_target_world'])-world)/S
  assert abs((q-b0)[2]*S-shift[s])<1e-10
  u=q-a;d=np.linalg.norm(u);u/=d
  A,Bb=np.linalg.norm(k0-a0),np.linalg.norm(b0-k0)
  assert abs(A-Bb)<d<A+Bb and (A+Bb-d)*S>=.003-1e-12
  assert abs(float(exact['anchor_solve'][s]['retained_extension_reserve_mm'])-(A+Bb-d)*S*1000)<1e-9
  x=(A*A-Bb*Bb+d*d)/(2*d)
  n=np.array([0.,0.,1.]);n-=u*(u@n);n/=np.linalg.norm(n)
  k=a+x*u+n*np.sqrt(A*A-x*x)
  R0=stock.swing(k0-a0,k-a);R1=stock.swing(b0-k0,q-k)
  slope=Rotation.from_euler('x',roll[s][0],degrees=True).as_matrix()
  ball=Rotation.from_euler('x',roll[s][0]+roll[s][1],degrees=True).as_matrix()
  control[s+'Hip']=move(R0,a0,a)@B[s+'Hip']
  control[s+'Shin']=move(R1,k0,k)@B[s+'Shin']
  control[s+'Heel']=move(slope,b0,q)@B[s+'Heel']
  # The softened collar is not a post-skin patch; it has its newly authored native frame and weights.
  axis=Rotation.from_matrix(R1.T@slope).as_rotvec()
  collar=R1@Rotation.from_rotvec(axis*.5).as_matrix()
  c0=current_point(s+'CollarFlex')
  control[s+'CollarFlex']=move(collar,c0, k+R1@(c0-k0))@B[s+'CollarFlex']
  t=q+slope@(t0-b0)
  control[s+'Ball']=move(ball,t0,t)@B[s+'Ball']
  for name,node in N.items():
   if name.startswith('Rigid_'+s+'_Boot'):
    assert node['parent']==s+'Heel'
 return pose_frames(control)
masks={}; near=[]
for s,sg in [('L',1),('R',-1)]:
 legnames=[s+t for t in ('Heel','Ball','CollarFlex','Shin','Hip')]
 mass=(weights*np.isin(indices,[slots.index(n) for n in legnames])).sum(1)
 footreg=(V[:,1]<current_point(s+'Shin')[1]-.048)&(sg*(V[:,0]-.014)>.038)
 sslot=slots.index(s+('Heel' if s=='L' else 'Ball'))
 w=(weights*(indices==sslot)).sum(1)
 floor=V[footreg,1].min()
 phys=footreg&(V[:,1]<floor+.023)&(w>.96)
 f=TR[phys[TR].all(1)]
 assert len(f)>10
 masks[s]=(footreg,f,mass)
def heights(x,idx):
 return np.asarray([row[1]-stock.height(*row[[0,2]]) for row in x[idx]])
unposed=skin(pose_frames({}))
old_floor={k:float(np.min(heights(unposed,dd[0]))) for k,dd in masks.items()}
datum=.00015-min(old_floor.values())
co=move(np.eye(3),[0,0,0],[0,datum/S,0])@B['Pelvis']
neutral=skin(pose_frames({'Pelvis':co}))
neutral_floor={k:float(np.min(heights(neutral,dd[0]))) for k,dd in masks.items()}
assert all(x>=-.001 for x in neutral_floor.values())
exact=json.loads((root/'hvn-l1-clean-character-contact-feasibility-v1'/'result.json').read_text())
assert exact['status']=='PREFLIGHT_FEASIBLE_HARD_ANCHORS_ONLY_NO_POSE' and exact['roll_art_plus_x']=={k:list(v) for k,v in roll.items()}
assert abs(exact['common_datum_mm']-datum*1000)<1e-12
root_Pelvis_y=exact['final_pelvis_world_control_offset_mm']/1000
H=joint_support();Y,T=skin(H,True)
for label in ('L','R'):
 for bone,expected in [('Heel',roll[label][0]),('Ball',sum(roll[label]))]:
  k=label+bone
  D=H[k]@np.linalg.inv(B[k])
  x=Rotation.from_matrix(D[:3,:3]).as_rotvec()
  assert np.max(abs(x-np.deg2rad(expected)*np.array([1.,0.,0.])))<1e-11
assert np.array_equal(H['Root'],B['Root']) and max(np.linalg.norm(H[s+'Heel']-B[s+'Heel']) for s in 'LR')>.03
edges=stock.edges
elen=np.linalg.norm(rest[edges[:,1]]-rest[edges[:,0]],axis=1);spent=np.linalg.norm(Y[edges[:,1]]-Y[edges[:,0]],axis=1)
ratio=spent/np.maximum(elen,1e-12);results={}
for s,(foot,F,mass) in masks.items():
 P=Y[:,[0,2,1]].copy()
 P[foot,2]=heights(Y,foot)
 support=connected(P,F,Weld)
 nearleg=(mass[edges].mean(1)>.90)&(V[edges,1].mean(1)<.270)&(elen>.0008)
 fa=np.flatnonzero(nearleg&((ratio<.5)|(ratio>2.)))
 kk=[H[s+n][:3,3] for n in ('Hip','Shin','Heel')]
 a,b=kk[0]-kk[1],kk[2]-kk[1]
 angle=float(np.rad2deg(np.arccos(np.clip(a@b/(np.linalg.norm(a)*np.linalg.norm(b)),-1,1))))
 results[s]=dict(heel_or_ball_support=support,internal_knee_deg=angle,grounded_leg_min_mm=float(P[foot,2].min()*1000),frozen_world_ankle=exact['anchor_solve'][s]['authored_ankle_target_world'],guarded_edges=int(nearleg.sum()),guard_failures=len(fa),guard_min_max_ratio=[float(ratio[nearleg].min()),float(ratio[nearleg].max())],worst_failed_raw_rows=edges[np.flatnonzero(nearleg)[ratio[nearleg].argmin()]].tolist())
# True local full triangles vs any potentially overlapping nonadjacent body triangle.
# Report static neutral relation and pose relation; no complete continuous collision claim.
mask=(V[:,1]<.32)
active=np.flatnonzero(mask[TR].any(1))
def mesh_overlap(P):
 xyz=P[TR];m=xyz.min(1);M=xyz.max(1);c=(m+M)*.5
 q=np.linalg.norm(M-c,axis=1);tree=cKDTree(c);qmax=q.max()
 pairs=[]
 def strict(X,Y):
  for a,b in ((X,Y),(Y,X)):
   O,U,Z=b; U=U-O; Z=Z-O
   p=np.roll(a,-1,axis=0)-a
   C=np.cross(p,Z);det=C@U
   ok=np.abs(det)>1e-13
   ds=np.where(ok,det,1.)
   v=a-O;u=(C*v).sum(1)/ds; g=np.cross(v,U)
   z=(p*g).sum(1)/ds; t=g@Z/ds
   if np.any(ok&(np.minimum.reduce([u,z,1-u-z,t,1-t])>1e-7)):return True
  return False
 checked=set()
 for i in active:
  I=np.asarray(tree.query_ball_point(c[i],qmax+q[i]+1e-10),dtype=int)
  I=I[((m[I]<=M[i]+1e-10)&(M[I]>=m[i]-1e-10)).all(1)]
  I=I[~np.isin(Weld[TR[I]],Weld[TR[i]]).any(1)]
  for j in I:
   j=int(j); pair=tuple(sorted((int(i),j)))
   if pair in checked:continue
   checked.add(pair)
   if strict(xyz[i],xyz[j]):pairs.append(pair)
 return set(pairs)
nb=mesh_overlap(rest);na=mesh_overlap(Y)
def normal(P):return np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0])
nr=normal(rest[TR[active]]); ny=normal(Y[TR[active]])
D=sum(T[indices[:,i],:3,:3]*weights[:,i,None,None] for i in range(4))
frame=D[TR[active]].mean(1)
# Compare geometric face normal to its independently transported bind normal.
pred=(frame@nr[:,:,None])[:,:,0]
orient=int(np.sum(((pred*ny).sum(1)<=0)&(np.linalg.norm(nr,axis=1)>1e-12)))
# Kinematic table only generated in memory. No pose output for a rejected specimen.
status='REJECT_FRESH_RIG_CALIBRATED_V3_KEY' if len(na-nb) or orient or any(a['guard_failures'] or a['grounded_leg_min_mm']<-1 or not a['heel_or_ball_support']['largest_face_count'] for a in results.values()) else 'PRELIMINARY_KEY_ONLY'
print(json.dumps(dict(status=status,initial_new_rig_digest=rec['local_payload_hashes']['rig.LOCAL.json'],stride_m=.16,key_angle_deg=roll,pose_uses_exact_frozen_true_ankle_targets=True,whole_control_datum_mm=datum*1000,final_pelvis_offset_world_mm=root_Pelvis_y*1000,original_neutral_floor_before_mm={k:a*1000 for k,a in old_floor.items()},corrected_neutral_floor_mm={k:a*1000 for k,a in neutral_floor.items()},gameplay_root_transform_exact=True,parts=results,checked_lower_faces=len(active),strict_nonadjacent_pairs_rest_key=[len(nb),len(na)],new_strict_pairs=len(na-nb),prior_v1_named_pair_still_present=((8674,8916) in na),first_new_strict_pair=list(map(int,min(na-nb))) if na-nb else None,orientation_alarms=orient,actual_game_world_camera_source=True,native_engine_or_render=False),indent=2))
