"""Export deterministic glTF explicit streams; no textures are copied or bound."""
import json, hashlib,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
assert len(sys.argv)==2
dest=Path(sys.argv[1]).resolve()
assert dest.is_relative_to(R) and dest.is_dir()
data=np.load(dest/'ExplicitSourceBasis.npz')
P,N,U,T,M,G=(data[k] for k in ('position','normal','source_uv','tangent_source','material','group'))
views=[]; acc=[]; buf=bytearray(); prim=[]; manifest=[]
materials=list(dict.fromkeys(M.tolist()))
def put(arr):
 a=np.ascontiguousarray(arr,dtype='<f4')
 i=len(views);k=len(buf); buf.extend(a.tobytes())
 views.append(dict(buffer=0,byteOffset=k,byteLength=a.nbytes,target=34962))
 attrs=dict(bufferView=i,componentType=5126,count=len(a),type='VEC'+str(a.shape[1]))
 if a.shape[1]==3:
  attrs.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 acc.append(attrs)
 assert np.array_equal(np.frombuffer(buf[k:],dtype='<f4').reshape(a.shape),a)
 return len(acc)-1
seen=[]
for g in dict.fromkeys(G.tolist()):
 for m in materials:
  ix=np.flatnonzero((M==m)&(G==g))
  if not len(ix):continue
  seen.extend(ix.tolist())
  points=P[ix].reshape(-1,3); norms=N[ix].reshape(-1,3)
  chart=U[ix].reshape(-1,2).copy()
  chart[:,1]=1-chart[:,1]
  attributes=dict(POSITION=put(points),NORMAL=put(norms),TEXCOORD_0=put(chart))
  if m=='emboss_atlas':
   basis=T[ix].reshape(-1,4).copy();basis[:,3]*=-1
   attributes['TANGENT']=put(basis)
  prim.append(dict(attributes=attributes,material=materials.index(m),mode=4))
  manifest.append(dict(object=str(g),material=m,source_faces_1based=(ix+1).tolist()))
assert sorted(seen)==list(range(len(P))) and len(prim)==8
doc=dict(asset=dict(version='2.0'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(mesh=0)],meshes=[dict(primitives=prim)],materials=[dict(name=m) for m in materials],accessors=acc,bufferViews=views,buffers=[dict(uri='Basis.bin',byteLength=len(buf))])
(dest/'Basis.gltf').write_text(json.dumps(doc,indent=2)+'\n')
(dest/'Basis.bin').write_bytes(buf)
(dest/'primitive-source-index.json').write_text(json.dumps(manifest)+'\n')
for n in ('Basis.gltf','Basis.bin','primitive-source-index.json'):
 print(hashlib.sha256((dest/n).read_bytes()).hexdigest(),n)
