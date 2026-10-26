#!/usr/bin/env python3
"""Candidate-only multi-material PBR baker.

Preserves every authored low-mesh material and its existing Base Color,
Metallic and Roughness channels. Each material gets a separate geometry-raycast
normal map and AO sidecar: UVs may overlap across *different* materials.
Never modifies production assets or the input .blend.

Requires joined DETAIL_MASTER and GAME_LOD0 mesh collections. This does NOT
automatically retopologize or improve reference style. In particular, an old
R07 cooker GLB without a separate high/low sculpt cannot be passed off as
a finished high-detail bake.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys
import bpy

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from bvh_bake import bake as geometry_bake

def _one_mesh(name):
    collection=bpy.data.collections.get(name)
    if collection is None:
        raise RuntimeError("Missing required collection "+name)
    meshes=[x for x in collection.all_objects if x.type=="MESH"]
    if len(meshes)!=1:
        raise RuntimeError(name+" requires exactly one joined mesh, got "+str(len(meshes)))
    return meshes[0]

def _target(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    return str(path.resolve())

def _snapshot(mat):
    bs=mat.node_tree.nodes.get("Principled BSDF") if mat.use_nodes else None
    if bs is None:
        raise RuntimeError("Preserving PBR materials requires Principled BSDF "+mat.name)
    data={}
    for name in ("Base Color","Metallic","Roughness"):
        socket=bs.inputs[name]
        data[name]={
            "default":list(socket.default_value) if hasattr(socket.default_value,"__len__") else float(socket.default_value),
            "links":sorted((link.from_node.name, link.from_socket.name) for link in socket.links)
        }
    return data

def _add_normal(mat,image):
    bs=mat.node_tree.nodes["Principled BSDF"]
    if bs.inputs["Normal"].is_linked:
        raise RuntimeError("Refusing to replace pre-existing authored normal shader for "+mat.name)
    nodes=mat.node_tree.nodes
    image_node=nodes.new("ShaderNodeTexImage")
    image_node.name="HL_GEOMETRY_BAKE_NORMAL"
    image_node.image=image
    normal=nodes.new("ShaderNodeNormalMap")
    normal.name="HL_GEOMETRY_BAKE_TANGENT"
    normal.space="TANGENT"
    mat.node_tree.links.new(image_node.outputs["Color"],normal.inputs["Color"])
    mat.node_tree.links.new(normal.outputs["Normal"],bs.inputs["Normal"])

def main():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--asset-id",required=True)
    parser.add_argument("--size",type=int,default=128)
    parser.add_argument("--triangles-max",type=int,default=20000)
    parser.add_argument("--materials-max",type=int,default=12)
    a=parser.parse_args(argv)
    if a.size<64 or a.size>1024 or a.size&(a.size-1):
        raise RuntimeError("BVH material-preserving baker supports power-of-two 64..1024 only")
    if not re.fullmatch(r"[A-Za-z0-9_\\-]{1,64}",a.asset_id):
        raise RuntimeError("Invalid asset id")
    source=pathlib.Path(a.source).resolve()
    if not source.is_file():raise RuntimeError("Editable source .blend required")
    root=pathlib.Path(a.out).resolve()
    root.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    high=_one_mesh("DETAIL_MASTER")
    low=_one_mesh("GAME_LOD0")
    if high is low:raise RuntimeError("High and low source meshes must differ")
    if low.data.uv_layers.active is None:
        raise RuntimeError("Artist-authored GAME_LOD0 UVs required")
    originals=list(low.data.materials)
    if not 2<=len(originals)<=a.materials_max:
        raise RuntimeError("Preservation path requires 2..%d distinct material slots"%a.materials_max)
    if any(m is None for m in originals) or len({m.name for m in originals})!=len(originals):
        raise RuntimeError("Missing or duplicate source materials")
    if any(abs(float(v)-1.0)>1e-4 for o in (high,low) for v in o.scale):
        raise RuntimeError("Applied high and low transforms required for ray distance")
    triangles=sum(len(p.vertices)-2 for p in low.data.polygons)
    if triangles==0 or triangles>a.triangles_max:
        raise RuntimeError("Low mesh triangle limit exceeded")
    used={p.material_index for p in low.data.polygons}
    if used!=set(range(len(originals))):
        raise RuntimeError("Every source material must own actual geometry; unused slots rejected")
    before={m.name:_snapshot(m) for m in originals}
    record=[]
    images={}
    for i,material in enumerate(originals):
        name=material.name
        tex=root/"textures"
        normal=bpy.data.images.new("HL_BVH_NORMAL_"+str(i),width=a.size,height=a.size,alpha=False)
        ao=bpy.data.images.new("HL_BVH_AO_"+str(i),width=a.size,height=a.size,alpha=False)
        normal.colorspace_settings.name="Non-Color"
        ao.colorspace_settings.name="Non-Color"
        stats=geometry_bake(high,low,a.size,normal,ao,material_index=i,
                            minimum_pixels=8,minimum_coverage=.001)
        # The color/metallic/roughness source shader must stay intact.
        _add_normal(material,normal)
        if _snapshot(material)!=before[name]:
            raise RuntimeError("Authored PBR source inputs altered for "+name)
        targets={}
        for key,image in (("normal",normal),("ambient_occlusion",ao)):
            path=tex/("slot_%02d_%s.png"%(i,key))
            image.filepath_raw=_target(path)
            image.file_format="PNG"
            image.save()
            if path.stat().st_size<=128:
                raise RuntimeError("Empty material bake map "+str(path))
            targets[key]={"path":str(path.relative_to(root)),
                          "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        record.append({"slot":i,"original_name":name,
                       "material_source_pbr_unchanged":True,"textures":targets,"stats":stats})
        images[name]=normal
    # Original source file remains immutable. This copy is unapproved staged work.
    bpy.ops.file.pack_all()
    out_blend=root/(a.asset_id+"_MULTIMATERIAL_STAGE.blend")
    bpy.ops.wm.save_as_mainfile(filepath=_target(out_blend))
    bpy.ops.object.select_all(action="DESELECT")
    low.select_set(True)
    bpy.context.view_layer.objects.active=low
    out_glb=root/(a.asset_id+"_MULTIMATERIAL_STAGE.glb")
    bpy.ops.export_scene.gltf(filepath=_target(out_glb),
        export_format="GLB",use_selection=True,export_yup=True,
        export_apply=True,export_tangents=True)
    if out_glb.stat().st_size<=128:raise RuntimeError("Exported GLB empty")
    report={
        "state":"PRESERVED_MULTIMATERIAL_TECHNICAL_CANDIDATE_NOT_VISUAL_APPROVAL",
        "asset_id":a.asset_id,
        "input_source_blend_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "exported_glb_sha256":hashlib.sha256(out_glb.read_bytes()).hexdigest(),
        "materials_before":list(before),
        "low_triangles":triangles,
        "materials_preserved":len(originals),
        "source_pbr_base_metal_roughness_preserved":True,
        "independent_high_and_low_source_meshes":True,
        "native_godot_tested":False,
        "real_shipping_scene_tested":False,
        "physical_android_tested":False,
        "reference_style_approved":False,
        "source_file_overwritten":False,
        "material_results":record
    }
    (root/"multimaterial_bake_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("HAVENLINE_MULTIMATERIAL_TECHNICAL_CANDIDATE "+json.dumps(report))
if __name__=="__main__":
    main()
