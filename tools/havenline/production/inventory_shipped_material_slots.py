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
    use=[]
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
        raise ValueError("OBJ lacks explicit source material assignments")
    return {"status":"STATIC_OBJ_MTL_NAME_CENSUS_NEEDS_GODOT_IMPORT_VERIFICATION",
            "primitive_count":None,"material_slots":[
                {"slot_id":str(i)+":"+n,"slot_index":i,"name":n,
                 "used_in_render_mesh":True,"texture_channels_bound":[],
                 "material_json_sha256":None} for i,n in enumerate(order)
                if n],"material_slot_count":len(order)}


def inspect_sources(source_census: dict,root: pathlib.Path=ROOT) -> dict:
    items=[]
    total_model_slots=0
    failures=[]
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
