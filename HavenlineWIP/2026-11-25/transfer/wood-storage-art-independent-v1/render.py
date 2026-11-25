import sys,hashlib
from pathlib import Path
import bpy
from mathutils import Vector
staging,output=map(Path,sys.argv[sys.argv.index('--')+1:])
assert hashlib.sha256(staging.read_bytes()).hexdigest()=='0f961e1dbf66c954eb557ecbae54d34c34cf15121011c0866203d05cb73d419b'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(staging))
objs=list(bpy.context.scene.objects)
assert len(objs)==1 and objs[0].type=='MESH'
obj=objs[0]
assert len(obj.data.materials)==2 and len([i for i in bpy.data.images if i.packed_file])==1
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.0085))
pl=bpy.context.object;pl.name='Neutral warm context only'
m=bpy.data.materials.new('Matte taupe context');m.use_nodes=True
n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(.42,.31,.235,1); n.inputs['Roughness'].default_value=.9
pl.data.materials.append(m)
world=bpy.data.worlds.new('Neutral overcast review')
world.use_nodes=True; world.node_tree.nodes['Background'].inputs[0].default_value=(.70,.76,.83,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.65
scene=bpy.context.scene;scene.world=world
bpy.ops.object.light_add(type='AREA',location=(.5,-2,5.5));l=bpy.context.object
l.data.energy=370;l.data.shape='DISK';l.data.size=6
l.rotation_euler=(-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(7,-11,11));cam=bpy.context.object
cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=13*1280/720
cam.data.clip_end=200
scene.camera=cam
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.engine='CYCLES'; scene.cycles.device='CPU';scene.cycles.samples=8
scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.filepath=str(output)
print('STAGE camera_back_godot=(7,11,11) exact vertical_span=13 render=1280x720 CPU_threads=2',flush=True)
bpy.ops.render.render(write_still=True)
