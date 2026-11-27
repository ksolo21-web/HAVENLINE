#!/usr/bin/env python3
"""Prepare exact reviewed blobs for expected-SHA GitHub publication; no remote writes."""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT=pathlib.Path(__file__).resolve().parents[4]
PKG='Docs/Production/Completeness/2026-11-27/'
BASE='fd2e12c8734f49cda7eb3bbf97887406bd03a704'
OUT=ROOT.parent/'completeness-publication'
RECEIPTS={PKG+x for x in ('CHECKPOINT.json','VALIDATION.json','SCOPE_VALIDATION.json',
                         'CANDIDATE_FREEZE.json','FINAL_REVIEW.json','FINAL_REVIEW.md','PUBLICATION.json')}

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def changed():
    return sorted(set(git('diff','--name-only',BASE).decode().splitlines()) |
                  set(git('ls-files','--others','--exclude-standard').decode().splitlines()))

def receipt(path):return path in RECEIPTS or path.startswith(PKG+'Review/Final/')

def record(path):
    p=ROOT/path
    if not p.is_file() or p.is_symlink() or p.suffix=='.pyc' or '__pycache__' in p.parts:
        raise SystemExit('Invalid publication path: '+path)
    content=p.read_bytes();content.decode('utf-8')
    return {'path':path,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),
            'mode':'100755' if p.stat().st_mode & 0o111 else '100644'}

def freeze():
    files=[record(p) for p in changed() if not receipt(p)]
    manifest={'schema_version':1,'base_commit':BASE,'scope':'Exact planning/tooling candidate, not game approval',
              'runtime_approval_allowed':False,'game_score':None,'receipt_files_excluded':sorted(RECEIPTS),
              'independent_final_review_prefix_excluded':PKG+'Review/Final/','files':files}
    target=ROOT/PKG/'CANDIDATE_FREEZE.json';target.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'frozen_files':len(files),'freeze_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))

def prepare(parent=BASE):
    frozen=json.loads((ROOT/PKG/'CANDIDATE_FREEZE.json').read_text())
    for row in frozen['files']:
        if record(row['path'])!=row:raise SystemExit('Reviewed file changed: '+row['path'])
    paths=changed();allowed={x['path'] for x in frozen['files']}
    unexpected=[p for p in paths if p not in allowed and not receipt(p)]
    if unexpected:raise SystemExit('Unreviewed publication files: '+repr(unexpected))
    for path in paths:record(path)
    # Root entrypoints are intentionally materialized outside this worktree's
    # sparse directories. --sparse stages only these explicitly reviewed paths.
    subprocess.check_call(['git','add','--sparse','--',*paths],cwd=ROOT)
    modes={}
    for row in git('ls-files','--stage','-z').decode().split('\0'):
        if row:
            meta,path=row.split('\t',1);modes[path]=meta.split()[0]
    entries=[{'path':path,'mode':modes[path],'type':'blob','content':(ROOT/path).read_text()} for path in paths]
    for entry in entries:
        if entry['mode']!=record(entry['path'])['mode']:raise SystemExit('Index/worktree mode mismatch: '+entry['path'])
    OUT.mkdir(exist_ok=True)
    payload=json.dumps(entries,ensure_ascii=False,separators=(',',':'))
    (OUT/'tree-elements.json').write_text(payload)
    metadata={'base_commit':BASE,'parent_commit':parent,'base_tree':git('rev-parse',BASE+'^{tree}').decode().strip(),
       'expected_tree':git('write-tree').decode().strip(),'files':len(paths),'payload_bytes':len(payload.encode()),
       'payload_sha256':hashlib.sha256(payload.encode()).hexdigest(),'file_records':[record(p) for p in paths]}
    (OUT/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({k:v for k,v in metadata.items() if k!='file_records'}))

if __name__=='__main__':
    if len(sys.argv)<2:raise SystemExit('freeze | prepare [parent]')
    if sys.argv[1]=='freeze':freeze()
    elif sys.argv[1]=='prepare':prepare(sys.argv[2] if len(sys.argv)>2 else BASE)
    else:raise SystemExit('freeze | prepare [parent]')
