#!/usr/bin/env python3
"""Produce portable native receipts without emitting the disposable paths."""
import hashlib, json, re, sys
from pathlib import Path
runtime=Path(sys.argv[1])
out=Path(sys.argv[2])
out.mkdir(exist_ok=True)
records={}
for name in ('import','nostalgic','late_payment','restored_route_first','restored_cold'):
    text=(runtime/(name+'.log')).read_text()
    status=int((runtime/(name+'.exit')).read_text())
    keep=[x for x in text.splitlines() if x.startswith(('PASS ','FAIL ','Godot Engine','paid pine test checks=','integrated tree-regrowth checks='))]
    ticks=[int(t) for t in re.findall(r'tick=(\d+)',text)]
    diagnostic=bool(re.search(r'(SCRIPT ERROR|^ERROR:|Parse Error)',text,re.M))
    output='\n'.join(keep)+'\n'
    (out/(name+'.txt')).write_text(output)
    records[name]={'status_code':status,
                   'author_checks_pass':sum(x.startswith('PASS ') for x in keep),
                   'author_checks_fail':sum(x.startswith('FAIL ') for x in keep),
                   'max_tick':max(ticks) if ticks else None,
                   'engine_errors':diagnostic,
                   'sanitized_log_sha256':hashlib.sha256(output.encode()).hexdigest()}
print(json.dumps({'exact_baseline_commit':'11c14a1c41971067c7dc97db69375f720a408f68',
 'patch_sha256':hashlib.sha256(Path('renewal.patch').read_bytes()).hexdigest(),
 'evidence_scope':'Headless ordinary scene input and disposable-process recovery only; no device or render, applied only to exact detached archive.',
 'records':records},indent=2,sort_keys=True))
