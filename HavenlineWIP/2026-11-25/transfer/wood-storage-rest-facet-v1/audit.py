import sys, hashlib, json, math, re, struct
from pathlib import Path
import numpy as np

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(p, h):
    manifest = p / "SHA256SUMS"
    assert sha(manifest) == h, p
    for line in manifest.read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        assert sha(p / name) == expected, name

def decode(path):
    raw=path.read_bytes()
    assert sha(path)=="31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554"
    assert struct.unpack_from("<4sII", raw)==(b"glTF",2,len(raw))
    a, kind=struct.unpack_from("<II",raw,12); assert kind==0x4E4F534A
    doc=json.loads(raw[20:20+a])
    size, kind=struct.unpack_from("<II",raw,a+20); assert kind==0x004E4942
    binary=raw[a+28:a+28+size]
    def accessor(index):
        item=doc["accessors"][index]; view=doc["bufferViews"][item["bufferView"]]
        dt={5126:"<f4",5123:"<u2",5125:"<u4",5121:"u1"}[item["componentType"]]
        k={"SCALAR":1,"VEC3":3}[item["type"]]
        off=view.get("byteOffset",0)+item.get("byteOffset",0)
        stride=np.dtype(dt).itemsize
        assert view.get("buffer",0)==0
        assert not item.get("sparse") and not item.get("normalized")
        return np.ndarray((item["count"],k),dtype=dt,buffer=binary,offset=off,
                          strides=(view.get("byteStride",k*stride),stride))
    i=next(i for i,n in enumerate(doc["nodes"]) if n.get("name")=="Pickup LOD - Crown log")
    node=doc["nodes"][i]
    assert i in doc["scenes"][doc["scene"]]["nodes"]
    assert all(k not in node for k in ("matrix","translation","scale","rotation","skin"))
    groups=[]
    for prim in doc["meshes"][node["mesh"]]["primitives"]:
        assert prim.get("mode",4)==4 and "COLOR_0" in prim["attributes"]
        p=accessor(prim["attributes"]["POSITION"]).astype(float)
        indices=accessor(prim["indices"]).reshape(-1,3)
        groups.append(p[indices])
    return np.concatenate(groups), [len(g) for g in groups]

from scipy.spatial import ConvexHull
from collections import defaultdict
def faces_from_plate(path):
 b=path.read_bytes()
 assert sha(path)=='0f961e1dbf66c954eb557ecbae54d34c34cf15121011c0866203d05cb73d419b'
 a,t=struct.unpack_from('<II',b,12); D=json.loads(b[20:20+a]); assert t==0x4e4f534a
 pr=D['meshes'][0]['primitives'][0]; ac=D['accessors'][pr['attributes']['POSITION']]; bv=D['bufferViews'][ac['bufferView']]
 A=np.frombuffer(b[28+a:],dtype='<f4',count=3*ac['count'],offset=bv['byteOffset']).reshape(-1,3)
 assert (A[:,1]==0).all()
 return ConvexHull(np.unique(A[:,[0,2]],axis=0))
def centroid(tri,origin):
 x=tri-origin; vol=(np.cross(x[:,0],x[:,1])*x[:,2]).sum(1)/6.
 return np.sum((x.sum(1)*.25)*vol[:,None],axis=0)/vol.sum()+origin,vol.sum()
def topology(tri,quant=None):
 b=tri.reshape(-1,3)
 if quant:
  # Used only to assess approximate near splits, never in exact rest fit.
  b=np.rint(b/quant).astype(np.int64)
 _,ix=np.unique(b,axis=0,return_inverse=True); edges=defaultdict(list)
 for tr in ix.reshape(-1,3):
  for p in zip(tr,np.roll(tr,-1)):edges[tuple(sorted(p))].append(p)
 return dict(unique_vertices=int(ix.max())+1,boundary_edges=sum(len(x)==1 for x in edges.values()),nonmanifold_edges=sum(len(x)>2 for x in edges.values()),
  disconnected_orientations=sum(len(x)==2 and x[0]!=x[1][::-1] for x in edges.values()))
def unit(x):return x/max(np.linalg.norm(x),1e-30)
def sdist(H,uv):
 return float((-H.equations[:,:2]@uv-H.equations[:,2]).min())
src,plate=map(Path,sys.argv[1:3]); P=faces_from_plate(plate)
tri, nn=decode(src); assert nn==[1087,213]
T=np.unique(tri.reshape(-1,3),axis=0); H=ConvexHull(T)
closed=topology(tri); origin=T.mean(0)
approx=topology(tri,1e-6)
# Actual oriented triangular shell integral is only a volume COM if exact closure is proven.
closed_exact=not any(closed[k] for k in ('boundary_edges','nonmanifold_edges','disconnected_orientations'))
truecom,truev=centroid(tri,origin)
ht=T[H.simplices].copy()
bad=(np.cross(ht[:,1]-ht[:,0],ht[:,2]-ht[:,0])*H.equations[:,:3]).sum(1)<0
ht[bad]=ht[bad][:,[0,2,1]]
hullcom,hullv=centroid(ht,origin); assert abs(hullv-H.volume)<1e-10
proxy=truecom if closed_exact else hullcom
# Principal length axis sign is resolved by source +X; keep projected long axis
# along plate +X without arbitrary global yaw, and choose a near-level footprint.
_,_,axes=np.linalg.svd(T-origin,full_matrices=False)
a=axes[0]*np.sign(axes[0,0])
def evaluate(up):
 long=unit(a-up*(up@a)); dep=unit(np.cross(long,up)); basis=np.stack([long,up,dep])
 assert np.linalg.det(basis)>.99999
 r=T@basis.T; bottom=r[:,1].min(); flat=r[(r[:,1]-bottom)<1e-9]
 # Distinct actual source mesh points, not hull-only synthesized contact vertices.
 if len(flat)<3:return None
 try:C=ConvexHull(flat[:,[0,2]])
 except Exception:return None
 center=(r.max(0)+r.min(0))/2; xyz=(proxy@basis.T-np.array([0.,bottom,0.]))
 m=sdist(C,xyz[[0,2]])
 yawtilt=np.degrees(np.arcsin(abs(up@a)))
 return dict(basis=basis,r=r,bottom=bottom,center=center,flat=flat,C=C,m=m,com=xyz,tilt=yawtilt)
depth={} ; pass0=[]
for eq in H.equations:
 n=eq[:3]; key=tuple(np.round(eq,9))
 if key in depth:continue
 depth[key]=True
 z=evaluate(-n)
 if z is None:continue
 if z['tilt']<=8 and z['m']>=.002:pass0.append(z)
assert pass0
def rank(z):return (z['m'], z['C'].volume, -z['tilt'])
z=max(pass0,key=rank); Rot=z['basis']; Q=z['r']; bmin=Q.min(0);bmax=Q.max(0);span=bmax-bmin
pitch=span[2]+.001
copies=[]; guards=[]
for side in (-1,1):
 trans=np.array([-z['center'][0],-z['bottom'],-z['center'][2]+side*pitch/2])
 q=Q+trans
 support=z['flat'][z['C'].vertices][:,[0,2]]+trans[[0,2]]
 assert np.max(np.abs((z['flat'][z['C'].vertices]+trans)[:,1]))<1.e-9
 assert q[:,1].min()==0
 reserve=min(sdist(P,v) for v in q[:,[0,2]])
 co=proxy@Rot.T+trans
 copies.append(dict(source_to_plate_t=trans.tolist(),bounds_xyz=np.stack([q.min(0),q.max(0)]).tolist(),actual_contact_polygon_xz_m=support.tolist(),
 minimum_entire_projected_footprint_inset_m=reserve,proxy_center_3d_m=co.tolist(), projected_convex_boundary_xz_m=q[ConvexHull(q[:,[0,2]]).vertices][:,[0,2]].tolist()))
 guards.append((q[:,2].min(),q[:,2].max()))
assert guards[1][0]-guards[0][1]>.000999999
assert min(x['minimum_entire_projected_footprint_inset_m'] for x in copies)>.01
plane_contacts=tuple(np.flatnonzero(Q[:,1]-z['bottom']<1e-9))
mesh_plane_triangles=int(np.count_nonzero((np.abs((tri@Rot.T)[:,:,1]-z['bottom'])<1e-9).all(1)))
mesh_diag=truecom@Rot.T
geometry_area=z['C'].volume
print(json.dumps(dict(actual_coplanar_original_triangle_count=mesh_plane_triangles,
    contact_polygon_semantics='convex polygon of actual contacting vertices, not area of solid bark contact',
    invalid_open_mesh_integral_min_projected_edge_distance_diagnostic_m=sdist(z['C'],mesh_diag[[0,2]]),
    first_noncontact_vertex_height_m=float(np.min((Q[:,1]-z['bottom'])[(Q[:,1]-z['bottom'])>=1e-9])),
    source_sha256=sha(src),plate_sha256=sha(plate),triangles=len(tri),hull_candidate_planes=len(depth),admissible_facet_trials=len(pass0),
 exact_weld=closed,micrometre_bin_diagnostic=approx,center_method='mesh enclosed uniform density' if closed_exact else 'closed convex hull uniform-density proxy; original mesh not exact watertight',
 convex_hull_volume_m3=hullv,oriented_triangle_integral_diagnostic_m3=truev,source_center_proxy_xyz_m=proxy.tolist(),hull_to_mesh_integral_com_disagreement_m=float(np.linalg.norm(truecom-hullcom)),
 exact_source_basis_matrix_row_major=Rot.tolist(),long_axis_source_xyz=a.tolist(),angle_above_deck_deg=float(z['tilt']),
 source_oriented_bounds_span_xyz_m=span.tolist(),positive_contact_area_m2=float(z['C'].volume),minimum_projected_com_to_polygon_edge_m=z['m'],
 proxy_height_above_plate_m=float(z['com'][1]),proxy_worst_static_tipping_angle_deg=float(np.degrees(np.arctan2(z['m'],z['com'][1]))),
 contact_geometry_source_vertices=len(z['flat']),zero_rotation_lowest_vertex_count=int(np.count_nonzero(T[:,1]==T[:,1].min())),
 clearance_result=copies,copy_depth_axis_envelope_clearance_m=guards[1][0]-guards[0][1]),indent=2,sort_keys=True))
