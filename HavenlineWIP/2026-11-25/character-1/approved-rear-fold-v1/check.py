import os
import bpy,numpy as np,json
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
from scipy.spatial.transform import Rotation
from pathlib import Path
P=Path(__file__).resolve().parent
A=np.load(P/'new-rear-panel.npz');S=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz'))
exact0=np.load((Path(os.environ['C1_ANTERIOR_BIND_DATA'])/'exact-native-witness.npz'))
src=np.load((Path(os.environ['C1_COLLAR_DATA'])/'exact-assembled-surface.npz'))
assert json.loads((P/'silhouette.json').read_text())['gate'] is True
bpy.ops.wm.open_mainfile(filepath=str(P/'c1-visible-rear-knee-redesign-proof.blend'))
o=bpy.data.objects['Right boot new visible rear fold candidate'];b=bpy.data.objects['Manual upper-boot lapped trim panel rigid to right shin']
arm=next(ob for ob in bpy.context.scene.objects if ob.type=='ARMATURE')
U=bpy.context.view_layer.update
T=A['tri'];V=A['v']; w=A['w'];S0=float(S['scale']); O=S['source_origin']
assert len(src['v'])<len(V) and np.array_equal(src['v'],V[:len(src['v'])])
assert np.array_equal(A['w'][exact0['i']],np.tile([0.,1.,0.,0.],(4,1)))
trimT=np.array([tuple(p.vertices) for p in b.data.polygons]);assert len(T)==len(o.data.polygons)
old=A['old_kept']; panel=old<0; bound=A['boundary']
newv=np.arange(len(src['v']),len(V))
roi=np.isin(T,np.r_[newv,bound]).any(1)
E=np.unique(np.sort(T[:,((0,1),(1,2),(2,0))].reshape(-1,2),axis=1),axis=0)
n=np.linalg.norm(V[E[:,1]]-V[E[:,0]],axis=1);ed=(n>.0008)&np.isin(E,np.r_[newv,bound]).any(1)
def pts(ob):
 vs=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices
 x=np.empty((len(vs),3),np.float32);vs.foreach_get('co',x.ravel());return (x-O)*S0
def bvh(x,T):
 return BVHTree.FromPolygons(x.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
def audit(x,y):
 a=bvh(x,T);c=bvh(y,trimT)
 pairs=[(int(i),int(j)) for i,j in a.overlap(a) if i<j and not np.isin(T[i],T[j]).any()]
 return pairs,len(a.overlap(c))
def cross(X):
 tr=X[T];return np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0])
def boundary_degree(T):
 a=T[:,((0,1),(1,2),(2,0))].reshape(-1,2); b=np.sort(a,axis=1)
 _,i,c=np.unique(b,axis=0,return_inverse=True,return_counts=True)
 bal=np.bincount(i,weights=np.where(a[:,0]>a[:,1],1,-1),minlength=len(c))
 return [int(sum(c==1)),int(sum(c>2)),int(sum((c==2)&(bal!=0)))]
v=pts(o);t=pts(b);pair,r=audit(v,t)
rgb=lambda x: sorted([p.image.packed_file.data[:20].hex() for p in x.data.materials[0].node_tree.nodes if getattr(p,'image',None) and p.image.packed_file])
nd=boundary_degree(T)
uv=np.array([a.uv[:] for a in o.data.uv_layers.active.data])
qa={'neutral':{'native_shape_snapshot_mm':float(np.linalg.norm(v-V,axis=1).max()*1000),'shell_nonadjacent_pairs':pair,'trim_touch':r,'base_boundary_overused_reversed':nd,'uv_legal':bool(((uv>=0)&(uv<=1)).all()),'same_packed_pbr_material':o.data.materials[0]==b.data.materials[0], 'toe_alive_rows':int(sum(w[:,3]>.2))},'keys':[]}
good=not pair and r==0 and nd==[162,0,0] and qa['neutral']['uv_legal']
weights=w[T].mean(1).argmax(1)
rest=cross(V);norm=(rest*rest).sum(1)
ge=np.flatnonzero(old>=0)
keep=np.array([i for i in range(len(src['v'])) if i not in set(A['boundary'].tolist()) and not np.isin(i,T[roi]).any()])
for k in range(3):
 if not good:break
 for name,mat in zip(('thigh.R','shin.R','foot.R','toe.R'),S['bones'][k,1]):
  pb=arm.pose.bones[name];pb.matrix=Matrix(mat.tolist())@pb.bone.matrix_local;U()
 x=pts(o);q,t=audit(x,pts(b))
 e=np.linalg.norm(x[E[ed,1]]-x[E[ed,0]],axis=1)/n[ed]
 ro=Rotation.from_matrix(S['bones'][k,1,:,:3,:3]).as_matrix()
 orient=np.einsum('nij,nj->ni',ro[weights],rest)
 sig=np.sum(cross(x)*orient,axis=1)/np.maximum(norm,1e-24)
 local=[(i,j) for i,j in q if roi[i] or roi[j]]
 priorT=src['tri']
 sole=(src['v'][:,2]<=.075)
 data={'ms':[0,75,150][k],'whole_shell_pairs':len(q),'local_shell_pairs':len(local),'local_pair_ids':local[:60],'trim_pair_count':t,'local_edge_num_bad':int(sum((e<.5)|(e>2.))),'scoped_edge_minmax':[float(e.min()),float(e.max())],'local_area_under_point1':int(sum(roi&(sig<.1)&(norm>1e-22))),'local_area_reversed':int(sum(roi&(sig<=0)&(norm>1e-22))),'absolute_outsole_unchanged':bool(np.array_equal(x[:len(sole)][sole],exact0['after'][k+1][sole])),'existing_anterior_vertices_exact':bool(np.array_equal(x[exact0['i']],exact0['after'][k+1][exact0['i']])),'boot_min_mm':float(x[:len(sole)][sole,2].min()*1000)}
 qa['keys'].append(data)
 good=bool(not local and not t and data['local_edge_num_bad']==0 and data['local_area_under_point1']==0)
(P/'qa.json').write_text(json.dumps(qa,indent=2));print(qa,flush=True)
