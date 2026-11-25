import os
import numpy as np,json
from scipy.spatial import cKDTree
from pathlib import Path
P=Path(__file__).resolve().parent
A=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz')); B=np.load(P/'new-surface.npz')
src0=A['rest']; fc=A['tri'][B['original_face_ids']]
sel=np.unique(fc)
_,rep,w=np.unique(np.rint(src0[sel]/1e-6).astype('int64'),axis=0,return_inverse=True,return_index=True)
src=src0[sel[rep]]
sf=w[np.searchsorted(sel,fc)]
vc=(B['v']-A['source_origin'])*A['scale'];ff=B['tri']
def rays(f):
 e=np.sort(f[:,((0,1),(1,2),(2,0))].reshape(-1,2),axis=1)
 U,c=np.unique(e,axis=0,return_counts=True)
 return np.unique(U[c==1]),int(sum(c==1)),int(sum(c>2))
a,e,n=rays(sf);b,f,m=rays(ff)
g={}
for kind,U,V in [('original cut to new open rim',src[a],vc[b]),('new open rim to original cut',vc[b],src[a])]:
 d=cKDTree(V).query(U)[0]*1000
 g[kind]={'n':len(U),'p95_mm':float(np.quantile(d,.95)),'max_mm':float(d.max()),'exact_near_match_count':int(sum(d<.001))}
q={'boundaries':g,'raw_original_cut_edge_count':e,'candidate_cut_edge_count':f,'original_nonmanifold_overused':n,'new_nonmanifold_overused':m,'uv_coordinate_outside_0_1':int(np.sum((B['rest_uv']<0)|(B['rest_uv']>1))),'custom_split_normal_norm_error_max':float(abs(np.linalg.norm(B['projected_normals'],axis=1)-1).max())}
(P/'seam.json').write_text(json.dumps(q,indent=2));print(q)
