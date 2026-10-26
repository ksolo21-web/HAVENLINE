#!/usr/bin/env python3
"""HAVENLINE permanent cross-task art gate. Source lint != candidate pass != release.

Install for candidate/release: python -m pip install trimesh numpy pillow.
The core source-lint path is pure Python stdlib. The workflow NEVER writes GLBs
or Blender masters into the shipping game. It only reports evidence validity.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import pathlib
import struct
import sys
from typing import Any

REQUIRED_MAPS=("base_color","normal","roughness","metallic","ambient_occlusion")
REQUIRED_VIEWS=("front","rear","left","right","three-quarter","overhead","in_game_use")

def digest(path: pathlib.Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for buf in iter(lambda:f.read(1<<20),b""):
            h.update(buf)
    return h.hexdigest()

def load_json(path: pathlib.Path) -> dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict):raise ValueError("JSON object required: "+str(path))
    return data

def get_file(root: pathlib.Path,value: str) -> pathlib.Path:
    if not isinstance(value,str) or not value.strip():raise ValueError("Nonempty relative file path required")
    p=pathlib.Path(value)
    if p.is_absolute() or ".." in p.parts:raise ValueError("Path must stay inside workspace: "+value)
    full=(root/p).resolve()
    if not full.is_relative_to(root.resolve()):raise ValueError("File escaped workspace")
    return full

def parse_glb(path: pathlib.Path) -> dict:
    raw=path.read_bytes()
    if len(raw)<20:raise ValueError("Truncated GLB")
    magic,version,total=struct.unpack_from("<4sII",raw,0)
    if (magic,version,total)!=(b"glTF",2,len(raw)):raise ValueError("Invalid GLB v2 header/length")
    length,kind=struct.unpack_from("<I4s",raw,12)
    if kind!=b"JSON" or 20+length>len(raw):raise ValueError("GLB JSON chunk invalid")
    return json.loads(raw[20:20+length].decode("utf-8"))

def run(manifest: dict, policy: dict, root: pathlib.Path, mode: str) -> dict:
    checks=[]
    def check(name,condition,detail=None):
        checks.append({"check":name,"pass":bool(condition),"detail":detail})
        return bool(condition)
    def filecheck(name, rel, expected_sha=None):
        try:
            p=get_file(root,rel)
            ok=p.is_file() and p.stat().st_size>0
            if expected_sha is not None and ok:
                ok=digest(p).lower()==str(expected_sha).lower()
            check(name,ok,{"path":str(rel),"expected_sha256":expected_sha})
            return p if ok else None
        except (ValueError,OSError) as e:
            check(name,False,str(e))
            return None
    check("policy_global_scope",policy.get("scope")=="ALL_GAME_ART_ACROSS_ALL_TASKS_AND_FUTURE_BIOMES")
    check("owner_style_exact",policy.get("exact_style_scores")=={"reference_fidelity":10,"visual_language":10})
    check("asset_schema",manifest.get("schema_version")==1)
    check("asset_id",isinstance(manifest.get("asset_id"),str) and bool(manifest.get("asset_id","").strip()))
    check("task_id",isinstance(manifest.get("task_id"),str) and bool(manifest.get("task_id","").strip()))
    ref=manifest.get("owner_reference",{})
    check("exact_owner_reference_bound",ref.get("binding")=="exact_owner" and
          isinstance(ref.get("sha256"),str) and len(ref.get("sha256",""))==64 and
          isinstance(ref.get("path"),str) and bool(ref.get("path")))
    # External models and textures (even from "free" libraries) require
    # a recorded original source and license. Owner-provided target renders
    # are reference evidence, not automatically redistributable assets.
    external=manifest.get("external_assets")
    allowed=set(policy.get("license_policy",{}).get("allowed_license_spdx",[]))
    check("external_asset_license_census",isinstance(external,list) and all(
        isinstance(item,dict) and
        isinstance(item.get("name"),str) and bool(item.get("name")) and
        isinstance(item.get("source_url"),str) and item["source_url"].startswith("https://") and
        item.get("license") in allowed and item.get("license_verified") is True
        for item in (external if isinstance(external,list) else [])))
    outputs=manifest.get("outputs",{})
    check("master_low_and_bakes_declared",isinstance(outputs.get("master_blend"),str) and
          isinstance(outputs.get("low_glb"),str) and
          set(REQUIRED_MAPS).issubset(outputs.get("bake_maps",{})))
    limits=manifest.get("limits",{})
    required_limits=("footprint_x_m","footprint_z_m","triangles_max","materials_max",
                     "draw_calls_max","texture_mib_max","baseline_kit_triangles",
                     "baseline_asset_triangles","kit_triangles_max")
    check("strict_asset_limits_declared",all(isinstance(limits.get(k),(int,float)) and limits[k]>0
                                             for k in required_limits))
    if mode=="lint":
        return {"mode":mode,"task_id":manifest.get("task_id"),"asset_id":manifest.get("asset_id"),
                "checks":checks,"result":"SOURCE_LINT_PASS_NOT_ASSET_APPROVAL" if all(x["pass"] for x in checks)
                else "FAIL","asset_released":False}
    if not all(x["pass"] for x in checks):
        return {"mode":mode,"checks":checks,"result":"FAIL","asset_released":False}
    reference=filecheck("owner_reference_pixels_sha256",ref["path"],ref["sha256"])
    blend=filecheck("real_editable_blender_master",outputs["master_blend"])
    if blend:
        with blend.open("rb") as f:signature=f.read(7)
        check("blender_native_signature",signature==b"BLENDER")
    glb=filecheck("optimized_candidate_GLb",outputs["low_glb"])
    expected=outputs.get("low_glb_sha256")
    check("candidate_glb_hash_declared",isinstance(expected,str) and len(expected)==64)
    if glb and expected:check("candidate_glb_hash_matches",digest(glb)==expected)
    maps=outputs["bake_maps"]
    map_files={k:filecheck("baked_"+k,maps[k]) for k in REQUIRED_MAPS}
    try:
        from PIL import Image
        pixels=0
        for k,p in map_files.items():
            if p:
                with Image.open(p) as im:
                    check("texture_dimensions_"+k,im.width>=64 and im.height>=64 and
                          im.width<=4096 and im.height<=4096 and im.width&(im.width-1)==0 and
                          im.height&(im.height-1)==0,im.size)
                    # Blenders' bake operator may report FINISHED for an image
                    # that is still wholly transparent. Evaluate actual saved
                    # PNG alpha, not the API response or merely its byte size.
                    if k in ("normal","ambient_occlusion"):
                        with Image.open(p) as im_check:
                            alpha=im_check.convert("RGBA").getchannel("A")
                            hist=alpha.histogram()
                            coverage=sum(hist[1:])/max(1,sum(hist))
                            check("nontransparent_baked_"+k,coverage>=.05,
                                  {"opaque_pixel_ratio":round(coverage,5),"minimum":.05})
                    pixels+=im.width*im.height
        # RGBA8 conservative uncompressed estimate with mipmaps; packaging size != VRAM.
        tex_mib=pixels*4*4/3/1048576
        check("texture_gpu_budget_estimate",tex_mib<=limits["texture_mib_max"],
              {"estimated_rgba8_mipmap_mib":round(tex_mib,3),"limit_mib":limits["texture_mib_max"]})
    except ImportError:
        check("pillow_required_for_texture_check",False)
    if glb:
        try:
            gltf=parse_glb(glb)
            mat_names=[m.get("name","") for m in gltf.get("materials",[])]
            allowed=set(manifest.get("allowed_material_names",[]))
            check("material_names_present",bool(mat_names))
            check("material_palette_locked",bool(allowed) and set(mat_names).issubset(allowed),mat_names)
            check("material_slot_limit",len(mat_names)<=limits["materials_max"],len(mat_names))
            primitives=[p for m in gltf.get("meshes",[]) for p in m.get("primitives",[])]
            check("mesh_primitives_present",bool(primitives))
            check("drawcall_proxy_primitives",len(primitives)<=limits["draw_calls_max"],
                  {"primitive_count":len(primitives),"this_is_not_actual_Godot_drawcalls":True})
            check("no_animation_or_skin",not gltf.get("animations") and not gltf.get("skins"))
            check("GLB_binary_not_external_texture_paths",
                  all("uri" not in image for image in gltf.get("images",[])))
            # Triangle count and transformed Y-up bounds must be tested against actual vertices.
            import trimesh
            scene=trimesh.load(glb,force="scene",process=False)
            tris=sum(len(v.faces) for v in scene.geometry.values()
                     if isinstance(v,trimesh.Trimesh))
            check("triangle_hard_limit",0<tris<=limits["triangles_max"],tris)
            projected=limits["baseline_kit_triangles"]-limits["baseline_asset_triangles"]+tris
            check("kit_geometry_hard_limit",projected<=limits["kit_triangles_max"],
                  {"projected_triangles":projected,"hard_limit":limits["kit_triangles_max"]})
            bounds=scene.bounds
            if bounds is None or not math.isfinite(float(bounds.max())):
                check("Y_up_finite_bounds",False)
            else:
                width=float(bounds[1,0]-bounds[0,0])
                depth=float(bounds[1,2]-bounds[0,2])
                check("frozen_footprint",width<=limits["footprint_x_m"]+.06 and
                      depth<=limits["footprint_z_m"]+.06,{"width":width,"depth":depth})
                check("Y_up_nonnegative_height",bounds[0,1]>=-.15 and bounds[1,1]>0, bounds.tolist())
        except (ValueError,RuntimeError,ImportError,KeyError,TypeError) as e:
            check("GLB_geometry_and_material_inspection",False,str(e))
    candidate_ok=all(x["pass"] for x in checks)
    if mode=="candidate":
        return {"mode":mode,"checks":checks,"result":"CANDIDATE_TECHNICAL_PASS_NOT_VISUAL_APPROVAL"
                if candidate_ok else "FAIL","asset_released":False}
    if mode!="release":raise ValueError("Unknown mode "+mode)
    e=manifest.get("evidence",{})
    game=e.get("godot_shipping",{})
    check("real_shipping_scene",game.get("shipping_scene_loaded") is True and
          game.get("engine")=="Godot" and game.get("candidate_sha256")==expected)
    for view in REQUIRED_VIEWS:
        record=game.get("views",{}).get(view,{})
        if not isinstance(record,dict):
            check("shipping_native_pixels_"+view,False,"Expected path and SHA256 record")
            continue
        expected_image_sha=record.get("sha256")
        check("native_sha_declared_"+view,isinstance(expected_image_sha,str) and len(expected_image_sha)==64)
        native=filecheck("shipping_native_pixels_"+view,record.get("path",""),expected_image_sha)
        if native:
            try:
                from PIL import Image
                with Image.open(native) as image:
                    valid=image.format=="PNG" and image.width>=policy["evidence"]["minimum_native_frame"][0] and image.height>=policy["evidence"]["minimum_native_frame"][1]
                    check("native_full_resolution_"+view,valid,{"size":image.size,"format":image.format})
            except (ImportError,OSError,ValueError) as err:
                check("native_image_integrity_"+view,False,str(err))
    check("native_pixel_source_binding",game.get("source_commit") == manifest.get("source_commit")
          and bool(game.get("source_commit")))
    perf=e.get("android_physical",{})
    check("real_android_60fps",perf.get("device_type")=="physical_android" and
          isinstance(perf.get("sustained_fps"),(int,float)) and perf["sustained_fps"]>=60 and
          isinstance(perf.get("duration_seconds"),(int,float)) and
          perf["duration_seconds"]>=policy["performance"]["minimum_sustained_test_seconds"] and
          bool(perf.get("device_model")) and bool(perf.get("profiler_evidence_id")) and
          perf.get("candidate_sha256")==expected)
    cpu=perf.get("p95_cpu_frame_ms")
    gpu=perf.get("p95_gpu_frame_ms")
    calls=perf.get("measured_draw_calls")
    tex=perf.get("measured_texture_gpu_mib")
    check("physical_frame_drawcalls_texture_budget",
          all(isinstance(v,(int,float)) and v>=0 for v in (cpu,gpu,calls,tex)) and
          cpu<=policy["performance"]["global_max_frame_ms"] and
          gpu<=policy["performance"]["global_max_frame_ms"] and
          calls<=limits["draw_calls_max"] and tex<=limits["texture_mib_max"] if
          all(isinstance(v,(int,float)) for v in (cpu,gpu,calls,tex)) else False,
          {"p95_cpu_ms":cpu,"p95_gpu_ms":gpu,"draw_calls":calls,"texture_mib":tex})
    critic=e.get("independent_critic",{})
    scores=critic.get("scores",{})
    check("independent_reviewer",critic.get("reviewer_kind")=="independent" and
          critic.get("reviewer_id") and critic.get("reviewer_id")!=manifest.get("builder_id") and
          bool(critic.get("evidence_id")))
    # A visual review of R07 cannot approve R08: all critic evidence must be
    # tied to the exact GLB bytes and authoring commit being offered for release.
    check("critic_exact_candidate_and_source_bound",
          critic.get("candidate_sha256")==expected and
          critic.get("source_commit")==manifest.get("source_commit") and
          bool(critic.get("source_commit")))
    check("10_exact_reference_style",scores.get("reference_fidelity")==10 and
          scores.get("visual_language")==10 and critic.get("reference_pixels_reviewed") is True)
    other={k:v for k,v in scores.items() if k not in ("reference_fidelity","visual_language")}
    check("all_other_dimensions_above_9",bool(other) and
          all(isinstance(v,(int,float)) and v>9 for v in other.values()))
    check("zero_known_visual_defects",critic.get("defects")==[])
    auth=e.get("owner_approval",{})
    check("explicit_owner_source_bound_approval",auth.get("approved") is True and
          auth.get("candidate_sha256")==expected and bool(auth.get("evidence_id")))
    merge=e.get("integration_approval",{})
    check("integration_owner_authorized",merge.get("approved") is True and
          merge.get("candidate_sha256")==expected and bool(merge.get("evidence_id")))
    ready=all(x["pass"] for x in checks)
    return {"mode":mode,"checks":checks,
            "result":"RELEASE_EVIDENCE_COMPLETE_READY_FOR_AUTHORIZED_PROMOTION" if ready else "FAIL",
            "asset_released":False}

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("lint","candidate","release"))
    p.add_argument("--manifest",required=True)
    p.add_argument("--policy",required=True)
    p.add_argument("--workspace",default=".")
    p.add_argument("--report")
    a=p.parse_args()
    try:
        report=run(load_json(pathlib.Path(a.manifest)),load_json(pathlib.Path(a.policy)),
                   pathlib.Path(a.workspace).resolve(),a.mode)
    except (OSError,ValueError,KeyError,TypeError,ImportError) as e:
        report={"mode":a.mode,"result":"FAIL","error":str(e),"asset_released":False}
    data=json.dumps(report,indent=2)
    print(data)
    if a.report:
        pathlib.Path(a.report).parent.mkdir(parents=True,exist_ok=True)
        pathlib.Path(a.report).write_text(data+"\n")
    return 0 if report["result"] in ("SOURCE_LINT_PASS_NOT_ASSET_APPROVAL",
                                   "CANDIDATE_TECHNICAL_PASS_NOT_VISUAL_APPROVAL",
                                   "RELEASE_EVIDENCE_COMPLETE_READY_FOR_AUTHORIZED_PROMOTION") else 1

if __name__=="__main__":sys.exit(main())
