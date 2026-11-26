from pathlib import Path
import math,json,numpy as np,itertools
R=Path(__file__).resolve().parent
n={'__file__':str(R/'trial.py')}
exec((R/'trial.py').read_text().split('check=terrain(rail)')[0],n)
rail,O,polys,terrain,corner,knots,rise,world,pick,bound=[n[k] if k in n else n['V']['culled_intersections'] for k in ('rail','O','polys','terrain','corner','knots','rise','world','pick','bound')]
def tube(P,w,d):
 # Roll-continuous ring from horizontal transverse reference and successive center tangent.
 t=np.gradient(P,axis=0);t/=np.linalg.norm(t,axis=1)[:,None]
 ref=np.array([0,1,0.])
 b=np.cross(t,ref); b/=np.linalg.norm(b,axis=1)[:,None];a=np.cross(b,t)
 angle=np.arange(6)*math.tau/6
 return P[:,None,:]+a[:,None,:]*(np.cos(angle)*w)[None,:,None]+b[:,None,:]*(np.sin(angle)*d)[None,:,None]
def poly_closed(rows):
 body=polys(np.r_[rows,rows[:1]],False)
 signed=np.einsum('ij,ij->i',body[:,0],np.cross(body[:,1],body[:,2])).sum()
 return body if signed>0 else body[:,::-1]
def seat(points,axis,minv):
 # Hermite terminal graft geometry uses true rail center line; exact shared corner recess only.
 s=points[:,axis];d=np.maximum(0,minv-s); points[:,axis]+=d
 return points
# South lower original wet-side return is replaced only by a bent route
# on original signed loop rings 6…164; it doesn't enter West's negative-X quadrant.
for hand in (-1,1):
 key=f'SW0/front_X_distinct_return_1_{hand}'; src=world(pick[key.split('/')[1]],'SW0')
 keep=src[6:165]; a,b=keep[-1].mean(0),keep[0].mean(0)
 mid=np.array([corner[0]+.064+(hand==1)*.017,(a[1]+b[1])/2,corner[2]])
 from scipy.interpolate import CubicSpline
 c=CubicSpline([0,.5,1],[a,mid,b],axis=0)
 t=np.linspace(0,1,14)
 part=tube(c(t),.010,.006)
 # Match the retained material-corner index to the original exact ring orientation.
 def match(a,b):
  return min(range(6),key=lambda shift:np.square(a-np.roll(b,shift,axis=0)).sum())
 ss=match(keep[-1],part[0]);pp=np.roll(part,ss,axis=1)
 # Last-ring winding mismatch is an explicit HOLD downstream.
 O[key]=poly_closed(np.r_[keep,pp[1:-1]])
# Complete West lower closed wraps, taking the longitudinal crown grade from the new rail rather than old tubes.
for hand in (-1,1):
 key=f'West2/front_X_distinct_return_1_{hand}';src=world(pick[key.split('/')[1]],'West2')
 # Exact original rear→front remote end, plus surviving real front/rear seam rings.
 front_i,rear_i=3,167
 keep=np.r_[src[rear_i:180],src[:front_i+1]]
 a=keep[-1].mean(0);b=keep[0].mean(0)
 z0=max(a[2],b[2])+.028;zf=9.68
 zs=np.linspace(z0,zf,70); x0=-8.316885;yy=.24492188162515543
 yfactor=np.cos(np.pi*(zs-z0)/.33)
 delt=hand*.043*yfactor
 under=.052*np.sqrt(np.maximum(.12,1-(delt/.064)**2))
 x=x0-under- (.006 if hand==1 else -.004)
 f=np.c_[x, np.array([yy+rise(z)+v for z,v in zip(zs,delt)]), zs]
 rear=np.c_[np.full(len(zs),-8.127), np.array([yy+rise(z)+hand*.010 for z in zs]),zs]
 arc=[]
 for t in np.linspace(0,1,11)[1:-1]:
  q=f[-1]*(1-t)+rear[-1]*t
  q[0]=np.clip(q[0],-8.383,-8.13)
  q[2]+= .067*np.sin(math.pi*t)
  q[1]+=hand*.007*np.sin(math.pi*t)
  arc.append(q)
 P=np.r_[a[None],f,np.array(arc),rear[::-1],b[None]]
 C=tube(P,.014,.0047)
 ss=min(range(6),key=lambda shift:np.square(keep[-1]-np.roll(C[0],shift,axis=0)).sum())
 C=np.roll(C,ss,axis=1)
 O[key]=poly_closed(np.r_[keep,C[1:-1]])
lower={k:v for k,v in O.items() if ('return_1_' in k or 'front_rail_1' in k)}
res={}; collisions={}
for k,t in lower.items():
 res[k]=terrain(t)
 for k2,v in lower.items():
  if k2.startswith(k.split('/')[0]) or k>k2:continue
  q=bound(t,v,[k]*len(t),[k2]*len(v))
  if q:collisions.update(q)
# Source-only projected rope width and exact triangle self/other-arm checks:
# no petal/lighting/readability inferred. View basis from stock camera orientation.
view=np.array([7.,11.,11.]);view/=np.linalg.norm(view)
right=np.cross([0,1,0],view);right/=np.linalg.norm(right);up=np.cross(view,right)
px_scale=720/13
projection={}
for k,t in lower.items():
 basis=np.array([right,up]); _xy=(t.reshape(-1,3)@basis.T)*px_scale
 projection[k]=np.ptp(_xy,axis=0).tolist()
# Full cross-arm check against every protected component on the other arm.
for k,t in lower.items():
 for k2,v in O.items():
  if k2 in lower or k2.startswith(k.split('/')[0]) or k2.startswith('shared_'):continue
  q=bound(t,v,[k]*len(t),[k2]*len(v))
  if q:collisions.update(q)
self_report={}
span=n['V']['span']; normals=n['V']['norms']
for k,t in lower.items():
 l,h=t.min(1),t.max(1); N=normals(t); c=0; longest=0.
 for i in range(len(t)):
  I=np.flatnonzero((np.arange(len(t))>i)&np.all(l[i]<=h,axis=1)&np.all(h[i]>=l,axis=1))
  for j in I:
   if np.min(np.linalg.norm(t[i][:,None]-t[j][None,:],axis=-1))<1e-8:continue
   e=span(t[i],t[j],N[i],N[j])
   if e>4e-7:c+=1;longest=max(longest,e)
 self_report[k]=[c,longest*1000]
intended_seats={}
for k,t in lower.items():
 q=bound(t,O['shared_corner'],[k]*len(t),['shared_corner']*len(O['shared_corner']))
 intended_seats.update(q)
out={'status':'HOLD if any true terrain or cross-arm remains; scoped source trial only','lower_source_groups_tested':list(lower),'reference_understudy_not_native':True,
 'total_triangles_in_prior_detached_corner_with_this_substitution':sum(len(t) for t in O.values()),'protected_other_groups_not_changed_by_this_substitution':len(O)-5,
 'lower_group_terrain':res,'self_intersection_count_and_max_mm':self_report,'normal_stock_camera_outline_bbox_px_orthographic_only':projection,'cross_arm_remaining':collisions,'measured_shared_corner_contacts':intended_seats,'source_triangle_delta_vs_previous_partial':sum(len(t) for t in O.values())-23656,'source_triangle_delta_vs_original_pair':sum(len(t) for t in O.values())-23808}
(R/'rope-result.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
# Offline evidence actual math geometry only; no material, in-game scene, or acceptance.
lines=['# CAD-only HOLD, no runtime or visual signoff.'];i=1
for k,t in lower.items():
 lines.append('o '+k.replace('/','_'))
 for f in t:
  for q in f:lines.append('v '+' '.join(f'{v:.9f}' for v in q))
  lines.append(f'f {i} {i+1} {i+2}');i+=3
(R/'LowerRopesAndRails_HOLD.obj').write_text('\n'.join(lines)+'\n')
