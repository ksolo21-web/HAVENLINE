#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from lib import DOCS, load_json, any_match, changed_files

def calculate(files:list[str]):
    matrix=load_json(DOCS/"REGRESSION_MATRIX.json")
    impacted=set(); suites=set(matrix["universal_baseline"]); matched=False; governance_only=True
    for rule in matrix["impact_rules"]:
        if any(any_match(f,rule["patterns"]) for f in files):
            matched=True
            impacted.update(rule.get("tasks",[]))
            suites.update(rule.get("suites",[]))
            if not rule.get("governance_only",False):
                governance_only=False
    production=[f for f in files if f.startswith("HavenlineGodot/")]
    if production and not matched:
        # Unknown production changes force the full currently known baseline.
        governance_only=False
        for group in matrix["approved_task_suites"].values():
            suites.update(x for x in group if x.endswith(".gd") or not x.endswith(".py"))
        impacted.update(matrix["approved_task_suites"].keys())
    return {"changed_files":files,"impacted_approved_tasks":sorted(impacted),"required_suites":sorted(suites),"governance_only":governance_only and not production,"unknown_production_fallback":bool(production and not matched)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base");ap.add_argument("--head",default="HEAD");ap.add_argument("files",nargs="*")
    a=ap.parse_args()
    files=a.files or changed_files(a.base,a.head)
    print(json.dumps(calculate(files),indent=2))

if __name__=="__main__": main()
