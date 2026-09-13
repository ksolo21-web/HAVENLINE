#!/usr/bin/env python3
"""Expanded-evidence re-review for T03 cross-shelter-lanes.

The prior checksum-pinned local critic returned 6/10 with coverage_complete=false
because route/shelter frames did not always frame the gates it was also asked to
score. Preserve that failure. Add existing source-bound dedicated west/east gate
and native gate views to the SAME group, without altering game pixels or score
threshold. This is coverage repair, not unchanged rescoring.
"""
from pathlib import Path
import hashlib,os
base=Path('tools/havenline/review_task03_local_reference.py');source=base.read_text();base_sha=hashlib.sha256(base.read_bytes()).hexdigest()
marker="EXPECTED=set(sum(GROUPS.values(),[]));assert EXPECTED==set(FILES) and len(EXPECTED)==11"
assert source.count(marker)==1;source=source.replace(marker,marker+"\nGROUPS={2:['cross-shelter-lanes']}\n",1)
old="'cross-shelter-lanes':['gallery/cross-lane-west.png','gallery/cross-lane-centre.png','gallery/cross-lane-east.png','gallery/shelter-branch-west.png','gallery/shelter-branch-east.png','native4k/native-lane-network.png'],"
new="'cross-shelter-lanes':['gallery/cross-lane-west.png','gallery/west-work-gate.png','native4k/native-side-gate-west.png','gallery/cross-lane-centre.png','gallery/cross-lane-east.png','gallery/east-work-gate.png','native4k/native-side-gate-east.png','gallery/shelter-branch-west.png','gallery/shelter-branch-east.png','native4k/native-lane-network.png'],"
assert source.count(old)==1;source=source.replace(old,new,1)
assert source.count("OUT=Path('task03-local-reference')")==1;source=source.replace("OUT=Path('task03-local-reference')","OUT=Path('task03-local-expanded')",1)
assert source.count("'--image-max-tokens','2048'")==1;source=source.replace("'--image-max-tokens','2048'","'--image-max-tokens','1024'",1)
needle="SCHEMA={'type':'object'"
note="PROMPT += '''\nFor this expanded cross-shelter-lanes evidence group, the cross-lane and shelter-branch panels establish lane routing/composition, while the labelled west/east-work-gate and native-side-gate panels provide the dedicated pixels needed to judge whether those gate openings exist and whether fence ends contact the terrain. Do not infer a missing gate solely because a route panel does not frame it; inspect the dedicated gate panels. Conversely, if those dedicated views still show a floating fence, unclear opening, bad ground contact, or inconsistent geometry, report it as a defect.'''\n"
assert source.count(needle)==1;source=source.replace(needle,note+needle,1)
os.environ['REVIEW_SHARD']='2';out=Path('task03-local-expanded');out.mkdir(exist_ok=True)
(out/'coverage-repair-provenance.txt').write_text('base_sha256='+base_sha+'\nprior_local_failure_artifact=10267568985\nprior_lowest_score=6\nprior_coverage_complete=false\nadded_existing_source_bound_gate_context=true\nimage_tokens=1024\ngame_pixels_changed=false\n')
exec(compile(source,str(Path(__file__).resolve()),'exec'),{'__name__':'__main__','__file__':str(Path(__file__).resolve())})
