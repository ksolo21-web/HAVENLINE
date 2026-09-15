#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib
from lib import ROOT, DOCS, load_json

ALLOWED_KINDS={"image","motion_frame","json","text"}

def sha256(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def parse_item(spec:str)->dict:
    # group|category|kind|path|description ; description may contain spaces, not '|'.
    parts=spec.split('|',4)
    if len(parts)!=5:raise SystemExit("--item format: group|category|kind|path|description")
    group,category,kind,rel,description=parts
    if kind not in ALLOWED_KINDS:raise SystemExit("invalid kind "+kind)
    path=(ROOT/rel).resolve()
    if ROOT.resolve() not in path.parents and path!=ROOT.resolve():raise SystemExit("item outside repo: "+rel)
    if not path.is_file():raise SystemExit("missing evidence item: "+rel)
    return {"group":group,"category":category,"kind":kind,"path":str(path.relative_to(ROOT)),"description":description,"sha256":sha256(path)}

def validate(manifest:dict)->list[str]:
    cfg=load_json(DOCS/"CRITIC_EXECUTION.json");errors=[]
    cid=manifest.get('critic_id');candidate=manifest.get('candidate_commit')
    if cid not in cfg['critics']:errors.append('unknown critic')
    if not isinstance(candidate,str) or len(candidate)!=40:errors.append('invalid candidate commit')
    groups=manifest.get('groups')
    if not isinstance(groups,list) or not groups:errors.append('groups missing')
    categories=set()
    for g in groups or []:
        if not g.get('id') or not isinstance(g.get('items'),list) or not g['items']:errors.append('invalid group')
        for item in g.get('items',[]):
            if item.get('kind') not in ALLOWED_KINDS:errors.append('bad item kind')
            categories.add(item.get('category'))
            p=ROOT/item.get('path','')
            if not p.is_file():errors.append('missing item '+item.get('path',''))
            elif sha256(p)!=item.get('sha256'):errors.append('hash mismatch '+item.get('path',''))
    if cid in cfg['critics']:
        missing=set(cfg['critics'][cid].get('required_categories',[]))-categories
        if missing:errors.append('missing required categories: '+','.join(sorted(missing)))
    return errors

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    b=sub.add_parser('build');b.add_argument('--task',required=True);b.add_argument('--critic',required=True);b.add_argument('--candidate',required=True);b.add_argument('--out',required=True);b.add_argument('--item',action='append',default=[])
    v=sub.add_parser('validate');v.add_argument('manifest')
    a=ap.parse_args()
    if a.cmd=='build':
        rows=[parse_item(x) for x in a.item];by={}
        for r in rows:by.setdefault(r.pop('group'),[]).append(r)
        manifest={"schema_version":1,"task_id":a.task.upper(),"critic_id":a.critic.upper(),"candidate_commit":a.candidate,"groups":[{"id":k,"items":v} for k,v in by.items()]}
        errors=validate(manifest)
        if errors:raise SystemExit('\n'.join(errors))
        out=(ROOT/a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(manifest,indent=2)+'\n')
        print(out.relative_to(ROOT))
    else:
        p=ROOT/a.manifest;manifest=json.loads(p.read_text());errors=validate(manifest);print(json.dumps({"passed":not errors,"errors":errors},indent=2));raise SystemExit(0 if not errors else 1)
if __name__=='__main__':main()
