#!/usr/bin/env python3
"""Aggregate four exact T10 visual slices by min score + union defects."""
from __future__ import annotations
import argparse,hashlib,json,pathlib
DIMS={"C1":["reference_fidelity","visual_language","cross_view_consistency"],"C2":["geometry_contact","clipping_seams","intentional_gap_integrity","cross_view_integrity"]}
ORDER={"low":0,"medium":1,"high":2}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--critic",choices=["C1","C2"],required=True);ap.add_argument("--candidate",required=True);ap.add_argument("--manifest",required=True);ap.add_argument("--inputs",required=True);ap.add_argument("--out",required=True);ap.add_argument("--run-id",required=True);a=ap.parse_args()
 root=pathlib.Path(a.inputs);rows=[]
 for p in root.rglob("slice-result.json"):
  r=json.loads(p.read_text())
  if r.get("critic_id")==a.critic:rows.append(r)
 if {r.get("slice") for r in rows}!={0,1,2,3} or len(rows)!=4:raise ValueError("exact four slices required")
 mh=sha(a.manifest)
 if any(r.get("candidate")!=a.candidate or r.get("input_manifest_hash")!=mh for r in rows):raise ValueError("slice source mismatch")
 dims=DIMS[a.critic];defects=[];seen=set()
 for r in rows:
  for d in r["review"]["defects"]:
   if d not in seen:seen.add(d);defects.append(d)
 scores={d:min(r["review"]["scores"][d] for r in rows) for d in dims}
 coverage=all(r["review"]["coverage_complete"] is True for r in rows);confidence=min((r["review"]["confidence"] for r in rows),key=ORDER.get)
 passed=all(r["passed"] is True for r in rows) and all(v>9 for v in scores.values()) and not defects and coverage and confidence in ("medium","high")
 provider=rows[0]["provider"];model=rows[0]["model"]
 if any(r["provider"]!=provider or r["model"]!=model for r in rows):raise ValueError("reviewer identity mismatch")
 raw={"task_id":"T10","candidate_hash":a.candidate,"critic_id":a.critic,"input_manifest_hash":mh,"provider":provider,"model":model,"request_or_run_id":a.run_id+"/aggregate/"+a.critic,"independent_runtime":True,"aggregation":"minimum score across four independently executed slices; union defects; no averaging","slices":sorted(rows,key=lambda x:x["slice"]),"scores":scores,"defects":defects,"coverage_complete":coverage,"confidence":confidence}
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True);rawp=out/"raw-output.json";rawp.write_text(json.dumps(raw,indent=2)+"\n")
 rec={"task_id":"T10","critic_id":a.critic,"provider":provider,"model":model,"request_or_run_id":raw["request_or_run_id"],"candidate_hash":a.candidate,"input_manifest_hash":mh,"raw_output_path":str(rawp.resolve()),"raw_output_hash":sha(rawp),"scores":scores,"defects":defects,"coverage_complete":coverage,"confidence":confidence,"independent_runtime":True,"passed":passed}
 (out/"critic-record.json").write_text(json.dumps(rec,indent=2)+"\n");print(json.dumps(rec,indent=2));raise SystemExit(0 if passed else 1)
if __name__=="__main__":main()
