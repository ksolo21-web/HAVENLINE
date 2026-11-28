"""Bounded documentation consistency checks; never a runtime/game acceptance gate."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[4]
BASE='0a7587cf3e89397a760be4b4c606c54ad09d0e02'
EVIDENCE=Path(__file__).resolve().parent
def source(path):
    return subprocess.run(['git','show',BASE+':'+path],cwd=ROOT,capture_output=True,check=True).stdout
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
plan_path=ROOT/'Docs/Production/LIVING_WORLD_UI_PLAN.json'
doc_path=ROOT/'Docs/Production/LIVING_WORLD_UI_PLAN.md'
p=json.loads(plan_path.read_text())
graph=json.loads(source('Docs/Production/DEPENDENCY_GRAPH.json'))['tasks']
economy=json.loads(source('Docs/Production/Completeness/2026-11-27/PROGRESSION_ECONOMY_GAPS.json'))
art={r['design_key']:r for r in economy['enemy_roster_recommendation']}
checks=[]
def check(name,condition):
    if not condition:raise AssertionError(name)
    checks.append(name)
check('30 unique requirement identities',len(p['requirements'])==30==len({r['id'] for r in p['requirements']}))
check('Every requirement maps to real canonical tasks',all(r['tasks'] and all(t in graph for t in r['tasks']) for r in p['requirements']))
used={t for r in p['requirements'] for t in r['tasks']}
check('34 mapped tasks, no invented parent IDs',len(used)==34 and used=={t['task_id'] for t in p['task_map']} and not p['world_scope']['new_parent_task_ids'])
check('Canonical names/dependencies/states retained in crosswalk',all(t['recorded_title']==graph[t['task_id']]['name'] and t['recorded_dependencies']==graph[t['task_id']]['dependencies'] and t['historical_state']==graph[t['task_id']]['status'] for t in p['task_map']))
check('Every requirement appears in readable plan',all(r['id']+' — '+r['title'] in doc_path.read_text() for r in p['requirements']))
check('Every runtime obligation remains untested',all(r['status']=='UNTESTED_FOR_NEW_RUNTIME_SCOPE' for r in p['requirements']) and p['new_scope_runtime_approval'] is False)
expected={r['design_key'] for r in art.values() if r['disposition']=='SELECTED_LAUNCH_HOSTILE_FOR_FORWARD_IMPLEMENTATION'}
check('All six existing hostile families retained',len(expected)==6 and set(p['existing_hostile_keys'])==expected)
new=p['added_hostile_candidates'];keys={e['design_key'] for e in new}
check('Eight distinct additional reserve roles',len(new)==8==len(keys) and not keys&expected and all(e['existing_disposition']=='EXPLICIT_RENDER_RESERVE_NOT_AUTOMATIC_LAUNCH' for e in new))
check('Exact reserve art identities retained',all(all(e['source'][k]==art[e['design_key']][k] for k in ['render_pin','path','sha256','source_render_id']) for e in new))
prey=p['passive_prey'];preykeys={x['design_key'] for x in prey}
check('Six passive prey, five new asset gaps',len(prey)==6==len(preykeys) and sum(x['source'] is None for x in prey)==5 and 'tundra-stag' in preykeys)
check('Prey never hostile or retaliatory at night',all(x['category']=='NONAGGRESSIVE_HUNTABLE_PREY' and not x['initiates_aggression'] and not x['becomes_hostile_at_night'] and not x['attack_retaliation'] for x in prey))
check('Prey and hostile identities separated',not preykeys&(keys|expected))
check('Meat family conserved, no fixed new yields',all(x['resource_family']=='meat' and x['exact_yield'] is None for x in prey))
check('Siege machine is not meat',next(e for e in new if e['design_key']=='armored-ram-sled')['meat_source'] is False)
allowed={'dawn','day','dusk','night'}
check('All authored phase memberships valid',all(set(x['proposed_spawn_phases'])<=allowed and x['proposed_spawn_phases'] for x in new+prey))
for label,items in [('prey',prey),('enemies',new)]:
    day={x['design_key'] for x in items if 'day' in x['proposed_spawn_phases']}
    night={x['design_key'] for x in items if 'night' in x['proposed_spawn_phases']}
    check('Different day/night '+label+' membership',bool(day-night) and bool(night-day))
check('Food candidates in both main phases',all(any(phase in x['proposed_spawn_phases'] for x in prey) for phase in ['day','night']))
check('All seven useful attacking pet species preserved',set(p['invariants']['pets'])=={'guardian_dog','gray_wolf','fox','owl','male_lion','white_tiger','brown_bear'} and p['invariants']['all_pets_attack_and_have_specialties'] and p['invariants']['multiple_pets_and_survivors'] and not p['invariants']['new_slot_caps'])
check('Latest casualties and 300-second warning retained',p['invariants']['latest_casualty_repurchase_policy_preserved'] and p['invariants']['scheduled_raid_warning_active_seconds']==300 and not p['invariants']['raid_frequency_selected_here'])
check('Theme independent of active-play world time',p['invariants']['theme_does_not_set_world_phase'] and p['invariants']['ordinary_simulation_pauses_outside_active_play'])
check('Latest owner allows visible joystick',p['invariants']['visible_joystick_allowed'] and 'it can be visible' in p['authority']['latest_control_correction'])
check('Touch-anywhere activation independent of joystick position',p['invariants']['touch_anywhere_in_unclaimed_gameplay_required'] and p['invariants']['movement_must_start_on_joystick'] is False and 'far outside the displayed joystick' in next(r for r in p['requirements'] if r['id']=='UI02')['acceptance'])
check('Superseded visibility prohibition is not an active requirement',all('No fixed or pop-up joystick' not in r['requirement'] and 'with no visible joystick' not in r['requirement'] for r in p['requirements']))
check('10x50 and World1 first retained',p['world_scope']['worlds']==10 and p['world_scope']['local_levels_per_world']==50 and p['world_scope']['world1_first'] and not p['world_scope']['all_actors_in_level1'])
stages={x['id']:x for x in p['milestones']}
seen=set()
for stage in p['milestones']:
    check('Work-stage dependencies resolve: '+stage['id'],set(stage['depends_on'])<=seen and all(t in graph for t in stage['tasks']))
    seen.add(stage['id'])
consumers=p['forward_consumer_reconciliation']
check('Corrected prose and pending runtime consumers have distinct statuses',len(consumers)>=10 and consumers[0]['path']=='Docs/Production/HAVENLINE_BUILD_PLAN_V2.md' and consumers[0]['status']=='DOCUMENTATION_UPDATED_RUNTIME_CONSUMPTION_PENDING' and all(x['status']=='DOCUMENTED_FOLLOWUP_NOT_IMPLEMENTED' for x in consumers[1:]))
for path in ['Docs/Production/DEPENDENCY_GRAPH.json','Docs/Production/WORKSTREAM_REGISTRY.json','Docs/Production/CURRENT_GAMEPLAY_SOURCE.json','Docs/Production/WHOLE_GAME_COMPLETENESS.json','Docs/Production/PET_COMBOS_MAP_DISPLAY.json','Docs/Production/PET_COMBOS_MAP_DISPLAY.md']:
    result=subprocess.run(['git','diff','--quiet',BASE,'--',path],cwd=ROOT)
    check('Unchanged historical/source contract: '+path,result.returncode==0)
bindings_path=EVIDENCE/'SOURCE_BINDINGS.json'
bindings=json.loads(bindings_path.read_text())
check('Source bindings exist and parse',bool(bindings))
input_audit=EVIDENCE/'CURRENT_INPUT_SOURCE_AUDIT.json'
input_observation=json.loads(input_audit.read_text())
check('Current input source audit is bound without runtime approval',sha(input_audit)==bindings['current_input_source_audit']['sha256'] and input_observation['observed_commit']==p['current_input_source_observation']['commit'] and input_observation['runtime_executed'] is False and input_observation['tests_executed'] is False and input_observation['apk_correspondence_verified'] is False)
tracked=subprocess.run(['git','diff','--name-only',BASE],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
untracked=subprocess.run(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
allowed_existing={'AGENTS.md','BUILD_GAME.md','REPOSITORY_INDEX.md','Docs/Production/HAVENLINE_BUILD_PLAN_V2.md','Docs/Production/COMPLETENESS_STANDARD.md'}
def allowed_file(f):
    return f in allowed_existing or f in {'Docs/Production/LIVING_WORLD_UI_PLAN.md','Docs/Production/LIVING_WORLD_UI_PLAN.json'} or f.startswith('Docs/Production/LivingWorldUI/2026-11-28/')
check('Only bounded documentation/evidence changes',all(allowed_file(f) for f in tracked+untracked))
result={'status':'PASS_DOCUMENT_CONSISTENCY_ONLY','base_commit':BASE,'checks_passed':len(checks),'checks':checks,'requirements':30,'mapped_existing_tasks':34,'added_enemy_role_candidates':8,'passive_prey_entries':6,'new_prey_asset_requirements':5,'changed_or_added_paths':sorted(set(tracked+untracked)),'bindings':{'plan_json_sha256':sha(plan_path),'plan_md_sha256':sha(doc_path),'source_bindings_sha256':sha(bindings_path)},'runtime_tested':False,'runtime_approval':False,'task_state_promotions':0,'dependency_graph_changes':0,'workflow_changes':0}
(EVIDENCE/'VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in {'checks','changed_or_added_paths'}},indent=2))
