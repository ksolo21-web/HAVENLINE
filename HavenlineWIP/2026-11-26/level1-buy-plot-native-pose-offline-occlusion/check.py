from pathlib import Path
import json,hashlib,ctypes,subprocess,sys
import numpy as np
from PIL import Image
here=Path(__file__).resolve().parent
root=here.parent
par=root/'hvn-buy-plot-c1-native-arrays-censusfix'
run=par/'graphics-evidence.bPv5hUdD'
report=run/'native-arrays-intake.json'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(report)=='dc2b234ffbb101ee426178a5659c3e020c0f81e6dbba6c7cb3d1d9dcc41e5a48'
assert json.loads(subprocess.check_output([sys.executable,'-B',str(par/'parse.py'),str(run)],text=True))==json.loads(report.read_text())
# Source-exact terrain height function, relative camera and pad point registration.
p=Path('../hvn-l1-grounded-construction-marker-v1/terrain-fit.py')
exec(p.read_text().split('q=np.zeros(',1)[0].replace("Path('fitcheck.py')","Path('../hvn-l1-grounded-construction-marker-v1/fitcheck.py')"))
dll=ctypes.CDLL(str(here/'raster.so')); F64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS'); I32=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
dll.rast.argtypes=[F64,I32,ctypes.c_int,F64,*([ctypes.c_int]*5)]
def apply(q,a):
 M=np.array(a);return q@M[:3]+M[3]
def screen(q,cam,scale=1):
 C=np.array(cam);q=(q-C[3])@C[:3].T
 return q*np.array([720/13,-720/13,1])*np.array([scale,scale,1])+[640*scale,360*scale,0]
def owner_position(q,j,w,m):
 # Transform3D columns in each native pose: world(mesh) * bone_pose * inverse bind * vertex
 j=j.reshape(-1,4);w=w.reshape(-1,4)
 B=np.array([a['inverse'] for a in m['palette']])[j]
 P=np.array([a['pose'] for a in m['palette']])[j]
 local=np.einsum('ni,nkij->nkj',q,B[:,:,:3])+B[:,:,3]
 local=np.einsum('nki,nkij->nkj',local,P[:,:,:3])+P[:,:,3]
 return apply(np.einsum('nkj,nk->nj',local,w),m['world'])
def dilate(a,r):
 z=a.copy()
 for dy in range(-r,r+1):
  for dx in range(-r,r+1):z|=np.roll(np.roll(a,dx,axis=1),dy,axis=0)
 return z
def roledata(n):
 pp=run/'enabled'; po=json.loads((pp/(n+'.pose.json')).read_text()); a=json.loads((pp/(n+'.arrays.json')).read_text()); by={s['relative']:s for s in po['surfaces']}
 roles=[]
 for part in a['parts']:
  x=[np.fromfile(pp/d['file'],dtype=('<f4' if k in 'pw' else '<i4')) for k,d in zip('pijw',part['arrays'])]
  q,idx,j,w=x;q=q.reshape(-1,3)
  m=by[part['relative']]
  world=owner_position(q,j,w,m) if len(j) else apply(q,m['world'])
  # Godot native viewport Y is down; cull_mode 0 back, mode 2 disabled.
  assert part['decl']['cull'] in (0,2)
  roles.append((world,idx,1 if part['decl']['cull']==0 else 0))
 return po,a,roles
names=['funded-approach-moving','funded-near-moving']
a=[roledata(n) for n in names]
# Native pose/viewport state from original log for label-registration of candidate footprint.
draws=[json.loads(s.split(' ',1)[1])['draw'] for s in (run/'enabled.log').read_text().splitlines() if s.startswith('L1_PAD_DRAW ')][:2]
sv={}
for n,(po,ar,roles),dr in zip(names,a,draws):
 im=np.array(Image.open(run/'enabled'/(n+'.png')))[:,:,:3].astype(int)
 ox,oy=int(dr['label_anchor_px'][0])-80,int(dr['label_anchor_px'][1])-110; ww,hh=155,155
 z=np.full((hh,ww),-np.inf,dtype=np.float64); zs=[]
 for c in (1,-1,0):
  z.fill(-np.inf)
  for g,i,f in roles:
   dll.rast(np.ascontiguousarray(screen(g,po['camera'])),i,len(i)//3,z,ww,hh,ox,oy,f*c)
  zs.append(np.isfinite(z).copy())
 R,G,B=np.moveaxis(im[oy:oy+hh,ox:ox+ww],2,0)
 Y,X=np.mgrid[oy:oy+hh,ox:ox+ww]
 # Strong game character garment swatch colors only, bounded by actual actor-centered crop.
 s=(Y>250)&(Y<362)&(X<686)&(X>613)&(((R>G+24)&(G>B+20))|((B>R+38)&(B>G+17)))
 # Exclude known old art RGB and test both exact raw cull directions plus no-cull.
 for q in [(147,77,23),(255,224,166),(171,102,38),(133,76,26)]:s&=~((R==q[0])&(G==q[1])&(B==q[2]))
 sv[n]={'native_high_chroma_subset_not_full_silhouette':int(s.sum()),'matches_or_within_2px_cull_plus_minus_none':[int((dilate(z,2)&s).sum()) for z in zs],
 'raw_projected_area_pixels_plus_minus_none':[int(z.sum()) for z in zs],'plus_minus_xor_pixels':int((zs[0]^zs[1]).sum()),'label_bound':[float(np.max(np.asarray(l['pixel_bounds_corners'])[:,1])) for l in ar['labels']]}
# True nominal geometry is NOT authored. Clip rounded gray to .711m and require
# sample targets all in matte, while maintaining 2 screen pixels/8mm double-sided conservative separation.
def rects(mask,w,h,U,V):
 hit=[]
 for y in range(mask.shape[0]-h+1):
  for x in range(mask.shape[1]-w+1):
   k=int(mask[y:y+h,x:x+w].sum());hit.append((w*h-k,int(U[x]),int(V[y])))
 return min(hit),sum(v[0]==0 for v in hit)
marker=json.loads((root/'hvn-l1-grounded-construction-marker-icon-study-v1/marker.json').read_text())
protected=[np.asarray(marker['vertices'][name])+[anchor[0],ZERO,anchor[1]] for name in ('castle','price','brackets')]
res={}; frozen={}
for hgt,wdt in ((720,1280),(540,960),(475,844)):
 scale=hgt/720
 U=np.arange(-32,33); V=np.arange(-24,24)
 stack=[]
 for (po,ar,roles),dr in zip(a,draws):
  gAnchor=np.array(dr['label_anchor_px'])*scale
  gAnchor[0]+=(wdt-1280*scale)/2
  ax,ay=np.floor(gAnchor).astype(int)
  world=[]
  for yy in V:
   for xx in U:
    p2=(np.array([ax+xx+.5,ay+yy+.5])-gAnchor)/scale
    q=place(p2,.006)
    world.append([anchor[0]+q[0],ZERO+terrain_height(q)+.006,anchor[1]+q[1]])
  world=np.array(world)
  local=world[:,[0,2]]-anchor
  fit=np.array([ok(x,z,.511,.073) and np.linalg.norm([x,z])<=.711 for x,z in local]).reshape(len(V),len(U))
  z=np.full((len(V),len(U)),-np.inf,dtype=np.float64)
  for g,i,f in roles:
   q=np.ascontiguousarray(screen(g,po['camera'],scale)); q[:,0]+=(wdt-1280*scale)/2
   dll.rast(q,i,len(i)//3,z,len(U),len(V),ax+U[0],ay+V[0],0)
  C=np.array(po['camera']); terrain_z=((world-C[3])@C[:3].T)[:,2].reshape(len(V),len(U))
  bad=z>=(terrain_z-.008)
  Y,X=np.meshgrid(ay+V+.5,ax+U+.5,indexing='ij')
  label=np.zeros(Y.shape,dtype=bool)
  for l in ar['labels']:
   b=np.array(l['pixel_bounds_corners'])*scale;b[:,0]+=(wdt-1280*scale)/2
   lo=b.min(0)-2;hi=b.max(0)+2; label|=(X>=lo[0])&(X<=hi[0])&(Y>=lo[1])&(Y<=hi[1])
  expected_xy=np.stack((X,Y),axis=-1).reshape(-1,2)
  actual_xy=screen(world,po['camera'],scale)[:,:2]+[(wdt-1280*scale)/2,0]
  reproj=float(np.max(abs(actual_xy-expected_xy)))
  assert reproj<.02,reproj
  reserved=np.full(z.shape,-np.inf,dtype=np.float64)
  for g in protected:
   q=np.ascontiguousarray(screen(g,po['camera'],scale));q[:,0]+=(wdt-1280*scale)/2
   idx=np.arange(len(g),dtype=np.int32)
   dll.rast(q,idx,len(idx)//3,reserved,len(U),len(V),ax+U[0],ay+V[0],0)
  stack.append((fit,~(dilate(bad,2)|label),fit & (X>gAnchor[0]+3),dilate(np.isfinite(reserved),1)))
 common=stack[0][0]&stack[1][0]&stack[0][1]&stack[1][1]&stack[0][2]&stack[1][2]
 res[f'{wdt}x{hgt}']={f'{w}x{h}':rects(common,w,h,U,V) for w,h in ((14,8),(16,9),(18,9),(20,10))}
 owned=common&~(stack[0][3]|stack[1][3])
 frozen[f'{wdt}x{hgt}']={f'{w}x{h}':rects(owned,w,h,U,V) for w,h in ((10,8),(12,8),(14,8),(16,9),(18,9))}
print(json.dumps({'after_existing_price_build_brackets_reservations':frozen,'receipt_sha256':sha(report),'absolute_screen_color_calibration':sv,'clipped_114_common_rect_measurement':res,
    'limits':'opaque all-sided union and 2px/8mm dilation; approximate GPU/pose, 2 exact capture times only; Label3D bounds not glyphs, no actual 960/844 draws'},indent=2))
