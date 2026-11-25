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
from collections import defaultdict
ad=defaultdict(list)
for fi in np.flatnonzero((P[F,0]<-.52).any(1)):
 t=F[fi]
 for a,b in zip(t,np.roll(t,-1)):ad[tuple(sorted((int(a),int(b))))].append(int(fi))
def intersects_edge(edge):
 a,b=V[list(edge)]; e=b-a
 lo,hi=np.minimum(a,b),np.maximum(a,b)
 ids=np.flatnonzero((toollo<=hi).all(1)&(toolhi>=lo).all(1))
 h=[]
 for j in ids:
  tri=tool[j]; o=tri[0]; e1,e2=tri[1:]-o; hh=np.cross(e,e2); det=e1@hh
  if abs(det)<1e-15:continue
  aa=a-o; uu=aa@hh/det; cc=np.cross(aa,e1); vv=e@cc/det; tt=e2@cc/det
  if min(uu,vv,1-uu-vv,tt,1-tt)>1e-8:h.append((int(j),float(tt)))
 return h
lock=set(np.r_[locked])
outside_chart=set(F[allchart].ravel())
sets=set(patch.tolist())
steps=[]
for _ in range(12):
 ec=defaultdict(list)
 for i in sorted(sets):
  t=F[i]
  for a,b in zip(t,np.roll(t,-1)):ec[tuple(sorted((int(a),int(b))))].append(i)
 boundary={e:ii[0] for e,ii in ec.items() if len(ii)==1}
 bad=[]
 for e,i in boundary.items():
  hh=intersects_edge(e)
  if hh:
   adjacent=[j for j in ad[e] if j!=i]
   bad.append({'e':e,'inner':i,'outer':adjacent,'hits':hh,'locked_vertices':[i for i in e if i in lock]})
 steps.append({'faces':len(sets),'boundary':len(boundary),'hits':bad})
 if not bad:break
 adds=set()
 for fault in bad:
  if len(fault['outer'])==1:
   j=fault['outer'][0]
   if j in allchart and not fault['locked_vertices']:adds.add(j)
 if not adds:break
 sets |= adds
report={'source_hashes':expected,'strict_finite_perimeter_rechecks':steps,'final_faces':len(sets),'final_protected_vertices':sum(i in lock for i in set(sum((list(i) for i in boundary),[]))),'boundary_clear':not steps[-1]['hits']}
def winding(pos):
 g=tool-np.asarray(pos)[None,None,:]
 a,b,c=g.transpose(1,0,2)
 A=np.linalg.norm(a,axis=1);B=np.linalg.norm(b,axis=1);C=np.linalg.norm(c,axis=1)
 div=A*B*C+(a*b).sum(1)*C+(a*c).sum(1)*B+(b*c).sum(1)*A
 return float(np.arctan2((np.cross(a,b)*c).sum(1),div).sum()/(2*np.pi))
vs=np.unique(np.array(list(boundary)))
summary={}
for k,pp in [('vertices',V[vs]),('midpoints',V[np.array(list(boundary))].mean(1))]:
 w=[winding(x) for x in pp]; summary[k]=[len(w),min(w),max(w),sum(abs(q)>.5 for q in w)]
report['tool_winding_exact_mesh']=summary
