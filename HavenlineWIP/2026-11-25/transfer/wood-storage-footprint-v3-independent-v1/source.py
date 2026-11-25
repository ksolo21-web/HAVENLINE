import json,struct,hashlib,sys
import numpy as np
from pathlib import Path
b,c=map(Path,sys.argv[1:])
def load(p,h):
 d=p.read_bytes(); assert hashlib.sha256(d).hexdigest()==h
 m,v,total,n,k=struct.unpack_from('<4sIIII',d); assert m==b'glTF' and v==2 and total==len(d) and k==0x4e4f534a
 return json.loads(d[20:20+n]),memoryview(d)[28+n:]
a,A=load(b,'3db8ed722b3a41b31003a7a43b85c1b1344fc3e98dcd3c9c94a9f96d34838045')
g,G=load(c,'c89ee6e92e352f32586113c6d5e1d81b21bc7cfb84603ee70d16e0b0d426afc1')
def bv(d,z,i):
 x=d['bufferViews'][i]; j=x.get('byteOffset',0); return z[j:j+x['byteLength']]
changed=set()
for p,n in zip(a['meshes'][0]['primitives'],g['meshes'][0]['primitives']):
 assert p==n
 for k in ['POSITION','NORMAL']:
  n=p['attributes'][k]; x,y=a['accessors'][n],g['accessors'][n]
  j=x['bufferView']; assert j==y['bufferView']
  changed.add(j)
  U=np.frombuffer(bv(a,A,j),dtype='<f4').reshape(-1,3);V=np.frombuffer(bv(g,G,j),dtype='<f4').reshape(-1,3)
  W=U*np.array([4.4,1,4.4]) if k=='POSITION' else U/np.array([4.4,1,4.4])
  if k=='NORMAL':W=W/np.linalg.norm(W,axis=1)[:,None]
  else: assert np.array_equal(U[:,1],V[:,1])
  assert np.max(abs(W-V))<2e-7
  for k in ('min','max'):
   if k in y:y[k]=x[k]
assert a==g
for i in range(len(a['bufferViews'])):
 if i not in changed: assert bv(a,A,i)==bv(g,G,i)
print(json.dumps({'unchanged_embedded_image_sha256':hashlib.sha256(bv(a,A,a['images'][0]['bufferView'])).hexdigest(),
   'visual_material_and_uv_data_unchanged':True,'positions_XZ_scale_only':4.4,'position_Y_values_bitwise_unchanged':True,
   'normals_inverse_transpose_verified':True,'position_and_normal_views_changed':len(changed)},indent=2))
