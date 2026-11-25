import os
import bpy,numpy as np,json
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parent
A=Path(os.environ['C1_APPROVED_REAR_DATA'])
s=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz'))
old=np.load(A/'new-rear-panel.npz')
d=np.load(P/'gusset.npz')
V=d['v'];T=d['tri'];W=d['w'];src=d['src_face'];S=float(s['scale']);O=s['source_origin']
bpy.ops.wm.open_mainfile(filepath=str(A/'c1-visible-rear-knee-redesign-proof.blend'))
o=bpy.data.objects['Right boot new visible rear fold candidate'];tr=bpy.data.objects['Manual upper-boot lapped trim panel rigid to right shin']
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
ot=o.data; a=np.array([tuple(v.vector) for v in ot.corner_normals]).reshape(-1,3,3)
def bary(p,q):
 v=(q[1:]-q[0]).T;k=np.linalg.lstsq(v,p-q[0],rcond=None)[0]; return np.r_[1-k.sum(),k]
NR=np.empty((len(T),3,3)); oldv=old['v']; oldt=old['tri']
for z,f in enumerate(T):
 r=src[z];q=oldv[oldt[r]]
 if np.array_equal(f,oldt[r]):NR[z]=a[r];continue
 p=np.array([bary(V[v],q)@a[r] for v in f])
 NR[z]=p/np.linalg.norm(p,axis=1)[:,None]
mesh=bpy.data.meshes.new('Articulated connected Shin-Thigh gusset actual visible topology')
mesh.from_pydata((V/S+O).tolist(),[],T.tolist());mesh.update()
ob=bpy.data.objects.new('New rear boot independent shin thigh and rolling gusset proof',mesh);bpy.context.collection.objects.link(ob)
u=mesh.uv_layers.new(name='Exact source atlas subdivision');u.data.foreach_set('uv',d['uv'].astype(np.float32).ravel())
mesh.materials.append(o.data.materials[0])
for f in mesh.polygons:f.use_smooth=True
mesh.normals_split_custom_set(NR.reshape(-1,3).tolist())
groups=[ob.vertex_groups.new(name=k) for k in ('thigh.R','shin.R','foot.R','toe.R')]
for j,v in enumerate(W):
 for g,w in zip(groups,v):
  if w>1.e-10:g.add([j],float(w),'REPLACE')
md=ob.modifiers.new('Original native C1 rig','ARMATURE');md.object=arm
basis=ob.shape_key_add(name='Basis',from_mix=False)
sparse=ob.shape_key_add(name='0ms exact rear articulated and rolled seam',from_mix=False); sparse.value=0.
for k in np.flatnonzero(np.linalg.norm(d['delta'],axis=1)>1e-11):sparse.data[k].co=basis.data[k].co+Vector(d['delta'][k].tolist())
# Encode separate piece/hinge ancestry as face-domain attribute; seam remains
# genuinely shared, no hidden modifier deleting intersection patches.
names=['original','shin','gusset','thigh','unchanged sewing transition']
labels=np.asarray([names.index(n) for n in d['labels']],np.int32)
k=mesh.attributes.new(name='Authorized fabric panels and gusset',type='INT',domain='FACE')
k.data.foreach_set('value',labels)
o.hide_set(True);o.hide_render=True
def pts(o):
 p=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices
 x=np.empty((len(p),3),np.float32);p.foreach_get('co',x.ravel());return (x-O)*S
def bvh(v,t):
 return BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.)
gt=np.array([tuple(p.vertices) for p in tr.data.polygons]);active=d['scope']; changed=np.linalg.norm(d['delta'],axis=1)>1e-11
focus=active|changed[T].any(1)
def measure(x,y):
 a=bvh(x,T);q=bvh(y,gt)
 us=[(int(i),int(j)) for i,j in a.overlap(a) if i<j and not np.isin(T[i],T[j]).any()]
 ed=[z for z in us if any(focus[j] for j in z)]
 ft=sorted((i,j) for i,j in a.overlap(q))
 return {'shell_pairs':len(us),'scoped_pairs':len(ed),'scoped_existing_face_labels':[[names[labels[i]],names[labels[j]],i,j] for i,j in ed], 'boot_trim_pairs':len(ft),'direct_thigh_shin_crosses':sum({labels[i],labels[j]}=={1,3} for i,j in us)}
N=pts(ob);Q=pts(tr)
neutral=measure(N,Q)
neutral['exact_surface_max_delta_mm']=float(np.linalg.norm(N-V,axis=1).max()*1000)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'c1-visible-rear-rolling-gusset-proof.blend'),compress=True)
result={'neutral':neutral,'first_held':None}
if neutral['shell_pairs']==neutral['boot_trim_pairs']==0:
 for b,M in zip(('thigh.R','shin.R','foot.R','toe.R'),s['bones'][0,1]):
  b=arm.pose.bones[b];b.matrix=Matrix(M.tolist())@b.bone.matrix_local;bpy.context.view_layer.update()
 before=pts(ob);t=pts(tr);sparse.value=1.;bpy.context.view_layer.update(); after=pts(ob)
 E=np.unique(np.sort(T[:,((0,1),(1,2),(2,0))].reshape(-1,2),axis=1),axis=0)
 ar=np.linalg.norm(V[E[:,1]]-V[E[:,0]],axis=1)
 eg=(ar>.0008)&(changed[E].any(1))
 def lengths(x): return np.linalg.norm(x[E[eg,1]]-x[E[eg,0]],axis=1)/ar[eg]
 def cr(x): p=x[T];return np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
 b0=cr(before);x=cr(after);l0,l1=lengths(before),lengths(after)
 sign=np.sum(b0*x,axis=1)/np.maximum(np.sum(b0*b0,axis=1),1e-25)
 result['first_held']={'0ms_before':measure(before,t),'0ms_active':measure(after,t),'scoped_edges_bad_before_after':[int(sum((l<.5)|(l>2))) for l in (l0,l1)],'after_minmax':[float(l1.min()),float(l1.max())],'affected_signed_below_point1':int(sum(focus&(sign<.1))),'affected_signed_nonpositive':int(sum(focus&(sign<=0))),'max_outside_pose_delta_mm':float(np.linalg.norm((after-before)[~changed],axis=1).max()*1000),'predictive_vs_native_mm':float(np.max(np.linalg.norm(after-d['native0'],axis=1))*1000)}
(P/'qa.json').write_text(json.dumps(result,indent=2))
print({**neutral, 'held':[(z.get(k) if isinstance(z,dict) else None) for z in [result['first_held']] for k in ['scoped_edges_bad_before_after','affected_signed_below_point1','affected_signed_nonpositive']]},flush=True)
