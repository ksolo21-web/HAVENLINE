#!/usr/bin/env python3
"""Canonical owner promotion check. Never imports or executes candidate code."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess

PINNED_BRANCH = "codex/havenline-sequential-task-01"
SELF_PATH = "tools/havenline/production/verify_python_repair_bindings.py"


def verify_integration_branch(branch):
    return [] if branch == PINNED_BRANCH else ["active integration branch does not match pinned canonical branch"]


def _stable_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def repeated_python_bindings(plan: dict) -> list[dict]:
    rows = []
    for group in plan.get("repair_sufficiency", {}).get("repair_groups", []):
        if not isinstance(group, dict) or not isinstance(group.get("same_family_attempt_count"), int) or group["same_family_attempt_count"] < 2:
            continue
        contract = group.get("implementation_diff_contract", {})
        for path in contract.get("causal_files", []):
            if isinstance(path, str) and path.endswith(".py"):
                rows.append({"group_id": group.get("group_id"), "failure_family_id": group.get("failure_family", {}).get("id"),
                             "comparison_base": contract.get("comparison_base"), "path": path,
                             "operation_contract_sha256": _stable_digest(group)})
    return rows


def python_source_review_errors(plan: dict, review: dict | None, before: dict | None, after: dict | None) -> list[str]:
    expected = repeated_python_bindings(plan)
    if not expected and review is None:
        return []
    if not isinstance(review, dict):
        return ["trusted canonical Python source review missing"]
    errors = []
    required = {"schema_version": 1, "task_id": plan.get("task_id"), "diagnosis_id": plan.get("diagnosis_id"),
                "decision": "ACCEPTED_BOUNDED_SOURCE", "non_voting": True, "task_approved": False,
                "thresholds_unchanged": True, "runtime_model_contracts_unchanged": True}
    for key, value in required.items():
        if review.get(key) != value:
            errors.append("Python source review binding mismatch: " + key)
    provenance = review.get("independent_review", {})
    if not isinstance(provenance, dict) or not all(isinstance(provenance.get(k), str) and provenance[k] for k in ("reviewer", "review_id")):
        errors.append("Python source review independent provenance missing")
    for key, length in (("reviewed_commit", 40), ("reviewed_tree", 40), ("evidence_sha256", 64)):
        if not isinstance(provenance, dict) or re.fullmatch("[0-9a-f]{" + str(length) + "}", str(provenance.get(key, ""))) is None:
            errors.append("Python source review invalid provenance: " + key)
    rows = review.get("bindings", [])
    if not isinstance(rows, list):
        return errors + ["Python source review bindings invalid"]
    keys = [(row.get("group_id"), row.get("path")) for row in rows if isinstance(row, dict)]
    wanted = [(row["group_id"], row["path"]) for row in expected]
    if len(keys) != len(rows) or len(set(keys)) != len(keys) or len({row.get("path") for row in rows}) != len(rows) or len(set(wanted)) != len(wanted) or set(keys) != set(wanted):
        return errors + ["Python source review exact causal file set mismatch"]
    for binding in expected:
        row = rows[keys.index((binding["group_id"], binding["path"]))]
        for key, value in binding.items():
            if row.get(key) != value:
                errors.append("Python source review contract mismatch: " + binding["path"] + ": " + key)
        path = binding["path"]
        for label, sources in (("before", before), ("after", after)):
            source = (sources or {}).get(path)
            if not isinstance(source, str):
                errors.append("Python source evidence missing: " + path + ": " + label)
            elif hashlib.sha256(source.encode("utf-8")).hexdigest() != row.get(label + "_sha256"):
                errors.append("Python source review exact bytes mismatch: " + path + ": " + label)
    if review.get("causal_source_set_sha256") != _stable_digest(rows):
        errors.append("Python source review causal source set digest mismatch")
    return errors


def _remote_tip(raw: bytes) -> str:
    expected = "refs/heads/" + PINNED_BRANCH
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise ValueError("invalid remote ref encoding") from exc
    if len(lines) != 1 or re.fullmatch(r"[0-9a-f]{40}\t" + re.escape(expected), lines[0]) is None:
        raise ValueError("remote response must contain exactly the full pinned branch ref")
    return lines[0].split("\t", 1)[0]


def promotion_dag_errors(candidate: str, parents: list[str], reviewed: str, authority: str, is_ancestor) -> list[str]:
    errors=[]
    if parents != [reviewed, authority]:
        errors.append("promotion requires exact ordered reviewed-source and authority parents")
    if candidate in (reviewed, authority) or is_ancestor(authority, reviewed):
        errors.append("promotion authority must be outside reviewed-source ancestry")
    return errors


def authority_context(plan: dict, candidate: str, active: str | None, is_ancestor) -> tuple[str | None, list[str]]:
    """Classify actual Git identities, never a caller-selected execution mode."""
    snapshot = plan.get("reconciled_integration_head")
    if any(not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None for value in (snapshot, active)):
        return None, ["exact authority snapshot and active canonical head required"]
    if snapshot == candidate:
        return None, ["authority snapshot cannot authorize itself as repair candidate"]
    if not is_ancestor(snapshot, candidate):
        return None, ["authority snapshot is not candidate ancestor"]
    if active == snapshot:
        return "ISOLATED_REPAIR", []
    if candidate == active:
        return "INTEGRATED_REPAIR", []
    return None, ["stale isolated candidate: active canonical head differs from authority snapshot"]


def load_trusted_python_review(plan: dict, head: str, integration_head: str | None, branch: str | None, read_ref=None, is_ancestor=None):
    if not repeated_python_bindings(plan):
        return None, []
    errors = verify_integration_branch(branch)
    task = plan.get("task_id")
    if not isinstance(task, str) or re.fullmatch(r"T[0-9]{2}", task) is None:
        return None, errors + ["Python source review task invalid"]
    if read_ref is None:
        read_ref = lambda ref, path: subprocess.check_output(["git", "show", f"{ref}:{path}"])
    if is_ancestor is None:
        is_ancestor = lambda base, tip: subprocess.run(["git", "merge-base", "--is-ancestor", base, tip], check=False).returncode == 0
    mode, context_errors = authority_context(plan, head, integration_head, is_ancestor)
    errors.extend(context_errors)
    if errors:
        return None, errors
    authority_head = plan["reconciled_integration_head"]
    path = f"Docs/Production/ChangeRequests/{task}-repeated-python-source-review.json"
    try:
        trusted = read_ref(authority_head, path)
        if trusted != read_ref(head, path):
            errors.append("Python source review candidate record differs from canonical authority")
        review = json.loads(trusted)
    except (subprocess.CalledProcessError, ValueError, TypeError, KeyError):
        return None, errors + ["trusted canonical Python source review unavailable"]
    return (None if errors else review), errors


def verify_candidate(repo: pathlib.Path, canonical_head: str, candidate: str, task: str, require_promotion_dag: bool = False) -> dict:
    errors = []
    env = {key:value for key,value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_CONFIG_NOSYSTEM="1")
    def git(*args):
        return subprocess.check_output(["git", "--no-replace-objects", "-C", str(repo), *args], env=env, stderr=subprocess.PIPE, timeout=30)
    def blob(ref, path):
        if not isinstance(path, str) or path.startswith(("/", "-")) or any(x in ("", ".", "..") for x in path.split("/")):
            raise ValueError("unsafe source path")
        entry = git("ls-tree", "-z", ref, "--", path).split(b"\0")
        if len(entry) != 2 or not entry[0]:
            raise ValueError("missing or ambiguous regular blob: " + path)
        info, found = entry[0].split(b"\t", 1)
        mode, kind, oid = info.decode().split()
        if kind != "blob" or mode not in ("100644", "100755") or found.decode() != path:
            raise ValueError("nonregular source blob: " + path)
        raw = git("cat-file", "blob", oid)
        return raw, {"path":path,"mode":mode,"blob":oid,"sha256":hashlib.sha256(raw).hexdigest()}
    report = {"schema_version":1,"passed":False,"non_voting":True,"task_approved":False,"task_id":task,"errors":errors,"sources":[]}
    try:
        if re.fullmatch(r"T[0-9]{2}", task) is None or re.fullmatch(r"[0-9a-f]{40}", canonical_head) is None or re.fullmatch(r"[0-9a-f]{40}", candidate) is None:
            raise ValueError("exact task and commit identities required")
        resolved = git("rev-parse", "refs/remotes/origin/" + PINNED_BRANCH).decode().strip()
        if resolved != canonical_head:
            raise ValueError("canonical head differs from fetched pinned branch")
        plan_raw, _ = blob(candidate, f"Docs/Production/{task}/REPAIR_PLAN.json")
        plan = json.loads(plan_raw)
        def ancestor(base, tip):
            try:
                git("merge-base", "--is-ancestor", base, tip)
                return True
            except subprocess.CalledProcessError:
                return False
        mode, context_errors = authority_context(plan, candidate, canonical_head, ancestor)
        errors.extend(context_errors)
        if context_errors:
            raise ValueError("invalid repair authority lifecycle")
        authority_head = plan["reconciled_integration_head"]
        report.update(canonical_head=canonical_head,authority_head=authority_head,execution_mode=mode,candidate_commit=candidate,candidate_tree=git("rev-parse",candidate+"^{tree}").decode().strip())
        verifier, identity = blob(authority_head, SELF_PATH)
        if pathlib.Path(__file__).read_bytes() != verifier:
            raise ValueError("executing verifier differs from canonical bytes")
        report["verifier"] = identity
        if blob(candidate, SELF_PATH) != (verifier, identity) or blob(canonical_head, SELF_PATH) != (verifier, identity):
            raise ValueError("candidate verifier differs from canonical bytes or regular mode")
        record_path = f"Docs/Production/ChangeRequests/{task}-repeated-python-source-review.json"
        raw, identity = blob(authority_head, record_path)
        report["authorization_record"] = identity
        if blob(candidate, record_path) != (raw, identity) or blob(canonical_head, record_path) != (raw, identity):
            raise ValueError("candidate record differs from canonical authority bytes or regular mode")
        review = json.loads(raw)
        c0_raw, _ = blob(candidate, f"Docs/Production/{task}/C0_ROOT_CAUSE.json")
        plan = json.loads(plan_raw);c0=json.loads(c0_raw)
        if review.get("c0_sha256") != hashlib.sha256(c0_raw).hexdigest() or plan.get("c0_report_sha256") != review.get("c0_sha256"):
            errors.append("authoritative C0 source binding mismatch")
        if plan.get("task_id") != task or c0.get("task_id") != task:
            errors.append("task or integration binding mismatch")
        provenance=review.get("independent_review", {})
        reviewed=provenance.get("reviewed_commit", "")
        if re.fullmatch(r"[0-9a-f]{40}", reviewed) is None:
            raise ValueError("reviewed commit missing")
        git("merge-base", "--is-ancestor", reviewed, candidate)
        if git("rev-parse", reviewed+"^{tree}").decode().strip() != provenance.get("reviewed_tree"):
            errors.append("reviewed tree mismatch")
        inherited=review.get("canonical_inherited_paths", [])
        allowed_inherited={
            f"Docs/Production/ChangeRequests/{task}-benchmark-liveness-contract.json",
            f"Docs/Production/ChangeRequests/{task}-c0-decoded-complete-evidence.json",
            f"Docs/Production/ChangeRequests/{task}-c0r-structured-mechanism-detection.json",
            record_path,
        }
        if not isinstance(inherited,list) or len(set(inherited))!=len(inherited) or set(inherited)!=allowed_inherited:
            raise ValueError("invalid canonical metadata inheritance set")
        plan_path=f"Docs/Production/{task}/REPAIR_PLAN.json"
        report_path=f"Docs/Production/{task}/C0R_REPAIR_SUFFICIENCY.json"
        old_plan=json.loads(blob(reviewed,plan_path)[0])
        expected_plan=json.loads(json.dumps(old_plan))
        expected_plan["reconciled_integration_head"]=authority_head
        expected_plan["inherited_noncausal_files"]=list(dict.fromkeys(old_plan.get("inherited_noncausal_files",[])+inherited))
        for fix in expected_plan.get("fixes",[]):
            fix["files"]=[path for path in fix["files"] if path not in inherited]
        if plan!=expected_plan:
            errors.append("post-review plan exceeds exact reconciliation policy")
        old_report=json.loads(blob(reviewed,report_path)[0])
        old_report["input_bindings"]["plan_sha256"]=hashlib.sha256(plan_raw).hexdigest()
        if json.loads(blob(candidate,report_path)[0])!=old_report:
            errors.append("post-review C0R report exceeds exact plan-hash reconciliation")
        changed=git("diff-tree","-r","--no-commit-id","--name-only","-z",reviewed,candidate).decode().split("\0")
        for path in filter(None,changed):
            if path in (plan_path,report_path):
                continue
            if path not in inherited or blob(candidate,path)!=blob(authority_head,path):
                errors.append("unreviewed post-freeze path change: "+path)
        for path in plan.get("inherited_noncausal_files", []):
            if blob(candidate,path)!=blob(authority_head,path) or blob(canonical_head,path)!=blob(authority_head,path):
                errors.append("inherited metadata differs from canonical: "+path)
        before={};after={}
        for row in review.get("bindings", []):
            path=row["path"];base=row["comparison_base"]
            if re.fullmatch(r"[0-9a-f]{40}", base) is None:
                raise ValueError("invalid comparison base")
            old, old_id=blob(base,path);new,new_id=blob(candidate,path);accepted,accepted_id=blob(reviewed,path)
            before[path]=old.decode("utf-8");after[path]=new.decode("utf-8")
            if old_id["mode"] != row.get("before_mode") or new_id["mode"] != row.get("after_mode") or new_id != accepted_id:
                errors.append("source mode or reviewed blob mismatch: "+path)
            report["sources"].append({"group_id":row["group_id"],"comparison_base":base,"before":old_id,"candidate":new_id,"reviewed":accepted_id})
        errors.extend(python_source_review_errors(plan,review,before,after))
        report["causal_source_set_sha256"]=review.get("causal_source_set_sha256")
        parents=git("rev-list", "--parents", "-n", "1", candidate).decode().strip().split()
        if not parents or parents[0]!=candidate:
            raise ValueError("candidate parent identity mismatch")
        dag_errors=promotion_dag_errors(candidate,parents[1:],reviewed,authority_head,ancestor)
        report["promotion_dag"]={"required":require_promotion_dag,"passed":not dag_errors,"parents":parents[1:],"reviewed_source":reviewed,"authority_head":authority_head,"errors":dag_errors,"concurrency_policy":"OWNER_NO_FORCE_FORWARD_ONLY"}
        if require_promotion_dag:
            errors.extend(dag_errors)
        if git("rev-parse", "refs/remotes/origin/" + PINNED_BRANCH).decode().strip() != canonical_head:
            errors.append("pinned canonical head advanced during verification")
        remote_tip=_remote_tip(git("ls-remote", "--exit-code", "origin", "refs/heads/"+PINNED_BRANCH))
        report["remote_tip_at_completion"]=remote_tip
        if remote_tip!=canonical_head:
            errors.append("remote canonical head advanced during verification")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError, TypeError, KeyError, UnicodeError, OSError) as exc:
        errors.append("canonical source verification failed: "+str(exc))
    report["passed"]=not errors
    return report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=pathlib.Path,required=True)
    ap.add_argument("--canonical-head",required=True)
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--task",required=True)
    ap.add_argument("--output",type=pathlib.Path,required=True)
    ap.add_argument("--promotion-check",action="store_true",help="Require the restricted DAG needed for atomic forward-only canonical promotion")
    args=ap.parse_args()
    result=verify_candidate(args.repo,args.canonical_head,args.candidate,args.task,args.promotion_check)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0 if result["passed"] else 2


if __name__=="__main__":
    raise SystemExit(main())
