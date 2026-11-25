import os
import bpy, numpy as np, json
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
old=Path(os.environ['C1_COLLAR_DATA'])
d=np.load(P/'fold-panel.npz');A=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz'))
S=float(A['scale']);O=A['source_origin']
N=d['v'];T=d['tri'];R=d['w'];D=d['delta_in_rig_m']
bpy.ops.wm.open_mainfile(filepath=str(old/'c1-right-boot-layered-assembly-proof.blend'))
source=bpy.data.objects['Right boot visible repaired leather rest proof']
trim=bpy.data.objects['Manual upper-boot lapped trim panel rigid to right shin']
rig=next(q for q in bpy.context.scene.objects if q.type=='ARMATURE')
initial=np.array([r.vector[:] for r in source.data.corner_normals]).reshape(-1,3,3)
ids=d['rebuilt_source']; x=initial[ids]; sharp=x.mean(1);sharp/=np.linalg.norm(sharp,axis=1)[:,None]
normals=np.concatenate((initial[d['origface']],*[np.stack((x[:,i],x[:,(i+1)%3],sharp),1) for i in range(3)]))
m=bpy.data.meshes.new('Single sewn posterior flex panel new visible topology')
m.from_pydata((N/S+O).tolist(),[],T.tolist());m.update()
o=bpy.data.objects.new('C1 detached posterior knee panel proof',m);bpy.context.collection.objects.link(o)
layer=m.uv_layers.new(name='Exact source material correspondence')
layer.data.foreach_set('uv',d['uv'].astype(np.float32).ravel())
for q in m.polygons:q.use_smooth=True
m.normals_split_custom_set(normals.reshape(-1,3).tolist());m.materials.append(source.data.materials[0])
groups=[o.vertex_groups.new(name=r) for r in ('thigh.R','shin.R','foot.R','toe.R')]
for i,ww in enumerate(R):
 for g,w in zip(groups,ww):
  if w>1e-10:g.add([i],float(w),'REPLACE')
md=o.modifiers.new(type='ARMATURE',name='Original C1 anatomical rig');md.object=rig
basis=o.shape_key_add(name='Basis',from_mix=False)
key=o.shape_key_add(name='One posterior fold at original 0ms only',from_mix=False);key.value=0.
for i in np.flatnonzero(np.linalg.norm(D,axis=1)>1.e-10):key.data[i].co=basis.data[i].co+Vector(D[i].tolist())
source.hide_set(True);source.hide_render=True
o['scope']='Exact original neutral geometry, candidate localized held key only. Not approved.'
def calc(ob):
 verts=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices
 p=np.empty((len(verts),3),np.float32);verts.foreach_get('co',p.ravel())
 return (p-O)*S
def pairs(v,T):
 xx=BVHTree.FromPolygons(v.tolist(),T.tolist(),all_triangles=True,epsilon=0.)
 return xx,[(int(i),int(j)) for i,j in xx.overlap(xx) if i<j and not np.isin(T[i],T[j]).any()]
p0=calc(o);tb,nb=pairs(p0,T); tr=np.array([tuple(p.vertices) for p in trim.data.polygons]);q0=calc(trim);qb,_=pairs(q0,tr)
nm=len(N)
assert bpy.data.objects[o.name].data.has_custom_normals
neutral={'rest_max_native_delta_mm':float(np.linalg.norm(p0-N,axis=1).max()*1000),'nonadjacent_self_pairs':len(nb),'boot_trim_pairs':len(tb.overlap(qb)),'toe_vertices_kept':int(sum(R[:,3]>.20))}
bpy.ops.wm.save_as_mainfile(filepath=str(P/'c1-new-visible-posterior-knee-proof.blend'),compress=True)
if neutral['nonadjacent_self_pairs'] or neutral['boot_trim_pairs']:
 (P/'qa.json').write_text(json.dumps({'neutral':neutral,'held_not_evaluated':True},indent=2)); print(neutral);raise SystemExit(0)
for name,mat in zip(('thigh.R','shin.R','foot.R','toe.R'),A['bones'][0,1]):
 bone=rig.pose.bones[name];bone.matrix=Matrix(mat.tolist())@bone.bone.matrix_local;bpy.context.view_layer.update()
p=calc(o);key.value=1;bpy.context.view_layer.update();f=calc(o)
topp=d['origface']; rr=d['rebuilt_source']; prov=np.r_[topp,np.tile(rr,3)]
i0,i1=[np.flatnonzero(prov==j) for j in (38082,39703)]
assert len(i0)==len(i1)==3
E=np.unique(np.sort(T[:,((0,1),(1,2),(2,0))].reshape(-1,2),axis=1),axis=0)
leng=np.linalg.norm(N[E[:,1]]-N[E[:,0]],axis=1)
R0=np.linalg.norm(D,axis=1)>1e-10
guard=(leng>.0008)&R0[E].any(1)
focus=R0[T].any(1)
def cross(y):
 z=y[T];return np.cross(z[:,1]-z[:,0],z[:,2]-z[:,0])
basearea=cross(p);qnorm=(basearea*basearea).sum(1)
out=[]
for g in (p,f):
 b,s=pairs(g,T)
 h,_=pairs(calc(trim),tr)
 e=np.linalg.norm(g[E[guard,1]]-g[E[guard,0]],axis=1)/leng[guard]
 qs=(basearea*cross(g)).sum(1)/np.maximum(qnorm,1e-20)
 out.append({'all_self_pairs':len(s),'support_self_pairs':int(sum(focus[i] or focus[j] for i,j in s)),'named_cross_pairs':[(x,y) for x,y in s if (x in i0 and y in i1) or (y in i0 and x in i1)],'anterior_source_pair_present':any(set([int(prov[i]),int(prov[j])])=={26992,27689} for i,j in s),'scoped_edge_bad':int(sum((e<.5)|(e>2.))),'signed_under_point1':int(sum(focus&(qs<.1))),'signed_nonpositive':int(sum(focus&(qs<=0))),'real_trim_contact_pairs':len(b.overlap(h))})
qa={'neutral':neutral,'key_0ms_before_after':out,'all_else_fixed_posed_delta_mm':float(np.linalg.norm(f-p,axis=1)[~R0].max()*1000),'match_predicted_blender_array_mm':float(np.linalg.norm(f-d['held0'],axis=1).max()*1000)}
(P/'qa.json').write_text(json.dumps(qa,indent=2));print(qa,flush=True)
