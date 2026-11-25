import contextlib,io,json
from pathlib import Path
import numpy as np
buf=io.StringIO()
with contextlib.redirect_stdout(buf): import left as d
assert buf.getvalue()==Path('../hvn-c1-owner-left-band-preflight-v1/result.json').read_text()
F,V,P,tool=d.F,d.V,d.P,d.tool
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
assert all(cross(V[F[i]],tool[j]) for i,j in d.hold)
a,b=416457,416910
assert np.array_equal(P[a],P[b]) and np.array_equal(V[a],V[b])
assert (np.flatnonzero((P==P[a]).all(1))==[a,b]).all() and not np.array_equal(d.uv[a],d.uv[b])
refs=np.flatnonzero(np.isin(F,[a,b]).any(1)); assert len(refs)==6 and d.own[F[refs]].all()
assert not np.isin(d.E,[a,b]).any() and not np.isin(d.web,[a,b]).any()
def ray_hits(o,u,g):
 A=g[:,0]; B=g[:,1]-A; C=g[:,2]-A
 H=np.cross(u,C); den=np.einsum('ij,ij->i',B,H); good=abs(den)>1e-13
 safe=np.where(good,den,1.); q=o-A; z=np.cross(q,B)
 x=np.einsum('ij,ij->i',q,H)/safe; y=z@u/safe; t=np.einsum('ij,ij->i',C,z)/safe
 return t[good & (x>1e-9)&(y>1e-9)&(x+y<1-1e-9)&(t>1e-8)]
norm=tnormal(tool[277])
assert abs(np.linalg.norm(d.probe-V[a]) - .001005783)<1e-9
dirs=np.array([[1.,.573,.317],[-.271,.811,1.],[.413,-1.,.642]])
inside=[len(ray_hits(V[a],u,tool)) for u in dirs]
outside=[len(ray_hits(d.probe,u,tool)) for u in dirs]
assert all(x%2==1 for x in inside) and all(x%2==0 for x in outside)
def segment_hits(a,b,g):
 return ray_hits(a,b-a,g)
archive=[(tuple(k['vertices']),[j for j,t in k['strict_hits']]) for k in d.hist[-1]['crossing_boundary']]
for (a0,b0),j in archive:
 assert len(segment_hits(V[a0],V[b0],tool[j]))==1
localfaces=np.flatnonzero(d.own[F].all(1)&~np.isin(F,[a,b]).any(1)); shell=V[F[localfaces]]
vis=[]
for u in np.r_[dirs,-dirs,[[1.,1.,1.],[-1.,1.,-1.],[1.,-1.,-1.],[-1.,-1.,1.]]]:
 u=u/np.linalg.norm(u)
 hits=[ray_hits(x,u,shell) for x in (V[a],d.probe)]
 vis.append([len(t) for t in hits])
# Analytic replay of just the six incident faces around a hypothetical common point.
# No original coordinate rows are mutated; measure graph consequences, not a proposal.
native=V[F[refs]]; moved=np.where(np.isin(F[refs],[a,b])[:,:,None],d.probe,native)
def toolpairs(faces):
 lo=tool.min(1); hi=tool.max(1); q=[]
 for i,f in zip(refs,faces):
  for j in np.flatnonzero((lo<=f.max(0)).all(1)&(hi>=f.min(0)).all(1)):
   if cross(f,tool[j]):q.append([int(i),int(j)])
 return q
born=toolpairs(native); shifted=toolpairs(moved)
print(json.dumps({'original_pairs_independent':len(d.hold),'strict_candidate_edges':len(archive),'exact_aliases':[a,b],
 'original_tool_ray_parities':inside,'analytical_outside_ray_parities':outside,
 'oblique_distal_other_shell_RayHitCounts_original_and_probe':vis,
 'all_incident_faces':refs.tolist(),'incident_pairs_original':born,'incident_pairs_analytical_common_point_only':shifted,
 'earliest_clearance_only_test':'seam-coincident positional exploration across both indexed charts, preserve distinct UV and all cuff/web/outside rows'} ,indent=2))
