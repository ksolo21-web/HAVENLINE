#!/usr/bin/env python3
"""Read-only flat paint and projected size budget; not a scene render."""
import hashlib,io,json,struct,sys
from pathlib import Path
from PIL import Image
import numpy as np
def png(p):
 b=Path(p).read_bytes(); n=struct.unpack_from('<I',b,12)[0]
 d=json.loads(b[20:20+n]); r=b[28+n:]
 v=d['bufferViews'][d['images'][0]['bufferView']]; p=v['byteOffset']
 return np.asarray(Image.open(io.BytesIO(r[p:p+v['byteLength']])).convert('RGB')).astype(int),d,r
def convert(ij):
 # Flat texture pixel centers mapped through exact top UVs (x/.66+.5,z/.52+.5).
 return np.c_[(ij[:,1]+.5)/1320*.66-.33,np.zeros(len(ij)),(ij[:,0]+.5)/1040*.52-.26]
D=np.array([7.,11.,11.]);D/=np.linalg.norm(D)
cam_right=np.cross([0,1,0],D);cam_right/=np.linalg.norm(cam_right)
cam_up=np.cross(D,cam_right)
def projected(m):
 pts=convert(np.argwhere(m))
 axes=pts@np.array([cam_right,cam_up]).T*720/13
 return np.ptp(axes,axis=0).tolist()
def arg_masks(I):
 y,x=np.ogrid[:1040,:1320]; central=(x>350)&(x<970)&(y>200)&(y<840)
 r,g,b=I.transpose(2,0,1)
 bark=central&(r>=120)&(r-g>=30)&(g-b>=22)&(g<145)
 cut=central&(r>=210)&(g>=145)&(r-g<100)
 rim=(~central)&(r>=171)&(g>=140)&(b>=100)
 return bark,cut,rim
res={}
for tag,path in [('baseline',sys.argv[1]),('candidate',sys.argv[2])]:
 I,d,r=png(path); br,cu,rm=arg_masks(I)
 def t(m):return dict(source_texels=int(m.sum()),projected_coordinate_bbox_at_720p=projected(m),median_srgb=np.median(I[m],axis=0).tolist())
 mid=[rm[:80,660].sum(),rm[-80:,660].sum(),rm[520,:80].sum(),rm[520,-80:].sum()]
 assert min(mid)>0
 primer=d['meshes'][0]['primitives'][0]['attributes']['POSITION'];view=d['bufferViews'][d['accessors'][primer]['bufferView']]
 A=np.frombuffer(r[view['byteOffset']:view['byteOffset']+view['byteLength']],dtype='<f4').reshape(-1,3)
 P=A[1::3][:,[0,2]];E=np.roll(P,-1,axis=0)-P
 corner=convert(np.argwhere(rm))[:,[0,2]]
 sign=np.sign(E[0,0]*(-P[0,1])-E[0,1]*(-P[0,0]))
 dst=((corner[:,1,None]-P[:,1])*E[:,0]-(corner[:,0,None]-P[:,0])*E[:,1])*sign/np.linalg.norm(E,axis=1)
 res[tag]={'bark':t(br),'cut_end':t(cu),'combined_two_tone_mark':t(br|cu),'rim_cream_texels_in_four_midpoint_crossings':list(map(int,mid)),
           'bright_rim_texels_outside_actual_flat_top_mask':int((dst.min(1)<-1.e-9).sum())}
assert res['candidate']['bright_rim_texels_outside_actual_flat_top_mask']==0
print(json.dumps({'semantics':'unlit paint masks and coordinate span only, not actual final pixels or visibility; exact 1280x720 vector [7,11,11] and 13m stock orthographic vertical span','metrics':res},indent=2,sort_keys=True))
