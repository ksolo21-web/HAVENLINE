"""Read-only boundary census about the measured inter-fastener failure."""
import contextlib,io,heapq,json
from collections import Counter,defaultdict,deque
import numpy as np
from scipy.spatial import ConvexHull
with contextlib.redirect_stdout(io.StringIO()) as quiet:
 from analyze import f,F,V,R,P,D,edge_face,vicinity,oriented_edges,raw,investigated,Qf
rt={8677,8892,8893,8916,8918}
patch=set(investigated)
cores=set.union(*(d[0] for d in D))
rims=set.union(*(d[1] for d in D))
right_guard=(V[:,0]<-.045)&(V[:,1]>=.060)&(V[:,1]<=.125)
allowed=set(np.flatnonzero(right_guard[F].all(1)))-cores
assert rt<=allowed
def route(a,b):
 prev={a:None};queue=deque([a])
 while queue:
  u=queue.popleft()
  if u==b:
   path=[u]
   while prev[u] is not None:
    u=prev[u];path.append(u)
   return path[::-1]
  for v in sorted(vicinity({u})&allowed):
   if v not in prev:prev[v]=u;queue.append(v)
 return None
# One supplied candidate domain from ordered measured failure witnesses,
# not statically proposed new skin geometry/deformation.
paths=[route(8677,face) for face in sorted(patch)]
conn=all(paths)
joined=set(x for ray in paths if ray for x in ray)
A=joined|patch
for _ in [0]:A|=(vicinity(A)&allowed)
cnt=Counter(tuple(sorted(e)) for x in A for e in oriented_edges(x))
rim_faces=[(e,m,edge_face[e]) for e,m in cnt.items() if m==1]
rim=Counter(x for e,_,_ in rim_faces for x in e)
tags=np.unique(Qf[list(A)])
rowids=np.flatnonzero(np.isin(f.tags,tags))
interior_raw=np.flatnonzero(np.isin(f.tags,np.array(sorted(set(tags)-set(rim)))))
d=f.basis
def silhouette(A,t,boot=False):
 pts=A[t]
 X=(pts-f.cam)@d[:2].T*720/13
 YO=np.unique((((A[f.bounds["R"]["leg"]] if boot else A)-f.cam)@d[:2].T)*720/13,axis=0)
 hull=ConvexHull(YO)
 margins=np.max(X@hull.equations[:,:2].T+hull.equations[:,2],axis=1)
 return float(np.max(margins))
summary=dict(all_investigated_witnesses_connected_within_right_local_height_band=conn,
    source_face_path_hops_from_8677=[len(p)-1 if p is not None else None for p in paths],
    lower_upper_core_in_domain=len(A&cores),source_rigid_core_rim_edges_used_by_domain=len(set(cnt)&rims),
    cloth_domain_face_count=len(A),boundary_edge_count=len(rim_faces),boundary_valence=dict(Counter(rim.values())),
    nonmanifold_edges_in_source_domain=sum(len(edge_face[e])!=2 for e in cnt),
    exterior_branch_edges_with_opposite_winding=sum(len(e)==2 and e[0][1:]==e[1][1:][::-1] for _,_,e in rim_faces),
    interior_rows=len(interior_raw),domain_rest_bbox_art_m=[V[rowids].min(0).tolist(),V[rowids].max(0).tolist()],
    contains_physical_support_or_dedicated_toe_raw_rows=bool(any(np.isin(g['faces'],rowids).any() for g in f.bounds.values()) or ((f.W[rowids]*(f.J[rowids]==f.slots.index('RBall'))).sum(1)>.99).any()),
    full_character_global_convex_outline_projection_slack_rest_loaded_px=[silhouette(R,rowids),silhouette(P,rowids)],
    right_boot_convex_outline_projection_slack_rest_loaded_px=[silhouette(R,rowids,True),silhouette(P,rowids,True)],
    all_rigid_rim_intersections_are_fixed_boundary=all(cnt[x]==1 for x in set(cnt)&rims),
    convex_slack_is_not_raster_silhouette_acceptance=True,replaced_geometry=False)
print(json.dumps(summary,indent=2))
