#!/usr/bin/env python3
"""T02 fresh source-bound review; corrected evidence layout and blind control.
The previous control repeated an A/B reference montage under new A/B panel labels.
The repeated pixels were identical but every model answered otherwise. Preserve
that failed run. This control uses unlabelled candidate frames, explicitly checks
identical decoded image composition and keeps its answer key out of the request.
The independent model, art rubric, scores, temperature and >=9 gate are unchanged.
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
old="probe_files=[ref,ref,ROOT/'gallery/lakeshore-detail.png',ROOT/'gallery/workfloor-overhead.png']"
assert s.count(old)==1
s=s.replace(old,"probe_files=[ROOT/'gallery/lakeshore-detail.png',ROOT/'gallery/lakeshore-detail.png',ROOT/'gallery/workfloor-overhead.png',ROOT/'gallery/lakeshore-detail.png']\nassert Image.open(probe_files[0]).convert('RGB').tobytes()==Image.open(probe_files[1]).convert('RGB').tobytes()\nassert Image.open(probe_files[2]).convert('RGB').tobytes()!=Image.open(probe_files[3]).convert('RGB').tobytes()")
old='Inspect labelled panels A, B, C and D. Do A and B show the same scene image? Do C and D show the same scene image? Ignore panel labels when comparing. Return only A_B_same_scene and C_D_same_scene booleans from the pixels.'
assert s.count(old)==1
s=s.replace(old,'This is a four-panel image-comparison check, not an art review. Compare the entire picture inside each labelled panel, ignoring only the small A/B/C/D label above it. Return A_B_same_scene=true only when panels A and B show identical image composition and objects in identical positions. Return C_D_same_scene=true only when panels C and D show identical image composition and objects in identical positions. Otherwise use false. Determine both independently from the displayed pixels; do not infer from filenames or a desired result. JSON only.')
needle="(OUT/'schema.json').write_text(json.dumps(schema,indent=2))";assert s.count(needle)==1
s=s.replace(needle,"schema['properties']['defects']['items']={'type':'object','properties':{'view':{'type':'string'},'region':{'type':'string'},'issue':{'type':'string'}},'required':['view','region','issue'],'additionalProperties':False}\n"+needle)
needle="(OUT/'instructions.txt').write_text(PROMPT);";assert s.count(needle)==1
s=s.replace(needle,"PROMPT+='\\nDefects must be actual visible problems, each with a candidate filename, specific image region and issue. When none are visible, return an EMPTY defects array []; do not put statements saying no defects inside it. Distinguish ordinary cast shadows from holes or ground obstacles, and inspect the ground surface rather than mistaking overhanging roofs for terrain. Do not claim a single-pixel flaw from a small overview unless the supplied closeups resolve it. The unchanged per-task criteria still apply; report uncertainty honestly.'\n"+needle)
out=Path('task02-review');out.mkdir(exist_ok=True)
(out/'executed-reviewer.py').write_text(s)
(out/'review-code-provenance.json').write_text(json.dumps({'base_reviewer_blob':'e1084f9859f79af4e5b4febdb7b7cead783c387e','base_sha256':hashlib.sha256(base).hexdigest(),'executed_sha256':hashlib.sha256(s.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'groups':groups,'minimum_task_score_unchanged':9,'model_unchanged':True,'previous_control_failure_run':34504373276,'control_expected_answers_unchanged':True,'reason':'Fresh actual corridor revision. Earlier duplicated-reference montage contained nested A/B labels and failed factual recognition; candidate-only identical/different control removes that ambiguity without supplying the answer key or any art score.'},indent=2))
exec(compile(s,'T02-fullsize-evidence-review','exec'),{'__name__':'__main__','__file__':__file__})
