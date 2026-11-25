"""Default-camera depth buffer math only: no engine, pixels to user, or placement."""
import json,hashlib,sys,struct,runpy,importlib.util,tempfile
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
from scipy.ndimage import distance_transform_edt
H=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
old=Path('hvn-l1-wood-receiver-render-intake-v1/preflight.py')
assert H(old)=='5cea52436a695dcf9f396b2d323d5db40e8d4ff6dc95ef7e3791722a391fec9c'
mod=runpy.run_path(str(old))
p=mod['args'](sys.argv[1:]);spec,m,s,origin,names=mod['verify'](p)
origin=np.array(origin)
f=m['frames'][-1]
rs=importlib.util.spec_from_file_location('prior_exact_native_transform',p['bake'])
ba=importlib.util.module_from_spec(rs);rs.loader.exec_module(ba)
with tempfile.TemporaryDirectory(dir=Path(__file__).absolute().parent,prefix='owned-transient.') as private:
 pose=Path(private)/'pose.glb'
 ba.bake_factory(p['actor'],m,p['manifest'])(f,pose)
 b=pose.read_bytes()
 assert 0<len(b)<12_000_000
 sz=struct.unpack_from('<I',b,12)[0]
 d=json.loads(b[20:20+sz]);raw=memoryview(b)[28+sz:]
 def acc(index):
  item=d['accessors'][index];v=d['bufferViews'][item['bufferView']]
  k={'VEC3':3,'SCALAR':1}[item['type']]
  dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[item['componentType']]
  return np.frombuffer(raw,dtype=dtype,count=k*item['count'],offset=v['byteOffset']).reshape(-1,k)
 actor=acc(0)[acc(3).reshape(-1,3)].astype(float)
assert len(actor)==96001
decode=runpy.run_path('hvn-l1-transfer-crown-spacing-v1/audit.py')['decode']
tris,groups=decode(p['crown'])
assert groups==[1087,213] and len(tris)==1300
sc=spec['local_units_to_m']
mat=np.array(spec['linked_exact_source_log']['normalized_linear_source_to_deck'])
ofs=np.array(spec['linked_exact_source_log']['normalized_source_offset_before_inserting_seat'])
local=np.array(spec['one_near_row_two_anchor_offsets_local'])
o,right,up,back=np.array(f['camera'])
def project(x):
 q=(x-o)@np.array([right,-up,back]).T
 q[...,:2]=q[...,:2]*720/13+[640,360]
 return q
outer=[]
for line in (p['blockout']/'ReceiverBlockout.obj').read_text().splitlines():
 if line.startswith('v '):outer.append([float(x) for x in line.split()[1:]])
outer=np.array(outer)
assert len(outer)==105
inner=ConvexHull(outer[52:104][:,[0,2]]).equations
def supported(a):
 v=np.unique(a.reshape(-1,3),axis=0)
 y=v[:,1]
 assert y.min()>-1e-10
 c=v[np.abs(y)<1e-9];assert len(c)==3
 proxy=(v.max(0)+v.min(0))/2
 e=ConvexHull(c[:,[0,2]]).equations
 return dict(exact_contact_count=len(c),min_local_y_m=float(y.min()),
             support_margin_proxy_m=float(np.min(-e[:,2]-e[:,:2]@proxy[[0,2]])*sc),
             outline_reserve_to_inner_trim_m=float(np.min([-i[2]-np.max(v[:,[0,2]]@i[:2]) for i in inner])*sc))
def logs(anchors):return [tris@mat.T+ofs+k for k in anchors]
# One source-led front-row analogue moved to the same plate's distant half:
# mirror only the pair-center coordinate across central Z=0. Heading,
# geometry, interval, plate, world origin, paint, and actor stop untouched.
n=logs(local)
fl=local.copy();fl[:,2]*=-1
far=logs(fl)
layout={'prior_near_shadow_control':n,'one_far_row_candidate':far}
ap=project(actor); all_xy=[ap.reshape(-1,3)[:,:2]]
for pair in layout.values():
 for t in pair:all_xy.append(project(sc*t+origin).reshape(-1,3)[:,:2])
box=np.vstack(all_xy);x0,y0=np.floor(box.min(0)-2).astype(int);x1,y1=np.ceil(box.max(0)+2).astype(int)
assert 0<=x0<x1<1280 and 0<=y0<y1<720 and (x1-x0)*(y1-y0)<55000
# Subpixel sampled computational masks only, no media output; reference
# 1280x720 camera remains unchanged. Orthographic depth is linear per face.
ss=3
w,h=(x1-x0)*ss,(y1-y0)*ss
def zbuf(p,subsets):
 P=p.copy()
 P[...,:2]=(P[...,:2]-[x0,y0])*ss
 z=np.full((h,w),-np.inf)
 mid=np.full((h,w),-1,dtype=np.int32)
 # use exact normals only to skip projected-degenerate area; faces all opaque
 for i,t in enumerate(P):
  a,b=t[1]-t[0],t[2]-t[0]
  denom=a[0]*b[1]-a[1]*b[0]
  if abs(denom)<1e-10:continue
  l,u=np.clip(np.ceil(t[:,:2].min(0)-.5).astype(int),[0,0],[w,h])
  r,v=np.clip(np.floor(t[:,:2].max(0)-.5).astype(int)+1,[0,0],[w,h])
  if l>=r or u>=v:continue
  x=np.arange(l,r)[None,:]+.5-t[0,0];y=np.arange(u,v)[:,None]+.5-t[0,1]
  A=(x*b[1]-b[0]*y)/denom;B=(a[0]*y-x*a[1])/denom
  D=t[0,2]+A*a[2]+B*b[2]
  mask=(A>=-1e-10)&(B>=-1e-10)&(A+B<=1+1e-10)&(D>z[u:v,l:r])
  z[u:v,l:r][mask]=D[mask];mid[u:v,l:r][mask]=subsets[i]
 return z,mid
hero,_=zbuf(ap,np.zeros(len(ap),dtype=np.int8))
from PIL import Image
tex=np.array(Image.open(p['paint']).convert('RGB'))
y,x=np.indices(tex.shape[:2]);r,g,b=np.moveaxis(tex,2,0)
cut=(x>=525)&(x<=798)&(y>=537)&(y<=695)&(r>=180)&(g>=143)&(b>=68)
U=(x[cut]+.5)/tex.shape[1];V=(y[cut]+.5)/tex.shape[0]
# Exactly the existing texture's center and slopes as in the pinned blockout.
stamp=project(np.c_[(V-.5)/.437062941,np.zeros(len(U)),(.5-U)/.344352627]+origin)
xi,yi=np.floor((stamp[:,:2]-[x0,y0])*ss).astype(int).T
inside=(xi>=0)&(xi<w)&(yi>=0)&(yi<h)
def stamped(depth):
 result=np.zeros(len(stamp),bool)
 result[inside]=depth[yi[inside],xi[inside]]>stamp[inside,2]+1e-7
 return result
hero_stamp=stamped(hero)

results={}
for label,pair in layout.items():
 x0a=pair[0][...,0].max();x1b=pair[1][...,0].min()
 gap=float((x1b-x0a)*sc);assert gap>=.025-1e-10
 zr=[]
 for t in pair:zr.append(zbuf(project(sc*t+origin),np.r_[np.zeros(groups[0],dtype=np.int8),np.ones(groups[1],dtype=np.int8)]))
 report=[];winners=[]
 for j,(z,mid) in enumerate(zr):
  cz=zr[1-j][0]
  mask=np.isfinite(z); end=mid==1
  assert end.sum()>0
  safe=(z>hero+1e-7)&mask
  winning=safe&(z>cz+1e-7)
  winners.append(winning)
  report.append(dict(total_solo_sample_count=int(mask.sum()),solo_endgrain_samples=int(end.sum()),
             visible_after_actor_and_other_log_samples=int(winning.sum()),
             full_log_fraction_visible=float(winning.sum()/mask.sum()),
             occluded_by_actor_alone_fraction=float((mask&~safe).sum()/mask.sum()),
             visible_endgrain_samples=int((winning&end).sum()),
             endgrain_fraction_visible=float((winning&end).sum()/end.sum())))
 assert winners[0].any() and winners[1].any()
 adjacent_clearance=float(distance_transform_edt(~winners[0])[winners[1]].min()/ss)
 results[label]={'both_exact_flat_supports':list(map(supported,pair)),
  'pair_x_gap_m':gap,
  'stamp_subpixel_core':{'samples':int(len(stamp)),'only_actor_obscured':int(hero_stamp.sum()),'only_log_depth_obscured':int(stamped(np.maximum(zr[0][0],zr[1][0])).sum()),'visible_after_actor_and_logs':int((~stamped(np.maximum.reduce([hero,zr[0][0],zr[1][0]]))).sum()),'model':'same PNG exact texture center world coordinates; ray nearest 3x sample (not raster or readability score)'}, 'visible_masks_min_distance_equivalent_px':adjacent_clearance,'logs':report}
out={'scope':'OFFLINE_OPAQUE_TRIANGLE_DEPTH_ONLY_NO_RENDER_NO_REAL_TERRAIN_OR_SITE',
     'actor_triangles_evaluated':len(actor),'genuine_age':f['age_tick'],'camera_size':f['camera_size'],'viewport':f['viewport'],
     'samples_per_side_of_each_pixel':ss,'stock_camera_roi_only':box.min(0).tolist()+box.max(0).tolist(),
     'retained_normal_game_stop':True,'same_decorative_plate_paint':True,'directional_choice':'mirror pair midpoint onto far half of the same detached plate',
     'candidate_anchor_offsets_normalized':fl.tolist(),'evidence':results}
print(json.dumps(out,indent=2))
