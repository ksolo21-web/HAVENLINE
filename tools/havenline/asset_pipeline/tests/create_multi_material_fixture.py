#!/usr/bin/env python3
"""Turn known synthetic sphere+wall test into two authentic shader slots.

The source is an editable test fixture, never a customer production model.
"""
import pathlib,sys,bpy
root=pathlib.Path(sys.argv[sys.argv.index("--")+1]).resolve()
source=root/"fixture"/"test_master.blend"
if not source.is_file():raise RuntimeError("Missing original geometry smoke fixture")
bpy.ops.wm.open_mainfile(filepath=str(source))
low=[o for o in bpy.data.collections["GAME_LOD0"].all_objects if o.type=="MESH"]
assert len(low)==1
low=low[0]
assert len(low.data.materials)==1
one=low.data.materials[0]
two=one.copy()
two.name="HL_metal"
two.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value=.56
two.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.33
two.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.72,.76,.82,1)
low.data.materials.append(two)
uv=low.data.uv_layers.active.data
counts=[0,0]
for polygon in low.data.polygons:
    x=sum(uv[i].uv.x for i in polygon.loop_indices)/len(polygon.loop_indices)
    idx=0 if x<.5 else 1
    polygon.material_index=idx
    counts[idx]+=1
assert min(counts)>0,counts
output=root/"multimaterial-fixture.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(output))
print("HAVENLINE_MULTIMATERIAL_FIXTURE",{"source":str(source),"materials":counts,"file":str(output)})
