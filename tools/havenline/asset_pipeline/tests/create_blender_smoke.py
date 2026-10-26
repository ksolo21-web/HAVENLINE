#!/usr/bin/env python3
"""Deterministic synthetic smoke fixture. NOT Havenline reference artwork."""
import bpy,pathlib,sys
root=pathlib.Path(sys.argv[sys.argv.index("--")+1]).resolve()
root.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
hi=bpy.data.collections.new("DETAIL_MASTER")
lo=bpy.data.collections.new("GAME_LOD0")
bpy.context.scene.collection.children.link(hi)
bpy.context.scene.collection.children.link(lo)
mat=bpy.data.materials.new("HL_blue")
mat.diffuse_color=(.22,.41,.59,1)
mat.use_nodes=True
def move(obj,collection):
    for c in list(obj.users_collection):c.objects.unlink(obj)
    collection.objects.link(obj)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,radius=.46,location=(0,0,.52))
high=bpy.context.object;high.name="DETAIL_MASTER_High"
move(high,hi);high.data.materials.append(mat.copy())  # source shader independent from active low bake image target
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.45,location=(0,0,.52))
low=bpy.context.object;low.name="GAME_LOD0_Low"
move(low,lo);low.data.materials.append(mat)
assert low.data.uv_layers.active is not None

# Place a neighboring solid occluder close to the sphere so real hemisphere
# rays must encounter geometry. A convex sphere alone correctly bakes white AO
# and cannot prove that ambient occlusion intersection logic is functional.
# UV atlas: sphere on left half, wall on right half, with no overlaps.
for uv in low.data.uv_layers.active.data:
    uv.uv.x *= 0.5
bpy.ops.mesh.primitive_cube_add(size=1,location=(.56,0,.52))
wall_low=bpy.context.object
wall_low.name="AO_Occluder_Low"
wall_low.dimensions=(.09,.70,.70)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
move(wall_low,lo)
wall_low.data.materials.append(mat)
assert wall_low.data.uv_layers.active is not None
for uv in wall_low.data.uv_layers.active.data:
    uv.uv.x = 0.5 + uv.uv.x*0.5
bpy.ops.object.select_all(action="DESELECT")
low.select_set(True)
wall_low.select_set(True)
bpy.context.view_layer.objects.active=low
bpy.ops.object.join()
assert len(lo.all_objects)==1, "Low fixture must be one joined UV-atlased mesh"
assert len(low.data.materials)==1

bpy.ops.mesh.primitive_cube_add(size=1,location=(.56,0,.52))
wall_high=bpy.context.object
wall_high.name="AO_Occluder_High"
wall_high.dimensions=(.095,.705,.705)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
move(wall_high,hi)
wall_high.data.materials.append(high.data.materials[0])
bpy.ops.object.select_all(action="DESELECT")
high.select_set(True)
wall_high.select_set(True)
bpy.context.view_layer.objects.active=high
bpy.ops.object.join()
assert len(hi.all_objects)==1, "High fixture must be one joined mesh"

bpy.ops.wm.save_as_mainfile(filepath=str(root/"test_master.blend"))
for name,color in (("base_color",(.22,.41,.59,1)),("roughness",(.68,.68,.68,1)),("metallic",(.14,.14,.14,1))):
    img=bpy.data.images.new("TEST_"+name,width=128,height=128,alpha=True)
    img.pixels[:]=list(color)*(128*128)
    img.filepath_raw=str(root/(name+".png"));img.file_format="PNG";img.save()
print("Fixture prepared:",str(root))
