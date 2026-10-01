#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, subprocess, zipfile
from lib import ROOT, sha256_file, git

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--task",required=True);ap.add_argument("--candidate",required=True)
    ap.add_argument("--base",required=True);ap.add_argument("--evidence-dir",required=True)
    ap.add_argument("--out")
    a=ap.parse_args()
    ev=(ROOT/a.evidence_dir).resolve();assert ev.exists() and ev.is_dir()
    out=pathlib.Path(a.out) if a.out else ROOT/"Docs/Production/Evidence"/a.task/f"{a.task}-{a.candidate[:12]}.zip"
    if not out.is_absolute(): out=ROOT/out
    out.parent.mkdir(parents=True,exist_ok=True)
    changed=git("diff","--name-only",f"{a.base}..{a.candidate}").splitlines()
    files=sorted([p for p in ev.rglob("*") if p.is_file()])
    manifest={
      "task_id":a.task,"candidate_commit":a.candidate,"base_commit":a.base,
      "changed_files":[x for x in changed if x.strip()],
      "evidence_root":str(ev.relative_to(ROOT)),
      "files":{str(p.relative_to(ev)):sha256_file(p) for p in files},
      "known_failures_path":"known-failures.json" if (ev/"known-failures.json").exists() else None,
      "raw_critic_inputs_present":any("critic" in p.parts and "input" in p.name for p in files),
      "raw_critic_outputs_present":any("critic" in p.parts and ("raw" in p.name or "output" in p.name) for p in files)
    }
    tmp=ev/"PACKAGE_MANIFEST.json";tmp.write_text(json.dumps(manifest,indent=2)+"\n")
    try:
      with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted([p for p in ev.rglob("*") if p.is_file()]):
          z.write(p,p.relative_to(ev))
    finally:
      tmp.unlink(missing_ok=True)
    result={"package":str(out.relative_to(ROOT)),"sha256":sha256_file(out),"manifest":manifest}
    sidecar=out.with_suffix(out.suffix+".sha256.json");sidecar.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
