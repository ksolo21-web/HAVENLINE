from source import *
from scipy.sparse.csgraph import connected_components
S='R'
r=J['sides'][S]; E=s[S+'_loop_source_vertex_edges']; v=s[S+'_loop_source_edge_t']
cp=P[E[:,0]]*(1-v[:,None])+P[E[:,1]]*v[:,None]; c=cp.mean(0)
u=np.linalg.svd(cp-c)[2][-1];u*=np.sign((P[r['palm_vertex']]-c)@u); plane=(P-c)@u
owned=(-P[:,0]>.52)&(plane>0)
local=np.flatnonzero(owned); edges=bis[owned[bis].all(1)]; ij=np.searchsorted(local,edges)
l=np.linalg.norm(V[edges[:,0]]-V[edges[:,1]],axis=1)
g=coo_matrix((l,(ij[:,0],ij[:,1])),shape=(len(local),len(local))).tocsr()
targets=np.unique(F[[15906,15909]])
starts=[7002,7333]
ds,ps=dijkstra(g,directed=False,indices=np.searchsorted(local,starts),return_predecessors=True)
_,first,inv,cnt=np.unique(np.c_[P[local],V[local]],axis=0,return_index=True,return_inverse=True,return_counts=True)
dup=np.flatnonzero(np.arange(len(local))!=first[inv]); partners=first[inv[dup]]
ga=coo_matrix((np.r_[l,np.full(len(dup),1e-12)],(np.r_[ij[:,0],dup],np.r_[ij[:,1],partners])),shape=g.shape).tocsr()
dsa,psa=dijkstra(ga,directed=False,indices=np.searchsorted(local,starts),return_predecessors=True)
ids=np.flatnonzero(owned[F].all(1)); face=tool[124]; n=np.cross(face[1]-face[0],face[2]-face[0]); n/=np.linalg.norm(n)
n*=np.sign(n@np.array(r['outward']))
q=s['R_barycentric']@face
C,lab=connected_components(g,directed=False); tt=np.searchsorted(local,targets); ss=np.searchsorted(local,starts)
xyz=V[F[ids]]
norm=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]); norm/=np.maximum(1e-30,np.linalg.norm(norm,axis=1)[:,None])
import itertools
d=(V-face[0])@n
ct=lab[tt[0]]; chart=local[lab==ct]
allchart=np.flatnonzero(np.isin(F,chart).all(1))
locked=np.r_[local[cnt[inv]>1],E.ravel()]
toollo,toolhi=tool.min(1),tool.max(1)
def hit(g,h):
 return bool(crosses(g,h) or crosses(h,g))
def toolpairs(mesh):
 out=set()
 for i,gp in enumerate(mesh):
  js=np.flatnonzero((toollo<=gp.max(0)).all(1)&(toolhi>=gp.min(0)).all(1))
  for j in js:
   if hit(gp,tool[j]):out.add((i,int(j)))
 return out
from scipy.optimize import linprog
from collections import Counter
required={15906,15909,16269,16432,16328,16333,16383,16393,16395,16490,16491,16619}
p0=toolpairs(V[F[allchart]])
core=np.array(sorted(required|{int(allchart[i]) for i,j in p0 if j==124}))
patch=core.copy()
for _ in range(2):
 patch=allchart[np.isin(F[allchart],np.unique(F[patch])).any(1)]
outer=np.setdiff1d(np.arange(len(F)),patch)
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
Q=proj(face)
if np.linalg.det(Q[1:]-Q[0])<0: Q=Q[[0,2,1]]
def clip(x):
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
dz=(pt-ref)@n
A=[]; B=[]; witness=[]; clipped=[]
maxrhs=(0,None,None)
exact_cap=[]
for i,tri in enumerate(tris):
 w=np.array(clip(proj(pt[tri])))
 if len(w)<3 or area(w@proj(pt[tri]))<1e-14:continue
 clipped.append((i,w))
 for k in w:
  row=np.zeros(len(mov))
  for vi,weight in zip(tri,k):
   if vi in col: row[col[vi]]=weight
  rhs=.000075-k@dz[tri]
  if rhs>maxrhs[0]:maxrhs=(float(rhs),int(parents[i]),k.tolist())
  if rhs>1e-9 and not np.any(row>1e-10): witness.append((int(parents[i]),float(rhs*1000)))
  if rhs>.006*row.sum()+1e-9: witness.append((int(parents[i]),float((rhs-.006*row.sum())*1000)))
  if row.sum()>1e-10 and rhs>0: exact_cap.append((float(rhs/row.sum()),int(parents[i]),int(i)))
  A.append(-row);B.append(-rhs)
# The objective demands a smooth reconstructed surface across every internal
# grid edge: minimax differences of added depth across complete tessellation,
# with a deterministic minimal effort tie-break. None of this changes UVs.
A=np.array(A); B=np.array(B)
bounds=[(0,.006)]*len(mov)+[(0,None)]
all_edge=np.unique(np.sort(tris[:,[0,1,1,2,2,0]].reshape(-1,2),axis=1),axis=0)
A=np.c_[A,np.zeros(len(A))].tolist(); B=B.tolist()
for a,b in all_edge:
 row=np.zeros(len(mov)+1); row[-1]=-1
 if a in col:row[col[a]]=1
 if b in col:row[col[b]]=-1
 A.append(row); row=row*-1;row[-1]=-1;A.append(row);B.extend([0,0])
obj=np.r_[np.full(len(mov),1e-3),1.]
lp=linprog(obj,A_ub=A,b_ub=B,bounds=bounds,method='highs')
report={'source_hashes':expected,'scope':'owner right glove held-coordinate detached mesh, not PR108','status':'HOLD','core_faces':len(core),'patched_parent_faces':len(patch),'explicit_spillover_faces_all_in_patch':all(i in patch for i in required),'replacement_faces':len(tris),'perimeter_vertices':len(boundary),'unmodified_geometry_frozen_through_baseline_faces':len(outer),'selected_source_shaft_facet':124,'full_facet_refined_overlap_faces':len(clipped),'minimum_claimed_design_standoff_mm_diagnostic':.075,'locked_boundary_violations':sorted(set(witness)),'feasible':bool(lp.success)}
report["worst_required_at_cut"]=maxrhs
report["solver_status"]=lp.message
# A separate lower-bound witness deliberately produces the least-cap violating
# rejected mesh, solely to assess collisions; not an authorized adopted shape.
cap,capparent,capi=max(exact_cap)
report['exact_uniform_displacement_cap_lower_bound_mm']=cap*1000
report['bound_witness_source_face']=capparent
report['bound_witness_child_row']=capi
def norms(g):return np.cross(g[:,1]-g[:,0],g[:,2]-g[:,0])
capped=linprog(obj,A_ub=A,b_ub=B,bounds=[(0,cap+1e-8)]*len(mov)+[(0,None)],method='highs')
if capped.success:
 alt=pt.copy();alt[mov]+=capped.x[:-1,None]*n
 assert np.array_equal(alt[list(sorted(fixed))],pt[list(sorted(fixed))])
 assert np.array_equal(alt[F[outer]],V[F[outer]])
 before=toolpairs(V[F[patch]])
 after=toolpairs(alt[tris])
 old={(int(patch[i]),j) for i,j in before}
 new={(int(parents[i]),j) for i,j in after}
 origN=norms(pt[tris]); newN=norms(alt[tris]); div=np.linalg.norm(origN,axis=1)*np.linalg.norm(newN,axis=1)
 cos=(origN*newN).sum(1)/np.maximum(1e-30,div)
 assert min((w@((alt[tris[i]]-ref)@n)).min() for i,w in clipped)>=.000075-2e-7
 # Earlier crossing checker misses equivalent strict intersections lying
 # exactly on a subdivision edge; include control at unchanged first.
 identity=toolpairs(pt[tris])
 gb=(alt[tris]); gn0=gb.min(1).min(0); gn1=gb.max(1).max(0)
 bound=np.flatnonzero((V[F[outer]].min(1)<=gn1).all(1)&(V[F[outer]].max(1)>=gn0).all(1))
 def both(mesh):
  pair=set()
  m0=mesh.min(1);m1=mesh.max(1); keep=V[F[outer[bound]]]
  for i,gp in enumerate(mesh):
   lo=gp.min(0); hi=gp.max(0)
   # Exclude shared exact indexed neighbour vertices, test non-neighbour sheet.
   js=np.flatnonzero(((m0<=hi).all(1)&(m1>=lo).all(1))&(np.arange(len(mesh))>i))
   for j in js:
    if not np.isin(tris[i],tris[j]).any() and hit(gp,mesh[j]):pair.add((int(i),int(j)))
   ks=np.flatnonzero((keep.min(1)<=hi).all(1)&(keep.max(1)>=lo).all(1))
   for j in ks:
    if not np.isin(tris[i],F[outer[bound[j]]]).any() and hit(gp,keep[j]):pair.add((int(i),-1-int(outer[bound[j]])))
  return pair
 c0=both(pt[tris]); c1=both(alt[tris])
 uvnew=np.vstack([uv, [w@uv[ix] for ix,w in provenance.values()]])
 weightnew=np.vstack([W, [w@W[ix] for ix,w in provenance.values()]])
 assert np.array_equal(W,weightnew[:len(W)]) and np.array_equal(uv,uvnew[:len(uv)])
 report['least_cap_rejected_geometry']={'minimum_facet_height_mm':1000*float(min((w@((alt[tris[i]]-ref)@n)).min() for i,w in clipped)),
 'maximum_movement_mm':float(capped.x[:-1].max()*1000),'minimum_normal_cosine':float(cos.min()),'normal_reversals':int((cos<=0).sum()),
 'baseline_tool_parent_pairs':sorted(old),'identity_refinement_tool_parent_pairs':sorted({(int(parents[i]),j) for i,j in identity}),
 'new_tool_child_pairs':sorted(after),'new_tool_parent_pairs':sorted(new),'outside_broad_phase_source_faces':len(bound),
 'island_mesh_strict_crossings_baseline':len(c0),'island_mesh_strict_crossings_rejected_trial':len(c1),'new_strict_nonincident_crossings':len(c1-c0),
 'retained_immutable_source_position_uv_and_weight_rows':True,
 'replacement_row_table_parent_offsets':[[int(i),int(np.flatnonzero(parents==i)[0]),int(np.count_nonzero(parents==i))] for i in patch]}
report['least_cap_diagnostic_lp_success']=bool(capped.success)
bb=F[capparent]
report['binding_source_face_indices']=bb.tolist()
report['binding_source_face_fixed_flags']=[bool(i in fixed) for i in bb]
report['binding_source_face_exact_alias_pairs']=[
 [int(i),local[inv==inv[np.searchsorted(local,i)]].tolist()] for i in bb if cnt[inv[np.searchsorted(local,i)]]>1]
if capped.success:
 # Rays originate on real facet 124 at a deterministic interior barycentric
 # grid. Test positive/coherent sheet incidence, not shaded appearance.
 grid=np.array([(i,j,12-i-j) for i in range(1,11) for j in range(1,12-i)])/12
 def bearing(mesh):
  g0=mesh[:,0]; edge1=mesh[:,1]-g0; edge2=mesh[:,2]-g0
  hv=np.cross(n,edge2); det=(edge1*hv).sum(1); safe=np.where(abs(det)>1e-15,det,1)
  selected=[]
  for pos in grid@face:
   off=pos-g0; rayu=(off*hv).sum(1)/safe; h=np.cross(off,edge1); rayv=(h@n)/safe; dist=(edge2*h).sum(1)/safe
   ok=np.flatnonzero((abs(det)>1e-15)&(rayu>=-1e-9)&(rayv>=-1e-9)&(rayu+rayv<=1+1e-9)&(dist>.00000001)&(dist<.015))
   if len(ok):
    i=ok[np.argmin(dist[ok])]
    selected.append((float(dist[i]*1000),bool(norms(mesh[i:i+1])[0]@n<0)))
  return {'grid_count':len(grid),'positive_hit_count':len(selected),'facing_count':sum(i[1] for i in selected),'gaps_mm':[min(i[0] for i in selected),max(i[0] for i in selected)] if selected else None}
 report['finite_full_facet_124_grid']={'baseline_patch':bearing(V[F[patch]]),'rejected_patch':bearing(alt[tris])}
print(json.dumps(report,indent=2,sort_keys=True))
