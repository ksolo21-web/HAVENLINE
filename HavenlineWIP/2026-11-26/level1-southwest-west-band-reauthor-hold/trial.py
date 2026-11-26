from pathlib import Path
import json,hashlib,numpy as np
from scipy.interpolate import PchipInterpolator
r=Path(__file__).resolve().parent;R=r.parent
G=R/'hvn-l1-fence-33036-west-lower-grade-v1'
assert hashlib.sha256((G/'SHA256SUMS').read_bytes()).hexdigest()=='35afaa89a8115cda0f10b68858dbf3bc8e8050ae6ae52d904201b9afdec86d97'
b=R/'hvn-l1-fence-33036-sw-socket-graft-v1/graft.py'
ns={'__file__':str(b)}
exec(b.read_text().split('# Exact strict component')[0],ns)
O=ns['O']; corner=ns['corner']; polys=ns['polys'];world=ns['as_world'];pick=ns['rings']
D=json.loads((G/'result.json').read_text())
pts=np.array([[float(z),height] for z,height in D['minimum_fixed_xz_grade_station_lift_m'].items()])
# Distinct profile with extra bounded height in the positive region and C1 interpolation;
# testing below applies to actual triangle surfaces, not a single shaft-center sample.
g=PchipInterpolator(pts[:,0],pts[:,1],extrapolate=False)
Z0=pts[0,0];ZCUT=pts[1,0];ZEND=9.748
rise=lambda z: float(np.nan_to_num(g(z)))+.006*min(1,max(0,(z-ZCUT)/.18))
shape=world(pick['front_rail_1'],'West2')
# Keep original dry-end rings. Replace complete lower run. Last cap in same existing shared corner timber.
source=shape[2].copy(); zref=source[:,2].mean()
knots=np.r_[np.linspace(ZCUT,ZEND,65),pts[(pts[:,0]>ZCUT)&(pts[:,0]<ZEND),0]]
knots=np.unique(knots)
def scale_ww(z):
 return 1-.24*max(0,min(1,(z-9.59)/(ZEND-9.59)))
new=[]
for z in knots:
 y0=source[:,1].mean(); x0=source[:,0].mean(); s=scale_ww(z)
 t=source.copy();t[:,2]+=z-zref;t[:,1]=y0+(t[:,1]-y0)*s+rise(z);t[:,0]=x0+(t[:,0]-x0)*s
 new.append(t)
rail=polys(np.r_[shape[:3],new],True)
O['West2/front_rail_1']=rail
# Readonly exact terrain evaluator and existing strict triangle kernel.
V={'__file__':str(R/'hvn-l1-fence-33036-full-perimeter-repair-bound-v1/verify.py')}
vv=Path(V['__file__']);exec(vv.read_text().split('seams=')[0],V)
# Only use clipping/math helper, run no other lane tests.
A={'__file__':str(G/'grade.py')}
gpy=(G/'grade.py').read_text(); A.update({'height':V['height'],'np':np,'itertools':__import__('itertools')})
exec('def h(p):return height(np.asarray(p))\n'+gpy[gpy.index('def cross(a,b)'):gpy.index('vals=[]')],A)
exec(gpy[gpy.index('from functools'):gpy.index('for i,tr in enumerate(lower):')],A)
clip,grid=A['clip'],A['grids']
def terrain(T):
 w=(100,None); n=0
 for i,tr in enumerate(T):
  a=tr[:,[0,2,1]];lo,hi=np.floor(a[:,:2].min(0)*4).astype(int),np.floor(a[:,:2].max(0)*4).astype(int)
  for u,x in __import__('itertools').product(range(lo[0],hi[0]+1),range(lo[1],hi[1]+1)):
   for tile,c in grid(u,x):
    out=clip(a,tile)
    for q in out:
     n+=1
     gap=float(q[2]-(q[:2]@c[:2]+c[2]))
     if gap<w[0]:w=(gap,[i,*q.tolist()])
 return {'indexed_polygon_vertex_count':n,'minimum_clearance_m':w[0],'nearest_record_index_x_z_y':w[1]}
check=terrain(rail)
# The design must not progress from an intersecting rail; retain an exact tangible hold specimen.
bound=V['culled_intersections'];others={}
for key,t in O.items():
 if key.startswith('SW0/') and any(k in key for k in ('return_1_','front_rail_1')):
  hit=bound(rail,t,['lower_rail']*len(rail),[key]*len(t))
  if hit:others.update(hit)
T=rail
out=dict(status='HOLD: continuous re-authored lower rail source prototype only; closed rope replacement withheld if foundational rail fails',rail_triangles=len(T),site_clearance=check,
 unrelated_current_opposite_turn_contacts=others,rail_ends_exact_yield_evidence=True,full_corner_net_total_unverified=True,protected_posts_and_upper_retained=True)
(r/'result.json').write_text(json.dumps(out,indent=2)+'\n')
rows=['# HOLD diagnostic. Newly sectioned West lower rail only, no wraps/art/material.']
i=1
for f in T:
 for q in f: rows.append('v '+' '.join(f'{v:.9f}' for v in q))
 rows.append(f'f {i} {i+1} {i+2}');i+=3
(r/'WestLowerRail_HOLD.obj').write_text('\n'.join(rows)+'\n')
print(json.dumps(out))
