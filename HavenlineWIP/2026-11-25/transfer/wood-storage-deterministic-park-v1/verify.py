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
from fractions import Fraction
src,plate=map(Path,sys.argv[1:3])
base=Path('..')
p=base/'hvn-l1-wood-storage-rest-facet-v1'
verify(p,'76d3a59cc9dd3bda83c1abe187bc3d9ab81705bf162ba0b3edbd1f8f1af893e2')
r=json.loads((p/'result.json').read_text())
ref=base/'hvn-l1-reference-wood-transfer-v1'
verify(ref,'0c8a4210b6d9a953872f67451e1fb93dd225a826da671e2acb1557a109161f62')
ev={i['frame0']:i['seconds'] for i in json.loads((ref/'measurement.json').read_text())['events']}
first=(ev[802]-ev[795],ev[804]-ev[795]); last=(ev[820]-ev[795],ev[822]-ev[795])
R=np.array(r['exact_source_basis_matrix_row_major']); assert np.allclose(R@R.T,np.eye(3),atol=1e-12) and np.linalg.det(R)>.999999
T=[np.array(x['source_to_plate_t']) for x in r['clearance_result']]
tri,parts=decode(src); assert parts==[1087,213]
M=np.unique(tri.reshape(-1,3),axis=0)@R.T
deck=faces_from_plate(plate)
cert=[]
for i,t in enumerate(T):
 V=M+t
 coinc=np.flatnonzero(abs(V[:,1])<1e-9)
 assert len(coinc)==3
 contact=V[coinc]
 c=ConvexHull(contact[:,[0,2]])
 com=np.array(r['source_center_proxy_xyz_m'])@R.T+t
 clearance=float((-deck.equations[:,:2]@V[:,[0,2]].T-deck.equations[:,2,None]).min())
 assert abs(clearance-r['clearance_result'][i]['minimum_entire_projected_footprint_inset_m'])<1e-10
 assert clearance>.15 and abs(V.min(0)[1])<1e-9 and not (V[:,1]<-1e-9).any()
 assert abs(float((-c.equations[:,:2]@com[[0,2]]-c.equations[:,2]).min())-r['minimum_projected_com_to_polygon_edge_m'])<1e-10
 cert.append((clearance,len(coinc)))
# Simulated clock in integer microseconds. This local fixture uses stationary
# vertical lanes with zero tangent endpoint easing, not player-to-site flights.
START=(0,125_000); END=(300_000,875_000); HEIGHT=(.145,.185)
assert first[0]<END[0]*1e-6<first[1] and last[0]<END[1]*1e-6<last[1]
def pose(i,us):
 if us<START[i]: return T[i]+np.array([0,HEIGHT[i],0]),'entry_hover'
 if us>=END[i]: return T[i].copy(),'parked'
 u=(us-START[i])/(END[i]-START[i]); s=(1-u)**2*(1+2*u)
 return T[i]+np.array([0,HEIGHT[i]*s,0]),'eased_vertical_park'
def exact_metrics(poses):
 V=[M+p for p in poses]
 lo=[v.min(0) for v in V]; hi=[v.max(0) for v in V]
 return min(x[1] for x in lo),lo[1][2]-hi[0][2]
ROW={'marker':'other-type-fixture-row','resource':'diagnostic_nonwood','slot_ids':['other-a','other-b'],
     'local_transform_rows':[[1.,0,0,7.5],[0,1.,0,2.1],[0,0,1.,-3.]]}
row_copy=json.loads(json.dumps(ROW))
row_bytes=lambda v:json.dumps(v,separators=(',',':'),sort_keys=True).encode()
original=row_bytes(ROW)
event=[x+d for x in sorted(set(START+END)) for d in (-1,0,1)]
def hz(n):return [round(Fraction(i*1000000,n)) for i in range(n+1)]
jitter=[0]
while jitter[-1]<1_000_000:jitter.append(jitter[-1]+[7100,17600,24000,9900,33500][(len(jitter)-1)%5])
samples={}; checks=0
for name,series in [('30hz',hz(30)),('60hz',hz(60)),('120hz',hz(120)),('jitter',jitter)]:
 uss=sorted(set(series+event))
 coverage={'sample_count':len(uss),'plane_floor':1.,'pair_z_gap':1.,'max_park_error':0.,'both_in_motion_samples':0,'untouched_row':True}
 prior=[None,None]
 for us in uss:
  arr=[pose(i,us) for i in range(2)]
  q=[x[0] for x in arr]; tags=[x[1] for x in arr]
  ground,gap=exact_metrics(q)
  assert abs(gap-r['copy_depth_axis_envelope_clearance_m'])<1e-11 and ground>=-1e-10
  checks+=2
  for i,tag in enumerate(tags):
   assert np.array_equal(q[i][[0,2]],T[i][[0,2]])
   if tag=='parked':
    assert np.array_equal(q[i],T[i])
   if prior[i] is not None: assert q[i][1]<=prior[i][1]+1e-14
   prior[i]=q[i]
   checks+=2
  assert row_bytes(row_copy)==original
  checks+=1
  coverage['plane_floor']=min(ground,coverage['plane_floor']);coverage['pair_z_gap']=min(gap,coverage['pair_z_gap'])
  coverage['both_in_motion_samples']+=int(tags==['eased_vertical_park']*2)
 assert all(pose(i,START[i]-1)[1]=='entry_hover' and pose(i,START[i])[1]=='eased_vertical_park' and pose(i,END[i]-1)[1]=='eased_vertical_park' and pose(i,END[i])[1]=='parked' for i in range(2))
 assert coverage['both_in_motion_samples']>0
 samples[name]=coverage
# Three independent controls: crossing deck plane, duplicate full pose,
# unrelated row movement. Pose duplication makes identical meshes, not merely
# broadphase overlap.
dip=exact_metrics([T[0]-[0,.004,0],T[1]])[0]
dup=exact_metrics([T[0],T[0]])[1]
badrow=json.loads(original);badrow['local_transform_rows'][0][-1]+=.01
assert dip<-.00399 and dup<-.1 and row_bytes(badrow)!=original
print(json.dumps({'samples':samples,'sampled_contract_check_groups':checks,
 'reference_first_landing_bracket_s':first,'reference_last_landing_bracket_s':last,
 'fixture_launch_us':START,'fixture_park_us':END,'fixture_hover_height_m':HEIGHT,'path':'fixed exact rest orientation + monotonic C1 vertical cubic smoothstep, no yaw or tumble; XZ and therefore pair proof invariant',
 'whole_original_crown_points':len(M),'whole_original_crown_triangles_each':len(tri),
 'finite_outline_reserve_and_contact_vertices_each':cert,
 'negative_controls':{'plane_dip_m':dip,'duplicate_exact_mesh_interval_gap_m':dup,'other_row_shift_rejected':True},
 'untouched_row_bytes_sha256':hashlib.sha256(original).hexdigest()},indent=2,sort_keys=True))
