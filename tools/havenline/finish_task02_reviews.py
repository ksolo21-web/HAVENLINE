#!/usr/bin/env python3
"""Complete only unresolved T02 reviews; preserve every previous raw result.

Timeouts have no art verdict. Explicit day/night and visibility-state evidence
corrects demonstrated factual contradictions. The alternate Gemma run failed its
blind control and cannot approve anything. Qwen may review the clarified evidence
only after independently passing the control and the extra candidate-state facts.
No old score or factual answer key is supplied to the model. No image is retouched.
"""
from pathlib import Path
import hashlib,json,os

ROLE=os.environ['REVIEW_ROLE'];GROUP=os.environ['REVIEW_GROUP']
MODEL_FAMILY=os.environ.get('MODEL_FAMILY','gemma')
assert MODEL_FAMILY in ('qwen','gemma')
SOURCE='586604eb8ab6404fc8084b6853fd03cfa842d3af'
allowed={('reference-fidelity','workfloor'),('reference-fidelity','tree-visibility'),('visual-integrity','tree-visibility'),('reference-fidelity','night-overview'),('visual-integrity','night-overview')}
assert (ROLE,GROUP) in allowed
old_root=Path('previous/reviews')/f'T02-final-{ROLE}-{GROUP}-34510062914'
old=json.loads((old_root/'review.json').read_text());assert old['source']==SOURCE and old['passed'] is False
raw=(old_root/'executed-reviewer.py').read_bytes();s=raw.decode()
assert "with urllib.request.urlopen(req,timeout=900)" in s
s=s.replace('with urllib.request.urlopen(req,timeout=900)','with urllib.request.urlopen(req,timeout=1800)')
if GROUP=='workfloor':
    assert old.get('error')=='timed out' and 'review' not in old and not (old_root/'review-raw.json').exists()
    repair='No-verdict execution timeout. Identical image selection, rubric, model, seed and temperature; longer request timeout only.'
else:
    repair='State-explicit factual resolution after image contradictions. Original source pixels unchanged; additional factual recognition required; no old verdict or desired score supplied. Alternate failed-control reports remain rejected, not approved.'
    if MODEL_FAMILY=='gemma':
        old_cache="Path.home()/'.cache/havenline-t01-qwen35'"
        assert s.count(old_cache)==1;s=s.replace(old_cache,"Path.home()/'.cache/havenline-t01-gemma'")
        old_assert="assert manifest['base_model']=='Qwen/Qwen3.5-9B' and manifest['revision']=='3885219b6810b007914f3a7950a8d1b469d598a5'"
        assert s.count(old_assert)==1
        s=s.replace(old_assert,"assert manifest['base_model']=='google/gemma-3-12b-it' and manifest['publisher']=='ggml-org/gemma-3-12b-it-qat-GGUF' and manifest['revision']=='05c2df468ad7a0bb1284b3d6fe2bdf495a885567'")
        s=s.replace(",'--image-min-tokens','1024','--image-max-tokens','2048'",'')
        s=s.replace(",'chat_template_kwargs':{'enable_thinking':False}",'')
    if GROUP=='night-overview':
        marker='names=GROUPS[GROUP];'
        assert s.count(marker)==1
        s=s.replace(marker,"GROUPS['night-overview']=['gallery/terrain-overview.png','gallery/lakeshore-gameplay.png','gallery/lakeshore-night.png']\n"+marker)
        note='The panel named terrain-overview is DAYTIME; lakeshore-gameplay is DAYTIME; lakeshore-night is NIGHT plus snowfall at the saved simulation time. These are the same ground/water materials under different existing lights. Compare daytime material palette against the daytime reference; compare night against the appropriate lower-light readability, continuity and contact requirement. This is not a request to forgive darkness that prevents readable play. The reference clips contain no night benchmark, so do not invent one or require night to have identical pixel colors to daylight. Independently identify which panel is which and whether the surfaces remain coherent/readable. Deliberately clean smooth stylization remains required; unrelated gritty detail is not the target.'
        properties={'day_floor_color':{'type':'string','enum':['warm_peach_or_orange','cool_gray_or_blue','white_or_absent','unclear']},'night_is_darker_than_day':{'type':'boolean'}}
        expected={'day_floor_color':'warm_peach_or_orange','night_is_darker_than_day':True}
    else:
        note='Inspect the central player feet and the ground immediately beneath them in the baseline, disabled, enabled and depleted panels. The original complete frames are shown. Assess actual ground contact, shadow and visibility, not whether every pixel must be covered by the same material. Snow and cleared ground are both legitimate surfaces. A camera-hidden tree is not automatically missing terrain. The restored panel uses a different disclosed camera adjacent to the original resource. First provide factual observations from the candidate pixels; these facts are independently checked after your response, not supplied as answers.'
        properties={'enabled_ground_under_player':{'type':'string','enum':['warm_colored_ground','white_snow','no_ground','unclear']},'enabled_player_shadow_visible':{'type':'boolean'},'enabled_extra_tree_blocks_player':{'type':'boolean'}}
        expected={'enabled_ground_under_player':'warm_colored_ground','enabled_player_shadow_visible':True,'enabled_extra_tree_blocks_player':False}
    marker="(OUT/'instructions.txt').write_text(PROMPT);"
    assert s.count(marker)==1;s=s.replace(marker,'PROMPT+=' +repr('\n'+note+'\nAlso fill evidence_facts from the actual labelled pixels, independently of the scores.')+'\n'+marker)
    marker="(OUT/'schema.json').write_text(json.dumps(schema,indent=2))"
    assert s.count(marker)==1
    extra="schema['properties']['evidence_facts']="+repr({'type':'object','properties':properties,'required':list(properties),'additionalProperties':False})+"\nschema['required'].append('evidence_facts')\n"
    s=s.replace(marker,extra+marker)
    marker="report['lowest_score']=min(scores.values())"
    assert s.count(marker)==1
    s=s.replace(marker,"report['factual_recognition_passed']=review.get('evidence_facts')=="+repr(expected)+"\n assert report['factual_recognition_passed'],'Review facts contradict independently verified original pixels'\n "+marker)
    marker="(OUT/'provenance.json').write_text(json.dumps(provenance,indent=2))"
    assert s.count(marker)==1
    s=s.replace(marker,"provenance['different_model_family_resolution']="+repr(MODEL_FAMILY=='gemma')+"\n provenance['state_explicit_input_and_fact_checks']=True\n "+marker)

out=Path('task02-review');out.mkdir(exist_ok=True)
(out/'executed-reviewer.py').write_text(s)
(out/'resolution-provenance.json').write_text(json.dumps({'task':'T02','source':SOURCE,'role':ROLE,'group':GROUP,'model_selection':MODEL_FAMILY,'prior_run':34510062914,'rejected_alternate_control_run':34513749870,'prior_review_sha256':hashlib.sha256((old_root/'review.json').read_bytes()).hexdigest(),'prior_executed_code_sha256':hashlib.sha256(raw).hexdigest(),'executed_code_sha256':hashlib.sha256(s.encode()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'reason':repair,'original_source_and_capture_bytes_unchanged':True,'score_threshold_unchanged':9,'old_failures_retained':True,'task_approved':False},indent=2))
exec(compile(s,'T02-state-explicit-independent-reviews','exec'),{'__name__':'__main__','__file__':__file__})
