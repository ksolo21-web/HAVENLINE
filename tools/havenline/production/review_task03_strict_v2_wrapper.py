#!/usr/bin/env python3
"""Execute the established independent T03 visual reviewer under V2 strict >9 governance.

The base reviewer is already V2-provenance aware. This adapter changes only
acceptance language/threshold when still needed; model, evidence groups, seeds,
scoring dimensions, competency probe, and source-bound evidence remain unchanged.
"""
from pathlib import Path
import hashlib

base=Path('tools/havenline/review_task03_local_reference.py')
data=base.read_bytes()
source=data.decode()

# Provenance must already be V2. Never silently rewrite an unknown reviewer.
assert source.count("prov['task']=='T03-boundary-v2'")==1, (
    'expected exactly one V2 provenance assertion',
    source.count("prov['task']=='T03-boundary-v2'")
)
assert "prov['task']=='T03-boundary-v1'" not in source, 'stale V1 provenance remains'

prompt_old="Every score below 9 MUST cite an actionable defect actually visible in the supplied pixels."
prompt_new="Every score at or below 9.0 MUST cite an actionable defect actually visible in the supplied pixels. Forward approval requires every mandatory score strictly greater than 9.0 unrounded."
if prompt_new not in source:
    assert source.count(prompt_old)==1,(prompt_old,source.count(prompt_old))
    source=source.replace(prompt_old,prompt_new,1)
else:
    assert source.count(prompt_new)==1,(prompt_new,source.count(prompt_new))

pass_old="row['passed']=row['lowest_score']>=9 and review['defects']==[] and review['coverage_complete'] is True and review['confidence']!='low'"
pass_new="row['passed']=row['lowest_score']>9.0 and review['defects']==[] and review['coverage_complete'] is True and review['confidence']!='low'"
if pass_new not in source:
    assert source.count(pass_old)==1,(pass_old,source.count(pass_old))
    source=source.replace(pass_old,pass_new,1)
else:
    assert source.count(pass_new)==1,(pass_new,source.count(pass_new))

out=Path('task03-local-review')
out.mkdir(exist_ok=True)
executed=out/'executed-reviewer.py'
executed.write_text(source)
(out/'strict-wrapper-provenance.txt').write_text(
    'base_sha256='+hashlib.sha256(data).hexdigest()+'\n'
    'base_provenance=T03-boundary-v2_verified\n'
    'changes=score_rule_strict_gt_9;prompt_matches_strict_rule\n'
    'threshold=>9.0_unrounded\n'
    'model_groups_seeds_unchanged=true\n'
)
exec(compile(source,str(executed),'exec'),{'__name__':'__main__','__file__':str(executed.resolve())})
