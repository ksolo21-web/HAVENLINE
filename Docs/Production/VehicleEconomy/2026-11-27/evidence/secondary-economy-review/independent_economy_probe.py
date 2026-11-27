#!/usr/bin/env python3
"""Independent executable simulation and hostile-data probes; never changes inputs."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
E = json.loads((ROOT / 'RESOURCE_CHAINS.json').read_text())
W = json.loads((ROOT / 'WORLD_VEHICLES.json').read_text())
SOURCE_HASHES = {name: sha256((ROOT/name).read_bytes()).hexdigest() for name in ['RESOURCE_CHAINS.json','WORLD_VEHICLES.json','verify_economy.py']}
checks = []

def check(name, value, evidence):
    checks.append({'name':name,'passed':bool(value),'evidence':evidence})

def units(value):
    if type(value) is not str or not value or value[0] == '0' or not value.isascii() or not value.isdigit():
        raise ValueError('Noncanonical positive quantity')
    return int(value)

class Simulator:
    """Build actual prerequisites and consume sequential batches with surplus."""
    def __init__(self, economy):
        self.e = economy
        self.stock = Counter()
        self.gathered = Counter()
        self.batches = Counter()
        self.producers = set()
        self.raw = set(economy['bootstrap']['initial_manually_reachable_raw'])
        self.recipes = {next(iter(r['output'])): r for r in economy['recipes']}
        self.log = []

    def ensure(self, item, amount, trace=()):
        if self.stock[item] >= amount:
            return
        shortage = amount - self.stock[item]
        if item in trace:
            raise ValueError('Recursive production dependency: '+repr(trace+(item,)))
        if item in self.raw:
            self.stock[item] += shortage
            self.gathered[item] += shortage
            return
        if item not in self.recipes:
            raise ValueError('No reachable source: '+item)
        recipe = self.recipes[item]
        if recipe['producer'] not in self.producers:
            raise ValueError('Producer not yet built: '+recipe['producer'])
        if recipe['vehicle_fuel_required']:
            raise ValueError('Unspecified vehicle fuel required for bootstrap recipe')
        output = units(recipe['output'][item])
        batch_count = (shortage+output-1)//output
        for raw, qty in recipe['inputs'].items():
            self.ensure(raw, units(qty)*batch_count, trace+(item,))
            # Reserve this exact input before obtaining a sibling input whose
            # recipe could otherwise consume the already-promised stock.
            self.stock[raw] -= units(qty)*batch_count
            assert self.stock[raw] >= 0
        self.stock[item] += output*batch_count
        self.batches[recipe['id']] += batch_count

    def pay(self, bill):
        # Gather each line into protected project escrow; no promised stock may
        # be reused as feedstock while obtaining another line of the same bill.
        escrow=Counter()
        for item, qty in bill.items():
            self.ensure(item,units(qty))
            self.stock[item] -= units(qty)
            escrow[item] += units(qty)
            assert self.stock[item] >= 0
        assert dict(escrow)=={k:units(v) for k,v in bill.items()}

    def build_producer(self, producer):
        assert producer['id'] not in self.producers
        assert set(producer['requires_producers']) <= self.producers
        assert not producer['construction_vehicle_fuel_required']
        assert not producer['operation_vehicle_fuel_required']
        self.pay(producer['construction_bill'])
        self.producers.add(producer['id'])
        self.raw.update(producer['unlocks_resource_sources'])
        self.log.append({'producer':producer['id'],'raw_spent_to_date':dict(self.gathered),'retained_surplus':{k:v for k,v in self.stock.items() if v}})

def author_verify(economy, worlds):
    with TemporaryDirectory(prefix='havenline-economy-probe-') as temp:
        p = Path(temp)
        (p/'RESOURCE_CHAINS.json').write_text(json.dumps(economy))
        (p/'WORLD_VEHICLES.json').write_text(json.dumps(worlds))
        (p/'verify_economy.py').write_bytes((ROOT/'verify_economy.py').read_bytes())
        run = subprocess.run([sys.executable,str(p/'verify_economy.py')],capture_output=True,text=True,timeout=10)
        result_path=p/'evidence/economy_checks.json'
        result=json.loads(result_path.read_text()) if result_path.exists() else None
        return {'accepted':run.returncode==0 and bool(result and result['passed']),'exit_code':run.returncode,'stdout':run.stdout[-2000:],'stderr':run.stderr[-2000:],'result':result}

baseline = author_verify(E,W)
check('author_baseline_runs',baseline['accepted'],{'checks':baseline['result']['checks_passed']})

sim = Simulator(E)
for producer in E['producers_in_bootstrap_order']:
    sim.build_producer(producer)
check('ordered_bootstrap_actual_consumption',len(sim.producers)==9,sim.log)
profiles = {p['id']:p for p in E['build_profiles']}
sim.pay(profiles['garage_v2']['bill'])
sim.pay(profiles['snow_truck_v2']['bill'])
expected={k:int(v) for k,v in baseline['result']['new_producers_plus_garage_plus_truck_expansion']['raw_inputs'].items()}
check('independent_sequential_total_matches_report',dict(sim.gathered)==expected,{'actual':dict(sim.gathered),'expected':expected,'surplus':{k:v for k,v in sim.stock.items() if v},'batches':dict(sim.batches)})

for profile in E['build_profiles']:
    solo=Simulator(E)
    solo.producers={p['id'] for p in E['producers_in_bootstrap_order']}
    solo.raw.add('crude_oil')
    solo.pay(profile['bill'])
    report={k:int(v) for k,v in baseline['result']['profile_expansions'][profile['id']]['raw_inputs'].items()}
    check('sequential_profile_'+profile['id'],dict(solo.gathered)==report,dict(solo.gathered))

check('bundle_display_is_not_mass_or_ledger_multiplication',E['unit_contract']['legacy_raw_display_units_per_ledger_count']=='10' and E['recipes'][0]['inputs']=={'wood':'1'} and E['recipes'][0]['output']=={'planks':'1'},'216 wood ledger bundles display2160 raw units; no2160 ledger debit; processed count remains1 per existing recipe.')
check('source_unlock_order_excludes_oil_without_pump','crude_oil' not in E['bootstrap']['initial_manually_reachable_raw'] and any(p['id']=='manual_oil_pump' and p['site']=='outside_camp_reachable_manual_oil_site' and 'crude_oil' in p['unlocks_resource_sources'] for p in E['producers_in_bootstrap_order']),'Current source contract keeps crude locked to reachable outside manual pump.')
check('current_world_task_binding',all(v['authentic_task']=='T'+str(42+v['world']) for v in W['vehicles']),[(v['world'],v['authentic_task']) for v in W['vehicles']])
check('current_finite_project_not_currency',all('relay_component' not in p['bill'] for p in E['build_profiles']) and 'relay_component' not in {r['id'] for r in E['resources']},'Portable serialized relay module remains distinct finite project custody, not an ordinary material input or currency; its serial overlay and paid replacement are future world integration.')

def mutate(kind):
    e,w=deepcopy(E),deepcopy(W)
    if kind=='duplicate_recipe_id': e['recipes'][3]['id']=e['recipes'][2]['id']
    elif kind=='duplicate_producer_id': e['producers_in_bootstrap_order'].append(deepcopy(e['producers_in_bootstrap_order'][-1]))
    elif kind=='fuel_required_refinery_recipe': e['recipes'][-1]['vehicle_fuel_required']=True
    elif kind=='oil_pump_inside_camp': next(p for p in e['producers_in_bootstrap_order'] if p['id']=='manual_oil_pump')['site']='inside_camp'
    elif kind=='duplicate_vehicle_id': w['vehicles'][1]['vehicle_id']=w['vehicles'][0]['vehicle_id']
    elif kind=='wrong_authentic_world_task': w['vehicles'][-1]['authentic_task']='T44'
    elif kind=='vehicle_profile_misclassified_no_tank':
        p=next(p for p in e['build_profiles'] if p['id']=='reef_salvager_v1')
        p['kind']='garage'
        p['initial_tank_fuel_units']='0'
    elif kind=='zero_output': e['recipes'][-1]['output']['fuel']='0'
    elif kind=='negative_input': e['recipes'][2]['inputs']['metal']='-1'
    elif kind=='unfunded_initial_tank': next(p for p in e['build_profiles'] if p['id']=='snow_truck_v2')['initial_tank_fuel_units']='61'
    elif kind=='producer_self_output_cycle': next(p for p in e['producers_in_bootstrap_order'] if p['id']=='coal_smelter')['construction_bill']['iron_bars']='2'
    else: raise ValueError(kind)
    return e,w

mutations=[]
for name in ['duplicate_recipe_id','duplicate_producer_id','fuel_required_refinery_recipe','oil_pump_inside_camp','duplicate_vehicle_id','wrong_authentic_world_task','vehicle_profile_misclassified_no_tank','zero_output','negative_input','unfunded_initial_tank','producer_self_output_cycle']:
    e,w=mutate(name)
    result=author_verify(e,w)
    mutations.append({'name':name,'should_reject':True,'rejected':not result['accepted'],'exit_code':result['exit_code'],'diagnostic':result['stderr'] or result['stdout']})

large_e=deepcopy(E)
next(p for p in large_e['build_profiles'] if p['id']=='snow_truck_v2')['bill']['sheet_metal']=str(2**64+2)
large=author_verify(large_e,W)
large_sim=Simulator(large_e)
large_sim.producers={p['id'] for p in large_e['producers_in_bootstrap_order']}
large_sim.raw.add('crude_oil')
large_sim.pay(next(p for p in large_e['build_profiles'] if p['id']=='snow_truck_v2')['bill'])
large_result={k:int(v) for k,v in large['result']['profile_expansions']['snow_truck_v2']['raw_inputs'].items()}
check('integer_expansion_above_2_to_64',large['accepted'] and large_result==dict(large_sim.gathered),{'raw':large_result})

record={'scope':'Independent catalogue/batch/validator review; no scene/navigation/balance/media approval','input_sha256':SOURCE_HASHES,'current_data_checks':checks,'current_data_passed':all(x['passed'] for x in checks),'mutation_results':mutations,'mutation_rejections_passed':sum(x['rejected'] for x in mutations),'mutation_rejections_required':len(mutations),'unrejected_invalid_cases':[x['name'] for x in mutations if not x['rejected']],'notes':['Current material graph is constructively reachable under its stated renewable/manual-source assumptions. Actual world route/source quantities remain integration gates.','Legacy partially paid plot escrow is explicitly outside native full-bill component; migration prose is a requirement, not implementation proof.','World10 forward design now selects portable serialized project cargo, ordinary exterior loss, paid same-objective replacement and one-active/one-install proofs. This supersedes the fixed-site proposal; actual replacement bill, serial custody and runtime lifecycle remain unimplemented and unapproved. Existing-save identity requires explicit preservation.']}
filename=sys.argv[1] if len(sys.argv)>1 else 'secondary-economy-review-r1.json'
(HERE/filename).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'report':str(HERE/filename),'current_data_checks_passed':sum(x['passed'] for x in checks),'current_data_checks_required':len(checks),'invalid_cases_rejected':record['mutation_rejections_passed'],'invalid_cases_total':len(mutations),'unrejected':record['unrejected_invalid_cases']},indent=2))
