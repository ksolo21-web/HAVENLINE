#!/usr/bin/env python3
"""Construct standalone Y-up reference-inspired storage art; no scene/authority."""
from pathlib import Path
import hashlib,json,math,struct
from PIL import Image
import numpy as np
W,D=.660,.520
R=.028
THICK=.008
# Bottom, waist, and top bevel coordinate radii in XZ. Top = support datum.
levels=[(-.008, .004),(-.002,.002),(0.,.005)]
def ring(inset):
 hw,hd=W/2-inset,D/2-inset; r=R-inset
 return np.array([(sx*(hw-r)+r*math.cos(t),sz*(hd-r)+r*math.sin(t))
  for sx,sz,t0 in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]
  for t in np.radians(np.linspace(t0,t0+90,13))])
rings=[np.column_stack([q[:,0],np.full(len(q),y),q[:,1]]) for y,i in levels for q in [ring(i)]]
top=rings[-1]
png=Path('paint.png').read_bytes()
im=Image.open(Path('paint.png')).convert('RGBA')
assert im.size==(1320,1040) and im.getextrema()[-1]==(255,255)
# Solid baked paint regions must have local contrast, with no transparent faux shadows.
at=lambda x,y:im.getpixel((x,y))[:3]
assert at(660,575)[0]>220 and at(660,575)[1]>165
assert at(440,515)[0]<110 and at(440,515)[1]<105
for x,y in [(660,22),(1298,520),(660,1018),(22,520)]:
 assert min(at(x,y))>100
pts=[]; ns=[]; uv=[]; tris=[]
def add(a,flip=False):
  a=np.array(a)[[0,2,1]] if flip else np.asarray(a)
  n=np.cross(a[1]-a[0],a[2]-a[0]); d=np.linalg.norm(n);assert d>1e-11
  off=len(pts); pts.extend(a.tolist());ns.extend([list(n/d)]*3)
  uv.extend([(float(x/W+.5),float(z/D+.5)) for x,_,z in a])
  tris.extend([off,off+1,off+2])
N=len(top)
for i in range(N):
 j=(i+1)%N
 add([[0,0,0],top[j],top[i]])
top_count=len(tris)
assert all(n[1]>.999999 for n in ns)
for j in range(len(rings)-1):
 lower,upper=rings[j],rings[j+1]
 for a in range(N):
  b=(a+1)%N
  add([lower[a],lower[b],upper[b]],True)
  add([lower[a],upper[b],upper[a]],True)
# Side fit normal check before bottom. Every radial face must face outside.
for i in range(top_count,len(pts),3):
 assert np.mean(np.array(pts[i:i+3])[:,[0,2]],axis=0)@np.array(ns[i])[[0,2]]>0
for a in range(N):
 b=(a+1)%N
 add([[0,levels[0][0],0],rings[0][a],rings[0][b]])
B=bytearray();V=[];A=[]
def raw(b,target=None):
 while len(B)%4:B.append(0)
 d=dict(buffer=0,byteOffset=len(B),byteLength=len(b))
 if target:d['target']=target
 B.extend(b);V.append(d);return len(V)-1
def acc(x,kind,ty,target):
 x=np.asarray(x,dtype={5126:'<f4',5123:'<u2'}[ty])
 v=raw(x.tobytes(),target)
 d=dict(bufferView=v,componentType=ty,count=len(x),type=kind)
 if ty==5126:
  d.update(min=x.min(0).astype(float).tolist(),max=x.max(0).astype(float).tolist())
 A.append(d);return len(A)-1
def primitive(begin,end,mat):
 p=acc(pts[begin:end],'VEC3',5126,34962)
 n=acc(ns[begin:end],'VEC3',5126,34962)
 t=acc(uv[begin:end],'VEC2',5126,34962)
 i=acc(range(end-begin),'SCALAR',5123,34963)
 return dict(attributes=dict(POSITION=p,NORMAL=n,TEXCOORD_0=t),indices=i,material=mat)
pr=[primitive(0,top_count,0),primitive(top_count,len(pts),1)]
pv=raw(png)
G={'asset':{'version':'2.0','generator':'Havenline detached wood storage art v1'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':'WoodStoragePlate_Empty','mesh':0}],'meshes':[{'name':'LowSlatePaintedStoragePlate','primitives':pr}],'materials':[
 {'name':'Painted slate / warm continuous inlay / wood pictogram','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':.88}},
 {'name':'Graphite-brown slate edge','pbrMetallicRoughness':{'baseColorFactor':[.037,.027,.021,1],'metallicFactor':0,'roughnessFactor':.94}}],
 'images':[{'name':'Wood storage paint','bufferView':pv,'mimeType':'image/png'}],
 'textures':[{'sampler':0,'source':0}],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],
 'accessors':A,'bufferViews':V,'buffers':[{'byteLength':len(B)}]}
J=json.dumps(G,separators=(',',':'),sort_keys=True).encode()
J+=b' '*((-len(J))%4);B.extend(b'\0'*((-len(B))%4))
glb=struct.pack('<4sIIII',b'glTF',2,12+8+len(J)+8+len(B),len(J),0x4e4f534a)+J+struct.pack('<II',len(B),0x004e4942)+B
Path('wood_storage_empty.glb').write_bytes(glb)
