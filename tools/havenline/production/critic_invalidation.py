#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
SHA40=re.compile(r'^[0-9a-f]{40}$');SHA64=re.compile(r'^[0-9a-f]{64}$')
def load(p): return json.loads(Path(p).read_text())
def validate_state(row):
    errors=[]
    if not str(row.get('task_id','')).startswith('T'): errors.append('task_id required')
    if not SHA40.fullmatch(str(row.get('candidate_sha',''))): errors.append('candidate_sha must be exact SHA')
    critics=row.get('critics')
    if not isinstance(critics,dict) or not critics: errors.append('critics must be nonempty object');critics={}
    for cid,data in critics.items():
        if not re.fullmatch(r'C(?:[1-9]|10|11)',cid): errors.append('invalid critic id '+str(cid))
        if not isinstance(data,dict): errors.append(cid+' record must be object');continue
        if not SHA64.fullmatch(str(data.get('input_fingerprint',''))): errors.append(cid+' input_fingerprint must be SHA-256')
        if data.get('disposition') not in ('PASS','FAIL','BLOCKED','RETRY_REQUIRED','INCOMPLETE'): errors.append(cid+' invalid disposition')
    return errors
def evaluate(before,after):
    b=load(before);a=load(after);errors=validate_state(b)+validate_state(a)
    if b.get('task_id')!=a.get('task_id'): errors.append('task_id mismatch')
    bc=b.get('candidate_sha');ac=a.get('candidate_sha');bcrit=b.get('critics',{});acrit=a.get('critics',{});allc=sorted(set(bcrit)|set(acrit))
    if bc!=ac:
        rerun=allc;preserve=[];reason='candidate_source_changed_exact_source_reviews_fresh'
    else:
        rerun=[];preserve=[]
        for cid in allc:
            old=bcrit.get(cid);new=acrit.get(cid)
            if not old or not new:
                rerun.append(cid);continue
            same=old.get('input_fingerprint')==new.get('input_fingerprint')
            if same and old.get('disposition')=='PASS': preserve.append(cid)
            else: rerun.append(cid)
        reason='same_source_exact_critic_input_fingerprints'
    return {'passed':not errors,'task_id':a.get('task_id'),'candidate_sha':ac,'rerun_critics':rerun,'preserve_critics':preserve,'reason':reason,'errors':errors}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('before');ap.add_argument('after');a=ap.parse_args();out=evaluate(a.before,a.after);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
