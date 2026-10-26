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
bpy.ops.wm.save_as_mainfile(filepath=str(root/"test_master.blend"))
for name,color in (("base_color",(.22,.41,.59,1)),("roughness",(.68,.68,.68,1)),("metallic",(.14,.14,.14,1))):
    img=bpy.data.images.new("TEST_"+name,width=128,height=128,alpha=True)
    img.pixels[:]=list(color)*(128*128)
    img.filepath_raw=str(root/(name+".png"));img.file_format="PNG";img.save()
print("Fixture prepared:",str(root))
