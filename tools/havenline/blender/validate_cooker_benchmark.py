#!/usr/bin/env python3
"""Fail-closed technical checks for isolated Blender-authored T05 cooker export.

This checks production constraints, not image fidelity or owner approval.
It must never write into the canonical Godot asset directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import pathlib
import struct
import sys

import numpy as np
import trimesh
from PIL import Image, ImageChops, ImageStat

APPROVED_MATERIAL_NAMES={
    "HL_snow","HL_cream","HL_wood","HL_wood_light","HL_metal",
    "HL_blue","HL_cyan","HL_orange","HL_yellow","HL_green",
    "HL_red","HL_dark"
}
FRAMES=("front","three-quarter","right","rear")

def gltf_json(path):
    contents=path.read_bytes()
    assert len(contents)>=20,"GLB header too small"
    magic,version,length=struct.unpack_from("<4sII",contents,0)
    assert (magic,version,length)==(b"glTF",2,len(contents)),"Invalid GLB header"
    chunk_length,chunk_kind=struct.unpack_from("<I4s",contents,12)
    assert chunk_kind==b"JSON","First GLB chunk must be JSON"
    return json.loads(contents[20:20+chunk_length].decode("utf8"))

def check(out,catalog_path):
    out=pathlib.Path(out)
    catalog=json.loads(pathlib.Path(catalog_path).read_text())
    row=next(r for r in catalog["entries"] if r["id"]=="cooker_processor")
    base_tris=sum(r["triangles"] for r in catalog["entries"])
    max_kit_tris=catalog["performance_contract"]["triangles_max"]
    max_tris=int(max_kit_tris)-(base_tris-row["triangles"])
    model=out/"T05_cooker_BLENDER_CANDIDATE.glb"
    blend=out/"T05_cooker_EDITABLE.blend"
    assertions=[]
    def validate(name,condition,detail):
        assertions.append({"check":name,"pass":bool(condition),"detail":detail})
    validate("editable_blend_exists",blend.is_file() and blend.stat().st_size>16000,
             "editable source must exist and be nonempty")
    validate("game_glb_exists",model.is_file() and model.stat().st_size>6000,
             "game GLB must exist and be nonempty")
    if not model.is_file():
        return assertions,None
    blob=gltf_json(model)
    names=[m.get("name","") for m in blob.get("materials",[])]
    validate("shared_material_names",bool(names) and set(names).issubset(APPROVED_MATERIAL_NAMES),
             {"names":names,"illegal":sorted(set(names)-APPROVED_MATERIAL_NAMES)})
    validate("total_material_slots",len(names)<=12,{"count":len(names),"limit":12})
    names_in_nodes=[n.get("name","") for n in blob.get("nodes",[])]
    disallowed=("Studio ground","Review Camera","Light","RENDER_ONLY")
    validate("studio_not_exported",not any(any(w in node for w in disallowed) for node in names_in_nodes),
             "No stage floor, preview camera or lights in GLB")
    validate("no_skeleton_or_animations",not blob.get("skins") and not blob.get("animations"),
             "This static T05 prop must not contain skinned or animated parts")
    sc=trimesh.load(model,force="scene",process=False)
    meshes=[obj for obj in sc.geometry.values() if isinstance(obj,trimesh.Trimesh)]
    triangle_count=sum(len(m.faces) for m in meshes)
    # Reject invisible/empty Blender snow sculpts. A prior editable metaball
    # survived in the .blend but exported as NO mesh geometry: all four Godot
    # pictures showed bare blue oven roof despite an HL_snow material group.
    snow_sections=[]
    for node_name in sc.graph.nodes_geometry:
        transform, geometry_id = sc.graph[node_name]
        geometry = sc.geometry[geometry_id]
        material=getattr(geometry.visual,"material",None)
        if getattr(material,"name",None)!="HL_snow":
            continue
        elevated=geometry.copy()
        elevated.apply_transform(transform)
        snow_sections.append(elevated)
    roof_parts=[m for m in snow_sections if len(m.vertices) and float(m.bounds[1,1])>1.70]
    if roof_parts:
        all_vertices=np.vstack([m.vertices for m in roof_parts])
        snow_min=all_vertices.min(axis=0); snow_max=all_vertices.max(axis=0)
        roof_faces=sum(len(m.faces) for m in roof_parts)
        roof_present=(snow_max[1]>=1.88 and
                      snow_max[0]-snow_min[0]>=1.05 and
                      snow_max[2]-snow_min[2]>=.75 and
                      roof_faces>=250)
        snow_evidence={"roof_bounds":[snow_min.tolist(),snow_max.tolist()],
                       "roof_faces":roof_faces}
    else:
        roof_present=False
        snow_evidence={"roof_bounds":None,"roof_faces":0}
    validate("modelled_snow_hood_really_exported",roof_present,snow_evidence)
    validate("triangles_within_remaining_kit_budget",0<triangle_count<=max_tris,
             {"candidate":triangle_count,"allowable_if_others_unchanged":max_tris,
              "original_cooker":row["triangles"],"original_total":base_tris})
    bounds=np.asarray(sc.bounds,dtype=float)
    validate("finite_aabb",bounds.shape==(2,3) and bool(np.isfinite(bounds).all()),bounds.tolist())
    if bounds.shape==(2,3):
        min_x,min_y,min_z=bounds[0];max_x,max_y,max_z=bounds[1]
        # Fixed placement has 2.45m x 2.30m T05 footprint; no enlarged
        # collision/interaction area permitted from visual authoring.
        validate("locked_horizontal_footprint",
                 min_x>=-1.225-.035 and max_x<=1.225+.035
                 and min_z>=-1.15-.035 and max_z<=1.15+.035,
                 {"bounds":bounds.tolist(),"max_xz":[2.45,2.30]})
        validate("proper_game_Y_up",
                 min_y>=-.12 and 1.5<max_y<2.8,
                 {"game_y":[float(min_y),float(max_y)]})
    tex=[]
    for name in ("wood","wood_light","blue","metal"):
        p=out/f"T05_{name}_basecolor.png"
        if p.exists():
            with Image.open(p) as im:tex.append({"file":p.name,"size":im.size,"bytes":p.stat().st_size})
    validate("small_source_texture_tiles",len(tex)==4 and all(x["size"]==(256,256) for x in tex),
             tex)
    im_ref=None
    for name in FRAMES:
        p=out/f"T05_cooker_{name}.png"
        if not p.is_file():
            validate(f"render_{name}",False,"missing preview render")
            continue
        with Image.open(p) as source:
            im=source.convert("RGB")
            stddev=ImageStat.Stat(im).stddev
            validate(f"render_{name}",im.size==(640,640) and max(stddev)>8,
                     {"size":im.size,"contrast_stddev":stddev})
            if name=="front":im_ref=im.copy()
            if name=="rear" and im_ref is not None:
                validate("camera_views_differ",
                         ImageStat.Stat(ImageChops.difference(im,im_ref)).mean[0]>3,
                         "front and rear must not be identical frames")
    footprint_delta=triangle_count-row["triangles"]
    report={
      "schema_version":1,
      "task":"HAVENLINE T05 Blender cooker authoring benchmark",
      "technical_gate":"PASS" if all(x["pass"] for x in assertions) else "FAIL",
      "production_approval":False,
      "user_reference":"18567.png",
      "preview_not_godot":True,
      "target_kit_budget_triangle_delta":footprint_delta,
      "candidate_glb_sha256":hashlib.sha256(model.read_bytes()).hexdigest(),
      "editable_blend_sha256":hashlib.sha256(blend.read_bytes()).hexdigest() if blend.is_file() else None,
      "material_names":names,
      "checks":assertions,
      "remaining": [
        "manual object-specific reference comparison",
        "native Godot material and batch integration",
        "strict >9 independent critic on all axes and 10/10 reference standard",
        "on-device Android FPS/memory C6",
        "owner visual approval"
      ],
    }
    (out/"technical_validation.json").write_text(json.dumps(report,indent=2)+"\n")
    return assertions,report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True)
    parser.add_argument("--catalog",required=True)
    args=parser.parse_args()
    checks,report=check(args.out,args.catalog)
    print(json.dumps({"technical_gate":report["technical_gate"] if report else "FAIL",
                     "checks":checks},indent=2))
    sys.exit(0 if report and report["technical_gate"]=="PASS" else 1)
