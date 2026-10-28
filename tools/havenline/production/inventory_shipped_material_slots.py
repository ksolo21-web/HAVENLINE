#!/usr/bin/env python3
"""Read-only inventory of REAL authored material slots from shipping mesh sources.

This is source-level evidence only. glTF material slots/texture assignments are
not the actual Godot-rendered appearance, and neither scores nor independent
C1/C2 results are fabricated. This expands the T70 source-file census into
specific material-slot review work.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re
import struct
import collections

from inventory_shipped_visual_sources import ROOT, census

MAX_FILE_BYTES=90*1024*1024
VERSION=1


def digest(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()


def gltf_document(data: bytes, suffix: str) -> dict:
    if suffix==".glb":
        if len(data)<20 or data[:4]!=b"glTF":
            raise ValueError("Not a GLB; missing real binary header (possibly LFS pointer)")
        version,total=struct.unpack_from("<II",data,4)
        if version!=2 or total!=len(data):
            raise ValueError("Invalid binary glTF version or length")
        size,kind=struct.unpack_from("<I4s",data,12)
        if kind!=b"JSON" or size<2 or size>len(data)-20:
            raise ValueError("Missing valid glTF JSON chunk")
        return json.loads(data[20:20+size])
    if suffix==".gltf":
        return json.loads(data)
    raise ValueError("Not a glTF mesh source")


def gltf_slots(data: bytes,suffix: str) -> dict:
    doc=gltf_document(data,suffix)
    mats=doc.get("materials",[])
    if not isinstance(mats,list):
        raise ValueError("glTF materials is not an array")
    meshes=doc.get("meshes",[])
    if not isinstance(meshes,list) or not meshes:
        raise ValueError("Mesh lacks glTF geometry")
    # A variant-only material is STILL a real rendered material: it can be
    # selected in Godot even if no default primitive references the slot.
    variant_specs=(doc.get("extensions") or {}).get("KHR_materials_variants",{}).get("variants",[])
    if not isinstance(variant_specs,list):
        raise ValueError("Invalid glTF material variant registry")
    use=[]
    variants_by_slot={}
    for mesh in meshes:
        if not isinstance(mesh,dict):
            raise ValueError("Invalid glTF mesh")
        primitives=mesh.get("primitives",[])
        for primitive in primitives:
            if not isinstance(primitive,dict):
                raise ValueError("Invalid glTF primitive")
            index=primitive.get("material")
            if index is not None and (type(index) is not int or index<0 or index>=len(mats)):
                raise ValueError("Primitive references out-of-range material slot")
            use.append(index)
            mappings=(primitive.get("extensions") or {}).get("KHR_materials_variants",{}).get("mappings",[])
            if not isinstance(mappings,list):
                raise ValueError("Invalid GLB material variants mappings")
            for mapping in mappings:
                material=mapping.get("material")
                choices=mapping.get("variants",[])
                if type(material) is not int or not 0<=material<len(mats):
                    raise ValueError("Variant references out-of-range material slot")
                if not isinstance(choices,list) or not choices:
                    raise ValueError("Variant mapping has no target names")
                for variant in choices:
                    if type(variant) is not int or not 0<=variant<len(variant_specs):
                        raise ValueError("Variant references unregistered name")
                    name=variant_specs[variant].get("name")
                    if not isinstance(name,str) or not name.strip():
                        raise ValueError("Unnamed material variant")
                    variants_by_slot.setdefault(material,set()).add(name)
                use.append(material)
    if not use:
        raise ValueError("No glTF mesh primitives")
    uses={i:use.count(i) for i in set(use)}
    rows=[]
    for i,mat in enumerate(mats):
        if not isinstance(mat,dict):
            raise ValueError("Malformed PBR material slot")
        name=mat.get("name") or "Unnamed_Slot_"+str(i)
        if not isinstance(name,str):
            raise ValueError("Malformed GLB material name")
        pbr=mat.get("pbrMetallicRoughness",{})
        if not isinstance(pbr,dict):
            raise ValueError("Malformed PBR fields")
        slots={"albedo":pbr.get("baseColorTexture"),
               "metallic_roughness":pbr.get("metallicRoughnessTexture"),
               "normal":mat.get("normalTexture"),
               "occlusion":mat.get("occlusionTexture"),
               "emissive":mat.get("emissiveTexture")}
        tex=doc.get("textures",[])
        for channel,target in slots.items():
            if target is not None and (not isinstance(target,dict) or
              type(target.get("index")) is not int or not isinstance(tex,list) or
              not 0<=target["index"]<len(tex)):
                raise ValueError("Invalid texture index for "+name+" "+channel)
        rows.append({
            "slot_id":str(i)+":"+name,
            "slot_index":i,"name":name,"referencing_primitives":uses.get(i,0),
            "glTF_variant_names":sorted(variants_by_slot.get(i,set())),
            "used_in_render_mesh":uses.get(i,0)>0,
            "texture_channels_bound":[name for name,ref in slots.items() if ref is not None],
            "material_json_sha256":digest(json.dumps(mat,sort_keys=True,separators=(",",":")).encode())
        })
    if None in uses:
        rows.append({"slot_id":"__GLTF_IMPLICIT_DEFAULT__",
                     "slot_index":None,"name":"Godot/glTF implicit default",
                     "referencing_primitives":uses[None],
                     "used_in_render_mesh":True,"texture_channels_bound":[],
                     "material_json_sha256":None,
                     "implicit_default_must_be_replaced_before_visual_acceptance":True})
    return {"status":"STATIC_GLTF_SLOT_CENSUS_NOT_NATIVE_VISUAL_APPROVAL",
            "primitive_count":len(use),"material_slots":rows,
            "material_slot_count":len(rows),
            "unassigned_primitives":uses.get(None,0),
            "unused_authored_slots":sum(not r["used_in_render_mesh"] for r in rows)}


def obj_slots(data: bytes) -> dict:
    used=[]
    for line in data.decode("utf-8",errors="replace").splitlines():
        if line.lstrip().startswith("usemtl "):
            used.append(line.strip()[7:].strip())
    order=list(dict.fromkeys(used))
    if not order:
        # OBJ allows faces with no usemtl. This is an *implicit* default
        # material until a real runtime shader/material override is proven.
        # Do not mark a legitimate runtime VFX mesh broken merely because
        # its material is configured by the real Godot script instead.
        if not any(line.lstrip().startswith("f ") for line in
                   data.decode("utf-8", errors="replace").splitlines()):
            raise ValueError("OBJ has neither material assignment nor mesh faces")
        return {"status":"STATIC_OBJ_RUNTIME_MATERIAL_BINDING_REQUIRED",
                "runtime_override_required":True,
                "primitive_count":sum(line.lstrip().startswith("f ") for line in
                    data.decode("utf-8",errors="replace").splitlines()),
                "material_slots":[{"slot_id":"__OBJ_NO_AUTHORED_MATERIAL__",
                   "slot_index":None,"name":"OBJ geometry, runtime material not yet verified",
                   "used_in_render_mesh":False,"texture_channels_bound":[],
                   "material_json_sha256":None}],
                "material_slot_count":1}
    return {"status":"STATIC_OBJ_MTL_NAME_CENSUS_NEEDS_GODOT_IMPORT_VERIFICATION",
            "primitive_count":None,"material_slots":[
                {"slot_id":str(i)+":"+n,"slot_index":i,"name":n,
                 "used_in_render_mesh":True,"texture_channels_bound":[],
                 "material_json_sha256":None} for i,n in enumerate(order)
                if n],"material_slot_count":len(order)}


def resolve_obj_runtime_shader_binding(root: pathlib.Path, obj_shipping_path: str,
                                       script_paths: list[str]) -> dict:
    """Read-only link from source OBJ to actual Godot GDScript shader override.

    This checks the real runtime shader authoring path, not its rendered result.
    It requires the shader and concrete per-direction colored material setups.
    New shader styles or effects need explicit source binding changes, not
    permission to silently reuse a generic default.
    """
    if not obj_shipping_path.startswith("HavenlineGodot/") or not obj_shipping_path.endswith(".obj"):
        raise ValueError("Invalid shipping OBJ path")
    uri="res://"+obj_shipping_path[len("HavenlineGodot/"):]
    matches=[]
    for rel in script_paths:
        if not rel.startswith("HavenlineGodot/") or not rel.endswith(".gd"):
            continue
        script=(root/rel).resolve()
        script.relative_to(root.resolve())
        if not script.is_file():
            continue
        raw=script.read_bytes()
        body=raw.decode("utf-8")
        if uri not in body:
            continue
        # Ensure both a material and mesh reference are actually bound
        # together in runtime authoring. Mere text in a comment is insufficient.
        patterns=(r"ShaderMaterial\.new\s*\(",r"\bmaterial_override\s*=\s*material\b",
                  r"\bFEEDBACK_MESHES\s*:?\s*=",r"\bFEEDBACK_SHADER\s*:?\s*=",
                  r"result\.multimesh\s*=\s*instances",r"instances\.mesh\s*=\s*mesh")
        if any(not re.search(p,body) for p in patterns):
            raise ValueError(rel+" references OBJ but source runtime shader override chain is unproven")
        shaders=re.findall(r'["\'](res://[^"\']+\.gdshader)["\']',body)
        shader_uris=sorted(set(shaders))
        if len(shader_uris)!=1:
            raise ValueError(rel+" has ambiguous or absent actual runtime shader")
        shader_rel="HavenlineGodot/"+shader_uris[0][len("res://"):]
        shader=(root/shader_rel).resolve()
        shader.relative_to(root.resolve())
        if not shader.is_file() or "shader_type spatial;" not in shader.read_text():
            raise ValueError("Referenced native spatial shader missing/invalid")
        colors=sorted(set(re.findall(r'Color\s*\(\s*["\']([0-9a-fA-F]{6})["\']\s*\)',body)))
        required={"5deaff","ffb548"}
        if not required.issubset(set(c.lower() for c in colors)):
            raise ValueError("No exact independent two-direction runtime VFX colors")
        # Each OBJ is selected as trail/arrow/pulse and has both directions.
        # A varying shader role must be inspected in Godot; do not mark it as
        # a fixed authored OBJ material or assume it visually passes.
        stem=pathlib.PurePosixPath(obj_shipping_path).stem
        kind={"transfer_trail_ribbon":"trail",
              "transfer_arrow_sigil":"arrow",
              "transfer_arrival_burst":"pulse"}.get(stem)
        if kind is None or not re.search(
                rf'["\']{re.escape(kind)}["\']\s*:\s*["\']{re.escape(uri)}["\']',body):
            raise ValueError("OBJ runtime identity not actually bound to effect kind")
        role={"trail":0.0,"arrow":1.0,"pulse":2.0}[kind]
        if not re.search(rf'_make_feedback_instances\(\s*["\']{re.escape(kind)}["\'].*,\s*{role:.1f}\)',body):
            raise ValueError("Effect shader role binding missing")
        variants=[
            {"slot_id":"runtime:"+direction,"slot_index":i,
             "name":"Godot shader "+kind+" "+direction,
             "used_in_render_mesh":True,
             "shader_uniforms":{"tint":hexcolor,"role":role},
             "runtime_material_variant":True,
             "texture_channels_bound":[],
             "material_json_sha256":None}
            for i,(direction,hexcolor) in enumerate(
                (("source_to_actor","5deaff"),("actor_to_destination","ffb548")))
        ]
        matches.append({
            "status":"STATIC_SCRIPT_AND_SHADER_BOUND_RUNTIME_VFX_NOT_NATIVE_VISUAL_PROOF",
            "mesh_uri":uri,"script_path":rel,"script_sha256":digest(raw),
            "shader_path":shader_rel,"shader_sha256":digest(shader.read_bytes()),
            "effect_kind":kind,"role":role,
            "runtime_color_variants":[x["slot_id"] for x in variants],
            "runtime_material_variants":variants,
            "native_Godot_runtime_visual_checked":False
        })
    if len(matches)!=1:
        raise ValueError("OBJ runtime shader binding missing/ambiguous (matches="+str(len(matches))+")")
    return matches[0]


def inspect_sources(source_census: dict,root: pathlib.Path=ROOT) -> dict:
    items=[]
    total_model_slots=0
    failures=[]
    scripts=[x["shipping_path"] for x in source_census.get("source_items",[])
             if x.get("source_class")=="code_created_or_modified_material"]
    for entry in source_census.get("source_items",[]):
        if entry.get("source_class")!="mesh_or_geometry":
            continue
        path=entry["shipping_path"]
        suffix=pathlib.PurePosixPath(path).suffix.lower()
        r={"shipping_path":path,"git_blob_oid":entry.get("git_blob_oid"),
           "authoritative_reference_pixels_bound":False,
           "native_Godot_material_render_verified":False,
           "actual_C1_C2_review_passed":False}
        try:
            source=(root/path).resolve()
            source.relative_to(root.resolve())
            if not source.is_file() or not 0<source.stat().st_size<=MAX_FILE_BYTES:
                raise ValueError("Physical mesh source absent/invalid; LFS files must be hydrated")
            data=source.read_bytes()
            r["source_sha256"]=digest(data)
            if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
                raise ValueError("Unhydrated Git LFS pointer; real model unavailable")
            if suffix in (".glb",".gltf"):
                parsed=gltf_slots(data,suffix)
            elif suffix==".obj":
                parsed=obj_slots(data)
                if parsed.get("runtime_override_required"):
                    runtime=resolve_obj_runtime_shader_binding(root,path,scripts)
                    parsed["runtime_binding"]=runtime
                    parsed["material_slots"]=runtime["runtime_material_variants"]
                    parsed["material_slot_count"]=len(parsed["material_slots"])
                    parsed["status"]="STATIC_OBJ_RUNTIME_SHADER_VARIANTS_LINKED_NOT_VISUAL_APPROVED"
                    parsed["runtime_override_required"]=True
            else:
                raise ValueError("Other format requires native Godot mesh inspector")
            r.update(parsed)
            total_model_slots+=parsed["material_slot_count"]
            if parsed.get("unassigned_primitives",0) or parsed.get("unused_authored_slots",0):
                failures.append(path+": implicit/unused material slots need separate review")
        except (OSError,UnicodeError,ValueError,KeyError,IndexError,TypeError,struct.error) as exc:
            r["status"]="STATIC_MATERIAL_SLOT_INVENTORY_UNRESOLVED"
            r["error"]=str(exc)
            failures.append(path+": "+str(exc))
        items.append(r)
    return {
        "schema_version":VERSION,
        "status":"SOURCE_MATERIAL_SLOTS_ENUMERATED_NOT_GODOT_CRITIC_REVIEW",
        "shipping_ref_commit":source_census.get("shipping_ref_commit"),
        "mesh_source_count":len(items),
        "resolved_mesh_source_count":sum(x["status"].startswith("STATIC_") and
                                         x["status"]!="STATIC_MATERIAL_SLOT_INVENTORY_UNRESOLVED" for x in items),
        "glTF_and_OBJ_material_slots_known":total_model_slots,
        "unresolved_mesh_source_count":sum(x["status"]=="STATIC_MATERIAL_SLOT_INVENTORY_UNRESOLVED" for x in items),
        "source_art_and_shader_files_not_in_model_slot_count":source_census.get("identified_visual_source_paths",0)-len(items),
        "all_materials_reviewed":False,
        "source_slot_defects_or_inspection_gaps":failures,
        "models":items
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ref",default="HEAD")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    result=inspect_sources(census(a.ref))
    pathlib.Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="models"},indent=2))


if __name__=="__main__":
    main()
