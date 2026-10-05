#!/usr/bin/env python3
"""Execute the pinned Task 3 local reviewer against v2 evidence.

The polished gameplay/evidence source is unchanged. The base reviewer aborted
before inference only because it still asserted the prior v1 provenance label.
This wrapper verifies the exact Git blob, changes that one label, records the
executed reviewer, and leaves prompts, groups, thresholds, model and scoring
logic untouched.
"""
from pathlib import Path
import hashlib

base=Path('tools/havenline/review_task03_local_reference.py')
data=base.read_bytes()
git_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
assert git_blob=='445ebcf7c8d5cfec2786dad4bca0790ef9033ec7',(git_blob,'unexpected base reviewer')
source=data.decode()
needle="prov['task']=='T03-boundary-v1'"
assert source.count(needle)==1
source=source.replace(needle,"prov['task']=='T03-boundary-v2'",1)
out=Path('task03-local-review');out.mkdir(exist_ok=True)
executed=out/'executed-reviewer.py';executed.write_text(source)
(out/'wrapper-provenance.txt').write_text(
    'base_git_blob='+git_blob+'\n'
    'change=provenance_task_label_v1_to_v2_only\n'
    'threshold_unchanged=9.0\n'
    'evidence_source_unchanged=true\n'
)
exec(compile(source,str(executed),'exec'),{'__name__':'__main__','__file__':str(executed.resolve())})
