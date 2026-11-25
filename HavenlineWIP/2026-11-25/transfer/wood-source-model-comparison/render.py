import sys
from pathlib import Path
import bpy
from mathutils import Vector
p, output = map(Path, sys.argv[sys.argv.index('--') + 1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
s.render.engine='CYCLES'
s.cycles.samples=24
s.cycles.use_denoising=False
s.render.resolution_x=1420;s.render.resolution_y=530;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.view_settings.view_transform='AgX'
s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.62,.73,1,1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.34
sources = ['HavenlineGodot/assets/environment_v2/log.glb','HavenlineGodot/assets/world/log.glb','HavenlineLevel1/assets/studio/wood_bundle_v3.glb']
for x,path in zip((-1.2,0,1.2),sources):
 previous=set(s.objects);bpy.ops.import_scene.gltf(filepath=str(p/path)); imported=set(s.objects)-previous
 children=[ob for ob in imported if ob.type=='MESH']
 verts=[ob.matrix_world@Vector(b) for ob in children for b in ob.bound_box]
 mins=Vector(tuple(min(v[i] for v in verts) for i in range(3)))
 maxs=Vector(tuple(max(v[i] for v in verts) for i in range(3)))
 center=(maxs+mins)/2; center.z=mins.z
 size=maxs-mins; extent=max(size); f=.99/extent
 for ob in imported:
  if ob.parent not in imported:
   ob.location=(ob.location-center)*f+Vector((x,0,0))
   ob.scale*=f
 print('RAW_MESH',path,tuple(size),len(children),flush=True)
m=bpy.data.materials.new('Studio neutral');m.use_nodes=True
b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(.4,.52,.64,1);b.inputs['Roughness'].default_value=.89
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.007));bpy.context.object.data.materials.append(m)
def aim(ob,pos): ob.rotation_euler=(Vector(pos)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,xyz,power,co,size in [('Key',(1,-3,5),470,(1,.88,.75),5),('Fill',(-2,0,3),290,(.69,.81,1),4),('Rim',(0,3,4),360,(.82,.9,1),4)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=co;d.size=size
 ob=bpy.data.objects.new(name,d);s.collection.objects.link(ob);ob.location=xyz;aim(ob,(0,0,.1))
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));s.collection.objects.link(cam);s.camera=cam
cam.location=(0,-6,4);aim(cam,(0,0,.33));cam.data.type='ORTHO';cam.data.ortho_scale=3.62
s.render.filepath=str(output);bpy.ops.render.render(write_still=True)
