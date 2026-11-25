"""Optional reviewer import into fresh Blender process; no render call.
After its own authorization: blender -b --python import_stage_blender.py -- stage.LOCAL.json ORIGINAL_SOURCE.glb empty-or-stocked OUTPUT.blend
"""
import bpy,json,sys,hashlib
from mathutils import Vector, Matrix
from pathlib import Path
local, src, mode, out=sys.argv[sys.argv.index('--')+1:]
assert mode in ('empty','stocked')
local,src,out=Path(local).resolve(),Path(src).resolve(),Path(out).resolve()
assert not out.exists()
s=json.loads(local.read_bytes())
assert hashlib.sha256(src.read_bytes()).hexdigest()==s['pinned_crown_glb_sha256']
# Authorized reviewer runs on a newly launched isolated stage file only.
bpy.ops.wm.read_factory_settings(use_empty=True)
C=Matrix(((1.,0.,0.),(0.,0.,-1.),(0.,1.,0.)))
def v(x):return C@Vector(x)
M=bpy.data.meshes.new('Exact source-derived visible floor triangles')
M.from_pydata([v(p) for p in s['vertices_godot']],[],s['faces'])
M.update()
obj=bpy.data.objects.new('Visible camp floor / same-plane paint regions',M)
bpy.context.scene.collection.objects.link(obj)
uv=M.uv_layers.new(name='source_paletteUV')
for poly in M.polygons:
  for i in poly.loop_indices:
    u,w=s['uv_gltf'][M.loops[i].vertex_index]
    uv.data[i].uv=(u,1.-w)
def material(name,r):
  x=bpy.data.materials.new(name);x.use_nodes=True
  p=x.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=r;p.inputs['Metallic'].default_value=0
  return x,p
floor,p=material('Existing visible camp shader color approximation',s['floor']['roughness'])
p.inputs['Base Color'].default_value=(*s['floor']['linear_base_color'],1.)
paint,p=material('Exact V3 embedded paint on original visual surface',s['marker']['roughness'])
img=bpy.data.images.load(str(local.parent/s['marker']['png_file']),check_existing=False)
img.pack()
tx=paint.node_tree.nodes.new('ShaderNodeTexImage');tx.image=img;tx.extension='EXTEND'
paint.node_tree.links.new(tx.outputs['Color'],p.inputs['Base Color'])
M.materials.append(floor);M.materials.append(paint)
for p,k in zip(M.polygons,s['material_ids']):p.material_index=k
if mode=='stocked':
  bpy.ops.import_scene.gltf(filepath=str(src))
  original=bpy.data.objects.get('Pickup LOD - Crown log')
  assert original and original.type=='MESH'
  assert len(original.data.polygons)==1300
  copied=original.data
  mx=original.matrix_world.copy()
  for o in [o for o in bpy.context.scene.objects if o is not obj]:
    bpy.data.objects.remove(o,do_unlink=True)
  for i,d in enumerate(s['per_log_pose_godot']):
    ob=bpy.data.objects.new('Exact unchanged crown / display pose '+str(i+1),copied);bpy.context.scene.collection.objects.link(ob)
    r=C@Matrix(d['R_source_to_source_world'])@C.transposed()
    assert abs(r.determinant()-1.)<.000001
    tr=r.to_4x4();tr.translation=v(d['t_source_to_source_world'])
    ob.matrix_world=tr@mx
cam_data=bpy.data.cameras.new('Exact postpay stock camera geometry')
cam=bpy.data.objects.new('Exact postpay stock camera pose',cam_data)
bpy.context.scene.collection.objects.link(cam)
q=s['camera']
# bpy local axes +X right, +Y up, +Z back. Source Camera3D size is vertical.
r=Matrix((v(q['right']),v(q['up']),v(q['back']))).transposed().to_4x4()
r.translation=v(q['position']);cam.matrix_world=r
cam_data.type='ORTHO';cam_data.ortho_scale=q['size']*q['render_resolution'][0]/q['render_resolution'][1]
scene=bpy.context.scene;scene.camera=cam;scene.render.resolution_x,scene.render.resolution_y=q['render_resolution'];scene.render.resolution_percentage=100
# Reviewer chooses the independently documented comparison lighting, not a
# renderer or score here; empty and stocked scenes must share that exact setup.
bpy.ops.wm.save_as_mainfile(filepath=str(out))
