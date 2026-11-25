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
source,plate=map(Path,sys.argv[1:3]); restdir=Path('../hvn-l1-wood-storage-rest-facet-v1')
verify(restdir,'76d3a59cc9dd3bda83c1abe187bc3d9ab81705bf162ba0b3edbd1f8f1af893e2')
res=json.loads((restdir/'result.json').read_text())
g,parts=decode(source)
assert parts==[1087,213]
allv=np.unique(g.reshape(-1,3),axis=0); hull=ConvexHull(allv); hv=allv[np.sort(hull.vertices)]
# Independent containment residual and reconstructible convex support equivalence.
rehull=ConvexHull(hv)
assert abs(rehull.volume-res['convex_hull_volume_m3'])<1e-13
assert float((allv@rehull.equations[:,:3].T+rehull.equations[:,3]).max())<1e-10
assert sha(plate)==res['plate_sha256']
b=plate.read_bytes(); n=struct.unpack_from('<I',b,12)[0]; d=json.loads(b[20:20+n])
points=[]
for p in d['meshes'][0]['primitives']:
 a=d['accessors'][p['attributes']['POSITION']]; v=d['bufferViews'][a['bufferView']]
 points.extend(np.frombuffer(b,dtype='<f4',count=3*a['count'],offset=28+n+v['byteOffset']).reshape(-1,3).tolist())
U=np.unique(np.array(points),axis=0); ph=ConvexHull(U); hull_plate=U[np.sort(ph.vertices)]
assert np.count_nonzero(hull_plate[:,1]==0)==52 and U[:,1].max()==0 and abs(U[:,1].min()+.008)<1e-9
top=U[U[:,1]==0][:,[0,2]]; ordered=top[ConvexHull(top).vertices].tolist()
R=np.array(res['exact_source_basis_matrix_row_major'])
assert np.allclose(R@R.T,np.eye(3),atol=1e-12) and np.linalg.det(R)>0.99999999
l=[]
for c in res['clearance_result']:
 T=np.array(c['source_to_plate_t'])
 q=hv@R.T+T
 assert np.allclose([q.min(0),q.max(0)],c['bounds_xyz'],atol=1e-11)
 l.append(T.tolist())
nn=(allv.max(0)+allv.min(0))/2
print(json.dumps(dict(log_source_sha=sha(source),plate_source_sha=sha(plate),hull_points=hv.tolist(),plate_hull_points=hull_plate.tolist(),basis_columns=R.T.tolist(),ordered_top_xz=ordered,
  source_to_rest_t=l, source_com=res['source_center_proxy_xyz_m'], source_center_lift=[-nn[0],-allv[:,1].min(),-nn[2]],
  log_hull_volume_m3=hull.volume,lip_top_local_y=0, plate_bounds_xyz=np.stack([U.min(0),U.max(0)]).tolist()),sort_keys=True))
