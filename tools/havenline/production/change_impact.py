#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from lib import DOCS, load_json, any_match, changed_files

def calculate(files:list[str]):
    matrix=load_json(DOCS/"REGRESSION_MATRIX.json")
    impacted=set();suites=set(matrix["universal_baseline"])
    governance_only=True;unknown_production=[];file_matches={}
    for path in files:
        matched=[]
        for rule in matrix["impact_rules"]:
            if any_match(path,rule["patterns"]):
                matched.append(rule)
                impacted.update(rule.get("tasks",[]))
                suites.update(rule.get("suites",[]))
                if not rule.get("governance_only",False):
                    governance_only=False
        file_matches[path]=len(matched)
        if path.startswith("HavenlineGodot/") and not matched:
            unknown_production.append(path);governance_only=False
        elif matched and not all(r.get("governance_only",False) for r in matched):
            governance_only=False
    if unknown_production:
        # Unknown runtime changes always force the full currently known mandatory
        # regression baseline even if some other file in the same candidate matched.
        for group in matrix["approved_task_suites"].values():
            suites.update(group)
        impacted.update(matrix["approved_task_suites"].keys())
    return {
      "changed_files":files,
      "impacted_approved_tasks":sorted(impacted),
      "required_suites":sorted(suites),
      "governance_only":governance_only,
      "unknown_production_fallback":bool(unknown_production),
      "unknown_production_files":unknown_production,
      "file_rule_match_counts":file_matches
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base");ap.add_argument("--head",default="HEAD");ap.add_argument("files",nargs="*")
    a=ap.parse_args()
    files=a.files or changed_files(a.base,a.head)
    print(json.dumps(calculate(files),indent=2))

if __name__=="__main__": main()
