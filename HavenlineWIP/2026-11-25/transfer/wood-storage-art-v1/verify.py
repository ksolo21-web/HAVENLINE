import hashlib,io,json,struct
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
b=Path('wood_storage_empty.glb').read_bytes()
magic,v,length,n,t=struct.unpack_from('<4sIIII',b)
assert (magic,v,length,t)==(b'glTF',2,len(b),0x4e4f534a)
j=json.loads(b[20:20+n]); size,tag=struct.unpack_from('<II',b,20+n)
assert tag==0x004e4942 and size==len(b)-28-n
raw=memoryview(b)[28+n:]
def buf(i):
 v=j['bufferViews'][i];assert v['byteOffset']%4==0 and v['buffer']==0
 return raw[v['byteOffset']:v['byteOffset']+v['byteLength']]
def acc(i):
 a=j['accessors'][i]; dt={5126:'<f4',5123:'<u2'}[a['componentType']]
 d={'VEC2':2,'VEC3':3,'SCALAR':1}[a['type']]
 return np.frombuffer(buf(a['bufferView']),dtype=dt).reshape(a['count'],d)
assert len(j['nodes'])==len(j['meshes'])==len(j['scenes'])==1
assert j['nodes'][0] == {'mesh':0,'name':'WoodStoragePlate_Empty'}
assert not set(j)&{'animations','skins','extensions','extensionsUsed'}
pro=j['meshes'][0]['primitives'];assert len(pro)==2
pf=[];vertices=[];top=None
for m,p in enumerate(pro):
 V,N,U=(acc(p['attributes'][k]) for k in ['POSITION','NORMAL','TEXCOORD_0'])
 I=acc(p['indices']).reshape(-1,3); assert I.max()<len(V)
 T=V[I]; C=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);g=np.linalg.norm(C,axis=1)
 assert min(g)>1e-12
 assert np.allclose(C/g[:,None],N[I][:,0],atol=1e-4)
 assert np.all((U>=0)&(U<=1)) and np.allclose(U,(V[:,[0,2]]/np.array([.66,.52]))+.5,atol=1e-6)
 if m==0:assert np.all(V[:,1]==0) and np.all(N[:,1]>0);top=V[I]
 pf.append(T); vertices.extend(V.tolist())
faces=np.concatenate(pf)
_,IX=np.unique(faces.reshape(-1,3),axis=0,return_inverse=True)
E=defaultdict(list)
for a,b0,c in IX.reshape(-1,3):
 for p in ((a,b0),(b0,c),(c,a)):E[tuple(sorted(p))].append(p)
assert all(len(l)==2 and l[0]==l[1][::-1] for l in E.values())
assert len(np.unique(IX))-len(E)+len(faces)==2
raw_png=bytes(buf(j['images'][0]['bufferView']))
assert raw_png==Path('paint.png').read_bytes() and Image.open(io.BytesIO(raw_png)).size==(1320,1040)
# Signed actual flat convex top perimeter and the four corners of the rounded
# source envelope. Translation gives explicit per-copy centered envelopes;
# no claim the original crown pivot itself lies at this footprint center.
support=np.array([[-.309,-.239],[.309,-.239],[.309,.239],[-.309,.239]])
per=top[:,1][:,[0,2]]
axis=np.roll(per,-1,axis=0)-per
D=support[:,None,:]-per[None,:,:]
s=(axis[None,:,0]*D[:,:,1]-axis[None,:,1]*D[:,:,0])/np.linalg.norm(axis,axis=1)
assert s.min()>.001
gauge=np.array([.283674,.102561,.103835]);pitch=.104835
assert abs(pitch-gauge[2]-.001)<1e-9
q=np.array([[0,0,-pitch/2],[0,0,pitch/2]]); h=gauge[[0,2]]/2
assert (np.max(np.abs(q[:,[0,2]]),axis=0)+h < [.309,.239]).all()
rest={'semantics':'non-world art gauges, XZ is bounding-footprint center, local Y=0 is contact plane; bind log pivot later',
 'crown_bounds_conservative_xyz_m':gauge.tolist(),'positions_xyz_m':q.tolist(),'heading_deg_y':0,'axis_gap_m':.001,
 'reserved_clear_rectangle_xz_m':[.618,.478],'remaining_clearance_to_reserved_rectangle_each_side_xz_m':([.309,.239]-np.max(np.abs(q[:,[0,2]]),axis=0)-h).tolist(),
 'actual_top_edge_min_clearance_of_reserved_rectangle_corners_m':float(s.min())}
print(json.dumps({'glb_sha256':hashlib.sha256(Path('wood_storage_empty.glb').read_bytes()).hexdigest(),
 'source_checked':{'seam_weld_manifold':True,'triangles':len(faces),'paint_plane_triangles':len(top),'embedded_texture_dimensions':[1320,1040],
 'bounds_xyz':np.stack([faces.min((0,1)),faces.max((0,1))]).tolist()},'rest_gauges':rest,'scene_binding':False,'visual_score':None},indent=2,sort_keys=True))
