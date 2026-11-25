"""Conservative interval bounds, not engine CCD or certification."""
from pathlib import Path
import json,sys,runpy
import numpy as np
from scipy.spatial.transform import Rotation
p=Path(__file__).resolve().parent
tri, counts=runpy.run_path(str(p.parent/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](Path(sys.argv[1]))
src=tri.reshape(-1,3)
frames={}
def tf(r):
 t,*basis=np.array(r)
 return t,np.array(basis).T
def sat_gap(cloud,h):
 T=cloud.reshape(-1,3,3)
 E=np.roll(T,-1,axis=1)-T
 # Three box normals, triangle normal and nine edge cross box-axis vectors.
 axes=np.concatenate([np.broadcast_to(np.eye(3),(len(T),3,3)),
       np.cross(E[:,0],E[:,1])[:,None,:],
       np.cross(E[:,:,None,:],np.eye(3)[None,None,:,:]).reshape(len(T),9,3)],axis=1)
 norms=np.linalg.norm(axes,axis=2)
 axes=np.divide(axes,norms[:,:,None],out=np.zeros_like(axes),where=norms[:,:,None]>1e-13)
 proj=np.einsum('nvi,nai->nav',T,axes)
 rad=np.abs(axes)@h
 gap=np.maximum(proj.min(2)-rad,-rad-proj.max(2))
 gap[norms<=1e-13]=-np.inf
 return gap.max(1)

def bounds(q, o, dt, mounts=None, invariant_arc=False):
 a,A=tf(q['previous']); b,B=tf(q['current']); c,C=tf(o['transform'])
 I=np.linalg.inv(C); r=Rotation.from_matrix(A.T@B).as_rotvec(); angle=np.linalg.norm(r)
 leaf=np.linalg.norm(q['mounted_local'][0])
 # Linear crown origin + shortest rotation, padded by the source guard mount arc.
 # Bound any point's displacement about the interval midpoint. Absolute
 # inverse-basis row norms carry the world ball into obstacle local coordinates.
 length=np.linalg.norm(b-a)
 radius=np.linalg.norm(src,axis=1).max()
 if mounts is not None:
  m0,M0=tf(mounts[0]);m1,M1=tf(mounts[1])
  v,V=tf(q['mounted_local'])
  assert np.allclose(m0+M0@v,a,atol=2e-6) and np.allclose(m1+M1@v,b,atol=2e-6)
  assert np.allclose(M0@V,A,atol=2e-6) and np.allclose(M1@V,B,atol=2e-6)
  mr=Rotation.from_matrix(M0.T@M1).as_rotvec()
  angle=np.linalg.norm(mr)
  if invariant_arc:
   if angle>1e-10:
    leaf=np.linalg.norm(np.cross(v,mr/angle))
  else:
   radius=np.linalg.norm(src@V.T+v,axis=1).max()
   length=np.linalg.norm(m1-m0)
 assert np.allclose(A.T@A,np.eye(3),atol=2e-6) and np.allclose(B.T@B,np.eye(3),atol=2e-6)
 if o['class']=='BoxShape3D':
  h=np.array(o['size'])*.5
 elif o['class']=='CylinderShape3D':
  h=np.array([o['radius'],.5*o['height'],o['radius']])
 else:
  return {'status':'UNRESOLVED_SHAPE_CLASS'}
 minimum=np.inf; still=0; deep=0.; explicit=None
 for j in range(dt):
  t=(j+.5)/dt; R=A@Rotation.from_rotvec(t*r).as_matrix()
  cloud=(src@R.T+(1-t)*a+t*b-c)@I.T
  sag=leaf*(1-np.cos(angle*.5))
  if mounts is not None and not invariant_arc:
   mt=M0@Rotation.from_rotvec(t*mr).as_matrix()
   cloud=((src@V.T+v)@mt.T+(1-t)*m0+t*m1-c)@I.T
   sag=0.
  elif invariant_arc:
   sag=leaf*angle**2/8 # twice-differentiable linear-chord error bound
  d=length/(2*dt)+2*radius*np.sin(angle/(4*dt))+sag+.000022
  de=d*np.linalg.norm(I,axis=1)
  # Singleton axis separation is sufficient, and this checks all exact
  # crown vertices and therefore encloses each complete triangle.
  gap=np.maximum(cloud.min(0)-h,-h-cloud.max(0))-de
  best=float(np.max(gap))
  if best<=0:
   # h+de encloses the independent coordinate-wise uncertainty under motion.
   best=float(np.min(sat_gap(cloud,h+de)))
  minimum=min(minimum,best)
  still+=int(best<=0)
 for label,s,T in [('previous',a,A),('current',b,B)]:
  cloud=(src@T.T+s-c)@I.T
  inside=np.min(h-np.abs(cloud),axis=1)
  if o['class']=='BoxShape3D':
   g=sat_gap(cloud,h-.000022)
   if g.min()<0 and explicit is None:
    explicit={'endpoint':label,'triangle':int(np.argmin(g)),
              'intersects_box_shrunk_by_local_m':.000022}
    deep=.000023
  if o['class']=='BoxShape3D' and inside.max()>deep:
   ii=int(np.argmax(inside)); deep=float(inside[ii]); explicit={'endpoint':label,'triangle':ii//3,'corner':ii%3,'strict_interior_depth_local_m':deep}
 return {'minimum_certified_axis_gap_local_m':float(minimum),'subintervals':dt,
         'uncertified_subintervals':still,'exact_native_endpoint_inside_box':explicit,
         'status':'COLLISION_AT_NATIVE_SAMPLE' if deep>.000022 else ('SEPARATED' if not still else 'UNRESOLVED_TIGHT_GAP')}
# Simple positive/negative/edge controls exercise SAT fallback independently of route.
U=np.array([[0.,0.,0.],[.25,0.,0.],[0.,.25,0.]])
assert sat_gap(U,np.ones(3))[0]<0
assert sat_gap(U+[2.,0.,0.],np.ones(3))[0]>0
assert sat_gap(U+[0.,0.,1.],np.ones(3))[0]==0
for row in (p/'native.txt').read_text().splitlines():
 tag,body=row.split(' ',1)
 if tag=='TURN_DETAIL':
  f=json.loads(body);frames[f['tick']]=f
assert sorted(frames)==[1305,1306,1307,1352,1353,1354]
assert all(f['grounded'] for f in frames.values())
out=[]
for k,f in frames.items():
 for q in f['crowns']:
  key=lambda b:(b['body'],b['shape_index'])
  assert np.linalg.norm(src,axis=1).max() < .235427
  assert len(q['endpoint_shapes'])==2 and len(q['cast'])==2
  if k-1 in frames:
   _,M0=tf(frames[k-1]['mount']); _,M1=tf(f['mount'])
   rr=Rotation.from_matrix(M0.T@M1).as_rotvec()
   turn=np.linalg.norm(rr)
   leaf_perpendicular=np.linalg.norm(np.cross(q['mounted_local'][0],rr/turn)) if turn>1e-10 else 0.
   assert np.linalg.norm(src,axis=1).max()+leaf_perpendicular*turn**2/8 < q['radius']+.0001
  broad={key(b):b for b in q['midpoint_enclosing_shape_hits']}
  assert all(key(b) in broad for K in q['endpoint_shapes'] for b in K),'enclosing sphere did not report a native endpoint'
  assert len(broad)<64
  out.append({'tick':k,'crown':q['index'],'sphere_cast':q['cast'],
      'same_radius_endpoint_shapes':[[b['body'] for b in K] for K in q['endpoint_shapes']],
      'covering_sphere_shape_count':len(broad),
      'precision':[{**dict(zip(('body','shape_index'),K)),'kind':o['class'],**bounds(q,o,64),**({'exact_rigid_mount_interpolation':bounds(q,o,128,[frames[k-1]['mount'],f['mount']]),'yaw_perpendicular_arc_envelope':bounds(q,o,128,[frames[k-1]['mount'],f['mount']],True)} if k-1 in frames else {})} for K,o in sorted(broad.items())]})
logs=lambda f:[ln for ln in f.read_text().splitlines() if ln.startswith(('WALK_OBSTRUCTION ','WALK_SUM '))]
assert logs(p/'native.txt')==logs(p.parent/'hvn-l1-paid-storage-walkby-v1/native.log')
print(json.dumps({'crown_triangles':counts,'rows':out},indent=2,sort_keys=True))
