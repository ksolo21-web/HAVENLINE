#!/usr/bin/env python3
"""Bind the exact policy/code/test/documentation content reviewed in this change."""
from __future__ import annotations
import argparse,hashlib,json,pathlib,subprocess

ROOT=pathlib.Path(__file__).resolve().parents[4]
PACKAGE=pathlib.Path(__file__).resolve().parent
BASE='7180d1315af56228e7629735c2bd50bda3c43596'
RECEIPTS={'FREEZE.json','CHECKPOINT.json','PUBLICATION.json','SCOPE_VALIDATION.json','TEST_RESULTS.json','TEST_OUTPUT.txt','INDEPENDENT_REVIEW.md','INDEPENDENT_CHECKS.json'}

def snapshot():
    def paths(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).splitlines()
    changed=set(paths('diff','--name-only','--no-renames',BASE))|set(paths('ls-files','--others','--exclude-standard'))
    rows=[]
    for rel in sorted(changed):
        path=ROOT/rel
        if '__pycache__' in path.parts or path.suffix=='.pyc':raise ValueError('generated Python caches cannot enter the reviewed package: '+rel)
        if path.parent==PACKAGE and path.name in RECEIPTS:continue
        if not path.is_file() or path.is_symlink():raise ValueError('freeze requires ordinary file bytes: '+rel)
        body=path.read_bytes();rows.append({'path':rel,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
    encoded=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
    return {'schema_version':1,'base_commit':BASE,'scope':'Havenline reference-acceptance policy and tooling only','content_sha256':hashlib.sha256(encoded).hexdigest(),'files':rows,'file_count':len(rows),'excluded_receipt_names':sorted(RECEIPTS)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    current=snapshot();path=PACKAGE/'FREEZE.json'
    if args.check:
        expected=json.loads(path.read_text());passed=current==expected
        print(json.dumps({'passed':passed,'file_count':current['file_count'],'content_sha256':current['content_sha256']}))
        return 0 if passed else 2
    path.write_text(json.dumps(current,indent=2)+'\n')
    print(json.dumps({'file_count':current['file_count'],'content_sha256':current['content_sha256']}))
    return 0

if __name__=='__main__':raise SystemExit(main())
