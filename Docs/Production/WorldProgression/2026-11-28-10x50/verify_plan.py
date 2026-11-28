#!/usr/bin/env python3
"""Validate this planning package only. No gameplay, gate or asset approval."""
from pathlib import Path
import json, hashlib, re
from collections import Counter
ROOT=Path(__file__).resolve().parent
EXPECTED_BASELINE_TASK_PROJECTION="3c23e61146672744b6506a8a9e01422a6165894eb8cac8f7ca0654bc2c36d355"
def read(name): return json.loads((ROOT/name).read_text())
def digest(value): return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
c=read('WORLD_PROGRESSION_CONTRACT.json');d=read('TASK_SCOPE_DELTA_T01_T80.json');s=read('SOURCE_EVIDENCE.json')
checks=[]
def check(name,condition): checks.append({'id':name,'pass':bool(condition)})
w=c['worlds'];r=d['rows']
check('owner_fixed_ten_by_fifty',c['world_count']==10 and c['levels_per_world']==50 and c['planned_total_level_positions']==500)
check('exact_world_local_ranges',len(w)==10 and [x['world_index'] for x in w]==list(range(1,11)) and all(x['local_level_range']==[1,50] and x['local_level_count']==50 for x in w))
check('preserved_world_owner_order',[x['content_owner_task'] for x in w]==['T32','T44','T45','T46','T47','T48','T49','T50','T51','T52'])
ordinals=[(x['world_index']-1)*50+level for x in w for level in range(1,51)]
check('derived_ordinal_covers_500_positions',ordinals==list(range(1,501)) and [x['derived_campaign_ordinal_range'] for x in w]==[[n,n+49] for n in range(1,501,50)])
check('ordinal_is_proposal_not_ui_or_save_migration',c['identity_proposal']['status']=='PROPOSED_INTERFACE_NO_SAVE_MIGRATION' and c['identity_proposal']['ordinal_is_authorized_ui_display'] is False and c['identity_proposal']['legacy_save_ids_rewritten'] is False)
check('all_80_task_rows_once_in_order',[x['task_id'] for x in r]==[f'T{i:02d}' for i in range(1,81)])
projection=[{key:x[key] for key in ('task_id','source_name','dependencies_preserved','source_lifecycle_snapshot')} for x in r[:70]]
check('original_70_task_names_dependencies_status_snapshots_preserved',digest(projection)==EXPECTED_BASELINE_TASK_PROJECTION)
check('ten_missing_tasks_not_invented',all(x['disposition']=='source_missing' and x['source_name'] is None and x['dependencies_preserved'] is None for x in r[70:]))
check('all_task_dispositions_accounted_for',dict(Counter(x['disposition'] for x in r))==d['counts'] and sum(d['counts'].values())==80)
check('world1_release_separate_from_future_campaign',c['release_scope']['initial_release_worlds']==[1] and c['release_scope']['later_update_worlds']==list(range(2,11)) and c['release_scope']['initial_release_local_range']==[1,50] and c['release_scope']['future_campaign_total']==500 and c['release_scope']['future_campaign_acceptance_is_initial_release_prerequisite'] is False)
check('no_dependency_or_quality_waiver',c['release_scope']['task_dependencies_modified'] is False and c['release_scope']['existing_required_security_audio_economy_reference_device_gates_waived'] is False and d['dependencies_preserved'] is True and not any(x['candidate_task_activation'] for x in r))
check('no_invented_asset_levels_or_full_campaign_content',c['visual_upgrade_scope']['world_indices']==[1] and c['visual_upgrade_scope']['new_asset_level_caps_authored'] is False and c['visual_upgrade_scope']['new_numeric_upgrade_unlocks_authored'] is False and c['visual_upgrade_scope']['fifty_models_per_asset_required'] is False and c['authored_outcomes']['new_level_outcomes_authored_in_this_package']==0 and c['authored_outcomes']['complete_500_outcomes_exist'] is False)
check('fuel_required_and_conflicting_vehicle_policies_visible',c['vehicle_precedence']['fuel_required'] is True and c['vehicle_precedence']['fuel_open_or_absent_wording_superseded'] is True and {x['id'] for x in c['vehicle_precedence']['unresolved_source_conflicts']}=={'VC01','VC02'} and all('UNRESOLVED' in x['disposition'] or 'RECONCILIATION' in x['disposition'] for x in c['vehicle_precedence']['unresolved_source_conflicts']))
check('no_runtime_shipping_approval',c['approval_boundary']['planning_and_render_scope_only'] is True and c['approval_boundary']['runtime_integrated'] is False and c['approval_boundary']['shipping_approved'] is False and c['approval_boundary']['game_score'] is None and c['preservation']['runtime_source_modified'] is False)
check('source_manifest_has_primary_evidence_and_local_hashes',len(s['remote_sources'])==7 and len({x['id'] for x in s['remote_sources']})==7 and all(re.fullmatch(r'[a-f0-9]{64}',x['sha256']) for x in s['local_source_records']) and all(x['base_commit_is_not_asserted_to_contain_staged_bytes'] for x in s['local_source_records']))
check('markdown_has_all_80_rows',re.findall(r'^\| (T[0-9]{2}) \|',(ROOT/'TASK_SCOPE_DELTA_T01_T80.md').read_text(),re.M)==[f'T{i:02d}' for i in range(1,81)])
check('resumption_checkpoint_exists',(ROOT/'CHECKPOINT.json').is_file() and read('CHECKPOINT.json')['runtime_integrated'] is False)
PACKAGE_ROOT=ROOT.parents[3]
e=s['entrypoint_updates'];entries=e['files']
check('four_entrypoint_candidates_bound',len(entries)==4 and all((PACKAGE_ROOT/x['path']).is_file() and hashlib.sha256((PACKAGE_ROOT/x['path']).read_bytes()).hexdigest()==x['candidate_sha256'] for x in entries))
check('canonical_entrypoint_sources_verified',e['canonical_source_hashes_directly_verified'] is True and all(re.fullmatch(r'[a-f0-9]{40}',x['source_git_blob_sha']) and x['capture_transform'] for x in entries))
check('current_entrypoint_pointers_present',all('WORLD_PROGRESSION_CONTRACT.json' in (PACKAGE_ROOT/x['path']).read_text() and 'TASK_SCOPE_DELTA_T01_T80.md' in (PACKAGE_ROOT/x['path']).read_text() for x in entries))
plan=(PACKAGE_ROOT/'Docs/Production/HAVENLINE_BUILD_PLAN_V2.md').read_text()
names={m.group(1):m.group(2) for m in re.finditer(r'^\| (T[0-9]{2}) \| (.*?) \|',plan,re.M)}
check('current_build_plan_uses_revised_scope_titles',all(names[x['task_id']]==x['forward_scope_title'] for x in r[:70] if x['disposition']=='direct_change') and 'Launch remains Level 1–100' not in plan and 'Level 1–100 must remain realistically completable' not in plan)
states={m.group(1):m.group(2) for m in re.finditer(r'^\| (T[0-9]{2}) \| .*? \| (.*?) \|',plan,re.M)}
history_ok=True
for rec in e['history_sections'].values():
    section=plan.split(rec['start'],1)[1].split(rec['end'],1)[0]
    history_ok=history_ok and hashlib.sha256(section.encode()).hexdigest()==rec['sha256']
check('seventy_migration_states_and_two_history_sections_preserved',len(states)==70 and hashlib.sha256(json.dumps(states,sort_keys=True,separators=(',',':')).encode()).hexdigest()==e['migration_state_projection_sha256'] and history_ok)
check('entrypoint_change_has_no_gameplay_selector_graph_or_workflow_edit',e['current_gameplay_source_selector_edited'] is False and e['dependency_graph_edited'] is False and e['workflows_edited'] is False)
direct_ids={x['task_id'] for x in r if x['disposition']=='direct_change'}
unchanged_rows={m.group(1):m.group(0) for m in re.finditer(r'^\| (T[0-9]{2}) \|.*$',plan,re.M) if m.group(1) not in direct_ids}
check('unaffected_production_rows_preserved',len(unchanged_rows)==e['unchanged_production_row_count']==70-len(direct_ids) and digest(unchanged_rows)==e['unchanged_production_rows_sha256'])
owner_by_id={x['id']:x for x in s['owner_steering_sources']}
owner_contract={x['id']:x for x in c['authority']['latest_owner_instructions']}
check('latest_owner_quotes_exact_and_storage_followup_retained',set(owner_by_id)=={'U02','U03'} and all(owner_by_id[k]['verbatim']==owner_contract[k]['verbatim'] for k in owner_by_id) and owner_by_id['U03']['verbatim']=='dont forget the storage house too')
owner_source=PACKAGE_ROOT/owner_by_id['U02']['source_path']
check('owner_artifact_source_bound',owner_source.is_file() and hashlib.sha256(owner_source.read_bytes()).hexdigest()==owner_by_id['U02']['source_sha256'] and json.loads(owner_source.read_text())['verbatim']==owner_by_id['U02']['verbatim'])
v=c['visual_upgrade_scope'];value=c['purchase_value_contract'];actors=c['simultaneous_actors']
check('meaningful_production_defense_value_not_stats_approval',v['meaningful_visual_and_functional_change_required'] and v['minor_reinforcement_only_direction_superseded'] and len(value['production_gain_dimensions'])>=4 and len(value['defense_gain_dimensions'])>=4 and value['numeric_rates_hp_damage_costs_caps_approved'] is False and value['concept_is_native_implementation'] is False)
check('storage_house_explicit_without_fake_unlimited_capacity',v['storage_house_explicitly_included'] and value['fake_unlimited_capacity_upgrade_forbidden'] and len(value['storage_house_gain_dimensions'])>=4)
check('functional_upgrade_geometry_can_change_with_invariants',v['universal_same_footprint_requirement'] is False and v['upgraded_footprint_and_ports_may_change'] is True and v['ordinary_resource_and_conveyor_unit_scale_preserved'] is True and 'real_functional_benefit' in v['geometry_changes_require'] and 'two_bidirectional_camp_openings' in v['geometry_changes_require'])
prior=actors['prior_staged_policy']
check('multiple_simultaneously_active_actors_without_new_cap',actors['owner_requires_multiple_pets'] and actors['owner_requires_multiple_survivors'] and actors['simultaneous_not_just_owned_roster'] and actors['new_numeric_cap_authored'] is False and actors['total_local_worker_cap_inferred_from_escort_limit'] is False and prior['expedition_pet_limit']==3 and prior['survivor_escort_limit']==2 and prior['separate_local_workers'] is True and prior['status']=='PRESERVED_UNINTEGRATED_STARTING_POLICY_NOT_NEWLY_RATIFIED' and actors['native_integration_approved'] is False)
check('eighteen_owner_requirements_unique',len(c['requirements'])==18 and len({x['id'] for x in c['requirements']})==18 and {f'WP{i:02d}' for i in range(1,19)}=={x['id'] for x in c['requirements']})
check('entrypoints_surface_latest_upgrade_value',all('Latest upgrade-value direction' in (PACKAGE_ROOT/x['path']).read_text() and 'storage house' in (PACKAGE_ROOT/x['path']).read_text() and 'Multiple pets and multiple survivors' in (PACKAGE_ROOT/x['path']).read_text() for x in entries))
history_root=ROOT/'History/2026-11-28-before-functional-value';history_manifest=json.loads((history_root/'DISPOSITION.json').read_text())
check('prior_candidate_and_evidence_preserved',len(history_manifest['files'])==13 and all((history_root/x['path']).is_file() and hashlib.sha256((history_root/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in history_manifest['files']))
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.iterdir()) if p.is_file() and p.name!='VALIDATION.json'}
for x in entries: files['../../../../'+x['path']]=hashlib.sha256((PACKAGE_ROOT/x['path']).read_bytes()).hexdigest()
files['History/2026-11-28-before-functional-value/DISPOSITION.json']=hashlib.sha256((history_root/'DISPOSITION.json').read_bytes()).hexdigest()
result={'schema_version':1,'scope':'PLANNING_STRUCTURE_ONLY','pass':all(x['pass'] for x in checks),'passed':sum(x['pass'] for x in checks),'required':len(checks),'checks':checks,'candidate_files_sha256':files,'runtime_tested':False,'native_visual_motion_audio_device_reviewed':False,'shipping_approval':False,'independent_review':'SEPARATE_REVIEW_REQUIRED'}
(ROOT/'VALIDATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['scope','pass','passed','required','runtime_tested','shipping_approval']},indent=2))
raise SystemExit(0 if result['pass'] else 1)
