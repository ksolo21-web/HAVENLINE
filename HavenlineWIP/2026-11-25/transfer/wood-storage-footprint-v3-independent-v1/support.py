import hashlib,struct,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
plate,log=map(Path,sys.argv[1:])
def parse(p,h):
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==h
 n=struct.unpack_from('<I',raw,12)[0]; a=json.loads(raw[20:20+n]); b=memoryview(raw)[n+28:]
 def acc(i):
  v=a['accessors'][i]; w=a['bufferViews'][v['bufferView']];assert not v.get('sparse') and not v.get('normalized')
  X={'SCALAR':1,'VEC3':3}[v['type']]; dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[v['componentType']])
  return np.ndarray((v['count'],X),dtype=dt,buffer=b,offset=w.get('byteOffset',0)+v.get('byteOffset',0),
    strides=(w.get('byteStride',X*dt.itemsize),dt.itemsize))
 return a,acc
def triangles(a,f,name=None):
 n=next(i for i in a['nodes'] if i.get('name')==name) if name is not None else a['nodes'][0]
 assert not set(n)&{'translation','rotation','scale','matrix'}
 return np.concatenate([f(s['attributes']['POSITION'])[f(s['indices']).reshape(-1,3)] for s in a['meshes'][n['mesh']]['primitives']]).astype(float)
a,fa=parse(plate,'c89ee6e92e352f32586113c6d5e1d81b21bc7cfb84603ee70d16e0b0d426afc1')
b,fb=parse(log,'31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554')
P=triangles(a,fa); W=triangles(b,fb,'Pickup LOD - Crown log')
assert len(P)==312 and len(W)==1300
roof=P[np.abs(P[:,:,1]).max(1)<1e-10][:,:,[0,2]]
assert len(roof)==52
def seal(d,h):
 p=Path('..',d)
 sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
 assert sha(p/'SHA256SUMS')==h
 for l in (p/'SHA256SUMS').read_text().splitlines():
  a,b=l.split(); assert sha(p/b)==a
 return p
q=seal('hvn-l1-wood-storage-deterministic-park-v1','970c8aaff2cb0d128d13a31c2658c995f052c6674386fecd47a728e884cd6114')
f=seal('hvn-l1-wood-storage-rest-facet-v1','76d3a59cc9dd3bda83c1abe187bc3d9ab81705bf162ba0b3edbd1f8f1af893e2')
src=seal('hvn-l1-reference-wood-transfer-v1','0c8a4210b6d9a953872f67451e1fb93dd225a826da671e2acb1557a109161f62')
r=json.loads((f/'result.json').read_text()); known=json.loads((q/'result.json').read_text())
rot=np.array(r['exact_source_basis_matrix_row_major'])
assert np.linalg.det(rot)>1-1e-12 and np.linalg.norm(rot.T@rot-np.eye(3))<1e-12
piv=[np.array(x['source_to_plate_t']) for x in r['clearance_result']]
v=np.unique(W.reshape(-1,3),axis=0); assert len(v)==834
poses=[v@rot.T+t for t in piv]
E=[]
# Internal exact edge incidence leaves only physical closed boundary edges.
from collections import Counter,defaultdict
def key(x):return tuple(x.tolist())
hist=Counter()
for tri in roof:
 for a,b in zip(tri,np.roll(tri,-1,axis=0)):hist[tuple(sorted((key(a),key(b))))]+=1
bd=np.array([e for e,k in hist.items() if k==1])
nodes=np.unique(bd.reshape(-1,2),axis=0)
assert len(bd)==len(nodes) and all(c==2 for c in Counter(map(key,bd.reshape(-1,2))).values())
ctr=nodes.mean(0); edge=bd[:,1]-bd[:,0]; length=np.linalg.norm(edge,axis=1); assert min(length)>0
normal=np.c_[edge[:,1],-edge[:,0]]/length[:,None]
normal*=np.sign(((ctr-bd[:,0])*normal).sum(1))[:,None]
assert np.min((nodes-bd[:,0,None])@normal[:,:,None])>=-1e-9
fit=[]
for p in poses:
 xz=p[:,[0,2]]
 d=((xz[None]-bd[:,0,None])*normal[:,None]).sum(2).min()
 on=p[abs(p[:,1])<1e-9];assert len(on)==3 and abs(p[:,1].min())<1e-9
 ar=abs(np.linalg.det(on[1:,[0,2]]-on[0,[0,2]]))*.5
 fit.append({'outline_distance_mm':float(d*1000),'floor_m':float(p[:,1].min()),'contact_vertex_count':len(on),'contact_triangle_area_mm2':float(ar*1e6)})
gap=poses[1][:,2].min()-poses[0][:,2].max()
assert abs(gap-.001)<1e-12
# Degree-3 Bernstein form: H,H,0,0 means convex combo nonnegative
# for every u in [0,1]. Derivative coefficients 0,-3H,0 <= 0, exact
# zero endpoints match constant pre-/post-segments.
clock=list(zip(known['fixture_launch_us'],known['fixture_park_us'],known['fixture_hover_height_m']))
schedule=[]
for t0,t1,h in clock:
 assert t1>t0 and h>0
 b=[h,h,0,0]
 deriv=(3*np.diff(b)/(1e-6*(t1-t0)))
 assert min(b)==0 and max(deriv)==0 and deriv[0]==deriv[-1]==0
 schedule.append({'from_s':t0/1e6,'to_s':t1/1e6,'monotone_cubic_bernstein_coeffs_m':b,'derivative_coeffs_m_per_s':deriv.tolist()})
z={i['frame0']:i['seconds'] for i in json.loads((src/'measurement.json').read_text())['events']}
ranges=[[z[i]-z[795],z[j]-z[795]] for i,j in [(802,804),(820,822)]]
assert all(k[0]<r['to_s']<k[1] for k,r in zip(ranges,schedule))
overlap=min(x['to_s'] for x in schedule)-max(x['from_s'] for x in schedule); assert overlap>0
print(json.dumps({'exact_unscaled_points_per_crown':len(v),'rotated_end_pose_support':fit,'all_trajectory_pair_gap_mm':1000*gap,
 'projected_ground_never_crossed_for_author_vertical_fixture':True,'reference_visible_event_brackets_s':ranges,
 'schedule_proof':schedule,'both_moving_s':overlap},sort_keys=True,indent=2))
