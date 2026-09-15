#!/usr/bin/env python3
"""Correct a diagnosed reviewer-input failure, not game artwork or score thresholds.

The previous llama runtime explicitly warned that Qwen-VL grounding needs at least
1024 image tokens. The old launcher set a maximum of 1024 but no minimum. Its raw
clearance reports described opaque trees in the baseline/cleared images where
original pixels and measured image differences show the player unobstructed.
Keep all old reports, including low scores, as rejected/incomplete evidence.
This runner restores adequate image-token detail and requires explicit factual
state observations. It does not insert scores, desired facts, or approval.
"""
from pathlib import Path
import hashlib,subprocess

BASE='8632c5b2c2a70ec1eb88db08bef8ca18b707e1a6'
raw=subprocess.check_output(['git','show',BASE+':tools/havenline/review_task01_cached.py'])
assert hashlib.sha256(raw).hexdigest()=='1a3945a788aa4826995e6728b02a7257e99df3eace8abf3e563a564b9f144677'
source=raw.decode()
old="'--image-max-tokens','1024'"
assert source.count(old)==1
source=source.replace(old,"'--image-min-tokens','1024','--image-max-tokens','2048'")
assert source.count("'-c','8192'")==1
source=source.replace("'-c','8192'","'-c','12288'")
old="PROMPT += '\\nReviewer role: '"
assert source.count(old)==1
source=source.replace(old,"PROMPT += '\\nIn clearance groups the reference is a full-tree appearance guide, not the expected state of a depleted or camera-hidden resource. Judge whether the visibility transitions and depletion work correctly; an intentionally hidden/depleted tree must not be penalized merely for being absent. The six resource fade frames deliberately expose the actual dither transition, whose visual finish you should independently assess. For isolated variant images no ground plane is shown: do not claim those isolated images prove terrain contact; contact is reviewed in the separate forest group. In every observation identify the actual image content rather than substituting the reference tree for the central character. A concern about the dither visual finish is legitimate if supported; do not suppress it to obtain approval.'\n"+old)
old="(OUT/'response-schema.json').write_text(json.dumps(schema,indent=2))"
assert source.count(old)==1
source=source.replace(old,old+"\nimport copy\nBASE_SCHEMA=copy.deepcopy(schema)\nFACT_KEYS=['baseline_tree_blocks_central_player','disabled_tree_blocks_central_player','enabled_tree_blocks_central_player','depleted_resource_tree_visible']")
old="paths,note=prepare(group);content=[];inputs=[]"
assert source.count(old)==1
source=source.replace(old,old+"\n            schema=copy.deepcopy(BASE_SCHEMA)\n            if group=='clearance':\n                schema['properties']['evidence_facts']={'type':'object','properties':{key:{'type':'boolean'} for key in FACT_KEYS},'required':FACT_KEYS,'additionalProperties':False}\n                schema['required'].append('evidence_facts')\n                note+=' Before scoring, independently report the four boolean evidence_facts from the actual labelled images: whether a tree visually blocks the central player in baseline, disabled, and enabled, and whether the depleted resource tree is visible in resource-depleted. Do not infer these answers from desired functionality; inspect the pixels. The labels identify images but are not an answer key.'")
old="record['review']=parsed;record['lowest_score']=min(parsed['scores'].values())"
assert source.count(old)==1
source=source.replace(old,old+"\n            if group=='clearance':\n                facts=parsed.get('evidence_facts',{})\n                record['factual_image_recognition_passed']=(facts==dict(zip(FACT_KEYS,[False,True,False,False])))\n                assert record['factual_image_recognition_passed'],'Reviewer failed image-state recognition against verified original pixels; no valid clearance approval'")
old="'task_approved':False,'physical_4k60_verified':False}"
assert source.count(old)==1
source=source.replace(old,"'task_approved':False,'physical_4k60_verified':False,'reviewer_input_repair':{'reason':'Runtime warned to use image-min-tokens 1024 for grounding; prior clearance observations contradicted actual frames','image_min_tokens':1024,'image_max_tokens':2048,'minimum_score_unchanged':9,'old_raw_reports_preserved':True,'game_source_or_capture_changed':False,'factual_clearance_check_required':True}}")
output=Path('critic-results');output.mkdir(exist_ok=True)
(output/'executed-grounded-reviewer.py').write_text(source)
(output/'reviewer-code-provenance.json').write_text(__import__('json').dumps({'base_source':BASE,'base_reviewer_sha256':hashlib.sha256(raw).hexdigest(),'executed_reviewer_sha256':hashlib.sha256(source.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'purpose':'Diagnosed input-resolution correction and factual recognition check; never unchanged rescore just for a desired number'},indent=2))
exec(compile(source,'T01-corrected-image-grounding','exec'),{'__name__':'__main__'})
