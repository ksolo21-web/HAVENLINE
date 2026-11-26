from pathlib import Path
import hashlib,json,numpy as np
from collections import defaultdict
R=Path(__file__).resolve().parent;P=R.parent
q=P/'hvn-l1-fence-33036-emboss-end-fit-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(q/'SHA256SUMS')=='fd72a8b2f1b97bed6c3f1abab5f3cde878095700a7866ac08e2e9275b71fc733'
ctx={'__file__':str(q/'ends.py')};s=(q/'ends.py').read_text()
exec(s[:s.index('holds={')],ctx)
T=ctx['T']; A=ctx['A'];stock=ctx['stock'];M=ctx['M']
N=ctx['N']; C=ctx['C']
# Isolate actual stock closed parts; positive parity inside a particular
# unchanged solid is independent of how a new terminal will be sculpted.
V,index=np.unique(np.round(stock.reshape(-1,3),8),axis=0,return_inverse=True);ii=index.reshape(-1,3)
f=list(range(len(ii)));E={}
def find(x):
 while f[x]!=x:f[x]=f[f[x]];x=f[x]
 return x
for j,a in enumerate(ii):
 for e in zip(a,np.roll(a,-1)):
  k=tuple(sorted(e))
  if k in E:f[find(j)]=find(E[k])
  E[k]=j
G=defaultdict(list)
for j in range(len(ii)):G[find(j)].append(j)
# Independent non-axis ray parities; test no circumstantial degeneracy.
def inside(p,t):
 if (p<t.min((0,1))-1e-9).any() or (p>t.max((0,1))+1e-9).any(): return False
 d1=t[:,1]-t[:,0];d2=t[:,2]-t[:,0];dra=[]
 for d in [[1,.297,.161],[.149,1,.321],[.433,.135,1]]:
  h=np.cross(d,d2); q=np.einsum('ij,ij->i', d1,h);v=p-t[:,0]
  en=abs(q)>1e-12
  uu=np.zeros(len(t));vv=uu.copy();dist=uu.copy()
  uu[en]=np.einsum('ij,ij->i',v,h)[en]/q[en]
  z=np.cross(v,d1);vv[en]=(z@np.array(d))[en]/q[en]
  dist[en]=np.einsum('ij,ij->i',d2,z)[en]/q[en]
  valid=en&(uu>=-1e-9)&(vv>=-1e-9)&(uu+vv<=1+1e-9)&(dist>1e-9)
  hit=np.unique(np.round(dist[valid],8))
  dra.append(len(hit)%2)
 assert len(set(dra))==1,(p,dra)
 return bool(dra[0])
rows={}
for end,x,nb in [('left',-8.349,'West2'),('right',-6.408,'SW1')]:
 out={};target=A[nb][0]
 for k,t in T.items():
  if not k.startswith(('rail_','rear_')):continue
  # Interior cap spokes and circumferential vertices. Strict robust occupancy with small
  # axis perturbation is the minimum impossibility certificate; don't count touches.
  F=t[(abs(t[:,:,0]-x)<1e-9).all(1)]
  req=np.r_[F.reshape(-1,3),.5*(F[:,0]+F[:,1]),F.mean(1)]
  unique=np.unique(np.round(req,8),axis=0)
  positives=[]
  for v in unique:
   for inds in G.values():
    P0=target[inds]
    if not inside(v,P0):continue
    m=0
    for e in [.00025,.0005,.001,.002,.003,.005]:
     if all(inside(v+x,P0) for x in np.r_[np.eye(3)*e,-np.eye(3)*e]):m=e
     else:break
    positives.append((m, v.tolist(), [min(inds),max(inds)],M[inds[0]]))
  out[k]={'fixed_cap_plane_x_m':x,'tiles':len(F),'finite_sample_count':len(unique),
          'strictly_inside_immutable_adjacent_visual_closed_component':len(positives),
          'max_six_axis_probe_persistence_m_witness':max(positives,default=None)}
 rows[end]={'neighbor':nb,'signed_xz_neighbor_pose':A[nb][2].tolist(),'roof_and_ground_never_modified':True,'cap_collision_necessary_conflict':out}
(R/'result.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
print(json.dumps(rows))
