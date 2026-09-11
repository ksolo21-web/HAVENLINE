#!/usr/bin/env python3
"""Run only Task 3 review groups that previously returned no verdict.

This wrapper is intentionally transport-recovery only. It preserves completed
scored judgments rather than rerunning them. The base reviewer, rubric, provider,
evidence hashes and >=9 threshold remain unchanged.
"""
from pathlib import Path
import hashlib, os
base=Path('tools/havenline/review_task03_boundary.py')
source=base.read_text()
expected='ca6fc04ed17501667fc4acaac5ab91d75dd238c4'
actual=hashlib.sha256(base.read_bytes()).hexdigest()
assert actual==expected,(actual,expected)
groups=[x.strip() for x in os.environ['RETRY_GROUPS'].split(',') if x.strip()]
assert groups and len(groups)==len(set(groups))
allowed={'perimeter','north-gate','side-gates','river-gates','south-fence','central-lane','cross-shelter-lanes','bank-lane','detail-contact','gameplay','conditions'}
assert set(groups)<=allowed
needle="def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()"
assert source.count(needle)==1
filter_code="""retry_groups={x.strip() for x in os.environ['RETRY_GROUPS'].split(',') if x.strip()}\nGROUPS={k:v for k,v in GROUPS.items() if k in retry_groups}\nassert set(GROUPS)==retry_groups\n"""
source=source.replace(needle,filter_code+needle,1)
old="ROOT=Path('task03-evidence');OUT=Path('task03-review');OUT.mkdir(exist_ok=True)"
new="ROOT=Path('task03-evidence');OUT=Path('task03-review-retry');OUT.mkdir(exist_ok=True)"
assert source.count(old)==1
source=source.replace(old,new,1)
# Preserve provenance that this is a subset transport retry, not a new art pass.
marker="provider={'task':'T03-boundary-v1'"
assert source.count(marker)==1
source=source.replace(marker,"provider={'transport_retry_groups':sorted(retry_groups),'completed_scores_not_retried':True,"+marker.split("provider={",1)[1],1)
Path('task03-review-retry').mkdir(exist_ok=True)
executed=Path('task03-review-retry/executed-reviewer.py')
executed.write_text(source)
Path('task03-review-retry/wrapper-provenance.txt').write_text('base_sha256='+actual+'\nwrapper_sha256='+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()+'\nretry_groups='+','.join(groups)+'\n')
exec(compile(source,str(executed),'exec'),{'__name__':'__main__','__file__':str(executed.resolve())})
