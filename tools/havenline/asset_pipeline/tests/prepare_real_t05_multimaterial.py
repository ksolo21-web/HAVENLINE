#!/usr/bin/env python3
"""Read-only adapter for real unapproved T05 cooker to global material baker.

Blender editable R07 source and the R07 GLB are authoritative inputs, kept
byte-identical; this stages independent high and low mesh collections to test
compatibility with the 9-material BVH candidate tool. NOT visual approval.
"""
import argparse,hashlib,json,pathlib,sys,bpy
from mathutils import Vector

def mesh_collection(name):
    c=bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c

def selected_join(objects,active):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=active
    if len(objects)>1:
        bpy.ops.object.join()
    result=bpy.context.view_layer.objects.active
    bpy.ops.object.select_all(action="DESELECT")
    result.select_set(True)
    bpy.context.view_layer.objects.active=result
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    result.select_set(False)
    return result

def bounds(o):
    verts=[o.matrix_world @ Vector(corner) for corner in o.bound_box]
    return [min(x[i] for x in verts) for i in range(3)], [max(x[i] for x in verts) for i in range(3)]

def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument("--editable",required=True)
    parser.add_argument("--candidate-glb",required=True)
    parser.add_argument("--out",required=True)
    a=parser.parse_args(args)
    editable=pathlib.Path(a.editable).resolve()
    original_glb=pathlib.Path(a.candidate_glb).resolve()
    out=pathlib.Path(a.out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    if not editable.is_file() or not original_glb.is_file():
        raise RuntimeError("Exact original T05 R07 artifacts required")
    expected="ff9f548c2d16d1f5972b4da2f3162978e65e3caef20ec998ec222e9497cb3a0b"
    if hashlib.sha256(original_glb.read_bytes()).hexdigest()!=expected:
        raise RuntimeError("Unverified cooker GLB, refusing candidate bridge")
    bpy.ops.wm.open_mainfile(filepath=str(editable))
    source=bpy.data.collections.get("T05_Cooker_EDITABLE_Source")
    if source is None:raise RuntimeError("Original editable cooker source not found")
    authored=[o for o in source.all_objects if o.type in ("MESH","CURVE")]
    if not authored:raise RuntimeError("No authentic editable cooker source geometry")
    hi=mesh_collection("DETAIL_MASTER")
    clones=[]
    for o in authored:
        new=o.copy()
        new.data=o.data.copy()
        new.name="DETAIL_COPY_"+o.name
        hi.objects.link(new)
        clones.append(new)
    # Apply artist's bevel/subdivision modifiers on copied high-detail geometry,
    # never to the untouched original editable source collection.
    joined=[]
    for o in clones:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.convert(target="MESH")
        current=bpy.context.view_layer.objects.active
        if current is None or current.type!="MESH":
            raise RuntimeError("Blender failed to convert authored source "+o.name)
        joined.append(current)
    high=selected_join(joined,joined[0])
    high.name="REAL_T05_R07_DETAIL_MASTER_JOINED"
    # Keep original material appearance intact. Source palette names must not
    # shadow the separate imported low-GLB material names.
    original_names=("HL_wood","HL_dark","HL_wood_light","HL_blue",
                    "HL_metal","HL_orange","HL_red","HL_cream","HL_snow")
    for m in bpy.data.materials:
        if m.name in original_names:
            m.name=m.name+"__UNMODIFIED_EDITABLE"
    before=set(o.name for o in bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(original_glb))
    imported=[o for o in bpy.data.objects if o.name not in before and o.type=="MESH"]
    if len(imported)!=9:
        raise RuntimeError("Expected 9 separately optimized original GLB primitives, got "+str(len(imported)))
    low_collection=mesh_collection("GAME_LOD0")
    for o in imported:
        for c in list(o.users_collection):c.objects.unlink(o)
        low_collection.objects.link(o)
    low=selected_join(imported,imported[0])
    low.name="REAL_T05_R07_GAME_LOD0"
    low_names=[m.name for m in low.data.materials if m is not None]
    if len(low_names)!=9 or set(low_names)!=set(original_names):
        raise RuntimeError("Real cooker GLB PBR material identity changed: "+str(low_names))
    if not low.data.uv_layers.active:
        raise RuntimeError("Real cooker optimized UVs missing")
    if len({p.material_index for p in low.data.polygons})!=9:
        raise RuntimeError("Some real cooker shader slots were lost when joining")
    high_min,high_max=bounds(high)
    low_min,low_max=bounds(low)
    high_center=[(x+y)/2 for x,y in zip(high_min,high_max)]
    low_center=[(x+y)/2 for x,y in zip(low_min,low_max)]
    delta=max(abs(x-y) for x,y in zip(high_center,low_center))
    print("HAVENLINE_REAL_T05_COORDINATE_ALIGNMENT",{
      "high_bounds":[high_min,high_max],"low_bounds":[low_min,low_max],
      "center_delta_m":delta,"source_objects":len(authored)},flush=True)
    if delta>.3:
        raise RuntimeError("Author/source coordinate origins diverge >0.3m, cannot perform trustworthy bake")
    staged=out/"T05_R07_MULTIMATERIAL_HIGHLOW_STAGE.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(staged))
    expected_tri=sum(len(p.vertices)-2 for p in low.data.polygons)
    record={"status":"T05_R07_SOURCE_BRIDGE_NOT_REFERENCE_APPROVED",
            "input_editable_sha256":hashlib.sha256(editable.read_bytes()).hexdigest(),
            "input_glb_sha256":expected,
            "source_editable_original_untouched":True,
            "high_authored_objects":len(authored),
            "low_triangles":expected_tri,
            "low_materials":low_names,
            "source_highlow_center_delta_m":delta,
            "staged_blend":staged.name,
            "owner_style_approved":False,
            "t05_shipping_asset_modified":False}
    (out/"t05_bridge.json").write_text(json.dumps(record,indent=2)+"\n")
    print("HAVENLINE_REAL_T05_STAGE",json.dumps(record),flush=True)
if __name__=="__main__":
    main()
