#!/usr/bin/env python3
"""Execute the established independent T03 visual reviewer under V2 strict >9 governance.
Only provenance-label and acceptance-language/threshold are changed; model,
evidence groups, seeds and scoring dimensions remain the established reviewer.
"""
from pathlib import Path
import hashlib
base=Path('tools/havenline/review_task03_local_reference.py');data=base.read_bytes();source=data.decode()
changes=[
 ("prov['task']=='T03-boundary-v1'","prov['task']=='T03-boundary-v2'"),
 ("Every score below 9 MUST cite an actionable defect actually visible in the supplied pixels.","Every score at or below 9.0 MUST cite an actionable defect actually visible in the supplied pixels. Forward approval requires every mandatory score strictly greater than 9.0 unrounded."),
 ("row['passed']=row['lowest_score']>=9 and review['defects']==[]","row['passed']=row['lowest_score']>9.0 and review['defects']==[]")
]
for old,new in changes:
 assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new,1)
out=Path('task03-local-review');out.mkdir(exist_ok=True);executed=out/'executed-reviewer.py';executed.write_text(source)
(out/'strict-wrapper-provenance.txt').write_text(
 'base_sha256='+hashlib.sha256(data).hexdigest()+'\n'
 'changes=provenance_v2;score_rule_strict_gt_9;prompt_matches_strict_rule\n'
 'threshold=>9.0_unrounded\nmodel_groups_seeds_unchanged=true\n'
)
exec(compile(source,str(executed),'exec'),{'__name__':'__main__','__file__':str(executed.resolve())})
