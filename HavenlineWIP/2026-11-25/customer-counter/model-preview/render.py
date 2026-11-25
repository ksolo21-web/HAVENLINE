import math, os, sys
from pathlib import Path
import bpy
from mathutils import Vector
p=Path(sys.argv[sys.argv.index('--')+1]); out=Path(sys.argv[sys.argv.index('--')+2])
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene
s.render.engine='CYCLES'; s.cycles.device='CPU'; s.cycles.samples=40; s.cycles.use_denoising=False
s.render.image_settings.file_format='PNG'; s.view_settings.view_transform='AgX'
s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Studio'); s.world.use_nodes=True
s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.62,.73,1,1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28
bpy.ops.import_scene.gltf(filepath=str(p/'service_counter.glb'))
print('CounterBounds', [(o.name, [tuple(round(float(q),2) for q in o.matrix_world@Vector(v)) for v in [o.bound_box[0],o.bound_box[6]]]) for o in s.objects if o.type=='MESH'],flush=True)
def mat(name,c):
 m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); m.use_nodes=True
 b=m.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value=(*c,1); b.inputs['Roughness'].default_value=.94
 return m
def cube(name, xyz,size,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz); obj=bpy.context.object
 obj.name=name; obj.dimensions=size; obj.data.materials.append(m);return obj
cube('Studio snow ground',(0,0,-.038),(200,200,.07),mat('Studio snow',(.63,.73,.83)))
def light(name,xyz,power,color,size):
 d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.color=color; d.shape='DISK';d.size=size
 ob=bpy.data.objects.new(name,d);s.collection.objects.link(ob);ob.location=xyz
 ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
light('Key',(1,4,7),1350,(1,.87,.74),6)
light('Fill',(-5,2,4),720,(.66,.81,1),6)
light('Rim',(0,-4,6),1500,(.82,.9,1),5)
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera')); s.collection.objects.link(cam); s.camera=cam; cam.data.type='ORTHO'
def render(name,pos,target,scale,w,h):
 cam.location=pos; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.data.ortho_scale=scale
 s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
render('front',(4.6,9,4.6),(0,0,1.08),5.2,1100,680)
render('inside',(-4.6,-9,4.65),(0,0,1.08),5.2,1100,680)
def linear(x):
 return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
wall=mat('Existing plain wall',tuple(map(linear,[.3647059,.3176471,.2823529])))
for x in [-3.4125,3.4125]:
 cube('Existing wall flank',(x,0,.475),(3.175,.30,.95),wall)
bpy.ops.wm.obj_import(filepath=str(p/'gate_post.obj'),forward_axis='NEGATIVE_Y',up_axis='Y')
post=bpy.context.selected_objects[0]
post.location.x=-1.7025
right=post.copy(); s.collection.objects.link(right); right.location.x=1.71076069
render('fit',(4.5,12,5.25),(0,0,.99),10.9,1280,490)
