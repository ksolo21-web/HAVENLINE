"""Supplemental QA. Invoke via attached runner; no materialized arrays."""
import contextlib, io, json, runpy
from collections import Counter
from pathlib import Path
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
 d=runpy.run_path(str(Path(__file__).with_name('sheet.py')))
globals().update({k:d[k] for k in ("P","F","W","uv","V","tool","pt","alt","tris","patch","parents","provenance","outer","fixed","boundary","report","locked")})
def edgecounts(rows):
 c=Counter()
 for tri in rows:
  for u,v in zip(tri,np.roll(tri,-1)): c[(int(u),int(v))]+=1
 return c
def boundary_set(rows):
 c=edgecounts(rows)
 assert all(n==1 for n in c.values())
 return {(i,j) for i,j in c if (j,i) not in c}
assert boundary_set(F[patch])==boundary_set(tris)
assert set(np.unique(tris)) & set(np.unique(F[outer])) <= fixed
fix=list(sorted(fixed)); assert np.array_equal(alt[fix],V[fix])
assert np.array_equal(alt[F[outer]],V[F[outer]])
assert np.array_equal(alt[locked],V[locked])
for idx,(src,weights) in provenance.items():
 assert (weights>0).all() and abs(sum(weights)-1)<1e-15
 u=weights@uv[src]; w=weights@W[src]
 assert np.isfinite(u).all() and np.isfinite(w).all()
 assert np.array_equal(u,d['uvnew'][idx]) and np.array_equal(w,d['weightnew'][idx])
assert np.array_equal(d['uvnew'][:len(uv)],uv) and np.array_equal(d['weightnew'][:len(W)],W)
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
lo=tool.min(1); hi=tool.max(1)
def pairs(gg,pp):
 out=set()
 for f,id in zip(gg,pp):
  for j in np.flatnonzero((lo<=f.max(0)+1e-10).all(1)&(hi>=f.min(0)-1e-10).all(1)):
   if cross(f,tool[j]):out.add((int(id),int(j)))
 return out
original,identity,trial=(pairs(g,p) for g,p in ((V[F[patch]],patch),(pt[tris],parents),(alt[tris],parents)))
assert original==identity
# Separate independent angular classification via normalized cross vectors.
reverse=[]
for i,(a,b) in enumerate(zip(pt[tris],alt[tris])):
 if np.dot(tnormal(a),tnormal(b))<=0:reverse.append([int(i), int(parents[i])])
def support_segment(e,f):
 ns=tnormal(f); a,b=V[list(e)]; da,db=(a-f[0])@ns,(b-f[0])@ns
 if da*db>=-1e-18:return False
 p=a+(b-a)*da/(da-db)
 c=np.cross(np.roll(f,-1,axis=0)-f,p-f)@ns
 return {'t':float(da/(da-db)), 'minimum_signed_triangle_edge_mm':float(min(c/np.linalg.norm(np.roll(f,-1,axis=0)-f,axis=1))*1000)} if (c>1e-11).all() else False
tested=[]
for e in sorted(boundary_set(F[patch])):
 for j in [124,125,127]:
  hit=support_segment(e,tool[j]);
  if hit: tested.append({'edge':e,'facet':j,'inside':hit,'permanent_source_constraints':[int(k) in set(locked) for k in e],
   'outside_incident_faces': [int(f) for f in outer[np.isin(F[outer],e).sum(1)==2]],
   'source_patch_incident_faces': [int(f) for f in patch[np.isin(F[patch],e).sum(1)==2]]})
print(json.dumps({'exact_directed_perimeter_edges':len(boundary_set(tris)), 'fixed_perimeter_vertices':len(boundary),
 'verified_fixed_total':len(fix),'verified_barycentric_uv_weight_rows':len(provenance),
 'pairs_original':len(original),'pairs_identity':len(identity),'pairs_trial':len(trial),
 'added_pairs':sorted(trial-original),'reversal_child_source':reverse,
 'outer_boundary_edge_strict_penetrations_124_125_127':tested,
 'status':'HOLD; exact current perimeter itself penetrates the shaft and cannot be held fixed wholesale'}, sort_keys=True,indent=2))
