#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def load(p): return json.loads(Path(p).read_text())
def evaluate(before,after):
    b=load(before);a=load(after);errors=[]
    if b.get('task_id')!=a.get('task_id'): errors.append('task_id mismatch')
    bc=b.get('candidate_sha');ac=a.get('candidate_sha');bcrit=b.get('critics',{});acrit=a.get('critics',{});allc=sorted(set(bcrit)|set(acrit))
    if bc!=ac: rerun=allc;preserve=[];reason='candidate_source_changed_exact_source_reviews_fresh'
    else: rerun=[c for c in allc if bcrit.get(c)!=acrit.get(c)];preserve=[c for c in allc if bcrit.get(c)==acrit.get(c) and c in bcrit and c in acrit];reason='same_source_critic_specific_inputs'
    return {'passed':not errors,'task_id':a.get('task_id'),'candidate_sha':ac,'rerun_critics':rerun,'preserve_critics':preserve,'reason':reason,'errors':errors}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('before');ap.add_argument('after');a=ap.parse_args();out=evaluate(a.before,a.after);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
