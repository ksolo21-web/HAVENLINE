import hashlib,sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
source,out=map(Path,sys.argv[sys.argv.index('--')+1:])
assert hashlib.sha256(source.read_bytes()).hexdigest()=='31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554'
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False
s.render.resolution_x=620;s.render.resolution_y=440;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
s.world=bpy.data.worlds.new('Ambient');s.world.use_nodes=True
world=s.world.node_tree.nodes['Background'];world.inputs['Color'].default_value=(.44,.56,.74,1);world.inputs['Strength'].default_value=.32
bpy.ops.import_scene.gltf(filepath=str(source))
obj=next(o for o in s.objects if o.type=='MESH' and o.name=='Pickup LOD - Crown log')
worldverts=[obj.matrix_world@v.co for v in obj.data.vertices]
low=Vector(tuple(min(v[i] for v in worldverts) for i in range(3))); high=Vector(tuple(max(v[i] for v in worldverts) for i in range(3)))
center=(low+high)/2
obj.data.calc_loop_triangles(); faces=[tuple(x.vertices) for x in obj.data.loop_triangles]
assert len(faces)==1300
obj.location-=center
print('CROWN_DATA',tuple(center),tuple(high-low),len(faces),[a.name for a in obj.data.color_attributes])
bv=BVHTree.FromPolygons(worldverts,faces,all_triangles=True)
for name, delta in [('lengthwise',Vector((.035,0,0))),('depthwise',Vector((0,.035,0)))]:
 other=BVHTree.FromPolygons([v+delta for v in worldverts],faces,all_triangles=True)
 print('DETACHED_GODOT_GRID_SHIFT_CANDIDATE_PAIR_COUNT',name,len(bv.overlap(other)))
for o in s.objects:
 if o.type=='MESH':o.hide_render=o!=obj
def aim(ob,x): ob.rotation_euler=(Vector(x)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,xyz,power,colour,size in [('Key',(.05,-.5,.55),19,(1,.86,.7),.33),('Fill',(-.4,-.27,-.27),10,(.67,.83,1),.32),('Rim',(.32,.4,.31),14,(.78,.88,1),.26)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=colour;data.size=size;data.shape='DISK'
 ob=bpy.data.objects.new(name,data);s.collection.objects.link(ob);ob.location=xyz;aim(ob,(0,0,0))
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));s.collection.objects.link(cam);s.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=.4
for name,position in [('crown-positive-end',(.54,-.35,.31)),('crown-negative-end',(-.54,-.35,.31)),('crown-underside',(.10,-.48,-.42))]:
 cam.location=position;aim(cam,(0,0,0))
 s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
