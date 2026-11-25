import os
import bpy, numpy as np, hashlib, math, json
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parent
hair=Path(os.environ['C1_EXACT_GLB'])
file=Path(os.environ['C1_EXACT_BLEND'])
prior=(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(hair)=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
assert h(file)=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
assert h(prior)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
A=np.load(prior); C=A['source_origin']; S=float(A['scale'])
bpy.ops.wm.open_mainfile(filepath=str(file))
owner=next(o for o in bpy.context.scene.objects if o.type=='MESH')
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
assert len(rig.pose.bones)==52 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
def coords(items,k,n,ty=np.float32):
 x=np.empty(len(items)*n,dtype=ty);items.foreach_get(k,x);return x.reshape(-1,n)
m=owner.data;m.calc_loop_triangles()
P0=coords(m.vertices,'co',3).astype(float); T=coords(m.loop_triangles,'vertices',3,np.int32)
L=coords(m.loop_triangles,'loops',3,np.int32)
uv=coords(m.uv_layers.active.data,'uv',2);nrm=coords(m.corner_normals,'vector',3)
V=(P0-C)*S
assert np.max(np.abs(V-A['rest']))<2e-7 and np.array_equal(T,A['tri'])
w=A['weights'][:,4:8]
select=(V[:,0]<-.026)&(V[:,2]<.505)&(w.sum(1)>.82)
ti=np.flatnonzero(select[T].all(1)); srcTri=T[ti]; verts,loc=np.unique(srcTri,return_inverse=True)
Q=P0[verts]; loc=loc.reshape(-1,3); assert len(ti)>30000
qm=np.rint(Q/1e-6).astype(np.int64)
_,ri,weldid=np.unique(qm,axis=0,return_index=True,return_inverse=True)
pre=Q[ri]; poly=weldid[loc]; assert np.all(np.diff(np.sort(poly,axis=1),axis=1)>0)
# Welded new mesh baseline, not directly exposing original raw stream. Exact
# open material cutoff fixed in the visible collar. Record cut boundary.
edge=np.sort(poly[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1)
uu,ct=np.unique(edge,axis=0,return_counts=True)
border=np.unique(uu[ct==1]); pin=np.zeros(len(pre),bool);pin[border]=True
# Sculpt silhouette anchors in extreme sole and cap toe regions. Intentional
# strong weighting: (deep treads and open cut) preserved by denser source islands.
pn=(pre-C)*S
lock=pin|(pn[:,2]<.024)
work=bpy.data.meshes.new('C1 right boot replacement WIP')
work.from_pydata(pre.tolist(),[],poly.tolist());work.update()
obj=bpy.data.objects.new('Right boot-shin visible topology proof',work)
bpy.context.collection.objects.link(obj)
vgrp=obj.vertex_groups.new(name='Preserve cut and low sole')
for i in np.flatnonzero(lock):vgrp.add([int(i)],1.,'REPLACE')
mod=obj.modifiers.new('Local right-only silhouette protected topology rewrite','DECIMATE');mod.decimate_type='COLLAPSE';mod.ratio=.34
mod.vertex_group=vgrp.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1.
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
bpy.ops.object.modifier_apply(modifier=mod.name)
work=obj.data; work.calc_loop_triangles()
cf=coords(work.loop_triangles,'vertices',3,np.int32)
CV=coords(work.vertices,'co',3).astype(float)
# Explicitly independent new topology and material surface projection.
bvh=BVHTree.FromPolygons(Q.tolist(),loc.tolist(),all_triangles=True,epsilon=0.)
def bary(pt,abc):
 aa,bb,cc=abc; b=bb-aa; c=cc-aa; a=pt-aa
 m=np.array([[b@b,b@c],[b@c,c@c]])
 y=np.linalg.solve(m,np.array([a@b,a@c]))
 return np.clip(np.array([1-y.sum(),y[0],y[1]]),0,1)
uvdst=work.uv_layers.new(name='Transferred from exact owned master')
loop_normals=np.empty((len(work.loops),3),float)
prov=np.empty((len(CV),3),int);bar=np.empty((len(CV),3),float);origShift=[]
for j,v in enumerate(CV):
 pt,no,fi,di=bvh.find_nearest(Vector(v))
 xyz=np.asarray(pt)
 prov[j]=srcTri[fi]; yy=bary(xyz,P0[prov[j]])
 bar[j]=yy/yy.sum()
 new=bar[j]@P0[prov[j]]
 origShift.append(float(np.linalg.norm(new-v)*S*1000))
 work.vertices[j].co=new
 CV[j]=new
# Loop UV normals come from face-facing correspondence along each new face,
# avoiding assigning a single UV across a source atlas seam.
for f in work.polygons:
 f.use_smooth=True
 pids=list(f.vertices); facect=CV[pids].mean(0)
 for li in f.loop_indices:
  vi=work.loops[li].vertex_index
  key=CV[vi]
  inner=.998*key+.002*facect
  _,_,si,_=bvh.find_nearest(Vector(inner))
  wi=bary(CV[vi],P0[srcTri[si]])
  wi/=wi.sum()
  uvdst.data[li].uv=wi@uv[L[ti[si]]]
  nr=wi@nrm[L[ti[si]]];nr/=np.linalg.norm(nr)
  loop_normals[li]=nr
work.normals_split_custom_set(loop_normals.tolist())
work.materials.append(owner.data.materials[0])
# Surface-corresponding Rig mapping, with an actual ToeBase on the new visible foot.
# Source-correspondence rest material group kept for thigh/shin/foot; independent
# new welded visible forefoot nodes use smooth hinge around original ToeBase axis.
rootWeight=np.einsum('ni,nij->nj',bar,w[prov]).astype(float)
rootWeight/=rootWeight.sum(1)[:,None]
points=(CV-C)*S; toe=A['joints'][1,3]; ankle=A['joints'][1,2]
def sm(x):
 x=np.clip(x,0.,1.);return x*x*(3-2*x)
ytoe=toe[1]-points[:,1]
vv=sm((ytoe+.020)/.057)*sm((.119-points[:,2])/.049)
toe_offer=.88*np.maximum(vv,rootWeight[:,3])
# Explicit articulated toe rail, not static underside: genuine visible forefoot weight.
footToe=rootWeight[:,2]+rootWeight[:,3]; active=(points[:,2]<.087)&(ytoe>-.035)&(footToe>.75)
rootWeight[active,3]=(toe_offer*footToe)[active]
rootWeight[active,2]=footToe[active]-rootWeight[active,3]
assert np.max(abs(rootWeight.sum(1)-1))<1e-7
g=[obj.vertex_groups.new(name=n) for n in ('thigh.R','shin.R','foot.R','toe.R')]
for j,row in enumerate(rootWeight):
 for gg,k in zip(g,row):
  if k>1e-10:gg.add([j],float(k),'REPLACE')
arm=obj.modifiers.new('Articulated original C1 knee ankle toe','ARMATURE');arm.object=rig
owner.hide_render=True;owner.hide_set(True)
# Only detached proof: exact original remains as hidden immutable local reference.
obj['scope']='RIGHT VISIBLE BOOT / SHIN ONLY. Unapproved. Do not use as complete Character 1.'
obj['source_mesh_sha256']=h(hair)
report={}
for side,xyz,ids in [('original_to_proof',Q,loc),('new_to_master',CV,cf)]:
 tv,tf=(CV,cf) if side=='original_to_proof' else (Q,loc)
 bvhx=BVHTree.FromPolygons(tv.tolist(),tf.tolist(),all_triangles=True,epsilon=0.)
 distances=np.array([bvhx.find_nearest(Vector(v))[3]*S*1000 for v in xyz])
 zz=(xyz[:,2]-C[2])*S
 ref={}
 for sec,mk in [('sole',zz<.065),('boot',zz<.30),('toe_front',(zz<.115)&((xyz[:,1]-C[1])*S<toe[1])),('flex_cuff',zz>=.23),('whole',zz==zz)]:
  ref[sec]=np.quantile(distances[mk],[.50,.95,.99,1]).tolist()
 report[side]=ref
rest_norm=(CV-C)*S
newFace=coords(work.loop_triangles,'vertices',3,np.int32)
orig_v=Q
uv_saved=np.array([tuple(v.uv) for v in work.uv_layers.active.data])
assert np.isfinite(uv_saved).all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'c1-visible-right-boot-proof.blend'),compress=True)
np.savez_compressed(P/'new-surface.npz',v=CV,tri=newFace,w=rootWeight,original_face_ids=ti,closest_raw_source_ids=prov,bary=bar,rest_uv=uv_saved,projected_normals=loop_normals)
out={'sha_source':h(file),'sha_master':h(hair),'original_raw_vertices':len(verts),'original_welded':len(pre),'original_faces':len(srcTri),'new_vertices':len(CV),'new_faces':len(newFace),'face_count_ratio':len(newFace)/len(srcTri),'bidirectional_nearest_surface_mm':report,'rest_snap_displacement_max_mm':max(origShift),'toe_visible_weighted_vertices_n':int(sum(rootWeight[:,3]>.20)),'fw_bounds_stock_m':((Q-C)*S).min(0).tolist()+((Q-C)*S).max(0).tolist(),'fw_bounds_candidate_m':rest_norm.min(0).tolist()+rest_norm.max(0).tolist(),'normal_path':'source corner normals projected and custom split restored; not a rendered comparison'}
(P/'rest.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
