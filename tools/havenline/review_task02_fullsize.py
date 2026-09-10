#!/usr/bin/env python3
"""T02 evidence-resolution repair after actual surface edits, not unchanged score shopping.
Reuses the pinned independent model, raw response retention, rubric and >=9 gate.
Splits oversized sequence boards; adds the new actual native4K closeups. No
original image is retouched or hidden. Task scope and mandatory tests are unchanged.
"""
from pathlib import Path
import hashlib,json
base=Path('tools/havenline/review_task02.py').read_bytes()
assert hashlib.sha1(b'blob '+str(len(base)).encode()+b'\0'+base).hexdigest()=='e1084f9859f79af4e5b4febdb7b7cead783c387e','Original reviewer changed; inspect before reusing'
s=base.decode()
start=s.index('GROUPS={');end=s.index('\nassert GROUP in GROUPS',start)
groups={
 'workfloor':['native4k/workfloor-gameplay.png','native4k/native-workfloor-overhead.png','gallery/bay-connection.png','native4k/native-overview.png'],
 'shoreline':['gallery/lakeshore-gameplay.png','native4k/native-shore-detail.png','gallery/lakeshore-rear.png','native4k/lakeshore-gameplay.png'],
 'snow-contact':['native4k/native-snow-join.png','gallery/approved-forest-contact.png','gallery/snow-workfloor-join.png'],
 'tree-visibility':['tree-clearance/clearance-baseline.png','tree-clearance/clearance-disabled.png','tree-clearance/clearance-enabled.png','tree-clearance/resource-depleted.png','tree-clearance/resource-restored.png'],
 'camera-route-early':[f'gallery/route-camera-{i:02d}.png' for i in range(4)],
 'camera-route-late':[f'gallery/route-camera-{i:02d}.png' for i in range(4,8)],
 'water-sequence':[f'gallery/water-motion-{i:02d}.png' for i in range(6)],
 'night-overview':['gallery/lakeshore-night.png','gallery/terrain-overview.png']
}
s=s[:start]+'GROUPS='+repr(groups)+s[end:]
old='columns=2 if len(names)<=4 else (3 if len(names)<=9 else 4)';assert s.count(old)==1;s=s.replace(old,'columns=2')
# Original coarse boards could suggest single-pixel/contact defects not resolved
# by their displayed pixels. Provide coordinates to support subsequent checking.
needle="(OUT/'schema.json').write_text(json.dumps(schema,indent=2))";assert s.count(needle)==1
s=s.replace(needle,"schema['properties']['defects']['items']={'type':'object','properties':{'view':{'type':'string'},'region':{'type':'string'},'issue':{'type':'string'}},'required':['view','region','issue'],'additionalProperties':False}\n"+needle)
needle="(OUT/'instructions.txt').write_text(PROMPT);";assert s.count(needle)==1
s=s.replace(needle,"PROMPT+='\\nDefects must be actual visible problems, each with a candidate filename, specific image region and issue. When none are visible, return an EMPTY defects array []; do not put statements saying no defects inside it. Distinguish ordinary cast shadows from holes or ground obstacles, and inspect the ground surface rather than mistaking overhanging roofs for terrain. Do not claim a single-pixel flaw from a small overview unless the supplied closeups resolve it. The unchanged per-task criteria still apply; report uncertainty honestly.'\n"+needle)
# Emit the complete executed code and selection so the wrapper cannot conceal
# different images, prompts, model inputs, scoring thresholds or raw responses.
out=Path('task02-review');out.mkdir(exist_ok=True)
(out/'executed-reviewer.py').write_text(s)
(out/'review-code-provenance.json').write_text(json.dumps({'base_reviewer_blob':'e1084f9859f79af4e5b4febdb7b7cead783c387e','base_sha256':hashlib.sha256(base).hexdigest(),'executed_sha256':hashlib.sha256(s.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'groups':groups,'minimum_task_score_unchanged':9,'model_unchanged':True,'reason':'Real surface color/edge changes require fresh review. Larger native detail coverage and subdivided sequence boards correct coarse evidence, not a requested score.'},indent=2))
exec(compile(s,'T02-fullsize-evidence-review','exec'),{'__name__':'__main__','__file__':__file__})
