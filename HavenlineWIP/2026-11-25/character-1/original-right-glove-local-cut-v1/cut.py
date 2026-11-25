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
from scipy.optimize import linprog
d=(V-face[0])@n*1000
chart=lab[tt[0]]; var=local[(lab==chart)&(cnt[inv]==1)]
# Eligible contact sheet only: actual facing toward shaft, <=3mm proximity;
# far, reverse, and retained faces remain unchanged and are checked separately by 3D intersection.
a0=q[0]; axis=q[1]-a0; axis/=np.linalg.norm(axis); axis2=np.cross(n,axis)
proj=lambda pts: (pts-a0)@np.array([axis,axis2]).T
Q=proj(q); 
if np.cross(np.r_[Q[1]-Q[0],0],np.r_[Q[2]-Q[0],0])[2]<0: Q=Q[[0,2,1]]
def clip_weights(x):
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
X=proj(xyz); overlap=(X.max(1)>=Q.min(0)).all(1)&(X.min(1)<=Q.max(0)).all(1)
faceD=d[F[ids]]
consider=np.flatnonzero(overlap&(faceD.min(1)<.05)&(faceD.max(1)>-3)&(norm@n<-.25))
def polyarea(x):
 return .5*abs(np.dot(x[:,0],np.roll(x[:,1],-1))-np.dot(x[:,1],np.roll(x[:,0],-1)))
cuts=[]
for k in consider:
 w=np.array(clip_weights(X[k]))
 if len(w)<3 or polyarea(w@X[k])<1e-12:continue
 if (w@faceD[k]).min()<.05:
  cuts.append((int(ids[k]),w,float(polyarea(w@X[k])*1e6)))
assert {15906,15909}<=set(i for i,_,_ in cuts)
# Minimum sum of one-direction displacement; linear extrema exact at clipped vertices.
# Chart seams, fixed cuff, non-owned points protected.
def solve(cuts):
 active=np.intersect1d(var,np.unique(F[[i for i,_,_ in cuts]]))
 ptr={i:j for j,i in enumerate(active)}
 A=[]; B=[]; hard=[]
 for i,w,area in cuts:
  vi=F[i]
  for k in w:
   rhs=.05-k@d[vi]
   row=np.zeros(len(active))
   for vtx,vw in zip(vi,k):
    if vtx in ptr:row[ptr[vtx]]=vw
   if rhs>1e-8 and np.all(row<1e-12):hard.append(i)
   A.append(-row); B.append(-rhs)
 lp=linprog(np.ones(len(active)),A_ub=A,b_ub=B,bounds=(0,None),method='highs')
 return lp,active,sorted(set(hard))
def pairs(M,verts):
 rows=np.flatnonzero(np.isin(F,verts).any(1)); geom=M[F[rows]]; out=set()
 lo=tool.min(1); hi=tool.max(1)
 for i,g0 in zip(rows,geom):
  elig=np.flatnonzero((lo<=g0.max(0)).all(1)&(hi>=g0.min(0)).all(1))
  for j in elig:
   if crosses(g0,tool[j]) or crosses(tool[j],g0):out.add((int(i),int(j)))
 return out
lp, av, hard=solve(cuts)
lp2, av2, hard2=solve([(i,w,a) for i,w,a in cuts if i in (15906,15909)])
trial=None
if lp2.success:
 used=av2[lp2.x>1e-9]; held=V.copy(); held[av2]+=lp2.x[:,None]*n/1000
 before=pairs(V,used); after=pairs(held,used); touch=np.flatnonzero(np.isin(F,used).any(1))
 base=V[F[touch]]; new=held[F[touch]]
 normals=lambda x:np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0])
 x1,x2=normals(base),normals(new)
 trial={'moved_indices':used.tolist(),'held_shift_mm':lp2.x[lp2.x>1e-9].tolist(),'affected_faces':len(touch),
  'minimum_face_normal_cosine':float(np.min((x1*x2).sum(1)/np.maximum(1e-30,np.linalg.norm(x1,axis=1)*np.linalg.norm(x2,axis=1)))),
  'tool_pairs_before':sorted(before),'tool_pairs_after':sorted(after),'new_pairs':sorted(after-before)}
if lp.success:
 full=V.copy(); full[av]+=lp.x[:,None]*n/1000
 aa=av[lp.x>1e-9]; p0=pairs(V,aa); p1=pairs(full,aa)
 xa=np.flatnonzero(np.isin(F,aa).any(1)); nb=normals(V[F[xa]]); na=normals(full[F[xa]])
 fulltrial={"moved_vertices":len(aa),"incident_faces":len(xa),"maximum_shift_mm":float(lp.x.max()),"sum_shift_mm":float(lp.fun),"cleared_pairs":sorted(p0-p1),"remaining_pairs":sorted(p1),"new_pairs":sorted(p1-p0),"minimum_face_normal_cosine":float(np.min((nb*na).sum(1)/np.maximum(1e-30,np.linalg.norm(nb,axis=1)*np.linalg.norm(na,axis=1))))}
else: fulltrial=None
# Store shortest exact-alias proof as path IDs and UV jumps only (no export of vertices).
aidx,bidx=np.unravel_index(np.argmin(dsa[:,tt]),(len(starts),len(tt)))
start=ss[aidx]; j=tt[bidx]; path=[j]
while j!=start:
 j=int(psa[aidx,j]); assert j>=0; path.append(j)
path=np.array(path[::-1])
jumps=[{'indices':local[[k,l]].tolist(),'uv_jump':float(np.linalg.norm(uv[local[k]]-uv[local[l]]))} for k,l in zip(path,path[1:]) if inv[k]==inv[l]]
out={'status':'HOLD_NO_BILATERAL_NEUTRAL_CANDIDATE','source_hashes':expected,
 'indexed_same_chart_route':bool(np.isfinite(ds[:,tt]).any()),
 'native_index_component_vertex_counts':[int(np.count_nonzero(lab==chart)),int(np.count_nonzero(lab==lab[ss[0]]))],
 'exact_alias_shortest_held_route_mm':float(dsa[aidx,tt[bidx]]*1000),'exact_alias_order':local[path].tolist(),'atlas_seams_read_only':jumps,
 'no_weld':True,'original_tool_finite_facet':124,'outward_margin_mm_diagnostic':.05,
 'sheet_facing_threshold_diagnostic':-.25,'screen_proximity_mm':3,
 'required_projected_faces': [{'id':i,'area_mm2':a,'component_ids':np.unique(lab[np.searchsorted(local,F[i])]).tolist()} for i,w,a in cuts],
 'exact_all_cut_lp_success':bool(lp.success),'exact_all_cut_fixed_point_blocker_faces':hard,
 "all_cut_held_only_trial":fulltrial, 'two_face_repair_lower_bound_success':bool(lp2.success),'two_face_lp_fixed_point_blockers':hard2,'two_face_held_only_trial':trial}
print(json.dumps(out,indent=2,sort_keys=True))
