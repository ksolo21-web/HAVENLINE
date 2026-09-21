#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production';HEX64=re.compile(r'^[0-9a-f]{64}$');HEX40=re.compile(r'^[0-9a-f]{40}$')
def load(p): return json.loads(Path(p).read_text())
def validate_manifest(path,candidate=None,critic=None):
    p=Path(path);policy=load(DOCS/'CRITIC_PACKAGE_PREFLIGHT_POLICY.json');lim=policy['limits'];errors=[];raw=p.read_bytes()
    if len(raw)>lim['manifest_bytes_max']: errors.append('manifest too large')
    try:m=json.loads(raw)
    except Exception as e:return {'passed':False,'errors':['invalid json: '+str(e)]}
    for k in policy['required']:
        if k not in m: errors.append('missing '+k)
    if candidate and m.get('candidate_commit')!=candidate: errors.append('candidate mismatch')
    if critic and m.get('critic_id')!=critic: errors.append('critic mismatch')
    if m.get('candidate_commit') and not HEX40.fullmatch(str(m['candidate_commit'])): errors.append('candidate_commit must be exact SHA')
    groups=m.get('groups',[])
    if not isinstance(groups,list) or not groups: errors.append('groups must be nonempty list');groups=[]
    if len(groups)>lim['groups_max']: errors.append('too many groups')
    gids=set()
    for g in groups:
        gid=g.get('id')
        if not gid or gid in gids: errors.append('duplicate/missing group id: '+str(gid))
        gids.add(gid);items=g.get('items',[])
        if not items: errors.append('empty group '+str(gid))
        if len(items)>lim['items_per_group_max']: errors.append('too many items in '+str(gid))
        seen=set()
        for item in items:
            rel=item.get('path')
            if not rel or rel in seen: errors.append('duplicate/missing item path in '+str(gid)+': '+str(rel))
            seen.add(rel);h=item.get('sha256')
            if h is not None and not HEX64.fullmatch(str(h)): errors.append('bad sha256 '+str(rel))
            if rel:
                fp=p.parent/rel
                if fp.exists() and fp.is_file():
                    data=fp.read_bytes()
                    if item.get('kind')=='text' and len(data)>lim['text_item_bytes_max']: errors.append('text item too large '+rel)
                    if h and hashlib.sha256(data).hexdigest()!=h: errors.append('hash mismatch '+rel)
                elif item.get('external_uri'):
                    if not h: errors.append('external evidence must be SHA-256 bound '+rel)
                else:
                    errors.append('evidence file missing '+rel)
    rc=m.get('response_contract')
    if rc:
        for field,cap in [('observations_max','response_observations_max'),('observation_chars_max','response_observation_chars_max'),('defects_max','response_defects_max'),('defect_chars_max','response_defect_chars_max'),('completion_tokens_max','response_completion_tokens_max')]:
            if int(rc.get(field,0))<=0 or int(rc[field])>lim[cap]: errors.append('response contract '+field+' outside policy')
    return {'passed':not errors,'task_id':m.get('task_id'),'critic_id':m.get('critic_id'),'candidate_commit':m.get('candidate_commit'),'group_count':len(groups),'errors':errors}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('manifest');ap.add_argument('--candidate');ap.add_argument('--critic');a=ap.parse_args();out=validate_manifest(a.manifest,a.candidate,a.critic);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 2)
if __name__=='__main__':main()
