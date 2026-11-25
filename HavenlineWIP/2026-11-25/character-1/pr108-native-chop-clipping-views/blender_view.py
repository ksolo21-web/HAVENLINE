"""Two detached CPU diagnostic views. Run only with graphics admission."""
import bpy
import json,math,pathlib,sys
from mathutils import Vector

inputs=sys.argv[sys.argv.index("--")+1:]
source=json.loads(pathlib.Path(inputs[0]).read_text())
out=pathlib.Path(inputs[1]); out.mkdir(parents=True,exist_ok=True)
assert source['native_chop_clip']=='l1_actions/chop' and abs(source['native_position_s']-.375)<1e-8
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
def point(p):
    return Vector((p[0],-p[2],p[1]))
def shader(name, base, roughness=.48):
    m=bpy.data.materials.new(name); m.diffuse_color=(*base,1)
    m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*base,1)
    b.inputs['Roughness'].default_value=roughness
    nodes=m.node_tree.nodes; links=m.node_tree.links
    emission=nodes.new('ShaderNodeEmission'); emission.inputs['Color'].default_value=(*base,1); emission.inputs['Strength'].default_value=.6
    mix=nodes.new('ShaderNodeMixShader'); mix.inputs[0].default_value=.55
    links.new(b.outputs[0],mix.inputs[1]); links.new(emission.outputs[0],mix.inputs[2]); links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
    return m
palette={
  'original_axe':shader('exact axe prop shown in gold',(.36,.19,.067)),
  'glove_L':shader('left glove shown in teal',(.028,.175,.37)),
  'glove_R':shader('right glove shown in blue',(.022,.09,.238)),
  'wrist_cuff_L':shader('left wrist cuff shown in lavender',(.34,.37,.40)),
  'wrist_cuff_R':shader('right wrist cuff shown in pale blue',(.50,.55,.61)),
}
alert=shader('selected strict-crossing face shown in red-orange',(.76,.014,.052))
targets=[]
for label,piece in source['pieces'].items():
    vertices=[]; indices={}; faces=[]
    # Consolidate only repeated coordinates without changing the exact float positions.
    for tri in piece['triangles']:
        face=[]
        for c in tri:
            c=tuple(c); key=point(c)
            if c not in indices:
                indices[c]=len(vertices); vertices.append(key)
            face.append(indices[c])
        faces.append(face)
    mesh=bpy.data.meshes.new(label)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    ob=bpy.data.objects.new(label,mesh)
    bpy.context.collection.objects.link(ob)
    mesh.materials.append(palette[label])
    mesh.materials.append(alert)
    flagged=set(piece['intersecting_faces'])
    for i,poly in enumerate(mesh.polygons):
        if i in flagged:
            if label!='original_axe':
                poly.material_index=1
                targets += [vertices[j] for j in faces[i]]
        poly.use_smooth=False
# Camera frames hands and clipping areas rather than the unrelated cropped head.
assert targets
origin=sum(targets,Vector())/len(targets)
range_world=max((v-origin).length for v in targets)
shaft=point(source['tool_transform']['y']).normalized()
normal=point(source['tool_transform']['x']).normalized()
third=normal.cross(shaft).normalized()
def aim(ob,target):
    ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
for label,offset,energy,size in [('key',normal+third+shaft,26,1.2),('fill',-normal+third*.7,17,1.8),('rim',-third+shaft*.8,22,1.5)]:
    l=bpy.data.lights.new(label,'AREA'); l.energy=energy;l.shape='DISK';l.size=size
    obj=bpy.data.objects.new(label,l);bpy.context.collection.objects.link(obj)
    obj.location=origin+offset.normalized()*1.7;aim(obj,origin)
scene=bpy.context.scene
scene.world.use_nodes=True
background=scene.world.node_tree.nodes.get('Background')
background.inputs['Color'].default_value=(.095,.12,.16,1);background.inputs['Strength'].default_value=.45
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=850;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new('exact geometry diagnosis'); cam=bpy.data.objects.new('diagnostic camera',cd);bpy.context.collection.objects.link(cam)
cd.type='ORTHO';cd.ortho_scale=max(.62,range_world*2.9);scene.camera=cam
for name,direction in [('01-shaft-side',normal+third*.34+shaft*.16),('02-perpendicular',third-normal*.20-shaft*.15)]:
    cam.location=origin+direction.normalized()*2.3
    aim(cam,origin)
    scene.render.filepath=str((out/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
