"""Re-extract the exact held coordinates and test the approved face's own perimeter."""
from pathlib import Path
import hashlib, json
p=Path(__file__).resolve().parent
def verify(name,expected):
 d=p.parent/name
 sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
 assert sha(d/'SHA256SUMS')==expected
 for line in (d/'SHA256SUMS').read_text().splitlines():
  h,f=line.split(maxsplit=1);assert sha(d/f)==h
 return d
baseline=verify('hvn-l1-c1-rear-pose-corrective-hold-v1','3f68050e897f1bcae4288898bac7e7c64d467f3101fed9efbc8fe7cfdb7299be')
review=verify('hvn-l1-c1-rear-fixed-boundary-independent-v1','977f3a2dd16eaa9198583943fb6c0936450e5da7fd8d9fa7575d508011de0165')
c={'__file__':str(baseline/'audit.py')}
exec(compile((baseline/'audit.py').read_text().split('# Precisely separate analytic operator audit')[0],str(baseline/'audit.py'),'exec'),c)
np=c['np'];T=c['T']; V=[c['neutral'],c['held']]
source=json.loads((review/'result.json').read_text())['results']
panel=28093; obstacles=[42401,28305]; baseface=T[panel]
edges=[(int(a),int(b)) for a,b in zip(baseface,np.roll(baseface,-1))]
rings={f'{a}:{b}':np.flatnonzero(np.isin(T,a).any(1)&np.isin(T,b).any(1)).tolist() for a,b in edges}
assert all(len(x)==2 and panel in x for x in rings.values())
def test(X,edge,f):
 a,b=X[list(edge)].astype(float); Q=X[T[f]].astype(float)
 n=np.cross(Q[1]-Q[0],Q[2]-Q[0]);n/=np.linalg.norm(n)
 d=(np.stack([a,b])-Q[0])@n
 out={'ordered_edge_source_indices':list(edge),'fixed_face':f,'fixed_face_vertex_indices':T[f].tolist(),
      'endpoint_distances_mm':(1000*d).tolist(),'strict_crossing':False}
 if min(d)<-1e-8<1e-8<max(d):
  t=d[0]/(d[0]-d[1]); q=a+t*(b-a)
  u,v=np.linalg.lstsq((Q[1:]-Q[0]).T,q-Q[0],rcond=None)[0]
  r=np.array([1-u-v,u,v])
  out.update(t=float(t),point_m=q.tolist(),bary=r.tolist(),strict_crossing=bool(1e-6<t<1-1e-6 and min(r)>1e-6))
  assert np.linalg.norm(r@Q-q)<1e-12
 return out
results={}
for label,x in zip(('bind','held'),V):
 for k in obstacles:
  S=source[label]['triangle_pairs'][f'{panel}:{k}']
  assert np.array_equal(x[baseface],S['triangle_a']) and np.array_equal(x[T[k]],S['triangle_b'])
 results[label]=[test(x,e,f) for e in edges for f in obstacles]
hits=[r for r in results['held'] if r['strict_crossing']]
assert len(hits)==2 and not any(r['strict_crossing'] for r in results['bind'])
assert {x['fixed_face'] for x in hits}==set(obstacles) and all(len(set(x['ordered_edge_source_indices'])&set(x['fixed_face_vertex_indices']))==0 for x in hits)
neighbor=sorted(set(sum(rings.values(),[]))|set(obstacles)|{27920})
stitch=[13771,14452]
assert set(stitch)<=set(T[42401])
np.savez_compressed(p/'exact_panel_boundary_counterexample.npz', face_ids=neighbor,vertex_ids=T[neighbor],neutral_m=V[0][T[neighbor]],held_0ms_m=V[1][T[neighbor]],fixed_stitch_vertex_ids=stitch,exact_stitch_neutral_m=V[0][stitch],exact_stitch_held_0ms_m=V[1][stitch])
out={'status':'HOLD_FIXED_28093_PERIMETER_EDGES_PIERCE_TWO_IMMUTABLE_FACES','face':panel,'boundary_vertices':baseface.tolist(),'edge_incident_faces':rings,'immutable_stitch_vertices':stitch,'poses':results,'minimal_obstructions':[dict(r,**{'incident_faces':rings[':'.join(map(str,r['ordered_edge_source_indices']))]}) for r in hits], 'unchanged_strict_triangle_pair_spans_mm':{k:source['held']['triangle_pairs'][k]['strict_overlap_span_mm'] for k in ('28093:42401','28093:28305','27920:42401')},'disposition':'Any interior-only repair retains these straight, fixed boundary segments; each still intersects the strict interior of an unchanged obstacle. No candidate justified; no silhouette or clearance approval, no 75/150ms follow-on.'}
(p/'result.json').write_text(json.dumps(out,indent=2)+'\n')
for r in hits: print(r)
