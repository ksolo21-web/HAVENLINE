from boundary import *
from collections import Counter
from scipy.optimize import linprog
import os
assert report['boundary_clear'] and all(a[3]==0 for a in report['tool_winding_exact_mesh'].values())
patch=np.array(sorted(sets));outer=np.setdiff1d(np.arange(len(F)),patch)
edges_all=Counter(tuple(sorted((int(a),int(b)))) for tri in F[patch] for a,b in zip(tri,np.roll(tri,-1)))
boundary=np.unique(np.array([edge for edge,val in edges_all.items() if val==1]).ravel())
fixed=set(np.r_[locked,boundary,np.intersect1d(np.unique(F[outer]),np.unique(F[patch]))])
assert edges_all and max(edges_all.values())<=2
# Conforming barycentric re-tessellation: split shared internal edges once, add one
# interior centroid to each core parent; never split a perimeter edge.
pt=list(V); provenance={}; shared={}; subdiv=[]
def append_point(indices,w):
 k=len(pt); pt.append(w@V[indices]); provenance[k]=(np.array(indices),np.array(w)); return k
for faceid in patch:
 tri=F[faceid]
 polys=[]
 for a,b in zip(tri,np.roll(tri,-1)):
  a,b=int(a),int(b); polys.append(a)
  key=tuple(sorted((a,b)))
  if edges_all[key]==2 and a not in locked and b not in locked:
   if key not in shared: shared[key]=append_point(list(key),np.array([.5,.5]))
   polys.append(shared[key])
 center=append_point(tri,np.full(3,1/3))
 subdiv.extend((int(faceid),[a,b,center]) for a,b in zip(polys,np.roll(polys,-1)))
parents=np.array([i for i,_ in subdiv]); tris=np.array([t for _,t in subdiv]); pt=np.array(pt)
ids0=np.unique(tris)
mov=np.array([i for i in ids0 if i not in fixed]); col={i:k for k,i in enumerate(mov)}
assert (plane[np.unique(F[patch])]>0).all() and not np.intersect1d(mov,boundary).size
ref=face[0]; x=face[1]-ref;x/=np.linalg.norm(x);y=np.cross(n,x)
proj=lambda g:(g-ref)@np.array([x,y]).T
def clip(x,Q):
 poly=list(np.eye(3))
 for a,b in zip(Q,np.roll(Q,-1,axis=0)):
  e=b-a; h=e[0]*(x[:,1]-a[1])-e[1]*(x[:,0]-a[0])
  new=[]
  for k,j in zip(poly,poly[1:]+poly[:1]):
   kk,jj=k@h,j@h
   if kk>=-1e-14:new.append(k)
   if (kk< -1e-14)!=(jj< -1e-14):new.append(k+(j-k)*kk/(kk-jj))
  poly=new
 return poly
def area(a):
 return abs(np.linalg.det(np.array([a[1]-a[0],a[2]-a[0]])))/2 if len(a)==3 else .5*abs(np.dot(a[:,0],np.roll(a[:,1],-1))-np.dot(a[:,1],np.roll(a[:,0],-1)))
X=proj(pt[tris]); minx=X.min(1); maxx=X.max(1)
tool_edges=np.cross(tool[:,1]-tool[:,0],tool[:,2]-tool[:,0]); center=tool.mean(1)
outwards=np.array([winding(c-ne/np.linalg.norm(ne)*.00003) for c,ne in zip(center,tool_edges)])
facets=np.flatnonzero((np.abs(outwards)>.5)&(tool_edges@n>1e-12))
# Lift the one editable sheet only above the actual outward-facing tool
# surfaces visible along the shaft normal. Use all finite overlapping faces;
# never carry any one infinite plane to the neighboring facets.
A=[]; B=[]; checks=[]; hard=[]; mincap=(0,None,None)
D=(pt-ref)@n
ptslab=X
for j in facets:
 Q=proj(tool[j]); z=(tool[j]-ref)@n
 if np.linalg.det(Q[1:]-Q[0])<0:Q=Q[[0,2,1]];z=z[[0,2,1]]
 aug=np.c_[Q,np.ones(3)]
 co=np.linalg.solve(aug,z)
 active=np.flatnonzero((maxx>=Q.min(0)).all(1)&(minx<=Q.max(0)).all(1))
 for i in active:
  w=np.array(clip(X[i],Q))
  if len(w)<3 or area(w@X[i])<1e-14:continue
  tri=tris[i]
  surf=np.c_[w@X[i],np.ones(len(w))]@co
  # Do not force a distinct backside shell through an occluding shaft;
  # this chart is one sheet and absence of contact is tested in 3D.
  for k,val in zip(w,surf):
   rhs=float(val+.000075-k@D[tri])
   row=np.zeros(len(mov)+1)
   for vi,weight in zip(tri,k):
    if vi in col: row[col[vi]]=weight
   mm=row.sum()
   if rhs>1e-9 and mm<1e-10:hard.append((int(parents[i]),int(j),rhs*1000))
   if rhs>0 and mm>=1e-10:mincap=max(mincap,(rhs/mm,int(parents[i]),int(j)))
   if mm>=1e-10 or rhs>1e-9:
    A.append(-row);B.append(-rhs)
   checks.append((int(i),int(j),k.tolist(),float(val)))
report.update({'volume_rule':'exact finite front surface envelope of original tool; 0.075 mm diagnostic buffer','replacement_child_faces':len(tris),
'new_mesh_rows':len(pt)-len(V),'perimeter_vertices':len(boundary),'frozen_original_outside_faces':len(outer),'exact_touched_outward_facets':sorted(set(z[1] for z in checks)),
'active_inequalities':len(A),'hard_fixed_cut_constraints':sorted(set(hard)),'cap_bound_m_parent_facet':mincap})
# Exact 3D baseline omitted after any hard fixed point, since no candidate.
if not hard and mincap[0] <= .006:
 for a,b in np.unique(np.sort(tris[:,[0,1,1,2,2,0]].reshape(-1,2),axis=1),axis=0):
  row=np.zeros(len(mov)+1); row[-1]=-1
  if a in col:row[col[a]]=1
  if b in col:row[col[b]]=-1
  A.append(row); row=row*-1;row[-1]=-1;A.append(row);B.extend([0,0])
 result=linprog(np.r_[np.full(len(mov),1e-3),1.],A_ub=A,b_ub=B,bounds=[(0,.006)]*len(mov)+[(0,None)],method='highs')
 report['candidate_feasible']=bool(result.success)
 if result.success:
  alt=pt.copy(); alt[mov]+=result.x[:-1,None]*n
  assert np.array_equal(alt[F[outer]],V[F[outer]])
  assert np.array_equal(alt[list(fixed)],pt[list(fixed)])
  parent_baseline={(int(patch[i]),j) for i,j in toolpairs(V[F[patch]])}
  trial_child=toolpairs(alt[tris]); trial_parent={(int(parents[i]),j) for i,j in trial_child}
  report['baseline_parent_shaft_pairs']=sorted(parent_baseline)
  report['trial_parent_shaft_pairs']=sorted(trial_parent)
  report['trial_new_parent_shaft_pairs']=sorted(trial_parent-parent_baseline)
  report['new_triangle_row_parent_mapping']=parents.tolist()
  nn=lambda a:np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0])
  n0,n1=nn(pt[tris]),nn(alt[tris])
  report['normal_inversions']=int(((n0*n1).sum(1)<0).sum())
  report['maximum_shift_mm']=float(1000*result.x[:-1].max())
else:report['candidate_feasible']=False
pface=F[mincap[1]]
report["binding_source_vertices"]=pface.tolist()
report["binding_source_scope"]=[{"id":int(i),"perimeter":bool(i in boundary),"original_glove_lock":bool(i in lock),"frozen_due_to_unchanged_neighbor":bool(i in fixed)} for i in pface]
report["closest_patch_source_vertex_to_cuff_cut_mm"]=float(1000*plane[np.unique(F[patch])].min())
report["boundary_degrees"]=sorted(set(Counter(np.ravel([e for e,v in edges_all.items() if v==1])).values()))
assert report["boundary_degrees"]==[2]
report["status"]="HOLD_STOP_LOCAL_ENVELOPE_STRATEGY_NO_MODEL_EXPORTED"
print(json.dumps(report,indent=2,sort_keys=True))
