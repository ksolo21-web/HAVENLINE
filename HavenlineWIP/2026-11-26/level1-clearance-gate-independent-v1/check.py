"""Independent source-space repair clearance, old-positive control and continuous containment."""
import contextlib,io,json,math,runpy,sys,hashlib
from pathlib import Path
import numpy as np
oldscript,old,cand=map(Path,sys.argv[1:4]); seal=sys.argv[4]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(oldscript.parent/'SHA256SUMS')=='65aa400c4e8639953f29b3607ed51a40ed08312cefa50f3812165a98b5a4f3f0'
assert sha(cand/'SHA256SUMS')==seal
for d in (oldscript.parent,cand):
 for l in (d/'SHA256SUMS').read_text().splitlines():
  h,n=l.split(maxsplit=1);assert sha(d/n)==h,n
argv=sys.argv[:];sys.argv=[str(oldscript),str(old)]
with contextlib.redirect_stdout(io.StringIO()): w=runpy.run_path(str(oldscript))
sys.argv=argv
assert all(len(q['intersecting_samples'])==35 and q['intersecting_samples']['90.00000000']['pairs']>=142 for q in w['results'].values())
# post exact explicit prior shape, already scaled and same frozen R17 transform.
post,pm=w['post'],np.asarray(w['pm'])
assert (cand/'donor/GateLeaf.mtl').read_bytes()==(old/'donor/GateLeaf.mtl').read_bytes()
parse,normal,span=w['obj'],w['norms'],w['span']
def extrema(points,ylo,yhi):
 o=[]
 for P in points:
  yy=P[:,1]
  if yy.max()<ylo or yy.min()>yhi:continue
  o.extend(P[(ylo<=yy)&(yy<=yhi)])
  for y in (ylo,yhi):
   for i,j in [(0,1),(1,2),(2,0)]:
    if min(yy[i],yy[j])<y<max(yy[i],yy[j]):
     o.append(P[i]+(P[j]-P[i])*((y-yy[i])/(yy[j]-yy[i])))
 return np.asarray(o)
def clip_poly(p,axis,bound,sense):
 if len(p)==0: return p
 out=[]
 for a,b in zip(p,np.roll(p,-1,axis=0)):
  A=sense*(a[axis]-bound);B=sense*(b[axis]-bound)
  if A>=0: out.append(a)
  if ((A>=0)!=(B>=0)):out.append(a+(b-a)*(A/(A-B)))
 return np.asarray(out)
rs={}
for key,v in w['results'].items():
 side=-1 if key.endswith('left') else 1
 f='GateLeaf.obj' if side==-1 else 'GateLeaf_Right.obj'
 leaf,lm=parse(cand/'donor'/f)
 art=leaf*np.array([-side,1,1])
 assert art[:,:,0].min()>0 and len(leaf)>1360
 assert set(lm)=={'board','board_warm','board_soft','beam','brace_back','snow','metal','rope','rope_dark'}
 y=v['post_minus_hinge_height_m']; P=post+np.array([side*.19616,y,0]);N=normal(P);b0,b1=P.min(1),P.max(1)
 margins={}; continuous={}
 for mat in np.unique(pm):
  Q=P[pm==mat]
  near=min(side*Q[:,:,0].ravel())
  C=extrema(art,Q[:,:,1].min(),Q[:,:,1].max())
  # Exact conservative outboard bound at all stock open yaws 0<=theta<=90.
  # Since inward u>0, -u*cos(theta)-z*sin(theta) <= max(0,-z).
  margin=float(near-max(0.,-C[:,2].min())) if len(C) else None
  margins[mat]=margin
  # If a point lies outboard, u > 0 gives |z_world| >= u throughout
  # the allowed quarter-turn (differentiate the rigid planar coordinates).
  # Thus an overlap needs u within the post's cross-axis bound. Independently
  # clip full triangles to that and exact padded post-material height range.
  reach=float(np.abs(Q[:,:,2]).max()+.002)
  lo=float(Q[:,:,1].min()-.002);hi=float(Q[:,:,1].max()+.002)
  idx=np.flatnonzero((art[:,:,0].min(1)<=reach)&(art[:,:,1].min(1)<=hi)&(art[:,:,1].max(1)>=lo))
  dist=[]
  for j in idx:
   cut=clip_poly(clip_poly(clip_poly(art[j],0,reach,-1),1,lo,1),1,hi,-1)
   if len(cut):dist.append(float(near-max(0.,-cut[:,2].min())))
  continuous[mat]=min(dist) if dist else None
 prevs=[float(i) for i in v['intersecting_samples']]
 sample=sorted({round(i,8) for i in [0.,15.,22.5,45.,67.5,90.]+prevs+[min(math.pi/2,i*2.3/60)*180/math.pi for i in range(1,42)]})
 crossings={}
 for angle in sample:
  theta=-side*math.radians(angle);c,s=math.cos(theta),math.sin(theta)
  T=leaf@np.array([[c,0,-s],[0,1,0],[s,0,c]])
  n=normal(T);lo,hi=T.min(1),T.max(1)
  qs=np.argwhere(np.all((b1[None,:,:]>=lo[:,None,:]-2e-7)&(hi[:,None,:]>=b0[None,:,:]-2e-7),axis=-1))
  found=[]
  for i,j in qs:
   length=span(T[i],P[j],n[i],N[j])
   if length>4e-7:found.append((length,int(i),int(j),lm[i],str(pm[j])))
  if found:
   crossings[str(angle)]={'count':len(found),'largest':max(found)}
 baseleaf,_=parse(old/'donor'/f); basecanon=baseleaf*np.array([-side,1,1])
 rs[key]={'sample_count':len(sample),'actual_strict_hits':crossings,'broad_axis_only_margin_m_by_post_material':margins, 'continuous_combined_cross_axis_and_height_margin_m':continuous,
   'triangle_count':len(leaf),'new_inward_x_extent_m':[float(art[:,:,0].min()),float(art[:,:,0].max())],
   'unchanged_closed_center_gap_m':float(2*(1.20-art[:,:,0].max())),
   'old_closed_center_gap_equals_new':bool(art[:,:,0].max()==basecanon[:,:,0].max()),
   'actual_extents_m':[art.min((0,1)).tolist(),art.max((0,1)).tolist()]}
print(json.dumps(dict(candidate_manifest=seal,original_control_replayed=True,original_source_positive_35_each=True,findings=rs,scope='exact pinned source meshes and source-derived static hinge and post seats; no engine or visual claims'),indent=2))
