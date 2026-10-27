#!/usr/bin/env python3
"""Exact shipping-branch source inventory for global material critic T70 census.

Not a visual review. Reports all tracked visual source paths and runtime
material-producing .gd scripts. A source path is NOT an individual PBR material
slot, so the actual Godot inspector/reviewer must expand this inventory later.
"""
from __future__ import annotations
import argparse
import collections
import fnmatch
import hashlib
import json
import pathlib
import subprocess

from reference_style_lock import visual_style_paths
from shipping_visual_gate import ROOT, policy


MESH={".glb",".gltf",".fbx",".obj",".dae"}
TEXTURE={".png",".jpg",".jpeg",".webp",".svg",".bmp",".tga",".exr",".hdr"}
MATERIAL={".gdshader",".shader",".material",".mat",".tres",".res"}
SCENE={".tscn",".scn"}


def classify(rel: str) -> str:
    ext=pathlib.PurePosixPath(rel).suffix.lower()
    if ext in MESH:return "mesh_or_geometry"
    if ext in TEXTURE:return "image_or_texture"
    if ext in MATERIAL:return "shader_or_material"
    if ext in SCENE:return "scene_material_assignments"
    if ext==".gd":return "code_created_or_modified_material"
    return "other_visual"


def census(ref: str="HEAD") -> dict:
    raw=subprocess.check_output(["git","ls-tree","-r","-z",ref,"--","HavenlineGodot"],cwd=ROOT)
    tree={}
    for part in raw.split(b"\0"):
        if not part:continue
        meta,rel=part.split(b"\t",1)
        bits=meta.split()
        if len(bits)!=3 or bits[1]!=b"blob":continue
        tree[rel.decode("utf-8")]=bits[2].decode("ascii")
    excluded=policy().get("excluded_patterns",[])
    paths=sorted(x for x in tree if not any(fnmatch.fnmatchcase(x,pat) for pat in excluded))
    detected=visual_style_paths(paths,(ref,))
    by_class=dict(sorted(collections.Counter(classify(x) for x in detected).items()))
    items=[{"shipping_path":x,"git_blob_oid":tree[x],"source_class":classify(x),
            "new_individual_material_critic_status":"UNVERIFIED_UNTIL_REAL_C1_C2_AND_NATIVE_GODOT_EVIDENCE",
            "legacy_user_acceptance_revoked_by_governance_alone":False} for x in detected]
    digest=hashlib.sha256(json.dumps(items,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    commit=subprocess.check_output(["git","rev-parse",ref+"^{commit}"],cwd=ROOT,text=True).strip()
    return {"schema_version":1,"status":"SHIPPING_MATERIAL_SOURCE_CENSUS_NOT_VISUAL_APPROVAL",
            "shipping_ref_commit":commit,"total_shipping_tracked_paths":len(paths),
            "identified_visual_source_paths":len(items),"by_source_class":by_class,
            "source_path_inventory_sha256":digest,
            "material_slot_count_known":False,
            "actual_material_slots_must_be_enumerated_in_native_godot":True,
            "complete_T70_C1_C2_critic_pass":False,
            "source_items":items}


def compare_receipt(c: dict,receipt: dict) -> dict:
    expected={x["shipping_path"] for x in c["source_items"]}
    actual=set(receipt.get("source_paths_covered") or [])
    missing=sorted(expected-actual)
    extra=sorted(actual-expected)
    passed=(not missing and not extra and bool(expected)
            and receipt.get("full_shipped_material_census_verified") is True
            and receipt.get("mode")=="release"
            and receipt.get("critic_ids_verified")==["C1","C2"]
            and receipt.get("real_visual_review_completed") is True)
    return {"passed":passed,"missing_paths":missing,"unexpected_paths":extra,
            "shipping_source_paths":len(expected),"reported_reviewed_paths":len(actual),
            "notice":"A census receipt alone is not owner or physical Android approval"}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ref",default="HEAD")
    ap.add_argument("--out",required=True)
    ap.add_argument("--receipt")
    a=ap.parse_args()
    result=census(a.ref)
    if a.receipt:
        result["comparison"]=compare_receipt(result,json.loads(pathlib.Path(a.receipt).read_text()))
    pathlib.Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="source_items"},indent=2))
    if a.receipt and not result["comparison"]["passed"]:
        raise SystemExit(2)


if __name__=="__main__":
    main()
