import json,hashlib,copy
from pathlib import Path
from PIL import Image
B=Path('/workspace/scratch/fc906e16b0fb/havenline-plot-renders');R=B/'reviews';G=B.parent/'generated_images'
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
corep=R/'final-independent-visual-review.json';corehash='f19f0774cd45e136b7d7429ccec0566fe6b798bd5c5a7ce12f7e0d3e8616598b';assert H(corep)==corehash
core=json.loads(corep.read_text());addp=B/'acceptance-addendum-extra-buy-plots.json';add=json.loads(addp.read_text())
initialp=R/'supplement-initial-review.json';initial=json.loads(initialp.read_text());latest={a['asset']:copy.deepcopy(a) for a in initial['assets']}
p=G/'exec-f9b776a3-ca3b-477f-b4d4-dbabdb0bae48.png'
counter=copy.deepcopy(latest['buy_counter_action'])
counter.update(candidate_path=str(p),sha256=H(p),bytes=p.stat().st_size,dimensions=list(Image.open(p).size),score=9.4,verdict='PASS_CONCEPT_SHEET',blocking_defects=[],evidence=[
 'Actual full-sheet retest and closeup confirm rear180 internal motif corrected: parallel strokes above and inverted scalloped curves below toward dome.',
 'Other seven interior motifs, all dome/frame orientations, cash600 reading directions and four corner brackets retained.',
 'Source dome/frame/internal-stroke identity, neutral action title, flat ground field and reference-price qualifier preserved.'])
retestp=R/'supplement-counter-retest-01.json'
retest={'reviewer_agent':'/root/turnaround_critic','contract_version':add['version'],'contract_path':str(addp),'contract_sha256':H(addp),'batch':'counter-interior-retest','iteration':2,'actual_closeup_inspected':{'path':str(R/'inspection-crops/counter-interior-retest.png'),'sha256':H(R/'inspection-crops/counter-interior-retest.png')},'assets':[counter],'gate':'PASS 9.4, all mandatory concept-image checks passed; no blocking defects.'}
retestp.write_text(json.dumps(retest,indent=2)+'\n');latest['buy_counter_action']=counter
suppassets=[]
for spec in add['assets']:
 a=latest[spec['id']];assert a['score']>9 and not a['blocking_defects'] and H(a['candidate_path'])==a['sha256']
 a.update(title=spec['title'],owner=spec['owner'],review_report=str(retestp if a['asset']=='buy_counter_action' else initialp),accepted_as='static_concept_sheet_not_native_mesh_or_runtime_asset')
 a['mandatory_checks']={
  'actual_full_sheet_and_source_crop_inspected':'PASS','source_glyph_identity':'PASS','flat_purchase_field_and_four_separate_corners':'PASS',
  'eight_ground_plane_directions':'PASS','all_cost_orientations_including_135_225':'PASS','fixed_major_glyph_parts':'PASS',
  'complete_framing_labels_and_reference_price_qualifier':'PASS','no_invented_action_economy_or_runtime_claim':'PASS'}
 suppassets.append(a)
for a in core['assets']:assert H(a['candidate_path'])==a['sha256']
for ref in core['source_reference_inspection_ledger']:assert H(ref['path'])==ref['sha256'],ref['path']
prior=json.loads((R/'prior33-final-preservation.json').read_text());assert all(H(c['path'])==c['expected_sha256'] for c in prior['checks'])
sourcep=B/'sources/additional-buy-plot-source-notes.json';assert H(sourcep)=='9927ef5b30dbed02b6b72bcbf6961ca446c407f5ed038ed6a93f2ef245cbfe94'
supp={
 'title':'Havenline additional buy plots: final independent visual review',
 'reviewer_agent':'/root/turnaround_critic','date':'2026-11-23','review_type':'Actual-source and actual-output independent visual review with targeted counter-motif repair and retest',
 'contract_version':add['version'],'contract_path':str(addp),'contract_sha256':H(addp),
 'visual_verdict':'PASS_SUPPLEMENT_CONCEPT_COLLECTION','minimum_score':9.4,
 'counts':{'required_sheets':3,'passed_sheets':3,'blocked_sheets':0,'unreviewed_sheets':0,'turnaround_views':24,'reviewed_candidates':4,'superseded_candidates_preserved':1},
 'source_review':{'path':str(R/'supplement-source-contract-review.json'),'sha256':H(R/'supplement-source-contract-review.json')},
 'source_addendum':{'path':str(sourcep),'sha256':H(sourcep)},
 'core_preservation':{'ledger':str(corep),'sha256':corehash,'selected_images_checked':26,'unchanged_images':26,'unchanged_paths_hashes_scores':True,'all_bound_core_source_review_files_unchanged':True},
 'prior33_rechecked_unchanged':33,
 'assets':suppassets,'review_history':[str(initialp),str(retestp)],
 'limits':['Static concept reconstructions, not native meshes or runtime implementation.','175,50,600 are source display examples, not canonical Havenline prices.','Person-plus and counter titles identify observed glyphs; exact actions, staffing, capacities and effects remain unproven.']}
suppp=R/'final-supplement-3-visual-review.json';suppp.write_text(json.dumps(supp,indent=2)+'\n')
combinedassets=copy.deepcopy(core['assets'])+copy.deepcopy(suppassets)
assert len(combinedassets)==29 and len({a['asset'] for a in combinedassets})==29
assert all((a['candidate_path'],a['sha256'],a['score'])==(b['candidate_path'],b['sha256'],b['score']) for a,b in zip(combinedassets[:26],core['assets']))
combined={
 'title':'Havenline storage, buy and activation plots: combined final 29-sheet independent visual review',
 'reviewer_agent':'/root/turnaround_critic','date':'2026-11-23','review_type':'Independent actual-image review; selected assets and scores preserved from core and additive ledgers',
 'visual_verdict':'PASS_COMBINED_CONCEPT_COLLECTION','minimum_score':min(a['score'] for a in combinedassets),
 'gate_rule':'Every selected sheet strictly above 9.0 and all applicable visual/source-boundary checks passed. No failed or unseen visual areas averaged away.',
 'scope':'29 static plot concept sheets: 26 eight-view turnarounds and 3 state plates. No native meshes, motion, runtime integration, exact action/economy or capacity certification.',
 'contracts':[{'path':str(B/'acceptance-contract.json'),'version':'2026-11-23-plots-v1','sha256':H(B/'acceptance-contract.json')},{'path':str(addp),'version':add['version'],'sha256':H(addp)}],
 'authoritative_component_ledgers':[{'path':str(corep),'sha256':corehash,'sheets':26},{'path':str(suppp),'sha256':H(suppp),'sheets':3}],
 'counts':{'required_sheets':29,'passed_sheets':29,'blocked_sheets':0,'unreviewed_sheets':0,'storage_turnarounds':16,'buy_and_material_turnarounds':9,'work_zone_turnarounds':1,'turnaround_sheets':26,'turnaround_views':208,'state_plates':3,'state_panels':17,'total_plot_panels':225,'prior_resource_sheets_preserved':33,'combined_collection_sheets':62,'combined_turnaround_sheets':59,'combined_turnaround_views':472,'combined_all_panels':489,'unique_reviewed_plot_candidates':51,'superseded_plot_candidates_preserved':22},
 'preservation':{'core26_ledger_hash_unchanged':True,'core26_selected_paths_hashes_scores_unchanged':True,'core26_selected_bytes_rechecked':26,'prior33_selected_bytes_rechecked':33,'core_bound_source_review_files_unchanged':True,'prior33_report':{'path':str(R/'prior33-final-preservation.json'),'sha256':H(R/'prior33-final-preservation.json')}},
 'acceptance_checks':core['acceptance_checks']+[
  {'id':'ADD1','status':'PASS','evidence':'Three distinct additional source crops directly inspected; neutral glyph names and source example prices retained.'},
  {'id':'ADD2','status':'PASS','evidence':'All 24 supplemental directions inspected; bow/person initially pass and counter rear internal motif repaired/retested.'},
  {'id':'ADD3','status':'PASS','evidence':'Core26 exact selected paths, hashes, scores, ledger and bound source/review files preserved unchanged.'}],
 'source_reference_inspection_ledgers':[{'path':str(corep),'sha256':corehash},{'path':str(R/'supplement-source-contract-review.json'),'sha256':H(R/'supplement-source-contract-review.json')},{'path':str(sourcep),'sha256':H(sourcep)}],
 'residual_minor_disposition':core['residual_minor_disposition'],
 'limits':core['limits']+supp['limits'],
 'assets':combinedassets,
 'review_history':{'core':core['review_history'],'supplement_reports':[str(initialp),str(retestp)]},
 'packaging_gate':'PENDING_EXTERNAL_PACKAGE_AND_PUBLICATION_VERIFICATION: image selection approved; packaging owner must verify copied/archive/GitHub bytes, scope, labels and access before claiming overall delivery complete.',
 'next_action':'Package exactly these 29 hash-bound PNGs and preserved source/prompt/review evidence, retain the 33 earlier approved resource sheets, then independently verify package and publication. No additional art edits required.'}
combp=R/'final-combined-29-visual-review.json';combp.write_text(json.dumps(combined,indent=2)+'\n')
idx={'reviewer_agent':'/root/turnaround_critic','status':'3_PASS_SUPPLEMENT_29_PASS_COMBINED','required':3,'pass':3,'blocked':0,'unreviewed':0,'source_review':str(R/'supplement-source-contract-review.json'),'asset_reviews':[str(initialp),str(retestp)],'final_supplement':str(suppp),'final_supplement_sha256':H(suppp),'final_combined':str(combp),'final_combined_sha256':H(combp)}
(R/'supplement-review-index.json').write_text(json.dumps(idx,indent=2)+'\n')
print('SUPPLEMENT',str(suppp),H(suppp));print('COMBINED',str(combp),H(combp));print('CORE_UNCHANGED',H(corep));print('TOTAL',len(combinedassets),'MIN',combined['minimum_score'])
