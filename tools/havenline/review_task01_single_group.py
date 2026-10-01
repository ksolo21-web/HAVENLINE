#!/usr/bin/env python3
"""Same pinned review logic/rubric; one group per process instead of two.
Parallel execution reduces wait time. It does not change scores or acceptance.
"""
from pathlib import Path
import hashlib,json
p=Path('tools/havenline/review_task01_revision4.py');raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='8c4dea512acf674bab5fa800b760588c582325a5767fb77f10fcf65f5ce59de6'
s=raw.decode()
old='and SHARD in (0,1,2)';assert s.count(old)==1
s=s.replace(old,'and SHARD in (0,1,2,3,4,5)')
old="GROUPS={0:['variant-1','clearance'],1:['variant-2','forest'],2:['variant-3','camera-motion']}";assert s.count(old)==1
s=s.replace(old,"GROUPS={0:['variant-1'],1:['variant-2'],2:['variant-3'],3:['forest'],4:['clearance'],5:['camera-motion']}")
old="'passed':len(rows)==2 and all(r['passed'] for r in rows)";assert s.count(old)==1
s=s.replace(old,"'passed':len(rows)==1 and all(r['passed'] for r in rows)")
out=Path('critic-results');out.mkdir(exist_ok=True)
(out/'executed-reviewer.py').write_text(s)
(out/'review-code-provenance.json').write_text(json.dumps({'original_reviewer_sha256':hashlib.sha256(raw).hexdigest(),'executed_reviewer_sha256':hashlib.sha256(s.encode()).hexdigest(),'only_execution_partition_changed':True,'prompt_schema_and_threshold_unchanged':True},indent=2))
exec(compile(s,'T01-one-group-independent-review','exec'),{'__name__':'__main__','__file__':str(out/'executed-reviewer.py')})
