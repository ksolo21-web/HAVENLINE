#!/usr/bin/env python3
"""Check/project the bounded forward plan. Never certify gameplay or activate tasks."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
DOCS = 'Docs/Production/'
PACKAGE = DOCS + 'Completeness/2026-11-27/'  # immutable source audit
CURRENT_PACKAGE = DOCS + 'GameplayRules/2026-11-27/'
BASE = 'fd2e12c8734f49cda7eb3bbf97887406bd03a704'
GAME = '3fad812b384335bd8ca9b5e47dc9d9557110eb4a'
LATEST = '2f46e72e300a719f34ca9b0e9b718282a5a88ddd'
BUILD13_SOURCE = '2654f5019b7212968d28600cb071bf1c231c9030'
TASKS = [f'T{i:02}' for i in range(1, 71)]
UNDEFINED = [f'T{i:02}' for i in range(71, 81)]
PETS = {'guardian_dog':'dog_attack','gray_wolf':'wolf_attack','fox':'fox_attack',
        'owl':'owl_attack','male_lion':'lion_attack','white_tiger':'tiger_attack','brown_bear':'bear_attack'}
TRANSACTIONS = {'cargo_transfer','plot_purchase','machine_recipe','sale_and_cash','attack_contact',
                'defeat_reward','actor_recovery','region_travel','event_reward','purchase_entitlement',
                'structure_damage_repair_rebuild','quote_feasibility_change'}
RENDER_CONCEPTS = {'wood','stone','slate','steel','metal_ore','fuel','meat','fish','wheat','cooked_food','money','cargo','coal',
                  'deer_meat','boar_meat','rabbit_meat','moose_meat','squirrel_meat','wild_bear_meat','wild_wolf_meat','wild_fox_meat',
                  'lynx_meat','wolverine_meat','processed_meat_portion','cooked_game_meat','dried_meat','prepared_fish_fillet',
                  'cooked_fish','dried_fish','timber_planks','split_firewood','hide','fur'}
SOURCE_UNIVERSE_SHA256 = '81045962596de729e0996296a2f6faa7849c7d957ebac37a3683c5e86dafd54a'


def read(root, rel):
    return json.loads((pathlib.Path(root) / rel).read_text(encoding='utf-8'))


def source_bytes(root, commit, path):
    return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=root,stderr=subprocess.PIPE)


def load(root=ROOT):
    contract=read(root,DOCS+'WHOLE_GAME_COMPLETENESS.json')
    details=contract['detail_files']
    return (contract,read(root,details['actors']),read(root,details['economy']),
            read(root,details['transactions']),read(root,DOCS+'CURRENT_GAMEPLAY_SOURCE.json'))


def validate_data(contract, actors, economy, transactions, selector):
    errors=[]
    if contract.get('base_commit') != BASE or contract.get('observed_gameplay_source') != GAME:
        errors.append('exact baseline/gameplay source changed')
    if contract.get('latest_observed_gameplay_source')!=LATEST or contract.get('reported_build13_game_source')!=BUILD13_SOURCE:
        errors.append('latest cutoff and reported runtime source must remain distinct and exact')
    if contract.get('task_ids') != TASKS or contract.get('undefined_task_ids') != UNDEFINED:
        errors.append('70 authentic / 10 undefined task boundary changed')
    if contract.get('runtime_approval_allowed') is not False or contract.get('game_score') is not None:
        errors.append('planning must not approve or score gameplay')
    policy=contract.get('selected_policy',{})
    required_policy={'all_placed_equipment_destructible': True,
     'all_seven_pets_attack': True,
     'background_simulation': 'PAUSED',
     'boundary_reconstruction_level': 'PURCHASED_TIER',
     'cash_register_required': False,
     'companion_earned_level_preserved': True,
     'companion_replacement': 'ORDINARY_PAID_NEW_INSTANCE',
     'companions_can_die': True,
     'constructive_acquisition_proof_required': True,
     'counter_service': 'CUSTOMER_SELF_SERVICE_BULK_TYPED_STOCK_AND_SEPARATE_CASH',
     'death_and_ruin_cargo': 'PERSISTENT_TYPED_SALVAGE',
     'destroyed_equipment_rebuild_level': 1,
     'dynamic_progression_quotes': True,
     'earned_event_claim_survives_expiry': True,
     'event_progress': 'SERVER_VERIFIED_CONNECTION_REQUIRED',
     'far_condition': 'PLAYER_AND_ALL_ELIGIBLE_LIVING_DEFENDING_PETS_ARE_FAR',
     'field_pet_limit': 3,
     'field_survivor_escort_limit': 2,
     'free_companion_revive': False,
     'furnace_destruction': 'AFFECTED_CAMP_BLACKOUT_AND_LEVEL1_REBUILD',
     'launch_event_currency': None,
     'local_worker_limit_is_not_field_escort_limit': True,
     'offline_income': False,
     'ordinary_currency_id': 'money',
     'orientation': 'LANDSCAPE_BOTH_ROTATIONS',
     'owned_inventory_loss_on_down': 0,
     'permanent_camp_coordinate_immunity': False,
     'post_launch_features_added_to_release': False,
     'premium_currency_id': 'premium_gems',
     'provoked_survivor_retaliation': True,
     'repair_cost': 'ASSET_MATERIAL_TIER_MISSING_HP_AND_PROGRESSION',
     'spawn_counter_attendant': False,
     'survivor_logical_capacity': 'UNLIMITED_MIXED_SAME_AS_PLAYER',
     'survivor_self_defense_only': False,
     'survivors_may_hunt': True,
     'survivors_may_initiate_authorized_attacks': True}
    if policy != required_policy:
        errors.append('selected forward policy changed or omitted')
    reqs=contract.get('requirements',[])
    if [x.get('id') for x in reqs] != [f'CG{i:02}' for i in range(1,25)]:
        errors.append('24 exact gap identities required')
    for r in reqs:
        if not r.get('owner_tasks') or not set(r.get('owner_tasks',[])+r.get('consumer_tasks',[])) <= set(TASKS):
            errors.append(f"{r.get('id')}: invalid owner/task mapping")
        if not r.get('selected_action') or not r.get('acceptance_checks') or not r.get('classification'):
            errors.append(f"{r.get('id')}: missing concrete disposition/evidence")
        if r.get('implementation_evidence_status') != 'NOT_CERTIFIED_BY_THIS_AUDIT':
            errors.append(f"{r.get('id')}: false implementation completion")
        if r.get('id')=='CG24' and r.get('specification_status')!='SOURCE_NOT_FOUND_NOT_CLOSED':
            errors.append('undefined source gap cannot be marked closed')
    decisions=contract.get('decisions',[])
    if [d.get('id') for d in decisions] != [f'CD{i:02}' for i in range(1,13)]:
        errors.append('12 selected decision identities required')
    for d in decisions:
        if d.get('status') != 'SELECTED_FORWARD_DESIGN_IMPLEMENTATION_AND_TUNING_UNPROVED' or d.get('runtime_approval_allowed') is not False:
            errors.append(f"{d.get('id')}: selected design is not implementation approval")
        if not d.get('selected_behavior') or not d.get('remaining_evidence_or_tuning'):
            errors.append(f"{d.get('id')}: decision/evidence missing")
    dispositions=contract.get('prior_decision_dispositions',[])
    if [d.get('prior_id') for d in dispositions] != [f'D{i:02}' for i in range(1,6)]:
        errors.append('all five prior open decisions require explicit disposition')
    for d in dispositions:
        expected=[x['id'] for x in decisions if d.get('prior_id') in x.get('supersedes_prior_open_decisions',[])]
        if not expected or d.get('new_decisions') != expected or d.get('status')!='BEHAVIOR_SELECTED_NUMERIC_TUNING_AND_RUNTIME_PROOF_OPEN':
            errors.append('prior decision mapping/status is incomplete')
    pa=actors.get('all_pets_attack_contract',{})
    species=pa.get('species',[])
    if len(species)!=7 or {p.get('actor_id') for p in species}!=set(PETS):
        errors.append('seven exact attacking species required')
    if {x.get('id') for x in pa.get('rules',[])} != {f'PA{i:02}' for i in range(1,13)} or len(pa.get('rules',[]))!=12:
        errors.append('all 12 attack rules required')
    for p in species:
        pid=p.get('actor_id')
        token='aerial_attack' if pid=='owl' else 'attack'
        if p.get('attack_required') is not True or p.get('registered_attack_allowed') is not True or p.get('attack_profile')!=PETS.get(pid):
            errors.append(f'{pid}: support-only or incorrect attack rejected')
        if p.get('attack_capability_token')!=token or token not in p.get('registered_capabilities',[]):
            errors.append(f'{pid}: species attack capability missing')
        if not p.get('render_starting_points') or not p.get('mandatory_combat_scenario') or not p.get('additional_specialty_recommendation'):
            errors.append(f'{pid}: actual render/attack/specialty contract missing')
        if p.get('implementation_state')!='NOT_CERTIFIED_BY_THIS_AUDIT':
            errors.append(f'{pid}: unproved runtime cannot pass')
    if actors.get('runtime_approval_allowed') is not False or actors.get('runtime_score') is not None:
        errors.append('actor contract cannot certify motion or gameplay')
    goals=economy.get('progression_goals',[])
    if [g.get('level') for g in goals]!=list(range(1,101)) or [g.get('level_id') for g in goals]!=[f't12.level.{i:03}' for i in range(1,101)]:
        errors.append('100 ordered real level identities required')
    if len({g.get('outcome') for g in goals})!=100 or any(not g.get('title') or not g.get('outcome') for g in goals):
        errors.append('100 distinct authored outcomes required')
    for g in goals:
        if g.get('content_owner') not in TASKS or g.get('status')!='AUTHORED_DESIGN_FOR_CURRENT_PLAN_FREEZE_NOT_RUNTIME_COMPLETION':
            errors.append(f"level {g.get('level')}: owner/status invalid")
        if g.get('exact_producer_receipt_binding')!='TO_BE_BOUND_BY_IMPLEMENTING_OWNER_NOT_INVENTED':
            errors.append('planning cannot invent completed producer receipt')
    regions=economy.get('region_designs',[])
    if len(regions)!=10 or len({r.get('id') for r in regions})!=10 or [r.get('range') for r in regions]!=[[i,i+9] for i in range(1,101,10)]:
        errors.append('ten authentic region bands required')
    if any(economy.get(k) is not False for k in ('runtime_edited','runtime_tested','runtime_approved')):
        errors.append('economy design must not claim runtime work or tests')
    values=economy.get('resource_value_decisions',[])
    value_ids={r.get('id') for r in values}
    required={'wood','stone','metal','coal','steel','slate','planks','blocks','fuel','meat','meal','fish','cooked_fish','wheat','bread','hide','fur','money','premium_gems','cargo','relay_component','species_cuts_and_other_food_art'}
    if len(values)!=22 or value_ids!=required:
        errors.append('bounded source/product/currency/concept inventory incomplete')
    for r in values:
        if any(not r.get(f) for f in ('disposition','source','primary_use','visible_payoff','surplus')):
            errors.append(f"{r.get('id')}: resource purpose/lifecycle missing")
    concept_uses=[]
    for r in values:
        concept_uses.extend([r.get('id')]+r.get('aliases',[])+r.get('art_aliases',[])+r.get('ids',[]))
    if any(concept_uses.count(x)!=1 for x in RENDER_CONCEPTS):
        errors.append('all 33 preserved resource render concepts require one explicit disposition')
    pet_unlocks=economy.get('pet_free_availability',[])
    if len(pet_unlocks)!=7 or {p.get('pet') for p in pet_unlocks}!=set(PETS) or any(p.get('premium_required') is not False or p.get('existing_ownership_preserved') is not True for p in pet_unlocks):
        errors.append('all seven free availability/ownership dispositions required')
    if economy.get('undefined_tasks')!=UNDEFINED:
        errors.append('economy cannot invent T71–T80')
    roster=economy.get('enemy_roster_recommendation',[])
    roster_ids={'hostile-wolf','raider','ice-brute','polar-bear','rival-rifleman','giant-elk','horned-snow-beast','spined-frostbeast',
        'tundra-stag','rival-leader','hooded-swarmer','hooded-siege-boss','shield-raider','harpoon-hunter','powder-sapper',
        'frost-stalker','tusk-boar','musk-ox-rampager','frostwing-raptor','armored-ram-sled'}
    if len(roster)!=20 or {r.get('design_key') for r in roster}!=roster_ids:
        errors.append('all 20 enemy render dispositions required')
    selected={r.get('design_key') for r in roster if r.get('disposition')=='SELECTED_LAUNCH_HOSTILE_FOR_FORWARD_IMPLEMENTATION'}
    if selected!={'hostile-wolf','raider','ice-brute','rival-rifleman','hooded-swarmer','hooded-siege-boss'}:
        errors.append('selected six hostile roles changed or omitted')
    prey={r.get('design_key') for r in roster if r.get('disposition')=='SELECTED_HUNTING_SOURCE_FOR_FORWARD_IMPLEMENTATION'}
    if prey!={'tundra-stag'} or any(r.get('runtime_activation_claimed') is not False for r in roster):
        errors.append('hunt/reserve identity or runtime boundary changed')
    weapons=economy.get('weapon_availability',[])
    if len(weapons)!=2 or {w.get('family') for w in weapons}!={'axe','spear'} or any(w.get('runtime_handling_approval') is not False for w in weapons):
        errors.append('two contextual weapon families required without fake runtime approval')
    tx=transactions.get('rows',[])
    if len(tx)!=12 or {t.get('id') for t in tx}!=TRANSACTIONS:
        errors.append('all twelve transaction boundaries required')
    for t in tx:
        if any(not t.get(k) for k in ('before_commit','commit_authority','after_commit','interruption_recovery','clock')) or t.get('runtime_test_status')!='NOT_RUN':
            errors.append(f"{t.get('id')}: boundary is incomplete or falsely tested")
    if transactions.get('runtime_approval_allowed') is not False:
        errors.append('transaction matrix cannot certify persistence')
    if selector.get('selected_branch')!='trial/world-one-expansion-2026-11-26' or selector.get('observed_head')!=LATEST or selector.get('audited_baseline_head')!=GAME or selector.get('reported_gameplay_source_commit')!=BUILD13_SOURCE or selector.get('project')!='HavenlineLevel1/project.godot' or selector.get('main_scene')!='res://field_opening.tscn':
        errors.append('current-source selector mismatch')
    if any(selector.get(k) is not False for k in ('runtime_approval_allowed','ownership_reassignment_allowed','gameplay_merge_performed','workflow_activation_allowed')):
        errors.append('source selection cannot approve, reassign, merge or activate')
    return errors


def validate_latest_source(note):
    errors=[]
    if (note.get('planning_main_baseline')!=BASE or note.get('prior_audited_gameplay_source')!=GAME or
        note.get('fixed_review_cutoff')!=LATEST or note.get('reviewed_gameplay_source')!=BUILD13_SOURCE):
        errors.append('latest source note confuses baseline, game source or evidence cutoff')
    if note.get('status')!='SOURCE_AND_RECEIPT_METADATA_INSPECTED_NOT_RUNTIME_APPROVED':
        errors.append('latest note is source/receipt evidence only')
    approvals=note.get('approval',{})
    if any(approvals.get(k) is not False for k in ('runtime_approved','motion_approved','visual_approved','device_approved','task_closure_approved')):
        errors.append('reported source evidence cannot certify game/motion/device/task closure')
    report=note.get('reported_build13',{})
    if report.get('source')!=BUILD13_SOURCE or report.get('all_values_are_reported_not_reexecuted') is not True:
        errors.append('reported Build13 tests must not become tests run by this audit')
    if note.get('reference_custody',{}).get('media_downloaded_or_played_back_by_this_audit') is not False:
        errors.append('metadata inventory must not claim media playback')
    if len(note.get('source_file_pairs',[]))!=27 or len(note.get('receipt_file_pins',[]))!=16:
        errors.append('bounded latest source/receipt universe incomplete')
    binding=note.get('code_to_cutoff_binding',{})
    if binding.get('identical') is not True or binding.get('source_tree_at_2654')!=binding.get('source_tree_at_2f46'):
        errors.append('reported game/evidence source tree binding incomplete')
    return errors


def task_row(task_id, root=ROOT):
    task_id=task_id.upper()
    if task_id not in TASKS: raise ValueError(f'{task_id} has no authentic definition')
    c=read(root,DOCS+'WHOLE_GAME_COMPLETENESS.json')
    task=read(root,DOCS+'DEPENDENCY_GRAPH.json')['tasks'][task_id]
    relevant=[r for r in c['requirements'] if task_id in r['owner_tasks']+r['consumer_tasks']]
    decision_ids=sorted({d for r in relevant for d in r['decision_ids']} | {d['id'] for d in c['decisions'] if task_id in d['owner_tasks']})
    return {'task_id':task_id,'name':task['name'],'dependencies_preserved':task['dependencies'],
            'owned_gap_ids':[r['id'] for r in relevant if task_id in r['owner_tasks']],
            'consumer_gap_ids':[r['id'] for r in relevant if task_id not in r['owner_tasks']],
            'decision_ids':decision_ids,'runtime_activation_allowed':False,'runtime_approval_allowed':False}


def task_section(task_id, root=ROOT):
    data=load(root)
    errors=validate_data(*data)
    if errors: raise ValueError('Invalid completeness contract: '+'; '.join(errors))
    row=task_row(task_id,root)
    c=data[0]
    lines=['\n## Current whole-game decisions and gap closure\n',
      'Read `Docs/Production/COMPLETENESS_STANDARD.md`, `WHOLE_GAME_COMPLETENESS.json` and `CURRENT_GAMEPLAY_SOURCE.json`. Latest user correction U3 and GAMEPLAY_RULES_CONTRACT.json govern current CD/GD choices; prior free-revival, free-repair and permanent-sanctuary choices are historical. Numeric tuning and actual game evidence remain open. These responsibilities are not new dependency edges or task activation, and preserve frozen historical scope.\n']
    selected=set(row['owned_gap_ids']+row['consumer_gap_ids'])
    for r in c['requirements']:
        if r['id'] in selected:
            role='owner' if r['id'] in row['owned_gap_ids'] else 'consumer'
            lines.append(f"- **{r['id']} — {r['title']} ({role}):** {r['selected_action']} Required evidence: {'; '.join(r['acceptance_checks'])}")
    lines.extend(['','Applicable selected decisions: '+', '.join(row['decision_ids'])+'.',
      'Use the revised 100 authored outcomes, seven attack/specialty/render bindings and twelve transaction boundaries in `GameplayRules/2026-11-27/`. All gameplay scenarios remain unrun by this audit. Current reference >=9.9 and stronger exact-10 visual requirements still apply.',''])
    return '\n'.join(lines)


def crosswalk(root=ROOT):
    return {'schema_version':1,'base_commit':BASE,'runtime_approval_allowed':False,
      'rows':[task_row(t,root) for t in TASKS]+[{'task_id':t,'status':'SOURCE_NOT_FOUND','runtime_activation_allowed':False,'runtime_approval_allowed':False} for t in UNDEFINED]}


def crosswalk_markdown(root=ROOT):
    lines=['# Havenline T01–T80 completeness crosswalk','','70 authentic task definitions;10 undefined requested IDs. IDs below link to the [24-row contract and 12 current selected decisions](../../WHOLE_GAME_COMPLETENESS.json). Responsibilities preserve existing dependencies, ownership and frozen scope. The earlier [reference/render map](../../ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md) and [gameplay-depth map](../../GameplayDepth/2026-11-27/TASK_GAMEPLAY_DEPTH_T01_T80.md) remain binding.','','| Task | Preserved task name | Owns gap rows | Consumes gap rows | Selected decisions |','|---|---|---|---|---|']
    for row in crosswalk(root)['rows']:
        if row.get('status')=='SOURCE_NOT_FOUND':
            lines.append(f"| {row['task_id']} | SOURCE_NOT_FOUND; no scope invented | — | — | — |")
        else:
            lines.append('| '+ ' | '.join([row['task_id'],row['name'],', '.join(row['owned_gap_ids']) or '—',', '.join(row['consumer_gap_ids']) or '—',', '.join(row['decision_ids']) or '—'])+' |')
    lines.extend(['','Full per-task projection: `python3 tools/havenline/production/completeness.py task T23`. Future `task_packet.py` output includes it automatically. No task is activated or approved by this table.',''])
    return '\n'.join(lines)


def validate(root=ROOT):
    errors=validate_data(*load(root))
    latest=read(root,PACKAGE+'LATEST_SOURCE_DELTA.json')
    errors.extend(validate_latest_source(latest))
    sources=read(root,PACKAGE+'SOURCE_BINDINGS.json')['sources']
    identity='\n'.join(sorted(x['commit']+':'+x['path'] for x in sources)).encode()
    if hashlib.sha256(identity).hexdigest()!=SOURCE_UNIVERSE_SHA256:
        errors.append('exact source universe omitted, duplicated or changed')
    verified=0
    for s in sources:
        try:
            data=source_bytes(root,s['commit'],s['path'])
            actual_blob=subprocess.check_output(['git','hash-object','--stdin'],input=data,cwd=root).decode().strip()
            if hashlib.sha256(data).hexdigest()!=s['sha256'] or len(data)!=s['bytes'] or actual_blob!=s['git_blob_sha']:
                errors.append('source hash/length/blob mismatch: '+s['path'])
            else: verified+=1
        except (OSError,subprocess.CalledProcessError) as exc: errors.append('source unreadable: '+str(exc))
    for path in ('DEPENDENCY_GRAPH.json','WORKSTREAM_REGISTRY.json','PATH_OWNERSHIP.json','APPROVAL_INVALIDATIONS.json','REFERENCE_ACCEPTANCE_POLICY.json','POST_LAUNCH_ROADMAP.md'):
        rel=DOCS+path
        if (pathlib.Path(root)/rel).read_bytes()!=source_bytes(root,BASE,rel): errors.append('protected authority changed: '+path)
    c,a,e,t,s=load(root)
    source_index={(x['commit'],x['path']):x for x in sources}
    for key,commit in [('source_tree_at_2654',BUILD13_SOURCE),('source_tree_at_2f46',LATEST)]:
        actual=subprocess.check_output(['git','rev-parse',commit+':HavenlineLevel1'],cwd=root).decode().strip()
        if latest['code_to_cutoff_binding'].get(key)!=actual:errors.append('actual latest game tree binding mismatch')
    project=s['project_source']
    if project!=source_index.get((LATEST,'HavenlineLevel1/project.godot')):
        errors.append('selector project source hash is stale or inconsistent')
    render_rows=[(r['render_pin'],r['path'],r['sha256']) for r in e['enemy_roster_recommendation']]
    for pet in a['all_pets_attack_contract']['species']:
        render_rows.extend(('a868ae89cdf2f120b478aa0a48fff35e09cc465c',r['path'],r['sha256']) for r in pet['render_starting_points'])
    for commit,path,digest in render_rows:
        if source_index.get((commit,path),{}).get('sha256')!=digest:
            errors.append('declared render does not match verified source: '+path)
    original=json.loads(source_bytes(root,BASE,DOCS+'T12/LEVEL_1_100_MATRIX.json'))
    original_rows=original.get('levels',original.get('rows',[]))
    if not original_rows: errors.append('T12 source structure unavailable')
    else:
        keyed={x.get('level',x.get('level_number')):x for x in original_rows}
        for goal in e['progression_goals']:
            prior=keyed.get(goal['level'],{})
            for old,new in {'id':'level_id','band':'band','owner':'content_owner','requires':'requires',
                            'role':'role','visible':'visible_hook_required','major':'major_milestone'}.items():
                if old not in prior or goal.get(new)!=prior[old]:
                    errors.append(f"T12 preserved {old} changed at {goal['level']}")
    if read(root,CURRENT_PACKAGE+'TASK_COMPLETENESS_T01_T80.json')!=crosswalk(root): errors.append('machine task map stale')
    if (pathlib.Path(root)/CURRENT_PACKAGE/'TASK_COMPLETENESS_T01_T80.md').read_text()!=crosswalk_markdown(root): errors.append('readable task map stale')
    for rel in c['detail_files'].values():
        if not (pathlib.Path(root)/rel).is_file(): errors.append('missing detail '+rel)
    from device_matrix import validate_layout_definition
    errors.extend(validate_layout_definition(read(root,DOCS+'DEVICE_LAYOUT_MATRIX.json')))
    return {'passed':not errors,'scope':'Bounded plan/source/task-projection validation only','runtime_approval_allowed':False,
       'runtime_tested':False,'game_score':None,'requirements':24,'selected_decisions':12,'defined_tasks':70,'undefined_tasks':10,
       'authored_level_outcomes':100,'pet_species':7,'transaction_boundaries':12,
       'preserved_deep_audit_source':GAME,'latest_evidence_cutoff':LATEST,'reported_build13_game_source':BUILD13_SOURCE,
       'sources_verified':verified,'sources_required':len(sources),'errors':errors}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['check','task','crosswalk','crosswalk-markdown'])
    p.add_argument('task_id',nargs='?')
    args=p.parse_args()
    if args.command=='task':
        if not args.task_id: p.error('task requires an authentic T01–T70 ID')
        print(task_section(args.task_id),end='')
    elif args.command=='crosswalk': print(json.dumps(crosswalk(),indent=2))
    elif args.command=='crosswalk-markdown': print(crosswalk_markdown(),end='')
    else:
        result=validate(); print(json.dumps(result,indent=2)); raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__': main()
