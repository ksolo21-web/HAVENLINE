import numpy as np, json
from pathlib import Path
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parent
D=np.load(p/'poses.npz');X=D['frames'];Y=np.load(p/'rejected-material-arrays.npz')['xyz']; R=D['rest']
_,weld=np.unique(np.rint(R/1e-6).astype('int64'),axis=0,return_inverse=True)
T=D['tri']
dom={k:D[k+'_tris'] for k in ['bootL','bootR','kneeL','kneeR','webL','webR','cloth']}
remote=[('bootL','bootR'),('kneeL','kneeR')]+[(a+s,'cloth') for a in ('boot','knee','web') for s in ('L','R')]
report=[]
for k,(u,v) in enumerate(zip(X,Y)):
 local={}
 for side,i in [('L',0),('R',1)]:
  center=D['joints'][i,1]
  m=(np.linalg.norm(R-center,axis=1)<.16)
  local[side]=T[m[T].all(1)]
 out=[]
 for Z in (u,v):
  pts=Z.tolist()
  bvh=lambda f:BVHTree.FromPolygons(pts,f.tolist(),all_triangles=True,epsilon=0.)
  trees={key:bvh(val) for key,val in dom.items()}
  rem={a+'-'+b:len(trees[a].overlap(trees[b])) for a,b in remote}
  self_output={}
  for side,f in local.items():
   b=bvh(f); W=weld[f]
   hits=[(i,j) for i,j in b.overlap(b) if i<j and not np.isin(W[i],W[j]).any()]
   self_output[side]={'pairs':len(hits),'first_pair_vertex_ids':[f[i].tolist() for i in hits[0]] if hits else None}
  out.append({'remote':rem,'local_nonadjacent':self_output})
 report.append({'t_ms':[0,75,150][k],'reference':out[0],'corrected':out[1]})
(p/'bvh.json').write_text(json.dumps(report,indent=2)+'\n')
