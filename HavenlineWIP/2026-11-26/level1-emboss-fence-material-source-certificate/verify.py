from pathlib import Path
import hashlib,json,shlex,io
from collections import defaultdict,Counter
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parent
src=root.parent/'hvn-l1-fence-33036-rooted-emboss-module-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src/'SHA256SUMS')=='cfe4449f40ff684aafe5565490d19de17684f9b2ebcd7e55180a291b66365c1d'
for row in (src/'SHA256SUMS').read_text().splitlines():
 h,name=row.split(maxsplit=1); assert sha(src/name)==h
v=[];uv=[];n=[]; faces=[];g=m=s=''
for line in (src/'RootedEmbossedFence_SourceOnly.obj').read_text().splitlines():
 w=line.split()
 if not w or w[0].startswith('#'):continue
 k=w[0]
 if k=='v':v.append(list(map(float,w[1:])))
 if k=='vt':uv.append(list(map(float,w[1:])))
 if k=='vn':n.append(list(map(float,w[1:])))
 if k=='o':g=w[1]
 if k=='s':s=w[1]
 if k=='usemtl':m=w[1]
 if k=='f':
  corners=[tuple(int(z) if z else None for z in x.split('/')) for x in w[1:]]
  assert len(corners)==3 and all(len(x)==2 for x in corners)
  faces.append((g,m,s,corners))
V,U=np.array(v),np.array(uv); counts=Counter(); seam=defaultdict(set); signs=defaultdict(set); runs=defaultdict(list); corners_out=[]
for ix,(g,m,s,c) in enumerate(faces,1):
 vi,ti=np.array(c).T
 assert vi.min()>0 and ti.min()>0 
 a,b=V[vi[1:]-1]-V[vi[0]-1]; r,t=U[ti[1:]-1]-U[ti[0]-1]
 N=np.cross(a,b); area=np.linalg.norm(N); assert area>1e-10
 N/=area; det=float(r[0]*t[1]-r[1]*t[0])
 hand=None;check=None
 if abs(det)>1e-12:
  T=(a*t[1]-b*r[1])/det; B=(-a*t[0]+b*r[0])/det
  T/=np.linalg.norm(T); B/=np.linalg.norm(B)
  hand=int(np.sign(np.dot(np.cross(N,T),B)))
  check=max(abs(np.dot(N,T)),abs(np.dot(N,B)))
  assert hand==int(np.sign(det)) and check<1e-11
 for j in range(3):
  k=(g,tuple(V[vi[j]-1]))
  seam[k].add((m,tuple(U[ti[j]-1])))
  if hand:signs[(k,m,tuple(U[ti[j]-1]))].add(hand)
 counts[(g,m,s,hand)]+=1
 runs[m].append((ix,det,check))
 entry={'face_obj_1based':ix,'group':g,'material':m,'smoothing_record':s,'corners_source_1based':c,'UV_det':det,'winding_geometric_N_not_authored':N.tolist(),'face_UV_hand':hand}
 corners_out.append(entry)
assert not n
assert not any(d==0 for _,d,_ in runs['emboss_atlas'])
assert len(runs['emboss_atlas'])==3200
imgs={}
for fname in ['RopeFiberBaseColor.png','RopeFiberNormal.png']:
 with Image.open(src/fname) as im:
  assert im.size==(1024,128) and im.mode=='RGB'
  a=np.asarray(im)
  imgs[fname]={'sha256':sha(src/fname),'width_height':im.size,'png_tags':sorted(im.info),'per_channel_min':a.min((0,1)).tolist(),'per_channel_max':a.max((0,1)).tolist()}
  if 'Normal' in fname: norm=a.astype(float)/127.5-1
assert np.all(norm[:,:,2]>.98)
# Re-run sealed pixel generator in memory; no rerender / no atlas bytes written.
srcpy=(src/'module.py').read_text()
class MemImage:
 data={}
 @classmethod
 def fromarray(cls,a):
  class Proxy:
   def __init__(self,b): self.a=b
   def save(self,p): MemImage.data[Path(p).name]=self.a
  return Proxy(a)
exec(srcpy[srcpy.index('u,v=np.meshgrid'):srcpy.index('gsrc=')],{'np':np,'Image':MemImage,'p':Path('.')})
for name,a in MemImage.data.items():
 with Image.open(src/name) as im: assert np.array_equal(a,np.asarray(im))
 imgs[name]['generator_pixels_exact']=True
assert 'map_Kd RopeFiberBaseColor.png' in (src/'RootedFence.mtl').read_text()
out={'status':'SOURCE CERTIFICATE HOLD for actual licensed import; exact source validation and hash-bound proposed color/data slots only',
     'mesh_faces':len(faces),'corners':3*len(faces),'v_vt_vn_records':[len(v),len(uv),len(n)],
     'geometry_basis':'identity; unchanged signed authored OBJ positions and ordering',
     'candidate_bindings_for_emboss_atlas_only':{'base_color':{'role':'sRGB color','asset':'RopeFiberBaseColor.png','existing_mtl_binding':True},'normal':{'role':'tangent-space +Y, data linear no sRGB decode','asset':'RopeFiberNormal.png','existing_mtl_binding':False,'required':'explicit import material and verified shader; never infer from asset presence'}},
     'tangent_proxy':'per face geometric normal; not final imported smoothing or per-vertex tangent, no native result',
     'per_group_material_handedness':[[str(i) for i in k]+[val] for k,val in sorted(counts.items(),key=lambda z:str(z[0]))],
     'coincident_same_group_positions_requiring_UV_or_material_corner_splits':sum(len(w)>1 for w in seam.values()),
     'same_group_position_material_UV_with_mixed_face_hand':sum(len(w)>1 for w in signs.values()),
     'atlas_min_absolute_uv_det':min(abs(d) for _,d,_ in runs['emboss_atlas']),
     'atlas_max_face_tangent_plane_dot_error':max(t for _,_,t in runs['emboss_atlas']),
     'images':imgs}
(root/'result.json').write_text(json.dumps(out,indent=2)+'\n')
(root/'face-corner-index.jsonl').write_text(''.join(json.dumps(i,separators=(',',':'))+'\n' for i in corners_out))
print(json.dumps(out,indent=2))
