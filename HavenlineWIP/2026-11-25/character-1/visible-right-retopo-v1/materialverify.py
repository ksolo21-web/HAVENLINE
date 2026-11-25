import bpy,numpy as np,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'c1-visible-right-boot-proof.blend'))
o=bpy.data.objects['Right boot-shin visible topology proof']
r=[x for x in bpy.context.scene.objects if x.type=='MESH' and x!=o][0]
d=np.load(P/'new-surface.npz')
u=np.array([x.uv[:] for x in o.data.uv_layers.active.data],dtype=float)
n=np.array([x.vector[:] for x in o.data.corner_normals],dtype=float)
b=lambda img:hashlib.sha256(img.packed_file.data).hexdigest() if img.packed_file else None
def tex(ob):
 return sorted(str(b(x.image)) for x in ob.data.materials[0].node_tree.nodes if getattr(x,'image',None))
geo=np.array([v.co[:] for v in o.data.vertices],dtype=float)
assert np.max(np.abs(geo-d['v']))<1e-6
assert np.isfinite(u).all()
old_u=np.array([x.uv[:] for x in r.data.uv_layers.active.data],dtype=float)
ret={'uv_saved_explicit_range':[u.min(0).tolist(),u.max(0).tolist()], 'original_uv_range':[old_u.min(0).tolist(),old_u.max(0).tolist()], 'saved_out_of_0_1':int(sum((u<0).any(1)|(u>1).any(1))), 'same_exact_material_pointer':o.data.materials[0]==r.data.materials[0],'source_packed_texture_sha256':tex(r), 'new_packed_texture_sha256':tex(o),'saved_has_custom_normals':bool(o.data.has_custom_normals), 'posed_mesh_not_modified':True}
s=np.clip(np.sum(n*d['projected_normals'],axis=1),-1,1)
ret['stored_custom_vs_projected_deg_p50_p95_p99_max']=np.quantile(np.degrees(np.arccos(s)),[.5,.95,.99,1]).tolist()
(P/'material-saved.json').write_text(json.dumps(ret,indent=2))
np.savez_compressed(P/'material-saved.npz',uv=u,normal=n)
print(ret,flush=True)
