#!/usr/bin/env python3
"""Exact arm material/cuff custody, with no writes to any source."""
import hashlib,io,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
files=[Path(x) for x in sys.argv[1:]]
expected=["7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb",
"d44de88c78aec4f98c80d379c549c2a9d2f6d1bf54d5288c150ed1d1f51aa336","0484d5e1ee3d9b54e67e7eacdd7df0fe9f5ca44fed8485fd09d5715adba8855f",
"14d72f4122ddd370663d1c25ea2560e4c79b0fde672f1a8ce4db207f2f0329d4","b536ab00fe111bd3b3dbf7a5326e9cd484002a3e68b43ec363091e21e42131ed",
"79a3c9e4d31c609f0dc552b8810ab4061256def22e2eb9e4cefc3c1a33f3677e"]
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert [digest(p) for p in files]==expected
def glb(path):
 raw=path.read_bytes(); n,t=struct.unpack_from('<II',raw,12)
 assert raw[:4]==b'glTF' and t==0x4e4f534a
 doc=json.loads(raw[20:20+n]); size,b=struct.unpack_from('<II',raw,20+n)
 assert b==0x004e4942 and len(raw)==28+n+size
 def view(i):
  a=doc['bufferViews'][i]; assert 'byteStride' not in a and a['buffer']==0
  return memoryview(raw)[28+n+a.get('byteOffset',0):28+n+a.get('byteOffset',0)+a['byteLength']]
 def acc(i):
  a=doc['accessors'][i];assert not a.get('sparse')
  shape={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
  return np.frombuffer(view(a['bufferView']),dtype={5125:'<u4',5126:'<f4'}[a['componentType']],count=a['count']*shape,offset=a.get('byteOffset',0)).reshape(-1,shape)
 prim=doc['meshes'][0]['primitives'][0]
 x=acc(prim['attributes']['POSITION'])
 return np.column_stack((x[:,0],-x[:,2],x[:,1])),acc(prim['indices']).reshape(-1,3),doc,prim,view,acc
p,f,doc,pr,view,acc=glb(files[0]);A,T,*_=glb(files[5]); assert len(T)==512
b,h,s=[np.load(i,allow_pickle=False) for i in files[1:4]]
J=json.loads(files[4].read_text())
P,F,W,names=(b[k] for k in ('P','F','W','names')); V=h['held'].astype(float)
assert np.array_equal(P,p) and np.array_equal(F,f) and np.array_equal(F,h['faces'])
uv=acc(pr['attributes']['TEXCOORD_0']);mat=doc['materials'][pr['material']]
assert len(doc['materials'])==len(doc['meshes'][0]['primitives'])==1
im=mat['pbrMetallicRoughness']['baseColorTexture']; assert im['texCoord']==0
tex=doc['images'][doc['textures'][im['index']]['source']]
I=np.asarray(Image.open(io.BytesIO(view(tex['bufferView']))).convert('RGB'))
def rgb_samples(ids):
 q=uv[ids]; ih,iw=I.shape[:2]
 px=np.minimum((q[:,0]*iw).astype(int),iw-1)
 py=np.minimum((q[:,1]*ih).astype(int),ih-1)
 return I[py,px].tolist()
M=np.array(J['orientation']);t=np.array(J['zero_depth_tool_origin'])-np.array([0.,J['only_selected_depth_m'],0.])
tool=(A@M.T+t)[T]
bis=np.unique(np.sort(F[:,[0,1,1,2,2,0]].reshape(-1,2),axis=1),axis=0)
a,z=bis.T
def crosses(first,second):
 o=second[0]; e1,e2=second[1:]-o; hits=[]
 for x,y in zip(first,np.roll(first,-1,axis=0)):
  d=y-x; h=np.cross(d,e2); det=e1@h
  if abs(det)<1e-15:continue
  n=x-o; u=(n@h)/det; q=np.cross(n,e1); v=(d@q)/det; t=(e2@q)/det
  if min(u,v,1-u-v,t,1-t)>1e-8:hits.append(x+t*d)
 return hits
