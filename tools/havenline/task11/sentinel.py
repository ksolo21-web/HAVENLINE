#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
T11=ROOT/"HavenlineGodot/data/camp_construction_recipes.json"
T10=ROOT/"HavenlineGodot/data/world_transform_recipes.json"
VIEW=ROOT/"HavenlineGodot/scripts/camp_construction_view.gd"
REG=ROOT/"Docs/Production/WORKSTREAM_REGISTRY.json"

def load(path):
    return json.loads(path.read_text())

def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()

def main():
    errors=[]
    for path in [T11,T10,VIEW,ROOT/"HavenlineGodot/tests/test_task11_camp_construction.gd",ROOT/"HavenlineGodot/tests/test_task11_integration.gd"]:
        if not path.is_file(): errors.append("missing "+str(path.relative_to(ROOT)))
    if errors:
        print(json.dumps({"passed":False,"errors":errors},indent=2));return 2
    t11=load(T11);t10=load(T10)
    if t11.get("authority_id")!="T11-camp-construction-content-v1":errors.append("wrong T11 content authority")
    if t11.get("transaction_authority")!="T10-world-transform-v1":errors.append("T10 transaction authority not preserved")
    if t11.get("presentation_only") is not True or t11.get("shadow_resource_authority") is not False:errors.append("T11 catalog is not strictly presentation-only")
    t10_by={row["recipe_id"]:row for row in t10.get("recipes",[])}
    seen=set()
    for row in t11.get("builds",[]):
        cid=row.get("construction_id")
        if not cid or cid in seen:errors.append("duplicate/empty construction_id")
        seen.add(cid)
        for forbidden in ("costs","prerequisites","progression_tags"):
            if forbidden in row:errors.append(f"{cid} shadows T10 {forbidden}")
        recipe=t10_by.get(row.get("world_transform_recipe_id"))
        if not recipe:
            errors.append(f"{cid} references missing T10 recipe");continue
        for key in ("presentation_key","source_state","target_state"):
            if row.get(key)!=recipe.get(key):errors.append(f"{cid} {key} diverges from T10")
        for scene_key in ("before_scene","after_scene"):
            rel=str(row.get(scene_key,"")).replace("res://","HavenlineGodot/",1)
            if not rel or not (ROOT/rel).is_file():errors.append(f"{cid} missing {scene_key}")
        try:
            if float(row.get("clearance_radius",0))<float(row.get("footprint_radius",0)) or float(row.get("footprint_radius",0))<=0:errors.append(f"{cid} invalid footprint/clearance")
        except Exception:errors.append(f"{cid} malformed footprint/clearance")
    body=VIEW.read_text()
    for token in ("presentation_only","mutates_resources","advances_transform_state","accepted_by_world_transform","placement_is_clear","MAX_AUTHORED_MESHES"):
        if token not in body:errors.append("view contract token missing: "+token)
    registry=load(REG);ws=next(x for x in registry["workstreams"] if x["task_id"]=="T11")
    bound=ws.get("assignment_integration_commit")
    if not bound or len(bound)!=40:errors.append("missing exact T11 assignment integration binding")
    else:
        changed=git("diff","--name-only",f"{bound}..HEAD").splitlines()
        protected=("HavenlineGodot/scripts/world_transform.gd","HavenlineGodot/scripts/world_transform_view.gd","HavenlineGodot/data/world_transform_recipes.json","HavenlineGodot/assets/world_transform_v1/","HavenlineGodot/tests/test_task10_","tools/havenline/task10/","Docs/Production/T10/")
        bad=[p for p in changed if any(p==x or p.startswith(x) for x in protected)]
        if bad:errors.append("T11 candidate modifies T10-owned paths: "+",".join(bad))
    out={
        "passed":not errors,
        "task_id":"T11",
        "sentinel":"placement validity, upgrade-state determinism, collision safety and T10 transaction reuse",
        "construction_count":len(t11.get("builds",[])),
        "t10_authority_preserved":not any("T10" in e for e in errors),
        "shadow_resource_authority":False,
        "errors":errors,
        "task_approved":False
    }
    print(json.dumps(out,indent=2))
    return 0 if not errors else 2

if __name__=="__main__":
    raise SystemExit(main())
