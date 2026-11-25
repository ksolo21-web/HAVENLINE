import runpy,sys,hashlib,json
from pathlib import Path
import bpy
from mathutils import Vector
p=Path(__file__).resolve().parent
s=Path(sys.argv[sys.argv.index('--')+1])
i=s.parent/'paint-inlay.png'
assert hashlib.sha256(s.read_bytes()).hexdigest()=='51e34077a346b0f60951d9ee18c43276c82e8a9787af8f82cdf14a1a7f84c31e'
assert hashlib.sha256(i.read_bytes()).hexdigest()=='9301e61ba2530431c0f1e3821fd9cc87a92e27bf4db50c40a86a62027b920cb1'
runpy.run_path(str(p/'import_stage_blender.py'))
scene=bpy.context.scene
objs=list(scene.objects); meshes=[o for o in objs if o.type=='MESH']
floor=[o for o in meshes if len(o.data.polygons)==3180][0]
logs=[o for o in meshes if len(o.data.polygons)==1300]
assert len(meshes)==len(logs)+1==3 and logs[0].data==logs[1].data
assert len(set(x.material_index for x in floor.data.polygons))==2
assert len(logs[0].data.materials)>0
mats=list(logs[0].data.materials)
assert [m.name for m in mats]==['Bark | painted ridges','End grain | amber']
assert len(logs[0].data.color_attributes)>0
assert all(any(n.type in ('VERTEX_COLOR','ATTRIBUTE') and n.outputs[0].is_linked for n in m.node_tree.nodes) for m in mats)
assert len([n for m in floor.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.packed_file])==1
cam=scene.camera
assert abs(cam.data.ortho_scale-13*1280/720)<1e-5
assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage)==(1280,720,100)
world=bpy.data.worlds.new('Neutral overcast review'); world.use_nodes=True; scene.world=world
world.node_tree.nodes['Background'].inputs[0].default_value=(.70,.76,.83,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.65
# Same comparison lighting as prior V3, translated with the plate.
target=Vector((-6.18,-5.755,.012))
bpy.ops.object.light_add(type='AREA',location=target+Vector((.5,-2,5.5)));l=bpy.context.object
l.data.energy=370;l.data.shape='DISK';l.data.size=6
l.rotation_euler=(target-l.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.filepath=str(p/'frame-LOCAL.png')
print('STAGE floor_faces=3180 crown_faces_each=1300 crown_exact_bark_and_amber_vertex_colors_linked vertical_ortho_span=13 uncropped_1280x720',flush=True)
bpy.ops.render.render(write_still=True)
