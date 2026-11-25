"""Exact native plan replay against unchanged padded actor AABB, offline."""
from pathlib import Path
import json,sys,runpy
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(__file__).resolve().parent
mesh=Path(sys.argv[1])
tri,counts=runpy.run_path(str(p.parent/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](mesh)
points=np.unique(tri.reshape(-1,3),axis=0)
raw=(p/'native.txt').read_text().splitlines()
def obj(label):
 rows=[x.split(' ',1)[1] for x in raw if x.startswith(label+' ')]
 assert len(rows)==1
 return json.loads(rows[0])
data=obj('EXAM_SUPPORT_INPUT')
faces=obj('EXAM_SUPPORT_GAPS')
b0,b1=np.asarray(data['body_padded_m'])
assert data['tick']==1333 and max(abs(np.asarray(data['pad_m'])-.025))<1e-8
assert data['needle_m']==.00008 and faces['i']==0
item=data['plan'][0]; holds=np.asarray(faces['signed_face_m'])
assert holds.shape==(3,6)
assert abs(holds[1].max()-(-.00219279527664185))<2e-7
def tf(r):
 o,*b=np.asarray(r)
 return o,np.asarray(b).T
m,M=tf(data['mount']); src,S=tf(item['source']); dest,D=tf(item['rest'])
keys=np.asarray(item['key'])
assert np.array_equal(keys[0],src) and np.array_equal(keys[3],dest)
J=np.linalg.inv(M)
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
 'original_six_all_legs_m':holds.tolist(),'original_leg1_limiting_face':int(np.argmax(holds[1])),
 'new_middle_worst_certified_face_m':float(G.min()),'new_middle_worst_face':lim,'worst_cell_eased':[worst_cell/len(V),(worst_cell+1)/len(V)],
 'cells':len(V),'uncertified_cells':int(np.sum(G<threshold)),
 'min_each_certified_face_m':V.min(axis=0).tolist(),
 'single_fixed_negative_x_face_entire_turn_m':float(V[:,0].min()),
 'endpoint_gaps_m':[support(witness(q)).tolist() for q in [0.,1.]],
 'source_residual_op_norm':rho,'destination_residual_op_norm':Dres,
 'float_padding_world_m':.000022,
 'assumption':'Shortest rigid orientation interpolation with existing linear basis residue and exact monotonic smoothstep position. Unchanged actor padded box; no actual movement simulation.'},sort_keys=True,indent=2))
