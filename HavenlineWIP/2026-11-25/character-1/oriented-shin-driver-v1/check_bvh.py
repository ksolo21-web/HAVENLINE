from pathlib import Path
import numpy as np,json
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parent
D=np.load(p.parent/'hvn-l1-c1-stride-broad-repair-v1'/'pose-inputs.npz')
V=np.load(p/'diagnostic-arrays.npz')['xyz']; base=D['xyz']; rest=D['rest']
_,W=np.unique(np.rint(rest/1e-6).astype('int64'),axis=0,return_inverse=True)
report=[]
def tr(x,t):return BVHTree.FromPolygons(x.tolist(),t.tolist(),all_triangles=True,epsilon=0.0)
for i,(x,y) in enumerate(zip(base,V)):
 out={}
 for key,g in [('stock',x),('prototype_bilateral',y)]:
  l,r,c=(tr(g,D[k]) for k in ('lboot','rboot','coat'))
  out[key]={}
  for side,a in [('L',l),('R',r)]:
   maps=W[D['lboot' if side=='L' else 'rboot']]
   out[key][side+'_nonadj']=sum(1 for i,j in a.overlap(a) if i<j and not np.isin(maps[i],maps[j]).any())
  out[key]['LR_Lcoat_Rcoat']=[len(a.overlap(b)) for a,b in [(l,r),(l,c),(r,c)]]
 for s in ('L','R'):
  ix=D['boot'+s];floor=float(rest[ix,2].min())
  assert np.array_equal(x[ix[rest[ix,2]<floor+.03]],y[ix[rest[ix,2]<floor+.03]])
  assert np.array_equal(x[D['phase'+s]],y[D['phase'+s]])
 report.append(out)
(p/'bvh-report.json').write_text(json.dumps(report,indent=2)+'\n')
