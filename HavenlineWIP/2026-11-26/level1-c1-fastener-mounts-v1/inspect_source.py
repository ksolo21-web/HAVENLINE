import struct,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
P=Path('../hvn-pad-mount-admission/isolated-source/HavenlineLevel1/assets/characters/Character1.glb')
def load(p=P):
 b=p.read_bytes(); assert hashlib.sha256(b).hexdigest()=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
 l=struct.unpack_from('<I',b,12)[0]; d=json.loads(b[20:20+l]); buf=memoryview(b)[28+l:]
 pr=d['meshes'][0]['primitives'][0]
 def get(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
  n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
  assert not v.get('byteStride')
  return np.frombuffer(buf,dtype,count=n*a['count'],offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
 v,n,u,j,w=[get(pr['attributes'][x]) for x in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']]
 t=get(pr['indices']).reshape(-1,3)
 return d,v,n,u,j,w,t
def edges(tri):return [(int(a),int(b)) for a,b in zip(tri,np.roll(tri,-1))]
def weld(v):
 _,orig,ids=np.unique(v,axis=0,return_index=True,return_inverse=True)
 return orig,ids
if __name__=='__main__':
 d,v,n,u,j,w,t=load(); o,i=weld(v); tw=i[t]
 print(len(o),len(t),t.shape, d['accessors'][3]); print('49721',j[t[49721]],w[t[49721]].tolist(),tw[49721])
 for k in [58,59,60,61,64,65]:
  vs=(np.where(j==k,w,0).sum(1)>.999999)
  ids=np.where(vs[t].all(1))[0]
  es=Counter(tuple(sorted(e)) for f in ids for e in edges(tw[f]))
  border=set(e for e,c in es.items() if c==1)
  neigh=[f for f in range(len(t)) if not vs[t[f]].all() and any(tuple(sorted(e)) in border for e in edges(tw[f]))]
  print(k,ids.tolist(),len(border),neigh)
