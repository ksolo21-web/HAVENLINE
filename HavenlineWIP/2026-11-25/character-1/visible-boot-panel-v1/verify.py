import os
import bpy,numpy as np,hashlib,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path(__file__).resolve().parent
source=Path(os.environ['C1_VISIBLE_BOOT_DATA'])
d=np.load(P/'manual-panel-surface.npz')
prev=np.load(source/'new-surface.npz')
R=d['shaft_source_world'];T=d['based'];q=d['trim_v'];t=d['trim_f'];orig=d['based_orig_face']
normal=d['trim_planar_normal']
def bvh(v,t):
 return BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.)
base=bvh(R,T);trim=bvh(q,t)
bb=[(int(orig[i]),int(orig[j])) for i,j in base.overlap(base) if i<j and not np.isin(T[i],T[j]).any()]
bt=[(int(orig[i]),int(j)) for i,j in base.overlap(trim)]
tt=[(int(i),int(j)) for i,j in trim.overlap(trim) if i<j and not np.isin(t[i],t[j]).any()]
def top(tt):
 e=tt[:,((0,1),(1,2),(2,0))].reshape(-1,2); E=np.sort(e,axis=1)
 _,i,c=np.unique(E,axis=0,return_inverse=True,return_counts=True)
 bal=np.bincount(i,weights=np.where(e[:,1]>e[:,0],1,-1), minlength=len(c))
 return {'open_edges':int(sum(c==1)),'excess_incidence':int(sum(c>2)), 'reversed_shared_edges':int(sum((c==2)&(bal!=0)))}
nearest=lambda bb,pts:np.array([bb.find_nearest(Vector(w))[3] for w in pts])
old=bvh(R,prev['tri']); comb=bvh(np.vstack((R,q)),np.vstack((T,t+len(R))))
g=np.linspace(0,1,7)
inter=np.array([(i,j,1-i-j) for i in g for j in g if i+j<=1.000001])
pts=np.einsum('ac,bcj->baj',inter,q[t]).reshape(-1,3)
rpts=np.einsum('ac,bcj->baj',inter,R[prev['tri'][[38197,38294,38308]]]).reshape(-1,3)
meshfile=P/'c1-right-boot-panel-rest-proof.blend'
bpy.ops.wm.open_mainfile(filepath=str(meshfile))
o=bpy.data.objects['Detached right boot base minus three mixed bridge faces']; p=bpy.data.objects['Manual upper-boot lapped trim panel rigid to right shin']
verify_obj=lambda k: np.array([v.co[:] for v in k.data.vertices],float)
A=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz'))
out={'base_neutral_pairs':bb,'base_trim_intersections':bt,'nonadjacent_trim_self_pairs':tt,'base_topology':top(T),'trim_topology':top(t),'old_topology':top(prev['tri']),'trim_to_pure_backing_plane_min_mm':float(np.min((q-R[d['backing_face'][0]])@normal)*1000),'sampled_trim_to_retained_surface_min_mm':float(nearest(base,pts).min()*1000),'sampled_new_trim_to_prior_whole_surface_max_mm':float(nearest(old,pts).max()*1000),'sampled_removed_region_to_new_whole_surface_max_mm':float(nearest(comb,rpts).max()*1000),'pure_normal_volume_mm3':float(np.einsum('ij,ij->i',q[t][:,0],np.cross(q[t][:,1],q[t][:,2])).sum()/6*1e9),'corrected_38294_38309_has_no_crossings':not bt and (38294,38309) not in bb,'rest_opened_actual_mesh_residual_mm':max(float(np.max(np.linalg.norm((verify_obj(o)-A['source_origin'])*A['scale']-R,axis=1))*1000),float(np.max(np.linalg.norm((verify_obj(p)-A['source_origin'])*A['scale']-q,axis=1))*1000)),'exact_shared_original_material':o.data.materials[0]==p.data.materials[0],'saved_uv_ok':bool(all(np.isfinite(np.array([w.uv[:] for w in k.data.uv_layers.active.data])).all() for k in (o,p))),'toe_weights_on_saved_base_n':int(sum(any(o.vertex_groups[g.group].name=='toe.R' and g.weight>.20 for g in w.groups) for w in o.data.vertices))}
out['passed_full_neutral']=not bb and not bt and not tt and not out['trim_topology']['open_edges'] and out['base_topology']['open_edges']==out['old_topology']['open_edges']
(P/'neutral-result.json').write_text(json.dumps(out,indent=2))
print(out,flush=True)
