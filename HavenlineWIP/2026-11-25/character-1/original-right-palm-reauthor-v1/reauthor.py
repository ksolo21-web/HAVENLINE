import os
from boundary import *
from collections import Counter
from scipy.spatial import ConvexHull
patch=np.array(sorted(sets)); fs=F[patch]; vert=np.unique(fs)
eall=Counter(tuple(sorted((int(a),int(b)))) for t in fs for a,b in zip(t,np.roll(t,-1)))
bd={k for k,v in eall.items() if v==1}
adj=defaultdict(list)
for a,b in bd:adj[a].append(b);adj[b].append(a)
assert all(len(v)==2 for v in adj.values())
b=np.array(sorted(adj)); loops=[]; unused=set(b)
while unused:
 start=min(unused); loop=[start]; pr=-1
 while True:
  cur=loop[-1]; z=min(i for i in adj[cur] if i!=pr)
  if z==start:break
  assert z not in loop
  loop.append(z);pr=cur
 loops.append(np.array(loop)); unused.difference_update(loop)
origin=face[0]; xx=face[1]-origin;xx/=np.linalg.norm(xx); yy=np.cross(n,xx)
cross2=lambda a,b:a[...,0]*b[...,1]-a[...,1]*b[...,0]
def crossings(x):
 y=np.roll(x,-1,axis=0)-x; out=[]
 for i in range(len(x)):
  for j in range(i+1,len(x)):
   h=cross2(y[i],y[j])
   if abs(h)<1e-15:continue
   d=x[j]-x[i]; a=cross2(d,y[j])/h; b0=cross2(d,y[i])/h
   if min(a,b0,1-a,1-b0)>1e-8:out.append((i,j))
 return out
xy=lambda p:(p-origin)@np.array([xx,yy]).T
Z=(V-origin)@n
def profile(Q):
 QA=xy(tool)
 E=np.r_[Q,1.]
 hits=[]
 for j,t in enumerate(QA):
  M=np.c_[t,np.ones(3)]
  if abs(np.linalg.det(M))<1e-14:continue
  w=np.linalg.solve(M.T,E)
  if w.min()>=-1e-10:
   hits.append((float(w@((tool[j]-origin)@n)),j))
 return hits
# Ear clipping builds two independent joined pressure surfaces from the authored
# perimeter. Original interior rows are discarded, not shifted.
def ear(pos):
 poly=list(range(len(pos))); out=[]
 if cross2(pos,np.roll(pos,-1,axis=0)).sum()<0:poly=poly[::-1]
 def in_tri(P,t):
  f=np.roll(t,-1,axis=0)-t
  return (cross2(f,P-t)>=-1e-13).all()
 while len(poly)>3:
  ears=[]
  for j,k in enumerate(poly):
   tri=[poly[j-1],k,poly[(j+1)%len(poly)]]
   t=pos[tri]; ar=cross2(t[1]-t[0],t[2]-t[0])
   if ar<=1e-13 or any(in_tri(pos[o],t) for o in poly if o not in tri):continue
   # least long diagonal first, tie by source walk order
   ears.append((float(np.linalg.norm(t[2]-t[0])),j,tri))
  assert ears
  _,j,t=min(ears); out.append(t); poly.pop(j)
 out.append(poly)
 return np.array(out)
from scipy.optimize import linprog
from scipy.sparse.linalg import spsolve
gg=V.copy(); GG=[]; uvbuf=list(uv); wbuf=list(W); points=list(V)
ts=[]; cutowner=[]; face_shift=[]
boundary_exact=np.unique(np.concatenate(loops))
inside_orig=np.setdiff1d(vert,boundary_exact)
assert len(np.intersect1d(inside_orig,locked))==0
assert set(sum((list(key) for key in bd),[]))==set(boundary_exact)
hull=ConvexHull(V[local]); source_hull_ids=local[hull.vertices]
all_extrema=np.intersect1d(source_hull_ids,inside_orig)
in_volume=np.array([i for i in all_extrema if abs(winding(V[i]))>.5])
views={str(axes):np.intersect1d(all_extrema,local[ConvexHull(V[local][:,axes]).vertices]).tolist() for axes in [(0,1),(0,2),(1,2)]}
assert not np.intersect1d(in_volume,np.concatenate(list(views.values()))).size
assert not np.intersect1d(in_volume,locked).size
protected_extrema=np.setdiff1d(all_extrema,in_volume)
directed={tuple(sorted((int(a),int(b)))):(int(a),int(b)) for t in fs for a,b in zip(t,np.roll(t,-1)) if tuple(sorted((int(a),int(b)))) in bd}
embed_failure=[]
for lp,loop in enumerate(loops):
 pos=xy(V[loop]); tri=loop[ear(pos)]
 if (int(loop[0]),int(loop[1]))==directed[tuple(sorted((int(loop[0]),int(loop[1]))))]:
  want=np.sign(cross2(pos,np.roll(pos,-1,axis=0)).sum())
 else:want=-np.sign(cross2(pos,np.roll(pos,-1,axis=0)).sum())
 if want<0:tri=tri[:,::-1]
 # Keep existing outer silhouette contributors as exact vertices with their
 # original source UV and weights. Embed them into new internal topology.
 chart_reach=set(loop)
 prv=set()
 while chart_reach!=prv:
  prv=set(chart_reach)
  sel=fs[np.isin(fs,list(chart_reach)).any(1)]
  chart_reach.update(sel.ravel())
 for pin in np.intersect1d(protected_extrema,list(chart_reach)):
  s0=xy(V[pin]); ge=xy(V[tri])
  q2=ge[:,1]-ge[:,0];q3=ge[:,2]-ge[:,0]; ss=cross2(q2,q3)
  u0=cross2(s0-ge[:,0],q3)/ss; v0=cross2(q2,s0-ge[:,0])/ss
  ok=np.flatnonzero((u0>1e-9)&(v0>1e-9)&(1-u0-v0>1e-9))
  if len(ok)!=1:
   embed_failure.append((int(pin),int(lp),len(ok)))
   continue
  ix=ok[0]; tri=np.vstack((np.delete(tri,ix,axis=0),[(a,b,pin) for a,b in zip(tri[ix],np.roll(tri[ix],-1))]))
 for _ in range(2):
  # actual re-tessellation with newly placed neutral points; no boundary splits
  cf=Counter(tuple(sorted((int(a),int(b)))) for t in tri for a,b in zip(t,np.roll(t,-1)))
  inserted={}; repl=[]
  for t in tri:
   rim=[]
   for a,b in zip(t,np.roll(t,-1)):
    rim.append(a); key=tuple(sorted((int(a),int(b))))
    if cf[key]==2:
     if key not in inserted:
      inserted[key]=len(points);points.append((points[a]+points[b])*.5)
     rim.append(inserted[key])
   center=len(points); points.append(np.mean(np.array([points[p] for p in t]),axis=0))
   repl.extend([a,b,center] for a,b in zip(rim,np.roll(rim,-1)))
  tri=np.array(repl)
 ts.extend(tri.tolist()); cutowner.extend([lp]*len(tri))
ts=np.array(ts); pts=np.array(points); G=xy(pts)
newids=np.arange(len(V),len(pts)); coord=(pts-origin)@n
# Solve for fresh surface depth. Positive facing portions of the exact volume
# impose a hard 0.075mm clearance on each clipped triangle corner, not only
# control nodes. Boundary remains exact and no inherited point path is kept.
def clip(x,Q):
 poly=list(np.eye(3))
 for a,b in zip(Q,np.roll(Q,-1,axis=0)):
  h=cross2(b-a,x-a); new=[]
  for k,j in zip(poly,poly[1:]+poly[:1]):
   kk,jj=k@h,j@h
   if kk>=-1e-14:new.append(k)
   if (kk< -1e-14)!=(jj< -1e-14):new.append(k+(j-k)*kk/(kk-jj))
  poly=new
 return np.array(poly)
TT=xy(tool); offsets=(tool-origin)@n
P2=G[ts]; min2=P2.min(1); max2=P2.max(1)
A=[]; B=[]; hard=[]; used=set(); cert=[]
for fi,Q0 in enumerate(TT):
 Q=Q0.copy(); off=offsets[fi].copy()
 ar=cross2(Q[1]-Q[0],Q[2]-Q[0])
 if ar <=1e-13:continue
 coeff=np.linalg.solve(np.c_[Q,np.ones(3)],off)
 for j in np.flatnonzero((min2<=Q.max(0)).all(1)&(max2>=Q.min(0)).all(1)):
  cs=clip(P2[j],Q)
  if len(cs)<3:continue
  rr=cs@P2[j]
  if abs(cross2(rr,np.roll(rr,-1,axis=0)).sum())<1e-14:continue
  hh=np.c_[rr,np.ones(len(rr))]@coeff; used.add(fi)
  for w,z in zip(cs,hh):
   row=np.zeros(len(newids))
   for v0,alpha in zip(ts[j],w):
    if v0>=len(V):row[v0-len(V)]+=alpha
   base=z+.000075-w@coord[ts[j]]
   if row.sum()<1e-10:
    if base>1e-8:hard.append((int(fi),int(j),float(base*1000)))
    continue
   A.append(-row);B.append(-(z+.000075-sum(a*coord[v0] for v0,a in zip(ts[j],w) if v0<len(V))))
   cert.append((int(j),w,float(z)))
retained=np.setdiff1d(np.arange(len(F)),patch)
assert not np.isin(F[retained],inside_orig).any()
assert not np.isin(ts,np.setdiff1d(inside_orig,protected_extrema)).any()
ed=Counter(tuple(sorted((int(a),int(b)))) for t in ts for a,b in zip(t,np.roll(t,-1)))
di={tuple(sorted((int(a),int(b)))):(int(a),int(b)) for t in ts for a,b in zip(t,np.roll(t,-1)) if tuple(sorted((int(a),int(b)))) in bd}
assert {k for k,v in ed.items() if v==1}==bd and di==directed
assert set(ed.values())=={1,2}
uvn=np.zeros((len(newids),2)); weights=np.zeros((len(newids),W.shape[1]))
ng=defaultdict(set)
for a,b in ed:ng[a].add(b);ng[b].add(a)
mr=[]; mc=[]; mm=[]
for i in newids:
 k=i-len(V); d=len(ng[i]);mr.append(k);mc.append(k);mm.append(d)
 for j in sorted(ng[i]):
  if j>=len(V):mr.append(k);mc.append(j-len(V));mm.append(-1)
  else:uvn[k]+=uv[j]; weights[k]+=W[j]
L=coo_matrix((mm,(mr,mc)),shape=(len(newids),len(newids))).tocsc()
ua=spsolve(L,uvn); wa=spsolve(L,weights)
U=np.vstack((uv,ua)); expandedW=np.vstack((W,wa)); assert np.array_equal(U[:len(uv)],uv) and np.array_equal(expandedW[:len(W)],W)
# Exact hull halfspaces enforce no growth of retained outer right glove support
# in any direction. Confirm all original hull extrema remain outside the cut.
hull=ConvexHull(V[local]); source_hull_ids=local[hull.vertices]
missing_extreme=np.setdiff1d(protected_extrema,np.unique(ts))
eq=hull.equations
ncoef=eq[:,:3]@n
C=origin+G[newids,0,None]*xx+G[newids,1,None]*yy
rhs=-(C@eq[:,:3].T+eq[:,3])+1e-10
lower=np.max(rhs[:,ncoef< -1e-12]/ncoef[ncoef< -1e-12],axis=1)
upper=np.min(rhs[:,ncoef>1e-12]/ncoef[ncoef>1e-12],axis=1)
assert not ((rhs[:,abs(ncoef)<=1e-12]<0).any())
assert (lower<=upper).all()
# Resolve a new shaft-facing shape from scratch, with a smooth
# second-difference field over the new network. Heights are absolute, not
# deltas inherited from the old topological area.
N=len(newids)
from scipy.sparse import csr_matrix,vstack,hstack
A= hstack((csr_matrix(A),csr_matrix((len(A),1))),format="csr")
AA=[]
for i in newids:
 k=i-len(V); d=len(ng[i]); row=np.zeros(N+1);row[k]=1
 f0=0
 for j in sorted(ng[i]):
  if j>=len(V):row[j-len(V)]-=1/d
  else:f0+=coord[j]/d
 for sg in (1,-1):
  rr=row*sg;rr[-1]=-1
  AA.append(rr);B.append(sg*f0)
# Minimizing roughness plus a small front-depth pressure bias preserves
# gentle shoulders while allowing the new middle region to cup the axe.
fit=None
if not hard and not len(missing_extreme):
 fit=linprog(np.r_[np.full(N,0.00002),1.],A_ub=vstack([A,csr_matrix(AA)],format="csr"),b_ub=B,bounds=list(zip(lower,upper))+[(0,None)],method='highs')
report={'status':'HOLD','source_hashes':expected,'assigned_shaft_band_id':124,'other_exact_overlapping_facets':sorted(used),
 'source_perimeter_loop_lengths':list(map(len,loops)),'source_perimeter_edge_directions_and_positions_preserved':True,'source_uv_and_weight_rows_preserved':True,'new_uv_and_weight_assignment':'Dirichlet harmonic transfer from exact island perimeter',
 'outer_hull_original_extrema_preserved':np.intersect1d(protected_extrema,np.unique(ts)).tolist(),'outer_hull_original_extrema_cut':missing_extreme.tolist(),'anchor_embed_failures':embed_failure,'new_rows':len(newids),'removed_parent_faces':len(patch),'new_faces':len(ts),'unchanged_source_faces':len(retained),'source_patch_face_indices':patch.tolist(),
 'fixed_corner_tool_conflicts':hard,'solver':fit.message if fit is not None else 'not run, source guard'}
if fit is not None and fit.success:
 new=pts.copy();new[newids]=C+fit.x[:-1,None]*n
 assert np.array_equal(new[F[retained]],V[F[retained]])
 assert np.array_equal(new[boundary_exact],V[boundary_exact])
 clipped_gap=min(float(w@((new[ts[j]]-origin)@n)-z) for j,w,z in cert)
 # exact collision QA with actual shaft and retained surrounding glove/coat
 m=new[ts]; collisions=toolpairs(m)
 mins=m.min(1); maxs=m.max(1)
 mmin=mins.min(0); mmax=maxs.max(0)
 raw=V[F[retained]]
 keep=(raw.min(1)<=mmax).all(1)&(raw.max(1)>=mmin).all(1)
 outrows=retained[keep]; raw=raw[keep]; mn=raw.min(1); mx=raw.max(1)
 selfp=[]; outerp=[]
 for i,tr in enumerate(m):
  for j in np.flatnonzero((mins<=maxs[i]).all(1)&(maxs>=mins[i]).all(1)&(np.arange(len(m))>i)):
   if not np.isin(ts[i],ts[j]).any() and hit(tr,m[j]):selfp.append((int(i),int(j)))
  for j in np.flatnonzero((mn<=maxs[i]).all(1)&(mx>=mins[i]).all(1)):
   if not np.isin(ts[i],F[outrows[j]]).any() and hit(tr,raw[j]):outerp.append((int(i),int(outrows[j])))
 uvdet=cross2(U[ts[:,1]]-U[ts[:,0]],U[ts[:,2]]-U[ts[:,0]])
 origuvdet=cross2(uv[fs[:,1]]-uv[fs[:,0]],uv[fs[:,2]]-uv[fs[:,0]])
 outside_count=sum(abs(winding(p))>.5 for p in m.mean(1))
 report.update({'new_strict_tool_crossings':sorted(collisions),'new_nonincident_patch_crossings':selfp,'new_strict_retained_crossings':outerp,
 'centroids_inside_original_tool_winding':outside_count,'envelope_min_standoff_mm':clipped_gap*1000,
 'UV_sign_counts_negative_zero_positive':[int((uvdet< -1e-12).sum()),int((abs(uvdet)<=1e-12).sum()),int((uvdet>1e-12).sum())],
 'orig_UV_sign_counts_negative_zero_positive':[int((origuvdet< -1e-12).sum()),int((abs(origuvdet)<=1e-12).sum()),int((origuvdet>1e-12).sum())],
 'new_weight_total_range':[float(wa.sum(1).min()),float(wa.sum(1).max())],
 'hull_inequality_high_m':float((new[newids]@eq[:,:3].T+eq[:,3]).max())})
 flipped=np.flatnonzero(uvdet>1e-12)
 report['reversed_uv_child_faces']=[{'row':int(i),'corner_ids':ts[i].tolist(),'disk':int(cutowner[i]),'twice_uv_area':float(uvdet[i])} for i in flipped]
 # finite assigned band bearing: positive directed outward line, using actual new
 # support sheet; sample-only, no force model or completed contact claim.
 def bearing(mesh):
  g=mesh[:,0]; e0=mesh[:,1]-g; e1=mesh[:,2]-g; h=np.cross(n,e1)
  det=(e0*h).sum(1); ww=np.where(abs(det)>1e-15,det,1); hits=[]
  for q1 in np.array([(i,j,12-i-j) for i in range(1,11) for j in range(1,12-i)])/12@face:
   off=q1-g; ray_u=(off*h).sum(1)/ww; v2=np.cross(off,e0); ray_v=v2@n/ww
   dist=(e1*v2).sum(1)/ww
   q=np.flatnonzero((abs(det)>1e-15)&(ray_u>=-1e-9)&(ray_v>=-1e-9)&(ray_u+ray_v<=1+1e-9)&(dist>1e-8)&(dist<.015))
   if len(q):
    j=q[np.argmin(dist[q])]; hits.append((float(dist[j]*1000),bool(np.cross(e0[j],e1[j])@n<0)))
  return {'positive_hits':len(hits),'shaft_facing_hits':sum(a[1] for a in hits),
          'clearance_mm':[min(a[0] for a in hits),max(a[0] for a in hits)] if hits else None}
 report['assigned_facet_124_positive_bearing_rays']={'grid':55,'new':bearing(m),'old':bearing(V[fs])}
 report['local_unmodified_neighbor_tool_strict_pairs']=sorted((int(outrows[i]),int(j)) for i,j in toolpairs(raw))
 report['status']='REJECT_UV_FOLD__SOURCE_SPATIAL_CONTROLS_PASS_ONLY'
 # Rebuild the rejected mesh locally when a critic explicitly requests it.
 if os.environ.get('LOCAL_GEOMETRY_NPZ')=='1':
  np.savez_compressed('reauthored-review-LOCAL.npz',vertices=new[newids],uv=ua,weights=wa,faces=ts,removed=patch)

pins=[]
for i in all_extrema:
 p=V[i]; hits=profile(xy(p)); h=max(hits) if hits else None
 pins.append({"source_id":int(i),"full_tool_winding":winding(p),"front_gap_mm":float(1000*(Z[i]-h[0])) if h else None,"front_facet":h[1] if h else None})
report["fixed_outer_silhouette_pin_controls"]=pins
report["inside_tool_buried_hull_pins_excluded_from_reconstruction"]=[x["source_id"] for x in pins if abs(x["full_tool_winding"])>.5]
view_axes={"owner_original_xy":(0,1),"owner_original_xz":(0,2),"owner_original_yz":(1,2)}
report["cardinal_silhouette_hull_pins"]={k:np.intersect1d(all_extrema,local[ConvexHull(V[local][:,axes]).vertices]).tolist() for k,axes in view_axes.items()}
print(json.dumps(report,indent=2,sort_keys=True))
