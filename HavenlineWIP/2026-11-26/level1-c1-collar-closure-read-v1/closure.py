"""Minimum read-only witness closure at the exact held key; never alter an asset or pose."""
import contextlib,io,json,sys,os,hashlib,heapq
from collections import Counter,defaultdict,deque
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
here=Path.cwd();parent=Path('../level1-c1-collar-assembly-read-v1').resolve()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(parent/'ASSEMBLY-READ-SHA256SUMS')=='d6a13f5c2891a905a22917e12789d2740d4124d317fafb7b700b91e9299ab966'
for line in (parent/'ASSEMBLY-READ-SHA256SUMS').read_text().splitlines():
 h,n=line.split();assert sha(parent/n)==h
sys.path.insert(0,str(parent));os.chdir(parent)
with contextlib.redirect_stdout(io.StringIO()):
 from scope import A,F,Qf,R,P,V,D,f,cnt,edge_face,oriented_edges,vicinity,silhouette,allowed,rims
os.chdir(here)
allmetal=V[:,1]>100 # zero mask, then any pure hardware row
for slot,n in enumerate(f.slots):
 if 'Rigid_R_BootFastener_' in n:
  allmetal|=((f.W*(f.J==slot)).sum(1)==1)
all_hw=set(np.flatnonzero(allmetal[F].all(1)))
metal_rows=set(map(int,f.tags[np.flatnonzero(allmetal)]))
support=set(f.bounds['R']['faces'].reshape(-1))
toe=((f.W*(f.J==f.slots.index('RBall'))).sum(1)>.99)
right=f.bounds['R']['leg']
allowed=set(i for i in allowed if i not in all_hw and not (support&set(F[i])) and not (toe[F[i]].any()))
assert A<=allowed
# Translate the two fixed preserved source geometries only; the function
# reuses actual coordinates and checks segment/triangle and line/line.
def prep(X):
 tri=X[F];lo=tri.min(1);hi=tri.max(1);mid=(lo+hi)*.5
 rad=np.linalg.norm(hi-mid,axis=1);tree=cKDTree(mid)
 return tri,lo,hi,rad,tree
states={'neutral':(R,prep(R)),'loaded':(P,prep(P))}
rawtag=dict(zip(map(int,f.tags[::-1]),range(len(f.tags)-1,-1,-1)))
def skeleton(S):
 e=Counter(tuple(sorted(e)) for i in S for e in oriented_edges(i))
 boundary={k for k,v in e.items() if v==1}
 adj=defaultdict(set)
 for x,y in boundary:adj[x].add(y);adj[y].add(x)
 if not adj or any(len(v)!=2 for v in adj.values()):return None
 Q=set(adj);comps=[]
 while Q:
  front={Q.pop()};seen=front.copy()
  while front:
   front=set.union(*(adj[x] for x in front))&Q;seen|=front;Q-=front
  comps.append(len(seen))
 tags=set(x for i in S for x in Qf[i])
 return e,boundary,adj,comps,tags
def piercers(S,bound,at):
 X,w=states[at];tri,lo,hi,rad,tree=w
 out=[]
 for a,b in sorted(bound):
  i,j=rawtag[a],rawtag[b];u,v=X[[i,j]]; di=v-u
  ids=np.array(tree.query_ball_point((u+v)*.5,np.linalg.norm(di)*.5+rad.max()+1e-10),dtype=int)
  ids=ids[~np.isin(ids,list(S))]
  ids=ids[((lo[ids]<=np.maximum(u,v)+1e-10)&(hi[ids]>=np.minimum(u,v)-1e-10)).all(1)]
  ids=ids[~((Qf[ids]==a)|(Qf[ids]==b)).any(1)]
  q=tri[ids];e=q[:,1]-q[:,0];g=q[:,2]-q[:,0];px=np.cross(di,g)
  den=np.sum(e*px,axis=1);ok=np.abs(den)>1e-13
  div=np.where(ok,den,1.)
  s=u-q[:,0];p2=np.cross(s,e)
  t0=(s*px).sum(1)/div;t1=p2@di/div;dt=(p2*g).sum(1)/div
  mm=np.minimum.reduce([t0,t1,1.-t0-t1,dt,1.-dt])
  for ip in np.flatnonzero(ok&(mm>1e-7)):
   z=int(ids[ip]); N=np.cross(e[ip],g[ip]);N/=np.linalg.norm(N)
   out.append(dict(edge=[a,b],raw=[i,j],outside=z,intersects_at=float(dt[ip]),
        interior_min=float(mm[ip]),endpoint_signed_mm=((X[[i,j]]-tri[z,0])@N*1000).tolist()))
 return out
def self_boundary(bound,at):
 X,_=states[at];links=sorted(bound); hits=[]
 for ix,(a,b) in enumerate(links):
  U,V=X[[rawtag[a],rawtag[b]]]
  for c,d in links[ix+1:]:
   if len({a,b,c,d})!=4:continue
   Q,Y=X[[rawtag[c],rawtag[d]]]
   mat=np.column_stack((V-U,Q-Y))
   w=np.linalg.lstsq(mat,Q-U,rcond=None)[0]
   if min(*w,*(1-w))>1e-7 and np.linalg.norm(mat@w-(Q-U))<1e-9:hits.append([a,b,c,d])
 return hits
def get(S):
 data=skeleton(S)
 if data is None:return None
 e,B,adj,cy,tag=data
 if len(cy)!=1 or len(tag)-len(e)+len(S)!=1:return None
 if (tag-set(adj))&metal_rows:return None
 if any(len(edge_face[x])!=2 for x in e):return None
 if any(count!=1 for x,count in e.items() if x in rims):return None
 for x in B:
  a,b=edge_face[x]
  if a[1:]!=b[1:][::-1]:return None
 ids=np.flatnonzero(np.isin(f.tags,list(tag)))
 # A strict inset protects the original convex outline. We report projected
 # bounds, not pixel exactness or a silhouette/appearance pass.
 envelope=[silhouette(X,ids,True) for X in (R,P)]
 if max(envelope)>=-1e-7:return None
 kept_neutral=piercers(S,B,'neutral')
 kept_loaded=piercers(S,B,'loaded')
 selfhits=[self_boundary(B,at) for at in states]
 return dict(edges=e,bound=B,adj=adj,cycles=cy,tags=tag,raw=ids,envelope=envelope,neutral=kept_neutral,loaded=kept_loaded,bound_self=selfhits)
def paths_to(S,q,budget):
 # Any connected internalization of outside face q must contain at least
 # one edge-adjacent path from A. Enumerate all simple allowed paths within
 # bounded budget, not just the shortest path to each branch.
 queue=deque([(i,) for i in sorted(S)])
 dist={q:0}; bfs=deque([q])
 while bfs:
  x=bfs.popleft()
  if dist[x]>=budget:continue
  for y in sorted(vicinity({x})&allowed):
   if y not in dist:dist[y]=dist[x]+1;bfs.append(y)
 while queue:
  l=queue.popleft();x=l[-1];nn=len(l)-1
  if x==q and nn>0:yield set(l[1:]);continue
  if nn>=budget or dist.get(x,1000)>budget-nn:continue
  queue.extend(l+(y,) for y in sorted(vicinity({x})&allowed) if y not in S and y not in l)
def describe(S,K):
 E,B,adj=K['edges'],K['bound'],K['adj']
 root0=min(adj); order=[root0];prev=None;x=root0
 while True:
  y=min(adj[x]-({prev} if prev is not None else set()))
  if y==root0:break
  order.append(y);prev,x=x,y
 assert len(order)==len(adj)
 row=np.array([rawtag[x] for x in order],int)
 ids=K['raw']; tag=K['tags']
 domain=np.array(sorted(S))
 def project(X):
  XY=(X-f.cam)@f.basis[:2].T*720/13
  xr=XY[ids];tri=XY[F[domain]]
  A,B=tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]
  pr=np.abs(A[:,0]*B[:,1]-A[:,1]*B[:,0]).sum()*.5
  return dict(frame_px_bounds=(xr.min(0)+[640,360]).tolist()+ (xr.max(0)+[640,360]).tolist(),
      width_height_px=np.ptp(xr,axis=0).tolist(),projected_triangle_area_sum_upper_bound_px2=float(pr))
 return dict(additions=sorted(S-A),all_source_faces=domain.tolist(),face_count=len(S),one_opposite_wound_boundary=len(B),
    fixed_boundary_raw_order=row.tolist(),sole_toe_and_pure_metal_faces_excluded=True,
    four_or_other_fixed_fused_metal_edges_raw=[list(map(rawtag.get,e)) for e in sorted(B&rims)],
    local_art_bbox_min_max=[V[ids].min(0).tolist(),V[ids].max(0).tolist()],
    interior_welded_and_raw_count=[len(tag-set(adj)),int(np.isin(f.tags,list(tag-set(adj))).sum())],
    right_boot_convex_envelope_inset_rest_loaded_px=[-v for v in K['envelope']],
    rest_and_loaded_normal_camera_projection=[project(R),project(P)],
    neutral_and_loaded_boundary_piercers=[K['neutral'],K['loaded']],boundary_self_piercers=K['bound_self'])
s0=get(A);assert len(s0['loaded'])==1 and s0['loaded'][0]['outside']==8946 and not s0['neutral']
limit=8
bestq=[(0,tuple(sorted(A)))];seen=set();done=[];trace=[];chosen=None
while bestq:
 k,b=heapq.heappop(bestq);S=set(b)
 if b in seen:continue
 seen.add(b)
 K=get(S)
 if K is None:
  trace.append(dict(additions=sorted(S-A),topological_or_protected_domain_refusal=True));continue
 trace.append(dict(additions=sorted(S-A),neutral=K['neutral'],loaded=K['loaded'],self_boundary=K['bound_self']))
 if not K['neutral'] and not K['loaded'] and not any(K['bound_self']):
  chosen=describe(S,K);break
 if k==limit or any(K['bound_self']):continue
 hits=K['neutral']+K['loaded']
 # For current earliest remaining strict witness any valid containing domain
 # must internalize its outside face or the single other edge-neighbor.
 w=hits[0]
 e=tuple(w['edge']); ext=[j for j,*_ in edge_face[e] if j not in S]
 for a in [({j} if j in allowed else set()) for j in ext]:
  if a:
   C=S|a;heapq.heappush(bestq,(len(C-A),tuple(sorted(C))))
 if w['outside'] in allowed:
  for a in paths_to(S,w['outside'],limit-k):
   C=S|a;heapq.heappush(bestq,(len(C-A),tuple(sorted(C))))
print(json.dumps(dict(original_disk_faces=len(A),read_only_closure_budget_faces=limit,first_piercer=s0['loaded'][0],
                     explored_states=trace,minimum_model_found=chosen,
                     no_geometry_weights_pose_or_install=True,no_raster_game_or_acceptance_claim=True),indent=2))
