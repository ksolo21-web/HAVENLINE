#!/usr/bin/env python3
"""Execute the established independent T03 visual reviewer under strict >9 governance.

The base reviewer remains the independent model/seed implementation. This T03
adapter binds it to the formal river-gate preflight, expands the river-gate
pixel set to all four required views per gate, and enforces strict >9.0.
"""
from pathlib import Path
import hashlib,json,os

root=Path('task03-evidence')
preflight=json.loads((root/'gate-preflight.json').read_text())
expected=os.environ['EXPECTED_SOURCE']
assert preflight.get('source')==expected,('preflight/source',preflight.get('source'),expected)
assert preflight.get('passed') is True,preflight
assert preflight.get('required_evidence_count')==12,preflight
assert preflight.get('visual_clearance_pass') is True,preflight
assert preflight.get('authority_id')=='T03-gate-geometry-v3',preflight

base=Path('tools/havenline/review_task03_local_reference.py')
data=base.read_bytes()
source=data.decode()

# Provenance must already be V2. Never silently rewrite an unknown reviewer.
assert source.count("prov['task']=='T03-boundary-v2'")==1, (
    'expected exactly one V2 provenance assertion',
    source.count("prov['task']=='T03-boundary-v2'")
)
assert "prov['task']=='T03-boundary-v1'" not in source, 'stale V1 provenance remains'

legacy_prov="prov['all61_images_verified'] is True"
strict_prov="prov['all_required_images_verified'] is True"
if strict_prov not in source:
    assert source.count(legacy_prov)==1,(legacy_prov,source.count(legacy_prov))
    source=source.replace(legacy_prov,strict_prov,1)
else:
    assert source.count(strict_prov)==1,(strict_prov,source.count(strict_prov))

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

river_old="'river-gates':['gallery/river-gate-west.png','gallery/river-gate-centre.png','gallery/river-gate-east.png','native4k/native-river-gate-west.png','native4k/native-river-gate-centre.png','native4k/native-river-gate-east.png'],"
river_new="'river-gates':['gallery/river-gate-west-approach.png','gallery/river-gate-west.png','gallery/river-gate-west-camp-side.png','gallery/river-gate-centre-approach.png','gallery/river-gate-centre.png','gallery/river-gate-centre-camp-side.png','gallery/river-gate-east-approach.png','gallery/river-gate-east.png','gallery/river-gate-east-camp-side.png','gallery/gameplay-river-gate-west.png','gallery/gameplay-river-gate-centre.png','gallery/gameplay-river-gate-east.png','native4k/native-river-gate-west.png','native4k/native-river-gate-centre.png','native4k/native-river-gate-east.png'],"
assert source.count(river_old)==1,(river_old,source.count(river_old))
source=source.replace(river_old,river_new,1)

gameplay_old="'gameplay':['gallery/gameplay-north-gate.png','gallery/gameplay-west-gate.png','gallery/gameplay-east-gate.png','gallery/gameplay-river-gate-centre.png'],"
gameplay_new="'gameplay':['gallery/gameplay-north-gate.png','gallery/gameplay-west-gate.png','gallery/gameplay-east-gate.png','gallery/gameplay-river-gate-west.png','gallery/gameplay-river-gate-centre.png','gallery/gameplay-river-gate-east.png'],"
assert source.count(gameplay_old)==1,(gameplay_old,source.count(gameplay_old))
source=source.replace(gameplay_old,gameplay_new,1)

river_note_old="'river-gates':'Judge the three river-facing gate corridors specifically. They intentionally have NO bridges yet. Require readable opened leaves/posts, dry approach, preserved bank, and clear future crossing space.',"
river_note_new="'river-gates':'Judge the three river-facing gate corridors specifically across river-side approach, threshold/three-quarter, camp-side outward and gameplay-scale evidence. They intentionally have NO bridges yet. With no caption needed, each must read protected camp -> authored gate structure -> clear threshold -> worn path through it -> continuation toward the river lane. Require readable opened leaves/posts, comfortable visual clearance, dry approach, preserved bank, and clear future crossing space.',"
assert source.count(river_note_old)==1,(river_note_old,source.count(river_note_old))
source=source.replace(river_note_old,river_note_new,1)

out=Path('task03-local-review')
out.mkdir(exist_ok=True)
executed=out/'executed-reviewer.py'
executed.write_text(source)
(out/'strict-wrapper-provenance.txt').write_text(
    'base_sha256='+hashlib.sha256(data).hexdigest()+'\n'
    'base_provenance=T03-boundary-v2_verified\n'
    'preflight_source='+expected+'\n'
    'changes=score_rule_strict_gt_9;prompt_matches_strict_rule;river_gate_four_view_contract\n'
    'threshold=>9.0_unrounded\n'
    'required_river_gate_evidence=12\n'
    'diagnostic_confidence=low_medium_high_only\n'
    'model_groups_seeds_unchanged=true\n'
)
exec(compile(source,str(executed),'exec'),{'__name__':'__main__','__file__':str(executed.resolve())})
