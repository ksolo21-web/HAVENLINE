#!/usr/bin/env python3
from __future__ import annotations
import argparse, fnmatch, hashlib, io, json, math, os, pathlib, posixpath, re, subprocess, tempfile
from fractions import Fraction
from typing import Any
from critic_profile import resolve_critic
from reference_acceptance import binding_errors, playback_errors, required_final_critics, score_errors, strict_json_loads
from reference_style_lock import _normal_root, shipping_roots

ROOT=pathlib.Path(__file__).resolve().parents[3]
DOCS=ROOT/"Docs"/"Production"
POLICY_PATH=DOCS/"SHIPPING_VISUAL_APPROVAL_POLICY.json"
INVALIDATIONS_PATH=DOCS/"APPROVAL_INVALIDATIONS.json"
HEX40=re.compile(r"^[0-9a-f]{40}$")

def load(path: pathlib.Path)->dict[str,Any]:
    return strict_json_loads(path.read_bytes())

def git(*args: str, text: bool=True):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=text,stderr=subprocess.PIPE,
                                   timeout=20,env={**os.environ,"GIT_NO_REPLACE_OBJECTS":"1","GIT_NO_LAZY_FETCH":"1","GIT_TERMINAL_PROMPT":"0"})

def match(path: str, patterns: list[str])->bool:
    return any(fnmatch.fnmatchcase(path,p) for p in patterns)

def policy()->dict[str,Any]:
    return load(POLICY_PATH)

def registry()->dict[str,Any]:
    return load(DOCS/"WORKSTREAM_REGISTRY.json")

def ownership()->dict[str,Any]:
    return load(DOCS/"PATH_OWNERSHIP.json")

def graph()->dict[str,Any]:
    return load(DOCS/"DEPENDENCY_GRAPH.json")

def invalidations()->dict[str,Any]:
    return load(INVALIDATIONS_PATH)

def task_invalidation_records(task_id: str)->list[dict[str,Any]]:
    return [r for r in invalidations().get("records",[]) if r.get("task_id")==task_id]

def active_invalidation(task_id: str)->dict[str,Any]|None:
    return next((r for r in task_invalidation_records(task_id) if r.get("status")=="ACTIVE"),None)

def task_number(task_id: str)->int:
    try: return int(task_id[1:])
    except Exception: return 0

def signoff_required(task_id: str)->bool:
    return task_number(task_id)>=12 or bool(task_invalidation_records(task_id))

def task_patterns(task_id: str)->list[str]:
    reg=registry(); own=ownership()
    row=next((w for w in reg.get("workstreams",[]) if w.get("task_id")==task_id),None)
    aliases=[]
    if row:
        aliases=list(row.get("owned_paths",[]))
    elif f"@protected:{task_id}" in own.get("aliases",{}):
        aliases=[f"@protected:{task_id}"]
    patterns=[]
    for item in aliases:
        if isinstance(item,str) and item.startswith("@"):
            patterns.extend(own.get("aliases",{}).get(item,[]))
        elif isinstance(item,str):
            patterns.append(item)
    return list(dict.fromkeys(patterns))

def _selected_roots(ref: str, manifest: dict|None)->tuple[list[str],dict]:
    cfg=policy(); shipping_roots(cfg,(ref,),manifest)
    paths=[x for x in git("ls-tree","-r","-z","--name-only",ref,"--").split("\0") if x]
    excluded=tuple(_normal_root(x) for x in cfg.get("candidate_root_discovery",{}).get("excluded_prefixes",[]))
    projects={str(pathlib.PurePosixPath(x).parent).rstrip("/")+"/" for x in paths
              if pathlib.PurePosixPath(x).name=="project.godot" and not x.startswith(excluded)}
    active={_normal_root(x) for x in cfg.get("active_project_roots",[])}
    preserved={_normal_root(x) for x in cfg.get("preserved_project_roots",[])}
    if manifest is None:
        # Inventory alone cannot grant approval. Prefer the active project; old
        # snapshots lacking it can still be inspected as historical diagnostics.
        selected=(active & projects) or projects
        if not selected: raise RuntimeError("candidate has no discoverable project for diagnostic inspection")
        return sorted(selected),{"selection_verified":False,"approval_allowed":False,
            "validation_kind":"DIAGNOSTIC_SOURCE_INVENTORY","project_roots":sorted(projects)}
    scope=manifest.get("shipping_scope")
    if not isinstance(scope,dict): raise RuntimeError("source-bound shipping_scope is required for final review")
    if scope.get("candidate_commit")!=ref: raise RuntimeError("shipping scope candidate identity mismatch")
    project=_normal_root(scope.get("project_root"))
    deps=scope.get("dependency_roots")
    if not isinstance(deps,list): raise RuntimeError("shipping dependency roots must be an explicit list")
    selected={project,*(_normal_root(x) for x in deps)}
    declared=manifest.get(cfg.get("candidate_root_discovery",{}).get("manifest_field","shipping_roots"),[])
    if not isinstance(declared,list): raise RuntimeError("declared shipping roots must be a list")
    if not {_normal_root(x) for x in declared}<=selected:
        raise RuntimeError("declared shipping roots were omitted from the source-bound scope")
    if not active or not active<=projects or not active<=selected or project not in active:
        raise RuntimeError("shipping scope must include every canonical active project at the candidate")
    unknown=projects-active-preserved
    if unknown: raise RuntimeError("unregistered candidate project roots require canonical scope resolution: "+",".join(sorted(unknown)))
    if any(root.startswith(excluded) for root in selected): raise RuntimeError("shipping scope conflicts with canonical archive exclusions")
    for root in selected:
        if not any(x.startswith(root) for x in paths): raise RuntimeError("selected shipping root has no candidate files: "+root)
    digest=scope.get("project_file_sha256")
    data=git("show",f"{ref}:{project}project.godot",text=False)
    if not isinstance(digest,str) or hashlib.sha256(data).hexdigest()!=digest:
        raise RuntimeError("selected candidate project.godot hash mismatch")
    return sorted(selected),{"selection_verified":True,"approval_allowed":False,
        "validation_kind":"SOURCE_BOUND_SHIPPING_SELECTION","project_roots":sorted(projects),"shipping_scope":scope}

def tracked_files(ref: str, manifest: dict|None=None)->list[str]:
    roots,_=_selected_roots(ref,manifest)
    return [x for x in git("ls-tree","-r","-z","--name-only",ref,"--").split("\0")
            if x and x.startswith(tuple(roots))]

def text_at(ref: str,path: str)->str:
    return git("show",f"{ref}:{path}")

def scan_task(task_id: str, ref: str="HEAD", manifest: dict|None=None)->dict[str,Any]:
    p=policy(); patterns=task_patterns(task_id); excluded=p.get("excluded_patterns",[])
    exts=set(p.get("text_extensions",[]))|{".py",".cs"}
    forbidden=[("render_type",x) for x in p.get("forbidden_render_types",[])]
    forbidden += [("material_type",x) for x in p.get("forbidden_material_types",[])]
    files=[]
    findings=[]
    try:
        candidate=git("rev-parse","--verify",f"{ref}^{{commit}}").strip()
        roots,selection=_selected_roots(candidate,manifest)
        paths=tracked_files(candidate,manifest)
    except (OSError,ValueError,TypeError,RuntimeError,subprocess.SubprocessError) as exc:
        return {"schema_version":1,"task_id":task_id,"ref":ref,"visual_task":True,"scanned_files":[],
                "approval_allowed":False,"finding_count":1,"findings":[{"category":"evidence","detail":"shipping source enumeration failed: "+str(exc)}],"passed":False}
    entries=git("ls-tree","-r","-z",candidate,"--").split("\0")
    modes={row.split("\t",1)[1]:row.split(" ",1)[0] for row in entries if "\t" in row}
    pending=[path for path in paths if not match(path,excluded)]; inspected=set()
    while pending:
        path=pending.pop(0)
        if path in inspected: continue
        inspected.add(path)
        if modes.get(path) not in {"100644","100755"}:
            findings.append({"path":path,"category":"evidence","detail":"shipping symlink/submodule requires explicit source dependency resolution"})
            continue
        if pathlib.PurePosixPath(path).suffix.lower() not in exts: continue
        files.append(path)
        try: body=text_at(candidate,path)
        except Exception as exc:
            findings.append({"path":path,"line":0,"token":"<unreadable>","category":"evidence","detail":str(exc)})
            continue
        # Candidate source may explicitly name upstream files outside its selected
        # project. Such dependencies require an additive root, never a skip rule.
        if manifest is not None:
            for literal in re.findall(r'["\']([^"\'\n]+)["\']',body):
                target=None
                if literal.startswith("res://"):
                    project=selection["shipping_scope"]["project_root"].rstrip("/")
                    target=posixpath.normpath(project+"/"+literal[6:])
                elif literal.startswith("../"):
                    target=posixpath.normpath(posixpath.dirname(path)+"/"+literal)
                elif literal.startswith(tuple(p.get("shipping_roots",[]))): target=posixpath.normpath(literal)
                if target and not target.startswith(tuple(roots)):
                    findings.append({"path":path,"line":0,"token":literal,"category":"unselected_dependency",
                                     "detail":"source references a path outside selected shipping roots"})
                elif target in paths and target not in inspected:
                    # A runtime dependency is shipped even when its folder name
                    # normally denotes a test/tool fixture.
                    pending.append(target)
        for lineno,line in enumerate(body.splitlines(),1):
            for category,token in forbidden:
                if re.search(r"(?<![A-Za-z0-9_])"+re.escape(token)+r"(?![A-Za-z0-9_])",line):
                    findings.append({"path":path,"line":lineno,"token":token,"category":category,"text":line.strip()[:240]})
    critics=set(next((w.get("critic_requirements",[]) for w in registry().get("workstreams",[]) if w.get("task_id")==task_id),[]))
    critics.update(graph().get("tasks",{}).get(task_id,{}).get("critics",[]))
    critics.update(load(DOCS/"CRITIC_MATRIX.json").get("task_applicability",{}).get(task_id,[]))
    visual=bool(critics.intersection(set(p.get("visual_critic_ids",[])))) or any(pathlib.PurePosixPath(x).suffix in {".tscn",".tres",".res",".gdshader"} for x in files)
    return {"schema_version":1,"task_id":task_id,"ref":candidate,"visual_task":visual,
            "scan_scope":"all_selected_active_project_and_dependency_files","shipping_roots":roots,
            "source_selection":selection,"approval_allowed":False,"ownership_patterns":patterns,
            "scanned_files":files,"finding_count":len(findings),"findings":findings,"passed":not findings}

def effective_candidate(task_id: str)->str|None:
    for record in reversed(task_invalidation_records(task_id)):
        candidate=record.get("repair_candidate_commit")
        if isinstance(candidate,str) and HEX40.fullmatch(candidate):
            return candidate
    row=next((w for w in registry().get("workstreams",[]) if w.get("task_id")==task_id),None)
    candidate=(row or {}).get("candidate_commit")
    return candidate if isinstance(candidate,str) and HEX40.fullmatch(candidate) else None

def signoff_path(task_id: str,candidate: str)->str:
    return f"Docs/Production/VisualApprovals/{task_id}/{candidate}.json"

def _read_record(path: str, integration_ref: str|None)->dict[str,Any]:
    if integration_ref:
        return strict_json_loads(git("show",f"{integration_ref}:{path}"))
    return strict_json_loads((ROOT/path).read_bytes())

def _number(value: Any)->bool:
    if type(value) not in (int,float): return False
    try: return math.isfinite(value)
    except (OverflowError,TypeError): return False

def _artifact_bytes(item: Any, integration_ref: str|None)->tuple[bytes|None,list[str]]:
    if not isinstance(item,dict): return None,["artifact entry must be an object"]
    rel=item.get("path");digest=item.get("sha256")
    if not isinstance(rel,str) or not rel or "\\" in rel or pathlib.PurePosixPath(rel).is_absolute() or ".." in pathlib.PurePosixPath(rel).parts:
        return None,["artifact path must remain inside the repository"]
    if not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest):
        return None,["artifact sha256 is missing or invalid"]
    try:
        if integration_ref:
            entry=git("ls-tree","-z",integration_ref,"--",rel)
            if not entry.startswith(("100644 ","100755 ")):
                return None,["artifact is missing or is not a regular Git file"]
            data=git("show",f"{integration_ref}:{rel}",text=False)
        else:
            raw=ROOT/rel; resolved=raw.resolve()
            if raw.is_symlink() or not resolved.is_relative_to(ROOT.resolve()) or not resolved.is_file():
                return None,["artifact is missing, escapes the repository or is a symlink"]
            data=resolved.read_bytes()
    except (OSError,subprocess.SubprocessError) as exc:
        return None,["artifact bytes unavailable: "+str(exc)]
    if hashlib.sha256(data).hexdigest()!=digest:
        return None,["artifact sha256 mismatch"]
    return data,[]

def _image_size(data: bytes)->tuple[int,int]:
    # Pillow is already pinned in tools/havenline/requirements-environment.txt.
    from PIL import Image
    with Image.open(io.BytesIO(data)) as img:
        if img.format not in {"PNG","JPEG","WEBP"}: raise ValueError("unsupported reference/capture image format")
        size=img.size;img.verify()
    if min(size)<=0: raise ValueError("empty image")
    return size

def _video_metadata(data: bytes)->dict[str,Any]:
    with tempfile.NamedTemporaryFile(suffix=".mp4") as video:
        video.write(data);video.flush()
        result=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0",
            "-show_entries","stream=width,height,avg_frame_rate,duration:format=duration","-of","json",video.name],stderr=subprocess.PIPE,text=True,timeout=20)
        subprocess.run(["ffmpeg","-v","error","-xerror","-i",video.name,"-map","0:v:0","-f","null","-"],
                       stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=60)
    result=json.loads(result); streams=result.get("streams",[])
    if len(streams)!=1: raise ValueError("motion artifact has no decodable video stream")
    stream=streams[0]
    return {"width":int(stream["width"]),"height":int(stream["height"]),
            "fps":float(Fraction(stream["avg_frame_rate"])),
            "duration":float(stream.get("duration",result.get("format",{}).get("duration",0)))}

def _reference_frames_errors(fidelity: dict,integration_ref: str|None)->list[str]:
    errors=[]
    sources={s["id"]:s for s in load(ROOT/"Docs/Design/ReferenceVideoLock/reference-video-sources.json")["sources"]}
    frames=fidelity.get("reference_frames")
    if not isinstance(frames,list) or not frames: return ["hash-bound actual reference frame artifacts are missing"]
    seen=set()
    for index,frame in enumerate(frames):
        prefix=f"reference frame {index}: "
        if not isinstance(frame,dict): errors.append(prefix+"entry must be an object");continue
        rid=frame.get("reference_id"); source=sources.get(rid) if isinstance(rid,str) else None
        if not source: errors.append(prefix+"unknown locked reference_id");continue
        seen.add(rid)
        if frame.get("video_sha256")!=source["sha256"]: errors.append(prefix+"original video hash mismatch")
        timestamp=frame.get("sampled_timestamp_seconds")
        if not _number(timestamp) or not 0<=timestamp<source["duration_seconds"]:
            errors.append(prefix+"sampled timestamp outside the locked original")
        data,failures=_artifact_bytes(frame,integration_ref);errors.extend(prefix+x for x in failures)
        if data is not None:
            try: _image_size(data)
            except Exception as exc: errors.append(prefix+"artifact is not a valid image: "+str(exc))
    if not {"A","B"}<=seen: errors.append("actual frame artifacts from both locked A/B originals are required")
    return errors

def _capture_errors(evidence: dict,candidate: str,req: dict,integration_ref: str|None)->list[str]:
    errors=[]
    if evidence.get("candidate_commit")!=candidate: errors.append("capture evidence candidate identity mismatch")
    minimum=req["minimum_internal_resolution"];seen=set()
    stills=evidence.get("stills")
    if not isinstance(stills,list) or len(stills)<int(req["minimum_stills"]):
        errors.append("actual hash-bound candidate stills are missing");stills=[]
    if evidence.get("stills_count")!=len(stills): errors.append("candidate still count does not match actual artifact list")
    videos=evidence.get("motion_videos")
    if not isinstance(videos,list) or not videos: errors.append("actual hash-bound candidate motion artifact is missing");videos=[]
    duration=0.0
    for kind,items in (("still",stills),("motion",videos)):
        for index,item in enumerate(items):
            prefix=f"candidate {kind} {index}: "
            if not isinstance(item,dict): errors.append(prefix+"entry must be an object");continue
            if item.get("candidate_commit")!=candidate: errors.append(prefix+"candidate identity mismatch")
            for field in ("scene","state","camera"):
                if not isinstance(item.get(field),str) or not item[field].strip(): errors.append(prefix+field+" metadata missing")
            digest=item.get("sha256")
            if isinstance(digest,str):
                if digest in seen: errors.append(prefix+"duplicate capture bytes do not add evidence coverage")
                seen.add(digest)
            data,failures=_artifact_bytes(item,integration_ref);errors.extend(prefix+x for x in failures)
            if data is None: continue
            try:
                if kind=="still": width,height=_image_size(data)
                else:
                    metadata=_video_metadata(data);width,height=metadata["width"],metadata["height"]
                    if not _number(metadata["fps"]) or metadata["fps"]<req["minimum_capture_fps"]: errors.append(prefix+"actual capture FPS below policy")
                    if not _number(metadata["duration"]) or metadata["duration"]<=0: errors.append(prefix+"invalid actual duration")
                    else: duration+=metadata["duration"]
                if width<minimum[0] or height<minimum[1]: errors.append(prefix+"actual capture dimensions below policy")
            except Exception as exc: errors.append(prefix+"actual media could not be decoded: "+str(exc))
    if duration<float(req["minimum_motion_seconds"]): errors.append("decoded motion proof is shorter than policy minimum")
    declared=evidence.get("motion_video_seconds")
    if not _number(declared) or abs(duration-declared)>0.05:
        errors.append("declared motion duration does not match decoded artifacts")
    return errors

def _visual_critic_errors(task_id: str,fidelity: dict)->list[str]:
    matrix=load(DOCS/"CRITIC_MATRIX.json");execution=load(DOCS/"CRITIC_EXECUTION.json")
    required=set(matrix.get("task_applicability",{}).get(task_id,[]))
    required.update(graph().get("tasks",{}).get(task_id,{}).get("critics",[]))
    if not required: return ["visual review requires an authentic known task definition"]
    required=set(required_final_critics(task_id,sorted(required),style_required=True))
    resource_policy=load(DOCS/"RESOURCE_ACTION_REGISTRY.json").get("task_policy",{})
    if task_id in resource_policy.get("always_motion_critic_tasks",[]) or (
            task_id in resource_policy.get("conditional_motion_critic_tasks",[]) and fidelity.get("animation_delta") is True):
        required.add("C5")
    required.intersection_update(policy().get("visual_critic_ids",[]));required.add("C1")
    maps=fidelity.get("critic_scores")
    if not isinstance(maps,dict): return ["per-critic exact visual dimension score maps are missing"]
    errors=[]
    if not required<=set(maps): errors.append("required visual critic score maps are missing: "+",".join(sorted(required-set(maps))))
    if any(not isinstance(cid,str) for cid in maps): return errors+["critic score map keys must be critic IDs"]
    for cid in sorted(set(maps)|required):
        if cid not in execution.get("critics",{}): errors.append("unknown visual critic score map: "+cid);continue
        spec,_=resolve_critic(task_id,cid,execution,matrix)
        errors.extend(f"{cid}: {message}" for message in score_errors(maps.get(cid),spec["dimensions"],cid,phase="final"))
    return errors

def _build_scope_errors(rec: dict,candidate: str,integration_ref: str|None)->list[str]:
    scope=rec.get("shipping_scope")
    if not isinstance(scope,dict): return ["source-bound shipping scope is missing"]
    data,errors=_artifact_bytes(scope.get("build_evidence"),integration_ref)
    if data is None: return ["shipping build receipt: "+x for x in errors]
    try: proof=strict_json_loads(data)
    except (ValueError,UnicodeError) as exc: return ["shipping build receipt must be structured JSON: "+str(exc)]
    if not isinstance(proof,dict): return ["shipping build receipt must be an object"]
    for field in ("candidate_commit","project_root","project_file_sha256","dependency_roots"):
        if proof.get(field)!=scope.get(field): errors.append("shipping build receipt "+field+" mismatch")
    if proof.get("candidate_commit")!=candidate: errors.append("shipping build receipt candidate identity mismatch")
    if proof.get("source_bound") is not True or proof.get("passed") is not True:
        errors.append("shipping build receipt must pass with exact source binding")
    if proof.get("dependency_census_complete") is not True:
        errors.append("shipping build receipt dependency census is incomplete")
    captures=rec.get("visual_evidence",{})
    if not isinstance(captures,dict): captures={}
    for field in ("workflow_run_id","artifact_id"):
        if type(proof.get(field)) is not int or proof.get(field,0)<=0 or proof.get(field)!=captures.get(field):
            errors.append("shipping build receipt "+field+" does not bind the captured build")
    return errors

def _independent_review_errors(rec: dict,candidate: str,integration_ref: str|None)->list[str]:
    fidelity=rec.get("reference_fidelity",{});errors=[]
    if not isinstance(fidelity,dict): fidelity={}
    independent=fidelity.get("independent_review")
    if not isinstance(independent,dict): return ["independent inspection provenance must be an object"]
    if independent.get("independent_runtime") is not True: errors.append("independent visual inspection provenance missing")
    if independent.get("candidate_commit")!=candidate: errors.append("independent inspection candidate identity mismatch")
    for field in ("provider","model","request_or_run_id"):
        if not isinstance(independent.get(field),str) or not independent[field].strip(): errors.append("independent inspection "+field+" missing")
    data,failures=_artifact_bytes({"path":independent.get("raw_output_path"),"sha256":independent.get("raw_output_sha256")},integration_ref)
    errors.extend("independent inspection: "+x for x in failures)
    if data is None: return errors
    try: raw=strict_json_loads(data)
    except (ValueError,UnicodeError) as exc: return errors+["independent raw report must be structured JSON: "+str(exc)]
    if not isinstance(raw,dict): return errors+["independent raw report must be an object"]
    errors.extend("independent raw report: "+x for x in binding_errors(raw,phase="final"))
    if raw.get("candidate_commit")!=candidate or raw.get("task_id")!=rec.get("task_id"):
        errors.append("independent raw report source/task identity mismatch")
    for field in ("independent_runtime","provider","model","request_or_run_id"):
        if raw.get(field)!=independent.get(field): errors.append("independent raw report "+field+" provenance mismatch")
    if raw.get("independent_runtime") is not True: errors.append("independent raw report must identify an independent runtime")
    for field in ("coverage_complete","passed","reference_pixels_reviewed","whole_frame_reviewed","side_by_side_reference_reviewed"):
        if raw.get(field) is not True: errors.append("independent raw report "+field+" must be true")
    if raw.get("status")!="PASS": errors.append("independent raw report must explicitly PASS")
    for field in ("defects","failed_visible_classes"):
        if raw.get(field)!=[]: errors.append("independent raw report "+field+" must be an explicit empty list")
    for field in ("critic_scores","reference_frames","primary_reference_ids","animation_delta"):
        if raw.get(field)!=fidelity.get(field): errors.append("independent raw report "+field+" differs from signoff")
    errors.extend("independent raw report: "+x for x in _visual_critic_errors(rec.get("task_id",""),raw))
    for field in ("visual_evidence","shipping_scope"):
        if raw.get(field)!=rec.get(field): errors.append("independent raw report "+field+" does not bind the inspected artifacts")
    if "C5" in fidelity.get("critic_scores",{}):
        media=rec.get("visual_evidence",{}).get("motion_videos",[])
        if integration_ref:
            # Decode the reviewed integration bytes, never a later worktree copy.
            with tempfile.TemporaryDirectory(prefix="havenline-reviewed-motion-") as directory:
                media_root=pathlib.Path(directory)
                for item in media:
                    data,failures=_artifact_bytes(item,integration_ref)
                    errors.extend("independent playback: "+x for x in failures)
                    if data is not None:
                        target=media_root/item["path"];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                errors.extend("independent playback: "+x for x in playback_errors(raw,media,root=media_root))
        else:
            errors.extend("independent playback: "+x for x in playback_errors(raw,media,root=ROOT))
    return errors

def validate_signoff(task_id: str,candidate: str,integration_ref: str|None=None)->dict[str,Any]:
    p=policy(); req=p["human_visual_gate"]; errors=[]
    if not re.fullmatch(r"T[0-9]{2}",task_id or "") or not isinstance(candidate,str) or not HEX40.fullmatch(candidate):
        return {"passed":False,"task_id":task_id,"candidate_sha":candidate,"errors":["task and candidate identities must be canonical task ID and exact 40-hex SHA"]}
    path=signoff_path(task_id,candidate)
    if integration_ref:
        try: integration_ref=git("rev-parse","--verify",f"{integration_ref}^{{commit}}").strip()
        except (OSError,subprocess.SubprocessError) as exc:
            return {"passed":False,"task_id":task_id,"candidate_sha":candidate,"errors":["signoff integration source is unavailable: "+str(exc)]}
    try: rec=_read_record(path,integration_ref)
    except Exception as exc:
        return {"passed":False,"task_id":task_id,"candidate_sha":candidate,"record_path":path,"errors":[f"visual signoff record missing/unreadable: {exc}"]}
    if not isinstance(rec,dict):
        return {"passed":False,"task_id":task_id,"candidate_sha":candidate,"record_path":path,"errors":["visual signoff record must be an object"]}
    if rec.get("schema_version")!=1 or rec.get("task_id")!=task_id or rec.get("candidate_sha")!=candidate:
        errors.append("visual signoff identity mismatch")
    errors.extend(binding_errors(rec,phase="final"))
    inv=active_invalidation(task_id)
    if inv: errors.append("active approval invalidation: "+str(inv.get("family")))
    if rec.get("user_visual_rejection") is True:
        errors.append("user explicitly rejected final visual reference fidelity")
    primitive=rec.get("primitive_audit",{})
    if not isinstance(primitive,dict) or primitive.get("passed") is not True or type(primitive.get("findings_count")) is not int or primitive.get("findings_count")!=0:
        errors.append("primitive audit must pass with zero findings")
    actual_scan=scan_task(task_id,candidate,rec)
    if not actual_scan.get("passed"): errors.append("actual candidate shipping primitive/source audit did not pass")
    errors.extend(_build_scope_errors(rec,candidate,integration_ref))
    evidence=rec.get("visual_evidence",{})
    if not isinstance(evidence,dict): evidence={};errors.append("visual evidence must be an object")
    if evidence.get("source_bound") is not True: errors.append("visual evidence must be exact-source bound")
    if type(evidence.get("workflow_run_id")) is not int or evidence.get("workflow_run_id",0)<=0: errors.append("workflow_run_id missing")
    if type(evidence.get("artifact_id")) is not int or evidence.get("artifact_id",0)<=0: errors.append("artifact_id missing")
    if type(evidence.get("stills_count")) is not int or evidence.get("stills_count",0)<int(req["minimum_stills"]): errors.append("not enough final stills")
    if not _number(evidence.get("motion_video_seconds")) or evidence.get("motion_video_seconds",0)<float(req["minimum_motion_seconds"]): errors.append("motion proof too short")
    res=evidence.get("internal_resolution",[])
    minimum=req["minimum_internal_resolution"]
    if not isinstance(res,list) or len(res)!=2 or any(type(x) is not int for x in res) or res[0]<minimum[0] or res[1]<minimum[1]: errors.append("visual proof is below native 4K minimum")
    if not _number(evidence.get("capture_fps")) or evidence.get("capture_fps",0)<int(req["minimum_capture_fps"]): errors.append("visual motion proof is below 60 FPS")
    errors.extend(_capture_errors(evidence,candidate,req,integration_ref))
    fidelity=rec.get("reference_fidelity",{})
    if not isinstance(fidelity,dict): fidelity={};errors.append("reference fidelity must be an object")
    if fidelity.get("candidate_commit")!=candidate: errors.append("reference fidelity candidate identity mismatch")
    if fidelity.get("whole_frame_reviewed") is not True: errors.append("whole-frame reference review is required")
    if fidelity.get("side_by_side_reference_reviewed") is not True: errors.append("side-by-side reference review is required")
    if fidelity.get("reference_pixels_reviewed") is not True: errors.append("actual reference pixels must be independently reviewed")
    if fidelity.get("coverage_complete") is not True: errors.append("reference fidelity evidence coverage is incomplete")
    if fidelity.get("passed") is not True: errors.append("whole-frame reference fidelity did not pass")
    failed=fidelity.get("failed_visible_classes")
    if not isinstance(failed,list) or failed: errors.append("zero failed visible asset classes are required")
    ids=fidelity.get("primary_reference_ids")
    if not isinstance(ids,list) or not {"A","B"}<=set(x for x in ids if isinstance(x,str)):
        errors.append("both locked A/B reference identities must be reviewed")
    try:
        errors.extend(_reference_frames_errors(fidelity,integration_ref))
        errors.extend(_visual_critic_errors(task_id,fidelity))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        errors.append("canonical reference/critic proof could not be validated: "+str(exc))
    try: errors.extend(_independent_review_errors(rec,candidate,integration_ref))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        errors.append("independent inspection could not be validated: "+str(exc))
    if rec.get("user_visual_approval") is not True: errors.append("explicit user visual approval is required")
    return {"passed":not errors,"validation_kind":"FINAL_VISUAL_SIGNOFF","task_id":task_id,"candidate_sha":candidate,"record_path":path,
            "actual_primitive_audit":actual_scan,"errors":errors}

def effective_approval(task_id: str, ref: str="HEAD")->dict[str,Any]:
    g=graph(); gates=load(DOCS/"task-gates.json"); errors=[]
    historical=g.get("tasks",{}).get(task_id,{}).get("status")=="APPROVED" and task_id in gates.get("approved_tasks",[])
    if not historical: errors.append("historical lifecycle/task-gate approval is absent")
    inv=active_invalidation(task_id)
    if inv: errors.append("active approval invalidation: "+str(inv.get("family")))
    candidate=None;signoff=None;scan=None
    try: candidate=git("rev-parse","--verify",f"{ref}^{{commit}}").strip()
    except (OSError,subprocess.SubprocessError): errors.append("current dependency source is not an exact available commit")
    if candidate:
        # Current-source proof selects the actual shipping project/dependencies.
        # A diagnostic inventory of unselected preserved projects is not a gate.
        signoff=validate_signoff(task_id,candidate,None)
        scan=signoff.get("actual_primitive_audit")
        if not signoff.get("passed"): errors.extend(["visual signoff: "+e for e in signoff.get("errors",[])])
    return {"passed":not errors,"task_id":task_id,"candidate_sha":candidate,"historical_approved":historical,
            "effective_approved":not errors,"approval_allowed":not errors,"active_invalidation":inv,
            "primitive_audit":scan,"visual_signoff":signoff,"errors":errors}

def audit_effective_approvals(ref: str="HEAD")->dict[str,Any]:
    gates=load(DOCS/"task-gates.json"); reg=registry(); rows=[]; errors=[]
    approved=set(gates.get("approved_tasks",[]))
    for task_id in sorted(approved):
        result=effective_approval(task_id,ref);covered=bool(result.get("active_invalidation"))
        if not result["passed"] and not covered: errors.extend(f"{task_id}: "+x for x in result["errors"])
        scan=result.get("primitive_audit") or {}
        rows.append({"task_id":task_id,"candidate_sha":result.get("candidate_sha"),"historical_approved":True,
                     "finding_count":scan.get("finding_count"),"invalidation_active":covered,
                     "effective_approved":result["passed"],"visual_signoff":result.get("visual_signoff")})
    for row in reg.get("workstreams",[]):
        task_id=row.get("task_id","")
        if row.get("status") not in {"INTEGRATION_READY","INTEGRATING","UNDER_REVIEW"}: continue
        inv=active_invalidation(task_id)
        if inv: errors.append(f"{task_id} cannot be {row.get('status')} with active visual invalidation")
        candidate=row.get("candidate_commit")
        if not isinstance(candidate,str) or not HEX40.fullmatch(candidate):
            errors.append(f"{task_id} integration-ready visual task has no exact candidate_commit")
        else:
            signoff=validate_signoff(task_id,candidate,None)
            if not signoff.get("passed"): errors.extend([f"{task_id} integration-ready visual signoff: {e}" for e in signoff.get("errors",[])])
    return {"passed":not errors,"ref":git("rev-parse",f"{ref}^{{commit}}").strip(),"rows":rows,"errors":errors}

def main()->None:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("audit-task");a.add_argument("task_id");a.add_argument("--candidate",default="HEAD");a.add_argument("--require-clean",action="store_true");a.add_argument("--output")
    e=sub.add_parser("effective-approval");e.add_argument("task_id");e.add_argument("--ref",default="HEAD")
    p=sub.add_parser("audit-effective-approvals");p.add_argument("--ref",default="HEAD")
    s=sub.add_parser("signoff");s.add_argument("task_id");s.add_argument("--candidate",required=True);s.add_argument("--integration-ref")
    args=ap.parse_args()
    if args.cmd=="audit-task":
        out=scan_task(args.task_id.upper(),args.candidate)
        if args.output: pathlib.Path(args.output).write_text(json.dumps(out,indent=2)+"\n")
        print(json.dumps(out,indent=2))
        if args.require_clean and not out["passed"]: raise SystemExit(2)
    elif args.cmd=="effective-approval":
        out=effective_approval(args.task_id.upper(),args.ref);print(json.dumps(out,indent=2));raise SystemExit(0 if out["passed"] else 2)
    elif args.cmd=="audit-effective-approvals":
        out=audit_effective_approvals(args.ref);print(json.dumps(out,indent=2));raise SystemExit(0 if out["passed"] else 2)
    else:
        out=validate_signoff(args.task_id.upper(),args.candidate,args.integration_ref);print(json.dumps(out,indent=2));raise SystemExit(0 if out["passed"] else 2)
if __name__=="__main__": main()
