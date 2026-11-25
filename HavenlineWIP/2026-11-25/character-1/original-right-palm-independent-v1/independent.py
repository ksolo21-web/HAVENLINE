"""Exact reauthor closed-shell and UV QA, no raw output."""
import contextlib, io, json,sys
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.spatial import ConvexHull
sys.path.insert(0,str(Path(__file__).resolve().parent))
buf=io.StringIO()
with contextlib.redirect_stdout(buf): import reauthor as d
src=json.loads(buf.getvalue())
np.testing.assert_equal(src,json.loads(Path("../hvn-c1-owner-right-palm-reauthor-v1/result.json").read_text()))
def orient(rows):
 c=Counter((int(a),int(b)) for row in rows for a,b in zip(row,np.roll(row,-1)))
 assert max(c.values())==1
 return {(a,b) for a,b in c if (b,a) not in c}
assert orient(d.F[d.patch])==orient(d.ts)
protected=np.unique(np.r_[d.boundary_exact,d.locked,d.protected_extrema])
assert np.array_equal(d.new[protected],d.V[protected])
assert np.array_equal(d.new[d.F[d.retained]],d.V[d.F[d.retained]])
assert np.array_equal(d.U[:len(d.uv)],d.uv) and np.array_equal(d.expandedW[:len(d.W)],d.W)
support=[]
for axes in ((0,1),(0,2),(1,2)):
 orig=d.V[d.local][:,axes]; h=ConvexHull(orig)
 ids=d.local[h.vertices]
 assert not set(ids).intersection(d.in_volume)
 assert np.array_equal(d.new[ids],d.V[ids])
 assert set(ids).issubset(set(d.ts.ravel())|set(d.F[d.retained].ravel()))
 side=(d.new[d.newids][:,axes]@h.equations[:,:2].T+h.equations[:,2]).max()
 assert side<1e-8
 support.append({'axes':axes,'hull_vertices':len(ids),'max_signed_growth_m':float(side)})
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
tool=d.tool; lo=tool.min(1); hi=tool.max(1)
new=d.new[d.ts]; raw=d.V[d.F[d.retained]]
def bphase(g):
 return ((g.min(1)<=tool.max((0,1))).all(1)&(g.max(1)>=tool.min((0,1))).all(1))
def pairs(g, ids):
 results=[]
 for f,i in zip(g[bphase(g)],ids[bphase(g)]):
  for j in np.flatnonzero((lo<=f.max(0)+1e-10).all(1)&(hi>=f.min(0)-1e-10).all(1)):
   if cross(f,tool[j]):results.append([int(i),int(j)])
 return results
patch_pairs=pairs(new,np.arange(len(new))); retained_pairs=pairs(raw,d.retained)
assert not patch_pairs
# All new/retained candidate face pairs in original held body, excluding indexed contact.
over=(raw.min(1)<=new.max((0,1))).all(1)&(raw.max(1)>=new.min((0,1))).all(1)
gg=raw[over]; use=d.retained[over]; g0=gg.min(1);g1=gg.max(1)
join_fault=[]
for i,f in enumerate(new):
 for j in np.flatnonzero((g0<=f.max(0)).all(1)&(g1>=f.min(0)).all(1)):
  if not np.isin(d.ts[i],d.F[use[j]]).any() and cross(f,gg[j]):join_fault.append([i,int(use[j])])
assert not join_fault
# Independent solid-angle calculation at all new vertices and child centroids.
# Each node offsets IDs only; no source arrays emitted.
def winding(p):
 A,B,C=(tool-p).transpose(1,0,2)
 a,b,c=(np.linalg.norm(z,axis=1) for z in (A,B,C))
 dot=lambda X,Y:np.einsum("ij,ij->i",X,Y)
 return np.arctan2(dot(np.cross(A,B),C), a*b*c+c*dot(A,B)+a*dot(B,C)+b*dot(C,A)).sum()/(2*np.pi)
def maxima(pts):
 w=np.array([winding(x) for x in pts]); assert max(abs(w))<1e-8
 return {'outside':len(w),'max_abs_winding':float(max(abs(w)))}
controls=[int(i) for i in d.in_volume if abs(winding(d.V[i]))>.5]
assert len(controls)==len(d.in_volume)==7
screen=d.U[d.ts]; det=np.linalg.det(np.stack([screen[:,1]-screen[:,0],screen[:,2]-screen[:,0]],axis=1))
assert np.flatnonzero(det>1e-12).tolist()==[v['row'] for v in src['reversed_uv_child_faces']]
assert Counter(np.asarray(d.cutowner)[det>1e-12])=={0:14}
# The minimum is directional, not geometric surface minimum or zero-gap contact.
gaps=[float(w@((new[i]-d.origin)@d.n)-s) for i,w,s in d.cert]
assert .0000748 <= min(gaps) <= .0000752
print(json.dumps({'directed_perimeter_edges':len(orient(d.ts)),'protected_positions_equal':len(protected),'cardinal_support':support,'new_tool_crossing_pairs':patch_pairs,
 'original_retained_tool_crossings':retained_pairs,'retained_body_faces_tested_broadphase':int(over.sum()),'new_retained_strict_nonincident_crossings':join_fault,
 'new_vertex_containment':maxima(d.new[np.unique(d.ts)]),'child_centroid_containment':maxima(new.mean(1)),'historical_inside_controls':controls,
 'directional_standoff_mm':1000*min(gaps),'reversed_uv_rows':np.flatnonzero(det>1e-12).tolist(),'positive_bearing':src['assigned_facet_124_positive_bearing_rays'],
 'status':'REJECT UV / HOLD grip'},indent=2,sort_keys=True))
