#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, pathlib, re, subprocess
from lib import ROOT, DOCS, load_json, sha256_file

POLICY_PATH=DOCS/"REFERENCE_STYLE_LOCK.json"
PRIMARY_LOCK=ROOT/"Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md"
PRIMARY_SOURCES=ROOT/"Docs/Design/ReferenceVideoLock/reference-video-sources.json"
SUPPLEMENTAL_LOCK=ROOT/"Docs/Design/ReferenceVideoLock/SUPPLEMENTAL_WHITEOUT_SURVIVAL_AD_REFERENCES.md"
SUPPLEMENTAL_SOURCES=ROOT/"Docs/Design/ReferenceVideoLock/supplemental-whiteout-survival-ad-sources.json"

def _changed(base:str,candidate:str)->list[str]:
    try:
        out=subprocess.check_output(["git","diff","--name-only",base,candidate],cwd=ROOT,text=True,stderr=subprocess.PIPE)
        return [x.strip() for x in out.splitlines() if x.strip()]
    except (OSError,subprocess.SubprocessError) as exc:
        raise RuntimeError("unable to resolve exact candidate diff: "+str(exc)) from exc

def _script_material_tokens(rel:str,tokens:list[str],refs:tuple[str,...]=())->bool:
    if pathlib.Path(rel).suffix!=".gd": return False
    texts=[]
    if refs:
        for ref in refs:
            try:
                texts.append(subprocess.check_output(["git","show",f"{ref}:{rel}"],cwd=ROOT,text=True,stderr=subprocess.PIPE))
            except (OSError,subprocess.SubprocessError):
                pass
    else:
        path=ROOT/rel
        if path.is_file():
            try: texts.append(path.read_text(errors="ignore"))
            except OSError: pass
    return any(token in text for text in texts for token in tokens)

def visual_style_paths(files:list[str],refs:tuple[str,...]=())->list[str]:
    policy=load_json(POLICY_PATH);det=policy["detection"]
    roots=tuple(det["visual_roots"]);exts=set(det["visual_extensions"]);tokens=det["script_tokens"];hits=[]
    for rel in files:
        if rel.startswith(roots) or pathlib.Path(rel).suffix.lower() in exts or _script_material_tokens(rel,tokens,refs): hits.append(rel)
    return sorted(set(hits))

def historical_exact_source_preserved(manifest:dict)->bool:
    task=str(manifest.get("task_id") or "");candidate=str(manifest.get("candidate_commit") or "")
    allowed=load_json(POLICY_PATH).get("invalidation",{}).get("historical_exact_sources",{}).get(task,[])
    return candidate in allowed

def style_lock_required(manifest:dict)->bool:
    task=str(manifest.get("task_id") or "");policy=load_json(POLICY_PATH)
    if task in policy["detection"].get("always_trigger_tasks",[]): return True
    if historical_exact_source_preserved(manifest) and manifest.get("reference_style_lock",{}).get("applicable") is not True: return False
    base=str(manifest.get("base_commit") or "");candidate=str(manifest.get("candidate_commit") or "")
    if re.fullmatch(r"[0-9a-f]{40}",base) and re.fullmatch(r"[0-9a-f]{40}",candidate):
        try:
            return bool(visual_style_paths(_changed(base,candidate),(base,candidate)))
        except RuntimeError:
            return True
    return bool(manifest.get("reference_style_lock",{}).get("applicable"))

def validate_manifest(manifest:dict,critics:dict|None=None)->dict:
    policy=load_json(POLICY_PATH);errors=[];task=str(manifest.get("task_id") or "");candidate=str(manifest.get("candidate_commit") or "");base=str(manifest.get("base_commit") or "")
    diff_error=None
    if re.fullmatch(r"[0-9a-f]{40}",base) and re.fullmatch(r"[0-9a-f]{40}",candidate):
        try: files=_changed(base,candidate)
        except RuntimeError as exc: files=[];diff_error=str(exc)
    else: files=[]
    detected=visual_style_paths(files,(base,candidate)) if files else [];block=manifest.get("reference_style_lock",{})
    preserved=historical_exact_source_preserved(manifest) and task not in policy["detection"].get("always_trigger_tasks",[])
    required=(task in policy["detection"].get("always_trigger_tasks",[])) or ((bool(detected) or diff_error is not None) and not preserved) or block.get("applicable") is True
    if diff_error and not preserved: errors.append(diff_error)
    if required:
        if block.get("applicable") is not True: errors.append("reference style lock required but not marked applicable")
        if block.get("validation_passed") is not True: errors.append("reference style lock validation not marked passed")
        if block.get("policy_sha256")!=sha256_file(POLICY_PATH): errors.append("reference style policy hash mismatch")
        expected={"primary_lock":sha256_file(PRIMARY_LOCK),"primary_sources":sha256_file(PRIMARY_SOURCES),"supplemental_lock":sha256_file(SUPPLEMENTAL_LOCK),"supplemental_sources":sha256_file(SUPPLEMENTAL_SOURCES)}
        got=block.get("reference_hashes",{})
        for key,value in expected.items():
            if got.get(key)!=value: errors.append("reference hash mismatch: "+key)
        if sorted(block.get("changed_visual_paths",[]))!=detected and task!="T70": errors.append("changed visual path coverage mismatch")
        if block.get("material_inventory_complete") is not True: errors.append("material inventory incomplete")
        if not isinstance(block.get("material_inventory_count"),int) or block.get("material_inventory_count",0)<=0: errors.append("material inventory empty")
        if block.get("reference_pixels_reviewed") is not True: errors.append("actual reference pixels not reviewed")
        if task=="T70" and block.get("full_release_census") is not True: errors.append("T70 full shipped-material census missing")
        ep=block.get("evidence_path");eh=block.get("evidence_sha256")
        if not ep or not eh: errors.append("reference style evidence proof missing")
        else:
            fp=(ROOT/ep).resolve()
            try: fp.relative_to(ROOT.resolve())
            except ValueError: errors.append("reference style evidence path escapes repository")
            if not fp.is_file() or sha256_file(fp)!=eh: errors.append("reference style evidence hash mismatch")
            else:
                proof=json.loads(fp.read_text())
                if proof.get("task_id")!=task or proof.get("candidate_commit")!=candidate: errors.append("reference style evidence source identity mismatch")
                if proof.get("coverage_complete") is not True or proof.get("reference_pixels_reviewed") is not True: errors.append("reference style evidence coverage incomplete")
                if sorted(proof.get("changed_visual_paths",[]))!=detected and task!="T70": errors.append("reference style evidence changed-path mismatch")
                if not {"A","B"}<=set(proof.get("primary_reference_ids",[])): errors.append("primary A/B references not both reviewed")
                inv=proof.get("material_inventory",[])
                if not isinstance(inv,list) or len(inv)!=block.get("material_inventory_count"): errors.append("material inventory count mismatch")
                if proof.get("known_style_defects") != []: errors.append("known_style_defects must be an explicit empty list")
                if task=="T70" and proof.get("full_release_census") is not True: errors.append("T70 evidence is not a full release census")
        c1=(critics or {}).get("C1",{});scores=c1.get("scores",{})
        for dim in policy["acceptance"]["c1_exact_score_dimensions"]:
            if scores.get(dim)!=policy["acceptance"]["required_style_fidelity"]: errors.append(f"C1 {dim} must equal 10.0 exactly under reference style lock")
        if c1.get("defects"): errors.append("C1 contains style/reference defects")
        if c1.get("coverage_complete") is not True: errors.append("C1 reference-style coverage incomplete")
    elif block.get("applicable") is True and block.get("validation_passed") is not True:
        errors.append("voluntary reference style lock marked applicable without validation pass")
    return {"task_id":task,"candidate_commit":candidate,"required":required,"historical_exact_source_preserved":preserved,"detected_visual_paths":detected,"passed":not errors,"errors":errors}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("manifest");a=ap.parse_args();p=pathlib.Path(a.manifest)
    if not p.is_absolute(): p=ROOT/p
    m=json.loads(p.read_text());out=validate_manifest(m,m.get("critics",{}));print(json.dumps(out,indent=2));raise SystemExit(0 if out["passed"] else 2)
if __name__=="__main__": main()
