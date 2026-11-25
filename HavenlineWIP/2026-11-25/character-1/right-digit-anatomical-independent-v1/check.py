import contextlib,io,json
import numpy as np
from pathlib import Path
with contextlib.redirect_stdout(io.StringIO()) as report:
 import audit as d
R=json.loads(report.getvalue())
P,V,F,tool=d.P,d.V,d.F,d.tool
# independent scalar-first Hamilton product via left-quaternion operator
def H(q):
 w,x,y,z=q
 return np.array([[w,-x,-y,-z],[x,w,-z,y],[y,z,w,-x],[z,-y,x,w]])
def conjugate(q):return q*[1,-1,-1,-1]
def u(v):return v/np.linalg.norm(v)
def rotor(m):return d.Rotation.from_matrix(m).as_quat()[[3,0,1,2]]
def skin(ids, frames, W):
 Q=[]; D=[]
 for j in d.relevant:
  r,t,*_=frames[str(d.names[j])]; q=rotor(r)
  Q.append(q); D.append(.5*H(np.r_[0.,t])@q)
 Q=np.array(Q);D=np.array(D); out=[]
 for idx in ids:
  k=W[idx,d.relevant]; k=k*np.where(Q@Q[np.flatnonzero(k)[0]]<0,-1,1)
  q=k@Q; dr=k@D; length=np.linalg.norm(q); q/=length;dr/=length
  # explicitly project onto dual-quaternion unit study condition
  dr-=(dr@q)*q
  out.append((H(q)@H(np.r_[0.,P[idx]])@conjugate(q)+2*H(dr)@conjugate(q))[1:])
 return np.array(out)
nd='thumb.03.R'; axis=np.array(R['signed_axes'][nd]['held_axis']); pivot=np.array(R['signed_axes'][nd]['pivot_held'])
def modify(rad):
 w,x,y,z=np.r_[np.cos(rad/2),axis*np.sin(rad/2)]
 A=H([w,x,y,z]); B=conjugate(np.array([w,x,y,z]))
 rot=np.array([(A@H(np.r_[0.,e])@B)[1:] for e in np.eye(3)]).T
 next=d.frames.copy(); r,t,*_=next[nd]
 next[nd]=(rot@r,pivot+rot@(t-pivot))
 return next
base=skin(d.move,d.frames,d.R); nxt=skin(d.move,modify(np.pi/60),d.R); rev=skin(d.move,modify(-np.pi/60),d.R)
assert np.max(abs(base-d.base))<1e-12
assert np.max(abs(nxt-d.skin(modify(np.pi/60))))<1e-12
maxdelta=np.max(np.linalg.norm(nxt-base,axis=1))
assert abs(maxdelta*1000-R['sole_static_specimen']['max_moved_original_vertex_mm'])<1e-6
actual=np.array(V);actual[d.move]+=nxt-base
assert np.array_equal(actual[d.se],V[d.se]) and np.array_equal(actual[d.cu],V[d.cu]) and np.array_equal(actual[d.web],V[d.web])
# Independent sign check: change in actual held traced palm-distance on purer
# terminal indexed landmarks without relying on builder's sign test projection.
pure=d.R[d.move,d.ix[nd]]>.99999
signed=np.flatnonzero(pure)
coords=V[d.move[signed]]
center=V[d.palm].mean(0)
tip=u(coords.mean(0)-pivot); step=coords@tip
signed=signed[step>=np.quantile(step,.75)]
toward=np.linalg.norm(V[d.move[signed]]-center,axis=1)
after=np.linalg.norm(V[d.move[signed]]+nxt[signed]-base[signed]-center,axis=1)-toward
negative=np.linalg.norm(V[d.move[signed]]+rev[signed]-base[signed]-center,axis=1)-toward
assert np.median(after)<-5e-5 and np.median(negative)>5e-5
a,b=d.ix['thumb.02.R'],d.ix[nd]
se02=d.se[d.R[d.se,a]>0]; assert len(se02)==4 and not np.any(d.R[d.se,b]>0)
assert not np.any(d.local['weights'][:,b]>0)
def tnormal(f):
 n=np.cross(f[1]-f[0],f[2]-f[0]); return n/np.linalg.norm(n)
# Intersect each triangle independently with the other supporting plane; overlap in
# common-line coordinates. Strict if interior on either triangle (the other may
# be a refinement edge). Coplanars and endpoint-only contacts are not counted.
def interval(f,h,u):
 xyz=(f-h[0])@tnormal(h)
 tol=1e-10
 if np.max(np.abs(xyz))<=tol: return None
 dots=[]
 for i,j in zip(range(3), (1,2,0)):
  if abs(xyz[i])<=tol: dots.append(f[i]@u)
  if xyz[i]*xyz[j]<-tol**2: dots.append((f[i]+(f[j]-f[i])*xyz[i]/(xyz[i]-xyz[j]))@u)
 if len(dots)<2:return None
 return min(dots),max(dots), bool(xyz.min()<-tol and xyz.max()>tol)
def cross(a,b):
 u=np.cross(tnormal(a),tnormal(b)); mag=np.linalg.norm(u)
 if mag<1e-10:return False
 u/=mag
 z=interval(a,b,u); zz=interval(b,a,u)
 return z is not None and zz is not None and (z[2] or zz[2]) and min(z[1],zz[1])-max(z[0],zz[0])>1e-9
# Orthogonal stand-ins test physical triangle overlap, separated finite facets and coplanars.
ctrl=np.array([[0,0,0],[4,0,0],[0,4,0]],float)
other=np.array([[1,1,-4],[1,1,4],[2,2,0]],float)
assert cross(ctrl,other) and not cross(ctrl,other+[8,0,0]) and not cross(ctrl,ctrl)
active=np.flatnonzero(np.any(np.isin(F,d.move),axis=1)&~np.isin(np.arange(len(F)),d.local['removed']))
lo=tool.min(1);hi=tool.max(1)
def toolpairs(geo):
 p=set()
 for i,f in zip(active,geo[F[active]]):
  for j in np.flatnonzero((lo<=f.max(0)+1e-10).all(1)&(hi>=f.min(0)-1e-10).all(1)):
   if cross(f,tool[j]):p.add((int(i),int(j)))
 return p
orig,after_p=toolpairs(V),toolpairs(actual)
def counts(pts,r):
 # Vectorized finite ray intersections; reference vertices fully original;
 # exact tool covers all parts. Non-cardinal ray prevents shared hit seams.
 A=tool[:,0];X=tool[:,1]-A;Y=tool[:,2]-A
 r=np.array(r);H0=np.cross(r,Y);det=np.einsum('ij,ij->i',X,H0);good=np.abs(det)>1e-14
 z=np.where(good,det,1.)
 B=pts[:,None]-A;Q=np.cross(B,X); bx=(B*H0).sum(2)/z;by=Q@r/z;t=(Y*Q).sum(2)/z
 return (good & (t>1e-9)&(bx>1e-10)&(by>1e-10)&(bx+by<1-1e-10)).sum(1)
offids=np.unique(F[np.unique(d.off_pairs[:,0])])
def wind(pts):
 a,b,c=(tool[None]-pts[:,None,None]).transpose(2,0,1,3)
 sa,sb,sc=map(lambda x:np.linalg.norm(x,axis=-1),(a,b,c))
 dot=lambda x,y: np.einsum('...i,...i->...',x,y)
 return np.arctan2(dot(np.cross(a,b),c),sa*sb*sc+sa*dot(b,c)+sb*dot(c,a)+sc*dot(a,b)).sum(1)/(2*np.pi)
def hist(x): 
 a,b=np.unique(x,return_counts=True);return dict(zip(a.tolist(),b.tolist()))
cont=[]
for geo in (V,actual):
 pts=geo[offids]
 ww=wind(pts)
 rays=[counts(pts,r) for r in ([1.,.573,.317],[-.271,.811,1.],[.413,-1.,.642])]
 cont.append({'winding_degrees':hist(np.rint(ww).astype(int)), 'odd_count_each_ray':[int((z%2).sum()) for z in rays],
  'ray_parity_equals_winding_mod2_count_each_ray':[int(np.count_nonzero((z%2)==(np.rint(ww).astype(int)%2))) for z in rays],
  'all_abs_winding_over_half':int((abs(ww)>.5).sum())})
print(json.dumps({'baseline_dqs_agreement_max_m':float(np.abs(base-d.base).max()),
 'independent_thumb_seam_02':se02.tolist(),'independent_thumb_seam_03_count':int(np.count_nonzero(d.R[d.se,b])),
 'authored_palm_03_count':int(np.count_nonzero(d.local['weights'][:,b])), 'authored_palm_rows':len(d.local['vertices']),
 'actual_palm_distance_change_median_positive_negative_mm':[float(np.median(after)*1000),float(np.median(negative)*1000)],
 'samples_in_independent_palm_distance_measurement':len(signed),
 'old_new_strict_pairs':[len(orig),len(after_p)], 'removed_and_added':[len(orig-after_p),len(after_p-orig)],
 'containment_predicate_diagnostics':cont},sort_keys=True,indent=2))
