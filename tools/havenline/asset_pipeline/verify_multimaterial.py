#!/usr/bin/env python3
"""Fail-closed technical audit for material-preserving geometry normal/AO GLBs."""
import argparse,hashlib,json,pathlib,struct,sys
from io import BytesIO
from PIL import Image

def read_glb(path):
    raw=path.read_bytes()
    if len(raw)<28 or raw[:4]!=b"glTF" or struct.unpack_from("<I",raw,4)[0]!=2:
        raise ValueError("Invalid glTF version 2 binary")
    if struct.unpack_from("<I",raw,8)[0]!=len(raw):raise ValueError("Inconsistent GLB length")
    size,kind=struct.unpack_from("<I4s",raw,12)
    if kind!=b"JSON":raise ValueError("GLB first chunk must be JSON")
    data=json.loads(raw[20:20+size])
    bstart=20+size
    blen,btype=struct.unpack_from("<I4s",raw,bstart)
    if btype!=bytes((66,73,78,0)):raise ValueError("No embedded GLB binary payload")
    return data,raw[bstart+8:bstart+8+blen]

def embedded_png(doc,payload,material):
    t=material.get("normalTexture")
    if not isinstance(t,dict):raise ValueError("Material lacks normalTexture: "+material["name"])
    tex=doc["textures"][t["index"]]
    im=doc["images"][tex["source"]]
    if im.get("mimeType")!="image/png":raise ValueError("Normal must be embedded PNG")
    v=doc["bufferViews"][im["bufferView"]]
    if v.get("buffer",0)!=0:raise ValueError("Image must use GLB binary")
    begin=v.get("byteOffset",0)
    end=begin+v["byteLength"]
    if begin<0 or end>len(payload) or end<=begin:raise ValueError("Embedded image bounds invalid")
    return payload[begin:end]

def execute(root,min_materials):
    report=json.loads((root/"multimaterial_bake_report.json").read_text())
    if report["state"]!="PRESERVED_MULTIMATERIAL_TECHNICAL_CANDIDATE_NOT_VISUAL_APPROVAL":
        raise ValueError("Candidate state invalid")
    if report["materials_preserved"]<min_materials or not report["source_pbr_base_metal_roughness_preserved"]:
        raise ValueError("Source shader preservation not established")
    if report.get("reference_style_approved") or report.get("real_shipping_scene_tested"):
        raise ValueError("No visual or shipping approval may be inferred from this test")
    glb=root/(report["asset_id"]+"_MULTIMATERIAL_STAGE.glb")
    if hashlib.sha256(glb.read_bytes()).hexdigest()!=report["exported_glb_sha256"]:
        raise ValueError("GLB identity changed")
    doc,binary=read_glb(glb)
    materials=doc.get("materials",[])
    entries=report["material_results"]
    if len(materials)!=len(entries) or len(materials)<min_materials:
        raise ValueError("Material slots dropped")
    names={m["name"] for m in materials}
    if names!={m["original_name"] for m in entries}:
        raise ValueError("Original material names not preserved")
    primitives=[p for m in doc["meshes"] for p in m["primitives"]]
    used={p["material"] for p in primitives}
    if used!=set(range(len(materials))):
        raise ValueError("One or more original material surfaces missing")
    if any("TANGENT" not in p.get("attributes",{}) for p in primitives):
        raise ValueError("Normal mapped primitives lack explicit tangent vectors")
    audit=[]
    ao_total=0
    for entry in entries:
        assert entry["material_source_pbr_unchanged"] is True
        mat=next(m for m in materials if m["name"]==entry["original_name"])
        normal=root/entry["textures"]["normal"]["path"]
        ao=root/entry["textures"]["ambient_occlusion"]["path"]
        for key,p in (("normal",normal),("ambient_occlusion",ao)):
            if hashlib.sha256(p.read_bytes()).hexdigest()!=entry["textures"][key]["sha256"]:
                raise ValueError("Saved map hash mismatch "+str(p))
            with Image.open(p) as image:
                rgba=image.convert("RGBA")
                if rgba.size[0]<64 or rgba.size[1]<64:
                    raise ValueError("Invalid texture resolution")
                rgba.load()
                colors=rgba.getdata()
                count=sum(1 for r,g,b,a in colors if a>127 and
                         ((b>=160 and b>=r+14 and b>=g+14) if key=="normal"
                          else max(r,g,b)>=32 and max(r,g,b)-min(r,g,b)<=10))
                if count<8:raise ValueError("Invalid saved material bake "+key)
        payload=embedded_png(doc,binary,mat)
        with Image.open(BytesIO(payload)) as image, Image.open(normal) as source:
            same=image.convert("RGBA").tobytes()==source.convert("RGBA").tobytes()
        if not same:raise ValueError("Embedded normal PNG pixels changed for "+mat["name"])
        stats=entry["stats"]
        if stats["material_index"]!=entry["slot"] or stats["high_to_low_ray_hits"]<8:
            raise ValueError("Geometry projection not verified for "+mat["name"])
        ao_total+=stats["ambient_occlusion_intersections"]
        audit.append({"name":mat["name"],"material_index":entry["slot"],
                      "rasterized_pixels":stats["rasterized_pixels"],
                      "projected_high_ray_hits":stats["high_to_low_ray_hits"],
                      "ao_intersections":stats["ambient_occlusion_intersections"],
                      "normal_map_embedded_pixel_match":True})
    if ao_total<=0:raise ValueError("Controlled multi-material fixture has no true AO intersections")
    result={"state":"MULTIMATERIAL_BVH_TECHNICAL_PASS_NOT_STYLE_APPROVAL",
            "material_count":len(materials),"primitive_count":len(primitives),
            "ao_real_intersections":ao_total,"materials":audit,
            "all_original_material_names_preserved":True,
            "all_encoded_normal_maps_bind_and_match":True,
            "native_game_render_tested":False,
            "real_shipping_scene_tested":False,
            "physical_android_tested":False,
            "owner_reference_approved":False}
    (root/"multimaterial_validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--min-materials",type=int,default=2)
    a=ap.parse_args()
    execute(pathlib.Path(a.workspace).resolve(),a.min_materials)
