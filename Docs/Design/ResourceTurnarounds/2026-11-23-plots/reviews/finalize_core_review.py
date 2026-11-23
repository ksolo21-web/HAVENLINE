import json,hashlib
from pathlib import Path
from collections import Counter
B=Path('/workspace/scratch/fc906e16b0fb/havenline-plot-renders');R=B/'reviews'
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
contract=json.loads((B/'acceptance-contract.json').read_text());index=json.loads((R/'review-index.json').read_text())
latest={};hist=[]
for rp in index['asset_reviews']:
 for a in json.loads(Path(rp).read_text())['assets']:
  v=dict(a);v['review_report']=rp;latest[a['asset']]=v
  hist.append({k:a[k] for k in ['asset','candidate_path','sha256','score','verdict']}|{'review_report':rp})
assert set(latest)=={a['id'] for a in contract['assets']}
assets=[]
for spec in contract['assets']:
 a=latest[spec['id']]
 assert a['score']>9 and a['verdict']=='PASS_CONCEPT_SHEET' and not a['blocking_defects']
 assert H(a['candidate_path'])==a['sha256']
 a.update(title=spec['title'],owner=spec['owner'],accepted_as='static_concept_sheet_not_native_mesh_or_runtime_asset')
 a['mandatory_checks']={
  'actual_full_sheet_inspected':'PASS','source_family_and_scope_classification':'PASS',
  'material_and_stock_identity':'PASS' if a['asset'].startswith('storage_') else 'NOT_APPLICABLE',
  'ground_flatness_and_correct_boundary_family':'PASS',
  'eight_view_order_and_meaningful_direction':'PASS' if a['format']=='8_view_turnaround' else 'NOT_APPLICABLE',
  'fixed_major_landmarks_and_visible_count_stability':'PASS',
  'state_behavior_and_same_footprint':'PASS' if a['format']!='8_view_turnaround' else 'NOT_APPLICABLE',
  'clear_framing_labels_and_qualifiers':'PASS','no_canonical_economy_capacity_or_runtime_claim':'PASS'}
 assets.append(a)
prior=json.loads((R/'prior33-final-preservation.json').read_text());assert prior['count']==33 and prior['passed']==33
covp=B/'sources/storage-resource-coverage-proposal.json';cov=json.loads(covp.read_text())
priorids={a['asset'] for a in prior['checks']};mappedids={a['resource_id'] for a in cov['resource_mapping']}
assert len(cov['resource_mapping'])==33 and mappedids==priorids
assert len({a['id'] for a in cov['representative_stocked_types']})==15
assert all(a['representative_storage_sheet'] in latest for a in cov['resource_mapping'])
coverage={'reviewer_agent':'/root/turnaround_critic','status':'PASS_VISUAL_MAPPING','resource_count':33,'mapping_entries':33,'representative_stocked_types':15,'shared_visual_groups':len(cov['groups']),'exact_id_set_matches_prior33':True,'every_mapping_targets_reviewed_sheet':True,'classification_boundary':'Only wood, generic meat and cash are direct video storage types. Other resource-content associations are proposals. Groups assert no inventory/custody or wildlife eligibility behavior.','source_file':str(covp),'sha256':H(covp)}
(R/'coverage-validation.json').write_text(json.dumps(coverage,indent=2)+'\n')
turns=[a for a in assets if a['format']=='8_view_turnaround'];states=[a for a in assets if a['format']!='8_view_turnaround']
assert len(turns)==23 and len(states)==3 and sum(a['panel_count'] for a in states)==17
unique_candidates={h['candidate_path']:h for h in hist};selected={a['candidate_path'] for a in assets}
assert all(Path(p).exists() for p in unique_candidates)
source_files=[*index['source_reviews'],str(R/'coverage-validation.json'),str(B/'sources/storage-source-notes.json'),str(covp),str(B/'sources/buy-activation-source-notes.json')]
source_records=[{'path':p,'sha256':H(p)} for p in source_files]
checkdata=[
 ('R1','PASS','Actual supplied video frames and sampled transitions inspected; old structural timber bins excluded as plot-form substitutes.'),
 ('R2','PASS','16 storage sheets preserve dark flush rounded field, continuous tan perimeter and centered painted/occluded type mark; stock remains separate.'),
 ('R3','PASS','Six buy/material sheets use four separated corners, ground-plane action and reference cost; source gray construction exception retained.'),
 ('R4','PASS','Work turnaround and state plate use 12-piece unfilled outline, green active and white idle.'),
 ('R5','PASS','Six-panel plate distinguishes one-time marker removal/hearth replacement from repeatable axe availability.'),
 ('R6','PASS_CONCEPT_SCOPE','All 23 turnarounds inspected through eight clockwise directions; fixed major features and broad whole-pad yaw coherent after targeted repairs. Minor illustration projection variation is not a metric camera certificate.'),
 ('R7','PASS','Prior material identities retained; 12 unseen storage variants remain proposals; all 33 prior resources mapped as visual families only.'),
 ('R8','PASS','Source prices labelled reference examples; state quantities labelled illustrative with no capacity implied; no invented durations or inventory rules.'),
 ('R9','PASS','All 17 actual state panels inspected across 9/6/2 layouts, including corrected flat empty icons and payment graphics.'),
 ('R10','PASS','Independent critic examined actual full sheets and useful original/repair closeups. All selected scores exceed 9.0; no blocked or unseen visual checks remain.'),
 ('R11','PASS_PRESERVATION_AND_REVIEW_HISTORY_PACKAGE_HANDOFF_PENDING','All 33 earlier selected PNG hashes unchanged; all reviewed candidates and revision reports retained. Archive/GitHub publication is packaging owner\'s next gate, outside this image approval.')]
ledger={
 'title':'Havenline plot render collection: final independent visual review of core 26',
 'reviewer_agent':'/root/turnaround_critic','review_type':'Independent actual-image concept critique, targeted repair and retest','date':'2026-11-23',
 'contract_version':contract['version'],'contract_path':str(B/'acceptance-contract.json'),'contract_sha256':H(B/'acceptance-contract.json'),
 'scope':'Core 26 static plot concept sheets: 16 storage, 6 buy/material, 1 work-zone turnaround and 3 use-state plates. Image approval only; package/publication verification is a separate handoff gate. Subsequent additive coverage is reviewed separately.',
 'visual_verdict':'PASS_CONCEPT_COLLECTION','minimum_score':min(a['score'] for a in assets),
 'gate_rule':'Each selected sheet strictly above 9.0 and every applicable visual/source-boundary check passed. No averaging of failed areas.',
 'counts':{'required_sheets':26,'reviewed_selected_sheets':26,'passed_sheets':26,'blocked_sheets':0,'unreviewed_sheets':0,'turnaround_sheets':23,'turnaround_views':184,'state_plates':3,'state_panels':17,'total_new_panels':201,'prior_resource_sheets_preserved':33,'combined_collection_sheets':59,'combined_turnaround_views':448,'combined_all_panels':465,'unique_reviewed_candidates':len(unique_candidates),'rejected_or_superseded_candidates_preserved':len(set(unique_candidates)-selected)},
 'acceptance_checks':[{'id':i,'status':s,'evidence':e} for i,s,e in checkdata],
 'source_reference_inspection_ledger':source_records,
 'prior33_preservation':{'path':str(R/'prior33-final-preservation.json'),'sha256':H(R/'prior33-final-preservation.json'),'passed':33,'required':33},
 'coverage_validation':coverage,
 'residual_minor_disposition':[
  'Minor surface and projection differences remain within static concept scope; no common executable mesh, metric camera or exact hidden geometry is certified.',
  'Centered type marks can be fully occluded by centered stock, as authorized; empty/state templates establish the flat-mark design.',
  'Cash is described by actual visible art: one banded pile with three green layers, not a certified count of separate gameplay money units.',
  'Food preserves the prior approved scoring pattern; an exact three-cut count from generation intent is not certified.',
  'Natural 180-degree symmetry of the unmarked work outline is accepted; no invented directional marking added.'],
 'limits':[
  'Unseen reverse views are concept reconstruction, not observed native source meshes.',
  'No runtime integration, interaction timing, economy, capacity, recipe, yield, drop table or wildlife food eligibility approval.',
  'Worker/hand action names identify visible glyphs; exact gameplay bindings remain unproven.',
  'Prices copied from source are display examples only.',
  'GitHub/archive bytes and publication access must be verified by packaging owner after copying selected assets.'],
 'review_history':{'index':str(R/'review-index.json'),'reports':index['asset_reviews'],'candidates':hist},
 'assets':assets,
 'next_action':'Packaging owner copies exactly these 26 hash-bound files with contract/source/review history and preserves prior 33. Additional observed glyphs receive a separate additive review; this core selection is frozen.'}
p=R/'final-independent-visual-review.json';p.write_text(json.dumps(ledger,indent=2)+'\n')
index.update(final_review=str(p),final_review_sha256=H(p),status='26_PASS_VISUAL_PACKAGE_HANDOFF_READY')
(R/'review-index.json').write_text(json.dumps(index,indent=2)+'\n')
print('FINAL',str(p),H(p));print(json.dumps(ledger['counts']));print('MIN_SCORE',ledger['minimum_score']);print('SOURCE_CLASSIFICATIONS',dict(Counter(a['source_status'] for a in assets)))
