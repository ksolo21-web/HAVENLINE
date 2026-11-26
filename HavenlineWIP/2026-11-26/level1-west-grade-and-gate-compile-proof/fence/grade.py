from pathlib import Path
import json, numpy as np, hashlib, math
from scipy.spatial import ConvexHull
R=Path(__file__).resolve().parent;P=R.parent
pkg=P/'hvn-l1-fence-33036-west1-terminal-grade-v1'
assert hashlib.sha256((pkg/'SHA256SUMS').read_bytes()).hexdigest()=='a34dc3d6d6679e6957471a59e1fb7409619f59edd06d823c18cc5680448eda53'
s=(pkg/'grade.py').read_text(); N={'__file__':str(pkg/'grade.py')}
exec(s[:s.index('critical={}')],N)
S,K,M,mat,terrain,sub=[N[k] for k in ('S','K','M','mat','terrain','sub')]
C=N['N'];V=N['V'];T=C['T'];d=C['d'];bound=C['C']['culled_intersections']
zstart,zfinish,ymax=6.9,7.132957507339023,.025
def ramp(z):
 t=np.clip((z-zstart)/(zfinish-zstart),0,1)
 return ymax*t*t*(3-2*t)
def warp(T,n=None):
 # The measured smooth profile is materialized as indexed cuts; no assumed
 # clearances between different terrain or authored 3D mesh grid cells.
 cuts=[zstart]+[x for x in np.linspace(zstart,zfinish,25)[1:-1]]+[zfinish]
 Q=[]
 for f in T:
  if f[:,2].max()<=zstart+1e-12:Q.append(f);continue
  z=np.unique([f[:,2].min(),*[k for k in cuts if f[:,2].min()<k<f[:,2].max()],f[:,2].max()])
  if len(z)==1:
   g=f.copy();g[:,1]+=ramp(g[:,2]);Q.append(g);continue
  for a,b in zip(z,z[1:]):
   g=C['within'](f,2,a,b)
   if len(g)<3:continue
   g[:,1]+=ramp(g[:,2])
   for tri in C['fan'](g):
    x=np.array(tri)
    if np.linalg.norm(np.cross(x[1]-x[0],x[2]-x[0]))>1e-13:Q.append(x)
 return np.asarray(Q)
A={'rail':S[K],'warm':S[M]}; B={k:warp(t) for k,t in A.items()}
new_post=d['new_assets']['West1/timber'];H=ConvexHull(np.unique(new_post.reshape(-1,3),axis=0)).equations
ret={}
local={k:v for k,v in T.items() if k.startswith('West2/') and 'post1' not in k}
for label,t in B.items():
 zmax=float(t[:,:,2].max())
 vv=t[(abs(t[:,:,2]-zmax)<1e-9).all(1)].reshape(-1,3)
 far=t[np.any(t[:,:,2]>zmax-.010,axis=1)].reshape(-1,3)
 q=terrain(t);j=bound(t,new_post,[label]*len(t),['rooted_terminal']*len(new_post))
 cross={}
 for k,v in local.items():
  hit=bound(t,v,[label]*len(t),[k]*len(v))
  if hit:cross.update(hit)
 ret[label]={'exact_indexed_clearance':q,'all_final_owner_vs_protected_crossings_should_be_zero':cross,'rooted_actual_contact':j,
 'original_faces':len(A[label]),'changed_total_faces':len(t),'actual_full_planar_cap_vertex_count':len(vv),
 'planar_cap_convex_safe_mm':float(-(vv@H[:,:3].T+H[:,3]).max()*1000) if len(vv) else None,
 'near_terminating_10mm_convex_binary_guard_mm':float(-(far@H[:,:3].T+H[:,3]).max()*1000)}
from collections import Counter
for k,F in B.items():
 c=Counter(); z=Counter()
 for q in np.round(F,8):
  f=list(map(tuple,q))
  for a,b in zip(f,f[1:]+f[:1]):
   g=tuple(sorted((a,b)));c[g]+=1;z[g]+=1 if a==g[0] else -1
 ret[k]['directed_edge_weld_pass']=all(v==2 and z[key]==0 for key,v in c.items())
 ret[k]['minimum_nonzero_tri_area_m2']=float(np.linalg.norm(np.cross(F[:,1]-F[:,0],F[:,2]-F[:,0]),axis=1).min()/2)
 # Exact changed-band self clipping, excluding shared indexed vertex adjacency.
 F=np.asarray(F);lo,hi=F.min(1),F.max(1);nn=V['norms'](F);seen=[]
 for i in range(len(F)):
  if F[i,:,2].max()<=zstart:continue
  J=np.flatnonzero(np.all((lo[i]<=hi)&(hi[i]>=lo),axis=1)&(np.arange(len(F))>i))
  for j in J:
   if (np.linalg.norm(F[i,:,None]-F[j,None,:],axis=-1)<1e-8).any():continue
   x=V['span'](F[i],F[j],nn[i],nn[j])
   if x>4e-7:seen.append([i,int(j),x*1000])
 ret[k]['strict_self_crossing_count_changed_axial']=len(seen)
 ret[k]['max_sample_strict_self_pair']=max(seen,key=lambda n:n[2],default=None)
cream=S[(mat=='ivory_hemp_cream')&(N['base'][:,:,1].mean(1)<.5)]
seats={}
for kind,T0 in [('old',A),('new',B)]:
 seats[kind]={k:bound(v,cream,[k]*len(v),['cream_other_source']*len(cream)) for k,v in T0.items()}
 seats[kind+'_near_only']={k:bound(v0,cm,[k]*len(v0),['cream_other_source']*len(cm)) for k,v in T0.items() for v0 in [v[v[:,:,2].max(1)>zstart]] for cm in [cream[cream[:,:,2].max(1)>zstart]]}
out={'state':'scoped source candidate only; accepted physical anchors untouched','tested_c1_shape_max_slope':ymax*1.5/(zfinish-zstart),'world_scope_grade_z_minmax':[zstart,zfinish],
 'peak_pairwise_equal_lift_mm':ymax*1000,'source_dimensions_no_normal_depth_change':True,'components':ret,'untouched_same_arm_cream_crossing_classes_old_new':seats,'stock_vert_pixel_drift_design_max':.025*.7643248*(720/13)}
(R/'result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
rr=['# West1 source test hold; never installed'];i=1
for k,t in B.items():
 rr.append('o '+k)
 for q in t:
  for g in q:rr.append('v '+' '.join(f'{x:.9f}' for x in g))
  rr.append(f'f {i} {i+1} {i+2}');i+=3
(R/'West1Grade_SourceOnly.obj').write_text('\n'.join(rr)+'\n')
print(json.dumps(out))
