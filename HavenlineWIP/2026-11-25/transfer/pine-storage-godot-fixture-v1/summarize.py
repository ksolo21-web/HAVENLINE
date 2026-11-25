#!/usr/bin/env python3
import hashlib,json,re,sys
from pathlib import Path
runtime=Path(sys.argv[1])
out=Path(sys.argv[2]);out.mkdir(exist_ok=True)
records={}
for name in ('import','invalid_owner','native_v1','native_v2','ordinary_deposit','fresh_process_next','failed_stage','restart_aborted'):
    text=(runtime/(name+'.log')).read_text()
    status=int((runtime/(name+'.exit')).read_text())
    lines=[x for x in text.splitlines() if x.startswith(('PASS ','FAIL ','Godot Engine','pine-store native fixture checks='))]
    diag=bool(re.search(r'(SCRIPT ERROR|^ERROR:|Parse Error)',text,re.M|re.I))
    output='\n'.join(lines)+'\n'
    (out/(name+'.txt')).write_text(output)
    records[name]={'exit':status,'checks_pass':sum(l.startswith('PASS ') for l in lines),
                   'checks_fail':sum(l.startswith('FAIL ') for l in lines),'engine_diagnostics':diag,
                   'sanitized_sha256':hashlib.sha256(output.encode()).hexdigest()}
print(json.dumps({'run_results':records,'exact_source_commit':'11c14a1c41971067c7dc97db69375f720a408f68',
 'deposits_in_native_fixture':1,'counts_gold_occ_harvest_carried_stored':[[2,2,0],[2,1,1],[2,1,1],[3,2,1]],
 'separate_POSIX_proof_not_in_Godot':True,'scope':'Fixture only if all expected native checks pass; no OS flush durability/game receiver/site.'},indent=2,sort_keys=True))
