#!/usr/bin/env python3
"""Reference-fidelity retry after an execution that returned zero verdicts.
The original reference role produced no scored groups, so rerunning all required
reference groups is transport recovery rather than score replacement.
"""
from pathlib import Path
import hashlib
base=Path('tools/havenline/review_task03_boundary.py')
source=base.read_text()
expected='2bc99cb544473513a2e139461239cac25c0c40e79022c83881c817291b093b90'
actual=hashlib.sha256(base.read_bytes()).hexdigest();assert actual==expected,(actual,expected)
old="ROOT=Path('task03-evidence');OUT=Path('task03-review');OUT.mkdir(exist_ok=True)"
new="ROOT=Path('task03-evidence');OUT=Path('task03-reference-retry');OUT.mkdir(exist_ok=True)"
assert source.count(old)==1;source=source.replace(old,new,1)
marker="provider={'task':'T03-boundary-v1'"
assert source.count(marker)==1
source=source.replace(marker,"provider={'transport_retry_after_zero_verdicts':True,"+marker.split("provider={",1)[1],1)
Path('task03-reference-retry').mkdir(exist_ok=True)
executed=Path('task03-reference-retry/executed-reviewer.py');executed.write_text(source)
Path('task03-reference-retry/wrapper-provenance.txt').write_text('base_sha256='+actual+'\nwrapper_sha256='+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()+'\nfirst_reference_scored_groups=0\n')
exec(compile(source,str(executed),'exec'),{'__name__':'__main__','__file__':str(executed.resolve())})
