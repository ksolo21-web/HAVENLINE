"""Exact native plan replay against unchanged padded actor AABB, offline."""
from pathlib import Path
import json,sys,runpy,hashlib,subprocess
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(__file__).resolve().parent
mesh=Path(sys.argv[1])
tri,counts=runpy.run_path(str(p.parent/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](mesh)
points=np.unique(tri.reshape(-1,3),axis=0)
packet=p.parent/'hvn-l1-near-flight-live-body-observer-v1'
assert hashlib.sha256((packet/'SHA256SUMS').read_bytes()).hexdigest()=='7688c8843dc45af01e8212304615e6652841dbbdd49c8b77cc32aba064334f08'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=packet,check=True)
raw=(packet/'native.txt').read_text().splitlines()
def obj(label):
 rows=[x.split(' ',1)[1] for x in raw if x.startswith(label+' ')]
 assert len(rows)==1
 return json.loads(rows[0])
runner=p.parent/'hvn-l1-first-turn-guard-native-result-v1'
assert hashlib.sha256((runner/'SHA256SUMS').read_bytes()).hexdigest()=='246c2f698724b32c40949ded91eafd43af493ccdecafbfc2b1c8896cc7392308'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=runner,check=True)
other=(runner/'native.log').read_text().splitlines()
row=lambda lines,tag:[x.split(' ',1)[1] for x in lines if x.startswith(tag+' ')]
other_auth=json.loads(row(other,'EXAM_FIRST_MID_SUPPORT')[0])
assert other_auth['unchanged_input_sha256']==hashlib.sha256(row(raw,'EXAM_SUPPORT_INPUT')[0].encode()).hexdigest()
hold=row(other,'EXAM_FLIGHT_GEOM_HOLD')
assert len(hold)==1 and hold[0].startswith('1 1 [')
held=json.loads(hold[0][4:])
assert held[1]==-.00219279527664 and min(held[j] for j in (0,2,3))>.00008
assert row(raw,'EXAM_ADMISSION_PREFIX')==row(other,'EXAM_ADMISSION_PREFIX')
data=obj('EXAM_SUPPORT_INPUT')
faces=obj('EXAM_SUPPORT_GAPS')
b0,b1=np.asarray(data['body_padded_m'])
assert data['tick']==1333 and max(abs(np.asarray(data['pad_m'])-.025))<1e-8
assert data['needle_m']==.00008 and faces['i']==0
item=data['plan'][1]
assert item!=data['plan'][0]
def tf(r):
 o,*b=np.asarray(r)
 return o,np.asarray(b).T
m,M=tf(data['mount']); src,S=tf(item['source']); dest,D=tf(item['rest'])
keys=np.asarray(item['key'])
assert np.array_equal(keys[0],src) and np.array_equal(keys[3],dest)
J=np.linalg.inv(M)
centers=(keys[1:3]-m)@J.T
broad_min=centers.min(axis=0)-.23545
broad_max=centers.max(axis=0)+.23545
broad_faces=np.stack((b0-broad_max,broad_min-b1),axis=1).ravel()
assert abs(broad_faces.max()-(-.00219279527664185))<2e-6
def godot_rot(B):
 # Godot Basis.orthonormalized Gram-Schmidt in axis order.
 x,y,z=B.T.copy()
 x/=np.linalg.norm(x)
 y-=x*np.dot(x,y); y/=np.linalg.norm(y)
 z-=x*np.dot(x,z)+y*np.dot(y,z); z/=np.linalg.norm(z)
 R=np.array([x,y,z]).T
 assert np.linalg.det(R)>0.9999999
 return R
A=godot_rot(S); C=godot_rot(D)
Dres=np.linalg.norm(D-C,ord=2)
assert Dres<.00001
q=Rotation.from_matrix(A.T@C).as_rotvec(); angle=np.linalg.norm(q)
res=A.T@S-np.eye(3)
rho=float(np.linalg.norm(res,ord=2)); R=float(np.linalg.norm(points,axis=1).max())
assert rho<.00001 and R<=.23545 and 0<angle<np.pi
length=np.linalg.norm(keys[2]-keys[1])
jnorm=np.linalg.norm(J,axis=1)
def support(cloud):
 near=b0-cloud.max(axis=0); far=cloud.min(axis=0)-b1
 return np.stack((near,far),axis=1).ravel()
def witness(u):
 Q=A@Rotation.from_rotvec(u*q).as_matrix()
 L=Q@(np.eye(3)+(1-u)*res)
 o=(1-u)*keys[1]+u*keys[2]
 return (points@L.T+o-m)@J.T
def intervals(N):
 vals=[]; raw=[]; eids=[]
 for i in range(N):
  u=(i+.5)/N
  cloud=witness(u)
  # Shortest-arc displacement over half-cell + translation + exact
  # linearly decreasing source polar residue; include observed terminal
  # basis residue and 22µm float inflation. Smoothstep is onto [0,1]:
  # every eased value lives in a bounded cell regardless of elapsed pace.
  displacement=2*R*(1+rho)*np.sin(angle/(4*N))+R*rho/(2*N)+length/(2*N)+R*Dres+.000022
  v=support(cloud)
  g=v-np.repeat(displacement*jnorm,2)
  vals.append(g)
  raw.append(v)
  eids.append(i)
 return np.array(vals),np.array(raw)
V,mid=intervals(2048)
G=V.max(axis=1)
worst_cell=int(G.argmin()); lim=int(V[worst_cell].argmax())
threshold=data['needle_m']
assert np.all(np.diff(item['age_ticks'])>0)
print(json.dumps({'status':'CLEAR_AGAINST_UNCHANGED_PADDED_BOX_UNDER_EXACT_PLAN_ENVELOPE' if G.min()>=threshold else 'HOLD_NOT_CERTIFIED',
 'pad_m':data['pad_m'],'required_clearance_m':threshold,'source_unique_vertices':len(points),'triangle_surfaces':counts,
 'plan_age_ticks':item['age_ticks'],'turn_deg':np.degrees(angle),'axis_order':['-x','+x','-y','+y','-z','+z'],
 'reconstructed_second_middle_broad_six_m':broad_faces.tolist(),'reconstructed_broad_limiting_face':int(np.argmax(broad_faces)),
 'new_middle_worst_certified_face_m':float(G.min()),'new_middle_worst_face':lim,'worst_cell_eased':[worst_cell/len(V),(worst_cell+1)/len(V)],
 'matched_live_unchanged_input_sha256':other_auth['unchanged_input_sha256'],'next_native_second_turn_broad_actor_m':held[1],'crown_index':1,'middle_leg_key_distance_world_m':length,'cells':len(V),'uncertified_cells':int(np.sum(G<threshold)),
 'min_each_certified_face_m':V.min(axis=0).tolist(),
 'single_fixed_negative_x_face_entire_turn_m':float(V[:,0].min()),
 'endpoint_gaps_m':[support(witness(q)).tolist() for q in [0.,1.]],
 'source_residual_op_norm':rho,'destination_residual_op_norm':Dres,
 'float_padding_world_m':.000022,
 'assumption':'Shortest rigid orientation interpolation with existing linear basis residue and exact monotonic smoothstep position. Unchanged actor padded box; no actual movement simulation.'},sort_keys=True,indent=2))
