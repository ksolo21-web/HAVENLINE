"""T05 R38 Blender workbench: pack EXACT owner images into three camera views.

This is an editable 3D photo-reference workbench. The base photocarved GLB is
only a reference study with fused parts, not a final sculpt or shipping mesh.
Usage: blender -b --python r38_blender_workbench.py -- MODEL.glb REF_DIR OUT.blend
"""
import bpy,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
assert len(args)==3,'Expected MODEL.glb REF_DIR OUT.blend'
model,refs,dest=Path(args[0]),Path(args[1]),Path(args[2])
dest.parent.mkdir(exist_ok=True,parents=True)
expected={
 'front':('32451.jpg',30.,15.,'70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4'),
 'side':('32450.jpg',90.,7.,'5b1831d03575e705f1baf5af5d4ac4b4ecd62e364b4287c7f841965625d4d719'),
 'rear':('32441.png',180.,7.,'0ff99199e1eb4bedeffe4d9953f5253a97e49366a2118d5976132c9137d93510')}
bpy.ops.wm.read_factory_settings(use_empty=True)
model_collection=bpy.data.collections.new('PHOTO_CARVED_GEOMETRY_UNAPPROVED')
bpy.context.scene.collection.children.link(model_collection)
reference_collection=bpy.data.collections.new('ORIGINAL_OWNER_IMAGES_DO_NOT_EDIT')
bpy.context.scene.collection.children.link(reference_collection)
bpy.ops.import_scene.gltf(filepath=str(model))
for obj in list(bpy.context.scene.objects):
    if obj.type=='MESH':
        for c in list(obj.users_collection):c.objects.unlink(obj)
        model_collection.objects.link(obj)
        obj['T05_status']='Actual owner image-projected geometry. Fused parts and unseen orbit FAIL critic.'
center=Vector((0.,0.,1.55)) # glTF Y-up becomes Blender Z-up
for name,(file,az,el,sha) in expected.items():
    source=refs/file
    assert hashlib.sha256(source.read_bytes()).hexdigest()==sha,'Reference SHA mismatch: '+file
    if source.suffix=='.png' and source.read_bytes().startswith(b'\xff\xd8'):
        # Owner rear is JPEG bytes under legacy .png filename.
        alias=dest.parent/'T05_32441_EXACT_REAR_AS_JPEG_EXTENSION.jpg'
        alias.write_bytes(source.read_bytes())
        source=alias
    img=bpy.data.images.load(str(source),check_existing=False)
    img.name='OWNER_UNALTERED_'+file
    img.pack()
    d=bpy.data.cameras.new('SOURCE_'+name+'_CAMERA')
    camera=bpy.data.objects.new('SOURCE_'+name+'_CAMERA',d)
    reference_collection.objects.link(camera)
    radians=math.radians(az);height=math.radians(el)
    pos=Vector((math.sin(radians)*math.cos(height)*7,
                -math.cos(radians)*math.cos(height)*7,
                1.55+math.sin(height)*7))
    camera.location=pos
    camera.rotation_euler=(center-pos).to_track_quat('-Z','Y').to_euler()
    d.type='ORTHO';d.ortho_scale=4.0
    d.show_background_images=True
    overlay=d.background_images.new()
    overlay.image=img;overlay.alpha=0.50
    camera['T05_original_filename']=file
    camera['T05_original_sha256']=sha
    camera['calibration']='HYPOTHESIS_NOT_CALIBRATED'
bpy.context.scene.camera=bpy.data.objects['SOURCE_front_CAMERA']
bpy.context.scene.render.resolution_x=960
bpy.context.scene.render.resolution_y=960
bpy.context.scene['task']='HAVENLINE_T05'
bpy.context.scene['status']='SOURCE_MATCHED_REFERENCE_WORKBENCH_NOT_VISUALLY_APPROVED'
bpy.context.scene['reference_images']='32451.jpg,32450.jpg,32441.png'
bpy.context.scene['geometry_limitation']='Watertight fused visual hull, lacks individual machine/food/wood/snow volume'
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
assert dest.stat().st_size>1000000
print('T05_R38_EDITABLE_BLENDER_SOURCE_CAMERAS_PACKED_3',dest,flush=True)
