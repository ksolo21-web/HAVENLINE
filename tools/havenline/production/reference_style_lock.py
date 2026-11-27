#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, re, subprocess
from lib import ROOT, DOCS, load_json, sha256_file
from reference_acceptance import strict_json_loads

POLICY_PATH=DOCS/"REFERENCE_STYLE_LOCK.json"
PRIMARY_LOCK=ROOT/"Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md"
PRIMARY_SOURCES=ROOT/"Docs/Design/ReferenceVideoLock/reference-video-sources.json"
SUPPLEMENTAL_LOCK=ROOT/"Docs/Design/ReferenceVideoLock/SUPPLEMENTAL_WHITEOUT_SURVIVAL_AD_REFERENCES.md"
SUPPLEMENTAL_SOURCES=ROOT/"Docs/Design/ReferenceVideoLock/supplemental-whiteout-survival-ad-sources.json"
HEX40=re.compile(r"[0-9a-f]{40}")

def _git(*args:str)->str:
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True,stderr=subprocess.PIPE,
                                   timeout=20,env={**os.environ,"GIT_NO_REPLACE_OBJECTS":"1","GIT_NO_LAZY_FETCH":"1","GIT_TERMINAL_PROMPT":"0"})

def _exact_commit(value:str)->str:
    if not isinstance(value,str) or not HEX40.fullmatch(value):
        raise RuntimeError("source identity must be an exact 40-hex commit")
    try:
        resolved=_git("rev-parse","--verify",f"{value}^{{commit}}").strip()
    except (OSError,subprocess.SubprocessError) as exc:
        raise RuntimeError("source commit is unavailable: "+value) from exc
    if resolved!=value:
        raise RuntimeError("source identity does not resolve to the declared commit")
    return resolved

def _tree_files(ref:str)->list[str]:
    try:
        return [p for p in _git("ls-tree","-r","-z","--name-only",ref,"--").split("\0") if p]
    except (OSError,subprocess.SubprocessError) as exc:
        raise RuntimeError("unable to enumerate candidate shipping paths") from exc

def _normal_root(value:str)->str:
    if not isinstance(value,str) or not value or "\\" in value:
        raise RuntimeError("shipping root must be a repository-relative POSIX directory")
    path=pathlib.PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) in {".",""}:
        raise RuntimeError("shipping root must stay inside the repository")
    return str(path).rstrip("/")+"/"

def shipping_roots(config:dict,refs:tuple[str,...]=(),manifest:dict|None=None)->list[str]:
    """Canonical roots plus additive declared/discovered projects; no candidate exclusions."""
    configured=config.get("shipping_roots",config.get("visual_roots",[]))
    if not isinstance(configured,list): raise RuntimeError("canonical shipping roots must be a list")
    roots=[_normal_root(x) for x in configured]
    discovery=config.get("candidate_root_discovery",{})
    if not isinstance(discovery,dict):
        raise RuntimeError("candidate root discovery policy must be an object")
    field=discovery.get("manifest_field","shipping_roots")
    if not isinstance(field,str) or not field: raise RuntimeError("shipping root declaration field is invalid")
    declared=(manifest or {}).get(field,[])
    if not isinstance(declared,list):
        raise RuntimeError("declared shipping roots must be a list")
    exclusions=discovery.get("excluded_prefixes",[])
    if not isinstance(exclusions,list): raise RuntimeError("canonical discovery exclusions must be a list")
    excluded=tuple(_normal_root(x) for x in exclusions)
    for value in declared:
        root=_normal_root(value)
        if root.startswith(excluded):
            raise RuntimeError("declared shipping root conflicts with a canonical archive exclusion")
        roots.append(root)
    if discovery.get("enabled") is True:
        markers=discovery.get("project_markers",["project.godot"])
        if not isinstance(markers,list) or not markers or any(not isinstance(x,str) or not x or "/" in x for x in markers):
            raise RuntimeError("project discovery markers are invalid")
        for ref in refs:
            for rel in _tree_files(ref):
                if rel.startswith(excluded) or pathlib.PurePosixPath(rel).name not in markers:
                    continue
                parent=str(pathlib.PurePosixPath(rel).parent)
                # A project at repository root intentionally covers all non-excluded paths.
                roots.append("" if parent=="." else _normal_root(parent))
    if not roots:
        raise RuntimeError("no canonical or discovered shipping roots")
    return sorted(set(roots))

def _changed(base:str,candidate:str)->list[str]:
    try:
        _exact_commit(base);_exact_commit(candidate)
        # Disabling rename folding retains both the removed and added names.
        out=_git("diff","--no-ext-diff","--no-textconv","--no-renames","--name-only","-z",base,candidate,"--")
        return [x for x in out.split("\0") if x]
    except (OSError,subprocess.SubprocessError) as exc:
        raise RuntimeError("unable to resolve exact candidate diff: "+str(exc)) from exc

def _script_material_tokens(rel:str,tokens:list[str],refs:tuple[str,...]=())->bool:
    if pathlib.Path(rel).suffix.lower() not in {".gd",".cs",".py"}: return False
    texts=[]
    if refs:
        for ref in refs:
            try:
                if rel in _tree_files(ref): texts.append(_git("show",f"{ref}:{rel}"))
            except (OSError,subprocess.SubprocessError) as exc:
                raise RuntimeError("unable to inspect material-producing source: "+rel) from exc
    else:
        path=ROOT/rel
        if path.is_file():
            try: texts.append(path.read_text(errors="ignore"))
            except OSError as exc: raise RuntimeError("unable to inspect material-producing source: "+rel) from exc
    return any(token in text for text in texts for token in tokens)

def visual_style_paths(files:list[str],refs:tuple[str,...]=(),manifest:dict|None=None)->list[str]:
    policy=load_json(POLICY_PATH);det=policy["detection"]
    roots=tuple(shipping_roots(det,refs,manifest));exts=set(det["visual_extensions"]);tokens=det["script_tokens"];hits=[]
    block=(manifest or {}).get("reference_style_lock",{})
    declared=block.get("changed_visual_paths",[]) if isinstance(block,dict) else []
    declared={x for x in declared if isinstance(x,str)} if isinstance(declared,list) else set()
    for rel in files:
        path=pathlib.PurePosixPath(rel);suffix=path.suffix.lower()
        documentation=suffix in {".md",".rst"} or (suffix in {".txt",""} and path.stem.upper() in {"README","CHANGELOG","LICENSE","COPYING","AUTHORS"})
        if rel in declared or (rel.startswith(roots) and not documentation) or suffix in exts or _script_material_tokens(rel,tokens,refs): hits.append(rel)
    return sorted(set(hits))

def historical_exact_source_preserved(manifest:dict)->bool:
    if manifest.get("review_scope")!="historical": return False
    from reference_acceptance import validate_historical_receipt
    result=validate_historical_receipt(str(manifest.get("task_id") or ""),
        str(manifest.get("candidate_commit") or ""),str(manifest.get("historical_receipt_path") or ""))
    return result.get("passed") is True

def style_lock_required(manifest:dict)->bool:
    if not isinstance(manifest,dict): return True
    task=str(manifest.get("task_id") or "");policy=load_json(POLICY_PATH)
    if task in policy["detection"].get("always_trigger_tasks",[]): return True
    if historical_exact_source_preserved(manifest): return False
    base=str(manifest.get("base_commit") or "");candidate=str(manifest.get("candidate_commit") or "")
    try:
        return bool(visual_style_paths(_changed(base,candidate),(base,candidate),manifest)) or manifest.get("reference_style_lock",{}).get("applicable") is True
    except (RuntimeError,OSError,ValueError,TypeError,AttributeError):
        return True

def _string_list(value)->bool:
    return isinstance(value,list) and all(isinstance(x,str) for x in value)

def validate_manifest(manifest:dict,critics:dict|None=None)->dict:
    if not isinstance(manifest,dict):
        return {"passed":False,"required":True,"historical_only":False,"approval_allowed":False,"errors":["manifest must be an object"]}
    policy=load_json(POLICY_PATH);errors=[];task=str(manifest.get("task_id") or "");candidate=str(manifest.get("candidate_commit") or "");base=str(manifest.get("base_commit") or "")
    if manifest.get("review_scope")=="historical":
        from reference_acceptance import validate_historical_receipt
        history=validate_historical_receipt(task,candidate,str(manifest.get("historical_receipt_path") or ""))
        return {**history,"candidate_commit":candidate,"required":False,"historical_exact_source_preserved":history["passed"],
                "historical_only":True,"detected_visual_paths":[]}
    diff_error=None;detected=[]
    try:
        files=_changed(base,candidate)
        detected=visual_style_paths(files,(base,candidate),manifest)
    except (RuntimeError,OSError,ValueError,TypeError) as exc:
        diff_error=str(exc)
    block=manifest.get("reference_style_lock",{})
    if not isinstance(block,dict): block={};errors.append("reference style lock must be an object")
    preserved=False
    required=(task in policy["detection"].get("always_trigger_tasks",[])) or bool(detected) or diff_error is not None or block.get("applicable") is True
    if diff_error: errors.append(diff_error)
    if required:
        if block.get("applicable") is not True: errors.append("reference style lock required but not marked applicable")
        if block.get("validation_passed") is not True: errors.append("reference style lock validation not marked passed")
        if block.get("policy_sha256")!=sha256_file(POLICY_PATH): errors.append("reference style policy hash mismatch")
        expected={"primary_lock":sha256_file(PRIMARY_LOCK),"primary_sources":sha256_file(PRIMARY_SOURCES),"supplemental_lock":sha256_file(SUPPLEMENTAL_LOCK),"supplemental_sources":sha256_file(SUPPLEMENTAL_SOURCES)}
        got=block.get("reference_hashes",{})
        if not isinstance(got,dict): got={}
        for key,value in expected.items():
            if got.get(key)!=value: errors.append("reference hash mismatch: "+key)
        paths=block.get("changed_visual_paths",[])
        if not _string_list(paths) or (sorted(paths)!=detected and task!="T70"): errors.append("changed visual path coverage mismatch")
        if block.get("material_inventory_complete") is not True: errors.append("material inventory incomplete")
        if type(block.get("material_inventory_count")) is not int or block.get("material_inventory_count",0)<=0: errors.append("material inventory empty")
        if block.get("reference_pixels_reviewed") is not True: errors.append("actual reference pixels not reviewed")
        if task=="T70" and block.get("full_release_census") is not True: errors.append("T70 full shipped-material census missing")
        ep=block.get("evidence_path");eh=block.get("evidence_sha256")
        if not isinstance(ep,str) or not ep or not isinstance(eh,str) or not re.fullmatch(r"[0-9a-f]{64}",eh): errors.append("reference style evidence proof missing or invalid")
        else:
            raw=ROOT/ep;fp=raw.resolve()
            safe=not pathlib.PurePosixPath(ep).is_absolute() and ".." not in pathlib.PurePosixPath(ep).parts and "\\" not in ep and fp.is_relative_to(ROOT.resolve()) and not raw.is_symlink()
            if not safe: errors.append("reference style evidence path escapes repository or is a symlink")
            if not safe or not fp.is_file() or sha256_file(fp)!=eh: errors.append("reference style evidence hash mismatch")
            else:
                try: proof=strict_json_loads(fp.read_bytes())
                except (OSError,ValueError,UnicodeError): proof={};errors.append("reference style evidence must be readable JSON")
                if not isinstance(proof,dict): proof={};errors.append("reference style evidence must be an object")
                if proof.get("task_id")!=task or proof.get("candidate_commit")!=candidate: errors.append("reference style evidence source identity mismatch")
                if proof.get("coverage_complete") is not True or proof.get("reference_pixels_reviewed") is not True: errors.append("reference style evidence coverage incomplete")
                paths=proof.get("changed_visual_paths",[])
                if not _string_list(paths) or (sorted(paths)!=detected and task!="T70"): errors.append("reference style evidence changed-path mismatch")
                ids=proof.get("primary_reference_ids",[])
                if not _string_list(ids) or not {"A","B"}<=set(ids): errors.append("primary A/B references not both reviewed")
                inv=proof.get("material_inventory",[])
                if not isinstance(inv,list) or len(inv)!=block.get("material_inventory_count"): errors.append("material inventory count mismatch")
                if proof.get("known_style_defects") != []: errors.append("known_style_defects must be an explicit empty list")
                if task=="T70" and proof.get("full_release_census") is not True: errors.append("T70 evidence is not a full release census")
        c1=critics.get("C1",{}) if isinstance(critics,dict) else {}
        if not isinstance(c1,dict): c1={}
        scores=c1.get("scores",{})
        if not isinstance(scores,dict): scores={}
        for dim in policy["acceptance"]["c1_exact_score_dimensions"]:
            if scores.get(dim)!=policy["acceptance"]["required_style_fidelity"]: errors.append(f"C1 {dim} must equal 10.0 exactly under reference style lock")
        if c1.get("defects")!=[]: errors.append("C1 must explicitly report no style/reference defects")
        if c1.get("coverage_complete") is not True: errors.append("C1 reference-style coverage incomplete")
        if c1.get("candidate_commit")!=candidate: errors.append("C1 reference-style candidate identity mismatch")
    elif block.get("applicable") is True and block.get("validation_passed") is not True:
        errors.append("voluntary reference style lock marked applicable without validation pass")
    return {"task_id":task,"candidate_commit":candidate,"required":required,"historical_exact_source_preserved":preserved,"historical_only":False,"detected_visual_paths":detected,"passed":not errors,"errors":errors}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("manifest");a=ap.parse_args();p=pathlib.Path(a.manifest)
    if not p.is_absolute(): p=ROOT/p
    m=strict_json_loads(p.read_bytes());out=validate_manifest(m,m.get("critics",{}) if isinstance(m,dict) else None);print(json.dumps(out,indent=2));raise SystemExit(0 if out["passed"] else 2)
if __name__=="__main__": main()
