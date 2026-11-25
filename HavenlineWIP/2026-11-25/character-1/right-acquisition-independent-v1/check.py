import contextlib,io,json
from pathlib import Path
import numpy as np
with contextlib.redirect_stdout(io.StringIO()) as capture:
 import audit as m
assert capture.getvalue()==Path('../hvn-c1-right-acquisition-proof-v1.1u1fZK/result.json').read_text()
T=m.tool
piv=m.deltas[m.selected][-1]; unit=m.deltas[m.selected][-2]; indices=m.pure
v=m.V[indices]-piv
delta=v-(v@unit)[:,None]*unit
vel=np.cross(unit,delta)
radius=np.linalg.norm(delta,axis=1)
A=T[:,0]; B=T[:,1]-A; C=T[:,2]-A
N=np.cross(B,C); N/=np.linalg.norm(N,axis=1)[:,None]
E=np.roll(T,-1,axis=1)-T
Einv=(E*E).sum(2)
# Independent finite distances use projected barycentric solve, not the producer's
# directed boundary signs; and vertex-to-segment controls for outside projections.
b11=(B*B).sum(1);b12=(B*C).sum(1);b22=(C*C).sum(1);det=b11*b22-b12*b12
def distances(q):
 U=q[:,None]-A
 t=(U*N).sum(2);p=U-t[:,:,None]*N
 pu=(p*B).sum(2);pv=(p*C).sum(2)
 k=(pu*b22-pv*b12)/det;l=(pv*b11-pu*b12)/det
 xyz=q[:,None,None]-T[None]
 ff=np.clip((xyz*E).sum(3)/Einv,0,1)
 m2=((xyz-ff[:,:, :,None]*E)**2).sum(3).min(2)
 return np.sqrt(np.where((k>=-1e-12)&(l>=-1e-12)&(k+l<=1+1e-12),np.minimum(t*t,m2),m2).min(1))
def winding(q):
 a,b,c=np.transpose(T[None]-q[:,None,None],(2,0,1,3))
 A,B,C=map(lambda x:np.linalg.norm(x,axis=2),(a,b,c))
 dot=lambda a,b:np.einsum('...i,...i->...',a,b)
 return np.arctan2(dot(np.cross(a,b),c),A*B*C+A*dot(b,c)+B*dot(c,a)+C*dot(a,b)).sum(1)/(2*np.pi)
def at(t): return piv+v+np.sin(t)*vel+(np.cos(t)-1)*delta
# Conservative analytic distance-motion certificate, independent of plane-circle
# event solving: positive finite distance at midpoint exceeding entire closed
# arc's maximum displacement proves that one inside witness cannot exit.
lo,hi=np.deg2rad([-104.70,134.28]); todo=[(lo,hi)]; done=[]; maxiter=5000
while todo and maxiter>0:
 l,r=todo.pop(); m0=(l+r)/2
 q=at(m0); pos=abs(winding(q))>.5
 ds=distances(q)
 bound=2*radius*np.sin((r-l)/4)
 score=np.where(pos,ds-bound,-np.inf)
 j=int(np.argmax(score))
 if score[j]>2e-8:
  done.append((l,r,int(indices[j]),float(score[j]),int(round(winding(q[j:j+1])[0]))))
 else:
  assert r-l>1e-6, (l,r,score[j])
  todo.extend(((l,m0),(m0,r)))
 maxiter-=1
assert not todo and done
sort=sorted(done)
assert sort[0][0]==lo and sort[-1][1]==hi and all(a[1]==b[0] for a,b in zip(sort,sort[1:]))
opening_thresholds={}
for d in (0,90,-90,-100,180):
 q=at(np.deg2rad(d)); w=np.rint(winding(q)).astype(int)
 opening_thresholds[d]={'nonzero':int(np.count_nonzero(w)),'degree_2':int((abs(w)==2).sum()),'max_certified_depth_mm':float(max(distances(q)[w!=0],default=0)*1000)}
source_pin={}
for i,nm in enumerate(('thumb.01.R','thumb.02.R')):
 modes=[m.ix[q] for q in ('thumb.01.R','thumb.02.R','thumb.03.R')[i:]]
 w=m.R[m.se][:,modes].sum(1); ids=m.se[w>0]
 c=np.array(m.per[nm]['held_origin']); unitoff=m.V[ids]-c
 ranks=np.linalg.matrix_rank(unitoff,tol=1e-6)
 assert ranks>=2
 pair=np.linalg.norm(np.cross(unitoff[:,None,:],unitoff[None,:,:]),axis=2).max()
 assert pair>.00001
 source_pin[nm]={'pair_noncollinear_cross_product_max_m2':float(pair),'count':len(ids),'rank':int(ranks),'ids':ids.tolist()}
print(json.dumps({'conservative_separate_method_continuous_unsafe_interval_deg':[-104.70,134.28],'arc_witness_intervals':len(done),
 'arc_min_margin_m':min(x[3] for x in done),'arc_winding_degree_two_witness_intervals':sum(abs(x[4])==2 for x in done),
 'arc_unique_vertex_count':len({x[2] for x in done}),'representative_certified_boundaries': [opening_thresholds[x] for x in [0,90,-90,-100,180]],
 'checks_by_degrees':opening_thresholds,'fixed_parent_seam_constraints':source_pin},indent=2,sort_keys=True))
