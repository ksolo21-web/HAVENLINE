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
a,fa=parse(plate,'0f961e1dbf66c954eb557ecbae54d34c34cf15121011c0866203d05cb73d419b')
b,fb=parse(log,'31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554')
P=triangles(a,fa); W=triangles(b,fb,'Pickup LOD - Crown log')
assert len(P)==312 and len(W)==1300
roof=P[np.abs(P[:,:,1]).max(1)<1e-10][:,:,[0,2]]
assert len(roof)==52
# Verify convex finite roof, not just the vertex AABB: exact top projected
# triangle area equals convex hull, and no overlap occurs beyond shared boundaries.
h=ConvexHull(np.unique(roof.reshape(-1,2),axis=0))
z=roof[:,1:]-roof[:,:1]
a_sum=.5*sum(abs(np.linalg.det(z)))
assert abs(a_sum-h.volume)<1e-10
# At each exact crown copy, place AABB midpoint X/Z and lower Y at authored datum.
# Meshes are unanalyzed stable pivots; this fit is a bounding/contact gauge.
points=np.unique(W.reshape(-1,3),axis=0); lo,hi=points.min(0),points.max(0)
sample=[]
for q in [-.0524175,.0524175]:
 p=points-np.array([(hi[0]+lo[0])/2,lo[1],(hi[2]+lo[2])/2-q])
 e=p[:,[0,2]]; s=e@h.equations[:,:2].T+h.equations[:,2]
 t=p[p[:,1]<1e-9]
 assert len(t)>0 and p[:,1].min()==0 and s.max()<0
 vol={'actual_geometry_margin_to_roof_m':float(-s.max()),'exact_lowest_contact_vertices_n':len(t),
   'center_minus_contact_xz_mm':(1000*t[:,[0,2]].mean(0)-[0,1000*q]).tolist(),
   'actual_w_nondegenerate_triangle_n':len(W),'z_aabb': [float(p[:,2].min()),float(p[:,2].max())]}
 sample.append(vol)
sep=sample[1]['z_aabb'][0]-sample[0]['z_aabb'][1]
assert sep>0
print(json.dumps({'plane_top_area_m2':float(a_sum),'plate_triangles':len(P),'source_log_bounding_mm':((hi-lo)*1000).tolist(),
 'two_contact_datum_gauges':sample,'no_pair_AABB_overlap_gap_m':sep,'physics_or_stability':False},indent=2,sort_keys=True))
