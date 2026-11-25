from source import *
from collections import defaultdict,Counter,deque
import glob
root=Path(glob.glob('../hvn-c1-retained-tool-scope-independent-v1.*')[0])
assert digest(root/'SHA256SUMS').startswith('7a939f74')
for row in (root/'SHA256SUMS').read_text().splitlines():
 sha, name=row.split(); assert digest(root/name)==sha
q=json.loads((root/'result.json').read_text())['R/distal_connected_to_owned_glove']['rows']
base=Path('../hvn-c1-owner-right-palm-reauthor-v1')
uvp=Path('../hvn-c1-owner-right-palm-uv-v1')
assert digest(base/'AUTHOR-SHA256SUMS')=='9e335e2772d593b3e1f7b9f27f331b36ca8f5283f998018b95c4d769bfda1a61'
assert digest(uvp/'SHA256SUMS').startswith('5dd917a3')
for root,manifest in ((base,'AUTHOR-SHA256SUMS'),(uvp,'SHA256SUMS')):
 for row in (root/manifest).read_text().splitlines():
  sha,name=row.split(); assert digest(root/name)==sha
orig=json.loads((base/'result.json').read_text()); patch=np.array(orig['source_patch_face_indices'])
old=np.load(uvp/'reauthored-review-LOCAL.npz')
assert np.array_equal(old['removed'],patch)
h0=json.loads((uvp/'result.json').read_text())
for k,d in h0['base_local_candidate_array_SHA256'].items():
 assert hashlib.sha256(np.ascontiguousarray(old[k]).tobytes()).hexdigest()==d
se=np.sort(np.concatenate([F[patch][:,[0,1]],F[patch][:,[1,2]],F[patch][:,[2,0]]]),axis=1)
se,n=np.unique(se,axis=0,return_counts=True); seam=se[n==1]
_,ix=np.unique(np.c_[P,V],axis=0,return_inverse=True) # exact aliases, adjacency only
G=defaultdict(list); own=np.flatnonzero((P[F,0]<-.52).all(1))
def es(t):return [tuple(sorted(x)) for x in zip(t,np.roll(t,-1))]
for i in own:
 for e in es(ix[F[i]]): G[e].append(int(i))
def adj(i):
 return set(j for e in es(ix[F[i]]) for j in G[e] if j!=i)
# Multi-source exact edge-ring distances across retained topology.
seen={int(i):0 for i in patch}; b=deque(seen)
while b:
 i=b.popleft()
 for j in adj(i):
  if j not in seen:seen[j]=seen[i]+1;b.append(j)
bad={int(t[0]) for t in q}; assert len(q)==206 and len(bad)==193 and not bad.intersection(patch)
unseen=set(bad); components=[]
while unseen:
 seed=min(unseen); stack=[seed]; unseen.remove(seed); comp={seed}
 while stack:
  i=stack.pop()
  for j in adj(i)&unseen: unseen.remove(j); comp.add(j);stack.append(j)
 components.append(comp)
norm=np.cross(tool[:,1]-tool[:,0],tool[:,2]-tool[:,0])
norm/=np.maximum(1e-30,np.linalg.norm(norm,axis=1)[:,None])
# Normal angle is relative to the assigned finite facet, not hand semantics.
dp=norm@norm[124]
seamids=np.unique(ix[seam])
def crosses_any(fi,facet):
 g=V[F[fi]]; h=tool[facet]
 return bool(crosses(g,h) or crosses(h,g))
assert all(crosses_any(r[0],r[1]) for r in q)
def bucket(j):
 return 'opposed_facet' if dp[j]<-.25 else 'assigned_hemisphere' if dp[j]>.25 else 'shaft_flank'
result=[]
for C in sorted(components,key=lambda c:(-len(c),min(c))):
 rows=[(i,j) for i,j,*_ in q if i in C]; d=[seen.get(i,-1) for i in C]
 result.append(dict(faces=len(C),pairs=len(rows),edge_ring_range=[min(d),max(d)],facet_buckets=Counter(bucket(j) for i,j in rows),seam_vertices_touched=len(np.intersect1d(ix[F[list(C)]],seamids)),raw_pairs=rows))
# Expand only across exact physical face adjacency, then test finite shaft
# piercings of the complete frontier and sensitivity to protecting source aliases.
def pierced(a,b):
 d=b-a; l,h=np.minimum(a,b),np.maximum(a,b)
 near=((tool.max(1)>=l)&(tool.min(1)<=h)).all(1)
 ans=[]
 for j in np.flatnonzero(near):
  tri=tool[j]; o=tri[0]; e,f=tri[1:]-o
  det0=e@np.cross(d,f)
  if abs(det0)<1e-15: continue
  y=a-o; m=np.cross(y,e)
  u=y@np.cross(d,f)/det0; v=d@m/det0; t=f@m/det0
  if min(u,v,1-u-v,t,1-t)>1e-8: ans.append(int(j))
 return ans
_, first, cnt=np.unique(ix,return_index=True,return_counts=True)
assert len(first)==len(cnt)
def inside(pos):
   v=tool-pos; a,b,c=v.transpose(1,0,2)
   x,y,z=np.linalg.norm(v,axis=-1).T
   den=x*y*z+(a*b).sum(1)*z+(a*c).sum(1)*y+(b*c).sum(1)*x
   return abs(float(np.arctan2((np.cross(a,b)*c).sum(1),den).sum()/(2*np.pi)))>.5
front=[]
C=set(bad)
for rings in range(5):
 ee=Counter(e for i in C for e in es(ix[F[i]]))
 frontier=[e for e,k in ee.items() if k==1]
 hard=[(a,b,p) for a,b in frontier if (p:=pierced(*V[first[[a,b]]]))]
 allids=np.unique(ix[F[list(C)]])
 vertices=np.unique(frontier); inside_ids=[int(i) for i in vertices if inside(V[first[i]])]
 mid_inside=sum(inside(V[first[[a,b]]].mean(0)) for a,b in frontier)
 degree=Counter(v for e in frontier for v in e)
 chi=len(allids)-len(ee)+len(C)
 front.append(dict(rings=rings,face_count=len(C),edge_count=len(frontier),finite_piercings=hard, inside_frontier_vertex_count=len(inside_ids), inside_frontier_midpoint_count=mid_inside, frontier_degree=Counter(degree.values()), euler=chi,
     internal_alias_count=int(np.count_nonzero(cnt[np.setdiff1d(allids,np.unique(frontier))]>1)),
     touches_fixed_palm_seam=int(np.intersect1d(allids,seamids).size),
     closest_original_palm_ring=min(seen.get(i,10000) for i in C)))
 if not (hard or inside_ids or mid_inside):break
 C.update(set().union(*(adj(i) for i in C)))
print(json.dumps({'frontier':front,'indices':result,'totals_by_ring':Counter(seen.get(i,-1) for i,j,*_ in q),'totals_by_side':Counter(bucket(j) for i,j,*_ in q),'facet_normal_dots':{j:float(dp[j]) for _,j,*_ in q},'seam_adjacent_retained_count':sum(v==1 for v in seen.values())},indent=2,sort_keys=True))
