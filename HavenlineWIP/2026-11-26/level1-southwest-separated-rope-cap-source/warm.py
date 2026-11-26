from pathlib import Path
import numpy as np,json,itertools,hashlib
R=Path(__file__).resolve().parent; parent=R.parent/'hvn-l1-fence-33036-sw-south-grade-v1'
assert hashlib.sha256((parent/'SHA256SUMS').read_bytes()).hexdigest()=='3b932cfbfcd5c990e46c3cc9af289865d905bd9d749d0ed93faeb7fa6b0891b7'
D={'__file__':str(parent/'south.py')}
src=(parent/'south.py').read_text()
exec(src[:src.index('\nlower={')],D)
O=D['O']; corner=D['corner']; world=D['world'];pick=D['pick'];S=D['S'];z_lift=D['z_lift']
polys=D['polys'];terrain=D['terrain'];bound=D['bound'];n=D['n']
key='SW0/front_X_distinct_return_1_-1'
seed=world(pick[key.split('/')[1]],'SW0')
moved=seed[:-1].copy()
x0=moved[:,:,0].mean(1)
shifted=x0+.080*S((corner[0]+.18-x0)/.13)
moved[:,:,0]+=(shifted-x0)[:,None]
moved[:,:,2]+=(.039*S((corner[0]+.167-x0)/.115))[:,None]
moved[:,:,1]+=np.array([z_lift(v) for v in x0])[:,None]
# The mid-body shared timber is a 20-facet polygon; its 142mm radius
# is unchanged from neutral shared geometry. Every cap vertex must sit inside
# all its support planes, not merely inside radial idealization.
angle=np.arange(20)*2*np.pi/20+np.pi/20
norm=np.c_[np.cos(angle),np.sin(angle)]
def halfspace(A):
 X=A[..., [0,2]]-corner[[0,2]]
 return .142*np.cos(np.pi/20)-X@norm.T
# Keep front cap at exact already-recessed ring zero. Remove old near orbit.
# Recess one rear closure ring toward the post's center in Z, not across the west arm.
rear=moved[165].copy();rear[:,2]+=.025
chosen=np.r_[moved[:165],rear[None]]
assert np.max(abs(chosen[:165]-moved[:165]))==0
gaps=[float(halfspace(q).min()*1000) for q in (chosen[0],chosen[-1])]
assert min(gaps)>2 and all(corner[1]+.01<q[:,1].min()<=q[:,1].max()<corner[1]+.8 for q in (chosen[0],chosen[-1]))
T=polys(chosen,True)
vol=float(np.einsum('ij,ij->i',T[:,0],np.cross(T[:,1],T[:,2])).sum())
if vol<0:T=T[:,::-1]
from collections import Counter
def sealed(T):
 hits=Counter();signed=Counter()
 for f in T:
  a=[tuple(v) for v in np.round(f,8)]
  for i in range(3):
   x,y=a[i],a[(i+1)%3];k=tuple(sorted((x,y))); hits[k]+=1;signed[k]+=1 if (x,y)==k else -1
 return all(v==2 and signed[k]==0 for k,v in hits.items())
assert sealed(T)
O[key]=T
D['R']=R
D['cuts'][key].update(cap_facet_min_inside_mm=gaps,retained_exact_signed_165_rings=True,
                     rear_cap_only_shift_relative_to_ring_165_m=[0.,0.,.025],post_source_radius_m=.142)
exec(src[src.index('\nlower={'):],D)
r=D['manifest'];r['closure_source_claim']='one capped path, physically separate sockets; hidden unmodified far part retained; no native LOD or trim lighting test'
r['exact_cap_facet_inside_margin_mm']=gaps
r['closed_edge_and_winding_valid']=True
r['old_component_triangle_count']=2160
r['new_component_triangle_count']=len(T)
r['disposition']='SOURCE PASS within measured lower-group scope only' if (not r['non_designated_contacts'] and not any(k['pairs'] for k in r['self_crossing'].values()) and all(k['minimum_clearance_m']>0 for k in r['terrain_clipped'].values())) else 'HOLD: at least one strict lower-component gate fails'
(R/'result.json').write_text(json.dumps(r,indent=2)+'\n')
print(r['disposition'],gaps,len(T),r['non_designated_contacts'])
