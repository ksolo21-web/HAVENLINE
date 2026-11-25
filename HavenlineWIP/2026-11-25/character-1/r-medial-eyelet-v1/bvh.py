import os
from pathlib import Path
import json,numpy as np
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parent
A=np.load(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
D=np.load(p/'internal-design-diagnostic.npz')
R=A['rest']; T=A['tri']; parts=D['local_part']
_,w=np.unique(np.rint(R/1e-6).astype('int64'),axis=0,return_inverse=True)
assert set(np.flatnonzero(np.isin(w,w[parts])))==set(parts)
center=R[parts].mean(0)
m=np.linalg.norm(R-center,axis=1) < .026
l=T[m[T].all(1)]
Remote=[('bootL','bootR'),('kneeL','kneeR')]+[(a+s,'cloth') for a in ('boot','knee','web') for s in ('L','R')]
def tree(V,F):
 return BVHTree.FromPolygons(V.tolist(),F.tolist(),all_triangles=True,epsilon=0.0)
def inside_self(b,inds):
 return sum(1 for x,y in b.overlap(b) if x<y and not np.isin(inds[x],inds[y]).any())
def witness(V,eye,back):
 vis=tree(V,l)
 e=tree(eye,D['mount_tri']); a=tree(back,D['backing_tri'])
 return {'visible_local_self_nonadjacent':inside_self(vis,w[l]),
 'hidden_metal_self_nonadjacent':inside_self(e,D['mount_tri']),
 'hidden_backing_self_nonadjacent':inside_self(a,D['backing_tri']),
 'hidden_metal_visible_pairs':len(e.overlap(vis)),'hidden_backing_visible_pairs':len(a.overlap(vis)),
 'metal_to_backing_exact_shared_ring_m':float(np.linalg.norm(eye[24:48]-back[:24],axis=1).max())}
out={'neutral':witness(R,D['mount_rest'],D['backing_rest']),'poses':[]}
for k,raw in enumerate(A['frames']):
 new=raw.astype(float);new[parts]=D['posed_visible_patches'][k]
 B={b:tree(new,A[b+'_tris']) for b in {q for keys in Remote for q in keys}}
 item=witness(new,D['mount_pose'][k],D['backing_pose'][k])
 item['source_visible_local_self_nonadjacent']=inside_self(tree(raw,l),w[l])
 item['remote_exact_pairs']={b+'-'+a:len(B[b].overlap(B[a])) for a,b in Remote}
 out['poses'].append(item)
(p/'bvh.json').write_text(json.dumps(out,indent=2)+'\n')
