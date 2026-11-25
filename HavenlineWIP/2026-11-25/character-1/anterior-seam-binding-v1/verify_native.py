import os
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
A=Path(os.environ['C1_COLLAR_DATA']); S=(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
W=Path(os.environ['C1_ANTERIOR_WITNESS'])
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert h(A/'exact-assembled-surface.npz')=='8a7222ecdb893da3da09dba34ac3c56f1f95f7f6e7269f1e9d165eca0ef074f7'
assert h(A/'c1-right-boot-layered-assembly-proof.blend')=='45c67804f7c2b82f278fdfbf19aab6491ee69512f11b8db65cde158ed59eca27'
assert h(S)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
assert h(W/'one-ring.json')=='254818c80690b18ac42d8a0f3e0dd0d27505c86181f9860b0fb9f0a1f7bbef84'
s=np.load(S);pre=np.load(A/'exact-assembled-surface.npz');T=pre['tri'];v=pre['v']; C=s['source_origin']; scale=float(s['scale'])
M=s['bones']; mask=np.zeros(len(v),bool)
def vec(items,prop,cols,dt=np.float32):
 a=np.empty(len(items)*cols,dtype=dt); items.foreach_get(prop,a);return a.reshape(-1,cols)
bpy.ops.wm.open_mainfile(filepath=str(A/'c1-right-boot-layered-assembly-proof.blend'))
ob=bpy.data.objects['Right boot visible repaired leather rest proof'];tr=bpy.data.objects['Manual upper-boot lapped trim panel rigid to right shin'];arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');U=bpy.context.view_layer.update
source=np.array([tuple(e.vertices) for e in ob.data.polygons]);assert np.array_equal(source,T)
T1=np.array([tuple(e.vertices) for e in tr.data.polygons])
norms0=vec(ob.data.corner_normals,'vector',3);uv0=vec(ob.data.uv_layers.active.data,'uv',2);co0=vec(ob.data.vertices,'co',3)
tex0=[hashlib.sha256(p.image.packed_file.data).hexdigest() for p in ob.data.materials[0].node_tree.nodes if getattr(p,'image',None) and p.image.packed_file]
names=('thigh.R','shin.R','foot.R','toe.R');groups=[ob.vertex_groups[k] for k in names]
assert int(ob.data.vertices.__len__())==len(v)
def wrows():
 p=np.zeros((len(v),4))
 for j,vg in enumerate(ob.data.vertices):
  for item in vg.groups:
   for k,gg in enumerate(groups):
    if item.group==gg.index:p[j,k]=item.weight
 return p
stock=wrows()
source_ids=np.array([13484,13613,14018,14078])
assert (stock[source_ids,2]>0).all() and (stock[source_ids,2]<.003).all() and not stock[source_ids,[0,0,0,0]].any()
keys=np.rint(v/1e-6).astype(np.int64); matches=[np.flatnonzero((keys==keys[i]).all(1)) for i in source_ids]
for i,raw in zip(source_ids,matches):
 assert np.max(abs(stock[i]-stock[raw]))<=1e-7
active=np.unique(np.concatenate(matches));mask[active]=True
assert len(active)>=4
def set_pose(i):
 for b in arm.pose.bones:b.matrix_basis=Matrix.Identity(4)
 U()
 if i>=0:
  for k,m in zip(names,M[i,1]):
   b=arm.pose.bones[k];b.matrix=Matrix(m.tolist())@b.bone.matrix_local
   U()
def pts(q):
 return (vec(q.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices,'co',3)-C)*scale
def get(i):
 set_pose(i)
 actual=np.array([np.array(arm.pose.bones[n].matrix) for n in names])
 return pts(ob),pts(tr),actual
before=[get(i) for i in (-1,0,1,2)]
for i in active:
 groups[2].remove([int(i)]);groups[1].add([int(i)],1.0,'REPLACE')
after=[get(i) for i in (-1,0,1,2)]
new=wrows()
assert np.array_equal(new[~mask],stock[~mask]) and np.array_equal(new[mask],np.tile([0.,1.,0.,0.],(len(active),1)))
set_pose(-1)
assert np.array_equal(co0,vec(ob.data.vertices,'co',3))
assert np.array_equal(uv0,vec(ob.data.uv_layers.active.data,'uv',2))
assert np.array_equal(norms0,vec(ob.data.corner_normals,'vector',3))
assert tex0==[hashlib.sha256(p.image.packed_file.data).hexdigest() for p in ob.data.materials[0].node_tree.nodes if getattr(p,'image',None) and p.image.packed_file]
for a,b in zip(before,after):assert np.array_equal(a[2],b[2]) and np.array_equal(a[1],b[1])
zone=np.isin(T,active).any(1)
src_one=json.loads((W/'one-ring.json').read_text())['neighbor_faces']
edges=np.unique(np.sort(T[:,((0,1),(1,2),(2,0))].reshape(-1,2),axis=1),axis=0)
e0=np.linalg.norm(v[edges[:,1]]-v[edges[:,0]],axis=1)
valid=e0>.0008;local=valid&mask[edges].any(1)
def vtree(V,T):return BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
def read(U,V):
 b=vtree(U,T);q=vtree(V,T1)
 return {tuple(sorted((int(i),int(j)))) for i,j in b.overlap(b) if i<j and not np.isin(T[i],T[j]).any()},len(b.overlap(q))
def cross(x):
 p=x[T];return np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
cases=[]
for i,(a,b) in enumerate(zip(before,after)):
 X,tr0,m0=a;Y,tr1,m1=b;other=np.linalg.norm(Y[~mask]-X[~mask],axis=1)
 assert np.max(other)==0
 p,q=read(X,tr0);r,z=read(Y,tr1)
 newly=r-p; gone=p-r
 rr=lambda v:np.linalg.norm(v[edges[:,1]]-v[edges[:,0]],axis=1)/np.maximum(e0,1e-19)
 rx,ry=rr(X),rr(Y)
 N=cross(X); P0=cross(Y); dn=(N*N).sum(1)
 sig=(N*P0).sum(1)/np.maximum(dn,1e-25)
 rec={'t_ms':[-1,0,75,150][i],'shell_nonadjacent_before_after':[len(p),len(r)],'pair_26992_27689_before_after':[(26992,27689) in q for q in (p,r)],'same_one_ring_before_after':[sorted([q for q in s if max(q) in src_one and min(q) in src_one]) for s in (p,r)], 'trim_contact_before_after':[q,z],'new_pairs':sorted(newly),'gone_pairs':sorted(gone),'local_edge_minmax_before_after':[[float(t[local].min()),float(t[local].max())] for t in (rx,ry)],'bad_edges_full_before_after':[int(sum(valid&((t<.5)|(t>2)))) for t in (rx,ry)],'new_affected_signed_under_point1':int(sum(zone&(sig<.1)&(dn>1e-25))),'new_affected_nonpositive':int(sum(zone&(sig<=0)&(dn>1e-25))),'protected_position_max_delta_mm':float(other.max()*1000),'max_modified_pose_delta_mm':float(np.linalg.norm(Y-X,axis=1).max()*1000)}
 cases.append(rec);print(rec,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'c1-right-anterior-seam-binding-proof.blend'),compress=True)
np.savez_compressed(P/'exact-native-witness.npz',v=v,tri=T,i=active,before=np.stack([k[0] for k in before]),after=np.stack([k[0] for k in after]),affected_faces=np.flatnonzero(zone),old=stock[active],new=new[active])
out={'exact_rows':active.tolist(),'alias_sets':[x.tolist() for x in matches],'actual_rest_uv_normal_material_and_geometry_unchanged':True,'native_trim_and_all_other_vertices_bitwise_unmoved':True,'cases':cases}
(P/'native.json').write_text(json.dumps(out,indent=2))
