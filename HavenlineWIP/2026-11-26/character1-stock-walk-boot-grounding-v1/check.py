from pathlib import Path
from functools import lru_cache
import hashlib,json,math,re
import numpy as np
P=Path(__file__).resolve().parent.parent
N=P/'hvn-l1-c1-stock-bounded-native-launch-v1/native.naCTgHpn'
D=N/'walk-trace-only'; S=P/'hvn-pad-mount-admission/isolated-source/HavenlineLevel1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(N/'SHA256SUMS')=='430e2352a7c29522de77dcc0cb7bcef2bd39def6d15b17f2b749ee8e0f897def'
for row in (N/'SHA256SUMS').read_text().splitlines():
 h,n=row.split('  ',1);assert sha(N/n)==h
T=P/'hvn-c1-contact-key-input'
assert sha(T/'source_inputs.py')=='08fc0bb9e9c4d8e7d1f0c736e2acf926da24f26e81e59e1021e5f255adcd6dd8'
assert sha(T/'SOURCE-SHA256SUMS')=='6d9c3a316def47cb4ccccba08cfba4465f0ceb399de423bcc5eb24b1835b13e2'
for row in (T/'SOURCE-SHA256SUMS').read_text().splitlines():
 h,n=row.split()
 if n in ('accepted_t02_surface.gd','terrain_source.gd','river_geometry.gd'):assert sha(S/n)==h
integrated=S/'previews/integrated_opening.gd';base=S/'opening.gd'
assert sha(integrated)=='29fc86cd076f98169e730bf59aacb63b25b4c28aef4326459679324169e3eba9'
assert sha(base)=='d1a8d6901a8d52a5c5084f19fe429c376800189c46dbeaea9a4012c7a72c59c1'
assert 'shape.position.y = capsule.height * 0.5 + 0.035' in integrated.read_text()
assert 'model_root.position = Vector3(-bounds.get_center().x, -bounds.position.y, -bounds.get_center().z) * factor' in base.read_text()
code=(T/'source_inputs.py').read_text()
exec('def clamp('+code.split('def clamp(',1)[1].split('def sources():',1)[0])
w=json.loads((D/'palette.json').read_bytes())
def stream(n,d):
 f=D/n;assert sha(f)==w['streams'][n]['sha256'];return np.fromfile(f,d)
src=stream('s0-source.f32','<f4').reshape(-1,3).astype(float)
ix=stream('s0-indices.i32','<i4').reshape(-1,3)
J=stream('s0-joints.i32','<i4').reshape(-1,4); wt=stream('s0-weights.f32','<f4').reshape(-1,4)
assert len(src)==52898 and len(ix)==96001
groups={}
for side in 'LR':
 slots=[k['slot'] for k in w['bindings'] if k['name'] in (side+'_Foot',side+'_ToeBase')]
 assert len(slots)==2
 mask=(src[:,1]<.110)&((wt*np.isin(J,slots)).sum(1)>.80)
 assert mask.sum()>100
 face=np.flatnonzero(mask[ix].any(1))
 assert mask.sum() and len(face)>100
 groups[side]=mask,face
assert not np.any(groups['L'][0]&groups['R'][0])
# Parametric boot edges/face clipping against projected exact 0.25 m grid
# triangles. Retain world xyz via interpolation, even if footprint degenerates.
def clip(poly,fn):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  x,y=fn(a),fn(b)
  if x>=-1e-12:out.append(a)
  if (x<0)!=(y<0) and x!=y:out.append(a+(b-a)*(x/(x-y)))
 return out
def exact_gap(nums,world):
 best=(float('inf'),None,None)
 checks=0
 for i in nums:
  tri=world[ix[i]]
  xa,za=np.floor(tri[:,[0,2]].min(0)*4).astype(int);xb,zb=np.floor(tri[:,[0,2]].max(0)*4).astype(int)
  for q in range(xa,xb+1):
   x=q/4
   for r in range(za,zb+1):
    z=r/4
    a=[t for t in tri]
    for f in (lambda p:p[0]-x,lambda p:x+.25-p[0],lambda p:p[2]-z,lambda p:z+.25-p[2]):
     a=clip(a,f)
     if not a:break
    if not a:continue
    for sign in [-1,1]:
     pts=clip(a,lambda p:sign*((p[0]-x)+(p[2]-z)-.25))
     for f in pts:
      d=float(f[1]-ground(float(f[0]),float(f[2])))
      checks+=1
      if d<best[0]:best=d,int(i),f.tolist()
 return best,checks
log=(N/'walk-trace-only.log').read_text()
receipt,=[json.loads(x) for x in re.findall(r'^C1_NORMAL_RECEIPT (.+)$',log,re.M)]
assert len(receipt['rows'])==174 and receipt['image']==[1280,720] and not receipt['rgb']
results=[]
model_poses=[]
for r in w['rows']:
 t=r['tick']; m=np.array(r['mesh']); c=receipt['rows'][t-1]; cam=np.array(c['camera'])
 assert all(r[k]==c[k] for k in ('tick','phase','clip','physics','process','draw'))
 assert c['clip']=='l1_hero_preview/walk' and c['floor'] and cam.shape==(4,3)
 xyz=stream(f'{t}-s0-baked.f32','<f4').reshape(-1,3).astype(float)
 model_poses.append(xyz)
 pose=xyz@m[1:]+m[0]
 x,y,z=c['position']
 item={'tick':t,'phase':r['phase'],'physics':r['physics'],'clip':c['clip'],'stock_camera_projected_height':int(np.ptp((pose-cam[0])@cam[2])*720/13),
    'actor_origin_above_terrain_mm':1000*(y-ground(x,z)),'feet':{}}
 for side,(mask,faces) in groups.items():
  qq=np.flatnonzero(mask); h=np.array([p[1]-ground(p[0],p[2]) for p in pose[qq]])
  gi=int(h.argmin());v=pose[qq[gi]]
  mined,checks=exact_gap(faces,pose)
  item['feet'][side]=dict(low_weighted_rows=len(qq),incident_triangles=len(faces),grid_clip_points=checks,
     minimum_exact_patch_gap_mm=1000*mined[0],hypothetical_plus35mm_RIGID_VISUAL_ONLY_residual_mm=1000*mined[0]+35,minimum_exact_indexed_face=mined[1],point_xyz_world_m=mined[2],
     projected_vertical_gap_px=float(abs(mined[0]*720/13*cam[2,1])),
     weighted_low_rows_more_than_10mm_under=int((h<-.010).sum()),
     min_indexed_row_gap_mm=float(h[gi]*1000),witness_row=int(qq[gi]),gap_row_world_m=v.tolist())
 results.append(item)
repeat_delta=float(np.max(np.linalg.norm((model_poses[0]-model_poses[2])*1.786305,axis=1)))
assert repeat_delta<.00001
print(json.dumps({'same_local_phase_tick20_160_max_abs_world_equiv_shape_delta_mm':repeat_delta*1000,'scope':'3 exact registered native stock Walk pose geometry samples only; projected ground replay (not runtime collision contact or gait certification)', 'samples':results},indent=2))
