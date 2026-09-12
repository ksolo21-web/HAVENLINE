#!/usr/bin/env python3
"""Execute the established independent T03 visual reviewer under strict >9 governance.

The base reviewer remains the independent model/seed implementation. This T03
adapter binds it to the formal river-gate preflight, expands the river-gate
pixel set to all four required views per gate, enforces strict >9.0, and
materializes/verifies the exact LFS-backed reference before any critic starts.
"""
from pathlib import Path
import hashlib,io,json,os,subprocess
from PIL import Image

root=Path('task03-evidence')
preflight=json.loads((root/'gate-preflight.json').read_text())
expected=os.environ['EXPECTED_SOURCE']
assert preflight.get('source')==expected,('preflight/source',preflight.get('source'),expected)
assert preflight.get('passed') is True,preflight
assert preflight.get('required_evidence_count')==12,preflight
assert preflight.get('visual_clearance_pass') is True,preflight
assert preflight.get('authority_id')=='T03-gate-geometry-v3',preflight

# The T02 reference is intentionally stored in Git LFS. A normal checkout with
# lfs:false leaves only the text pointer. Previous C1 jobs therefore launched
# but returned image-decode errors instead of real visual judgments. Make the
# exact LFS object an explicit pre-critic dependency and verify its content hash
# and decodability before the independent reviewer is allowed to execute.
reference_source=Path('Docs/Production/T02/reference-ground.webp')
reference_target=root/'reference-ground.webp'
reference_sha='3c424b0df53c1c6de49018278779a4ef1ced58562e5b9dbb54fe276d13aa2ddb'
reference_size=10784
pointer=reference_source.read_bytes()
assert b'version https://git-lfs.github.com/spec/v1' in pointer,'T02 reference is not the expected LFS pointer'
assert ('oid sha256:'+reference_sha).encode() in pointer,'T02 reference LFS oid changed'
assert ('size '+str(reference_size)).encode() in pointer,'T02 reference LFS size changed'

def verified_reference(data:bytes)->dict:
    digest=hashlib.sha256(data).hexdigest()
    assert digest==reference_sha,('reference sha256',digest,reference_sha)
    assert len(data)==reference_size,('reference size',len(data),reference_size)
    with Image.open(io.BytesIO(data)) as image:
        fmt=image.format
        size=image.size
        image.verify()
    return {'sha256':digest,'bytes':len(data),'format':fmt,'dimensions':list(size),'source_commit':expected,'lfs_oid':'sha256:'+reference_sha}

reference_bytes=reference_target.read_bytes() if reference_target.exists() else b''
if hashlib.sha256(reference_bytes).hexdigest()!=reference_sha:
    subprocess.run([
        'git','lfs','fetch','origin',expected,
        '--include=Docs/Production/T02/reference-ground.webp','--exclude='
    ],check=True)
    smudged=subprocess.run(['git','lfs','smudge'],input=pointer,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
    reference_bytes=smudged
reference_provenance=verified_reference(reference_bytes)
reference_target.write_bytes(reference_bytes)

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
(out/'reference-provenance.json').write_text(json.dumps(reference_provenance,indent=2))
executed=out/'executed-reviewer.py'
executed.write_text(source)
(out/'strict-wrapper-provenance.txt').write_text(
    'base_sha256='+hashlib.sha256(data).hexdigest()+'\n'
    'base_provenance=T03-boundary-v2_verified\n'
    'preflight_source='+expected+'\n'
    'reference_sha256='+reference_sha+'\n'
    'reference_lfs_materialized_and_decodable=true\n'
    'changes=score_rule_strict_gt_9;prompt_matches_strict_rule;river_gate_four_view_contract;verified_lfs_reference\n'
    'threshold=>9.0_unrounded\n'
    'required_river_gate_evidence=12\n'
    'diagnostic_confidence=low_medium_high_only\n'
    'model_groups_seeds_unchanged=true\n'
)
exec(compile(source,str(executed),'exec'),{'__name__':'__main__','__file__':str(executed.resolve())})
