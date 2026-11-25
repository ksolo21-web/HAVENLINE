import os
import numpy as np, json
from pathlib import Path
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parent
D=np.load(Path(os.environ['C1_KNEE_DATA'])/'poses.npz');X=D['frames'];Y=np.load(p/'numerical-poses-not-approved.npz')['xyz']; R=D['rest']
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
# Actual same-source signed contact set, read only. Uses exactly the prior
# dense group's own foot/toe orientation and original lowest 40mm partition.
clean={}
for side,idx in [('L',0),('R',1)]:
 F=D['tri']; ref=D['rest'];w=D['weights'][:,idx*4+2:idx*4+4].sum(1)
 sg=1 if side=='L' else -1;z=ref[:,2]
 boot=(ref[:,0]*sg>.025)&(z<.38)&(w>.35)
 f=-ref[:,1]; lower=boot&(z<.040); quant=np.quantile(f[lower],[.32,.68]);hh=(f<=quant[0]) if side=='L' else (f>=quant[1])
 faces=F[(lower&hh)[F].all(1)]
 assert len(faces)>50
 rr=[]
 for u,v in zip(X,Y):
  def read(x):
   v=x[faces]
   return np.flatnonzero(((v[:,:,2]>=-.001)&(v[:,:,2]<=.002)).all(1))
  a=read(u);b=read(v)
  rr.append({'old_new_face_counts':[len(a),len(b)],'set_exact':bool(np.array_equal(a,b)),'matching_face_vertices_exact':bool(np.array_equal(u[faces[a]],v[faces[a]])), 'original_candidate_low_mm':[1000*float(q[boot,2].min()) for q in (u,v)]})
 clean[side]=rr
(p/'contact-verification.json').write_text(json.dumps(clean,indent=2))
