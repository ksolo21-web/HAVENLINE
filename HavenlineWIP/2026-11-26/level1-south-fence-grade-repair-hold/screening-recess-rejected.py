from pathlib import Path
import hashlib, json, numpy as np, itertools
R=Path(__file__).resolve().parent
B=R.parent/'hvn-l1-fence-33036-sw-grade-reauthor-v1'
assert hashlib.sha256((B/'SHA256SUMS').read_bytes()).hexdigest()=='800e0dd400836468a77f46ac065120ac93471d70d73a8aea540c10aa0de208d0'
P={'__file__':str(B/'ropes.py')}
exec((B/'ropes.py').read_text().split('lower={')[0],P)
locals().update({k:P[k] for k in ('O','world','pick','polys','poly_closed','terrain','bound','corner','n')})
old=P['n']['ns']['O']
def S(x):
 v=np.clip(x,0,1);return v*v*(3-2*v)
def z_lift(x):
 return .018*S((x+6.96)/.27)*S((-6.396-x)/.016)
shape=world(pick['front_rail_1'],'SW0')
# Keep the admitted shared socket throat, then grade on far bank without reusing
# the one wide untouched shaft triangle through the nonlinear terrain.
x=shape[-3,:,0].mean()
rings=[]
# Pin previous shared socket section, preserve the exact opposite cap.
old_shape=shape.copy()
old_shape[:3]+=np.array([.050,0,-.014])
for z in np.linspace(old_shape[2,:,0].mean(),x,21)[1:]:
 q=shape[2].copy();q[:,0]+=z-q[:,0].mean();q[:,1]+=z_lift(z)
 rings.append(q)
old_shape[-2,:,1]+=z_lift(old_shape[-2,:,0].mean())
q0=np.r_[old_shape[:3],rings,old_shape[-2:]]
O['SW0/front_rail_1']=polys(q0,True)
cuts={}
for hand in (-1,1):
 key=f'SW0/front_X_distinct_return_1_{hand}'; base=world(pick[key.split('/')[1]],'SW0')
 moved=base[:-1].copy()
 x0=moved[:,:,0].mean(1)
 # A shared rigid registration shift avoids folding the section frames. Ease
 # along the positive arm only; the actual near loop cross-section is unmodified.
 shifted=x0+.064*S((corner[0]+.18-x0)/.13)
 moved[:,:,0]+=(shifted-x0)[:,None]
 moved[:,:,1]+=np.array([z_lift(v) for v in x0])[:,None]
 O[key]=poly_closed(moved)
 cuts[key]={'native_signed_near_ring_shift_mm':float(np.max(shifted-x0))*1000,'examined_rotationally_unchanged_rings':len(moved)}
lower={k:v for k,v in O.items() if ('return_1_' in k or 'front_rail_1' in k)}
results={k:terrain(t) for k,t in lower.items()}
inter={}
for k,t in lower.items():
 for k2,v in O.items():
  if k2<=k and k2 in lower:continue
  if k2==k:continue
  got=bound(t,v,[k]*len(t),[k2]*len(v))
  if got:inter.update(got)
sp=n['V']['span'];norms=n['V']['norms']
def self_cross(t):
 lo,hi=t.min(1),t.max(1);ns=norms(t)
 hit=[]
 for i in range(len(t)):
  candidates=np.flatnonzero((np.arange(len(t))>i)&np.all(lo[i]<=hi,axis=1)&np.all(hi[i]>=lo,axis=1))
  for j in candidates:
   if np.min(np.linalg.norm(t[i][:,None]-t[j][None,:],axis=-1))<1e-8:continue
   v=sp(t[i],t[j],ns[i],ns[j])
   if v>4e-7:hit.append([float(v)*1000,i,int(j)])
 return {'pairs':len(hit),'max_segment_mm_witness':max(hit,default=[])}
selfs={k:self_cross(t) for k,t in lower.items()}
# Explicit joint contact exemptions: spouse rope, supporting rails/posts, shared post only; 
# continued cross-arm contact always denied. No upper/course or cap contacts authorized.
designated={};unexpected={}
for k,c in inter.items():
 a,b=k.split(' / ')
 names=a+' '+b
 if a.split('/')[0]!=b.split('/')[0] and not b.startswith('shared_corner') and not a.startswith('shared_corner'):
  unexpected[k]=c;continue
 if 'shared_corner_cap' in names or 'icing' in names or 'rail_2' in names or 'return_2_' in names:
  unexpected[k]=c;continue
 if 'shared_corner' in names or ('rail_1' in names and ('post' in names or 'return_1_' in names)) or ('post' in names and 'return_1_' in names) or ('return_1_' in a and 'return_1_' in b):
  designated[k]=c
 else:unexpected[k]=c
def outline(t):
 normal=np.array([7.,11.,11.]);normal/=np.linalg.norm(normal)
 viewx=np.cross([0.,1.,0.],normal);viewx/=np.linalg.norm(viewx)
 viewy=np.cross(normal,viewx);px=t.reshape(-1,3)@np.array([viewx,viewy]).T*(720/13)
 return [px.min(0).tolist(),px.max(0).tolist()]
manifest=dict(status='source-only South lower repair; inspect all strict gates, no runtime',contact_classification_scope='lower vs all source group pairs; self strict positive only; intended body and lashing seats distinguished',
 terrain_clipped=results,self_crossing=selfs,non_designated_contacts=unexpected,designated_intersects=designated,
 front_mid_circumference_not_changed=True,closed_return_recipe=cuts,
 orientation_only_geometric_stock_outline={k:outline(t) for k,t in lower.items()},
 total_triangles=sum(len(t) for t in O.values()),exact_prior_total_triangles=25344,
 condition='HOLD on any ground deficit, unintended contact, or self-crossing')
(R/'result.json').write_text(json.dumps(manifest,indent=2)+'\n')
rows=['# South lower math-only candidate, not imported.']
i=1
for k,t in lower.items():
 rows.append('o '+k.replace('/','_'))
 for f in t:
  for v in f: rows.append('v '+' '.join(f'{p:.9f}' for p in v))
  rows.append(f'f {i} {i+1} {i+2}');i+=3
(R/'SouthLowerSourceReview.obj').write_text('\n'.join(rows)+'\n')
