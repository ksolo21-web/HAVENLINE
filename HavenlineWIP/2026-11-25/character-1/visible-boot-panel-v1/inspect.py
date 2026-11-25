import os
import json,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
A=np.load(Path(os.environ['C1_VISIBLE_BOOT_DATA'])/'new-surface.npz')
B=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz'))
V=(A['v']-B['source_origin'])*B['scale'];T=A['tri'];U=A['rest_uv'].reshape(len(T),3,2)
b=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
pairs=[(i,j) for i,j in b.overlap(b) if i<j and not np.isin(T[i],T[j]).any()]
all_faces=set(i for p in pairs for i in p)
out={'n':len(pairs),'pairs':[]}
for i,j in pairs:
 m=V[T[[i,j]]].mean((0,1))
 out['pairs'].append(dict(faces=[i,j],region_m=m.tolist(),max_paired_distance_mm=float(np.linalg.norm(V[T[i]].mean(0)-V[T[j]].mean(0))*1000),v=T[[i,j]].tolist(),uv=U[[i,j]].tolist()))
(P/'original-neutral.json').write_text(json.dumps(out,indent=2))
print('neutral count',len(pairs),len(all_faces),'height range',np.ptp([x['region_m'][2] for x in out['pairs']])*1000,'pairs',pairs,flush=True)
