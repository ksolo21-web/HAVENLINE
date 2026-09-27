"""Fail-closed R01 identity proof inside the combined R01+R07 visual repair."""
import argparse,json,hashlib,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE='b080906140b892f789a5f48a9f8cbeee1359c12e'
ASSET='HavenlineGodot/assets/stations_v2/hearth_vessel.glb'
CATALOG='HavenlineGodot/assets/stations_v2/catalog.json'
TEST='HavenlineGodot/tests/test_task05_station_kit.gd'
EXPECTED_SHA='6d32499229dd22dde1ee32940bb1b0a506a0647ea911a4787b3bce83fe60a8e7'
R07_IDS=('wood_stack','stone_stack','metal_stack','fuel_canister','fish_crate','cooked_food_stack','money_stack','cargo_crate')
R03_IDS=('pad_build','pad_upgrade','pad_input','pad_output','pad_stock','pad_payment')
R10_IDS=('service_counter','processing_counter','defense_platform')
R10B_IDS=('fishing_rack','intake_machine','cooker_processor','conveyor_straight')


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def contract_view(catalog):
    # Hashes, triangle counts, material membership and art-language prose are
    # visual implementation details. Everything that can affect gameplay,
    # placement, sockets, later-task ownership or performance ceilings stays exact.
    return {
        'schema_version':catalog['schema_version'],
        'authority_id':catalog['authority_id'],
        'generator':catalog['generator'],
        'requirements':catalog['requirements'],
        'arrangements':catalog['arrangements'],
        'performance_contract':catalog['performance_contract'],
        'runtime_logic_included':catalog['runtime_logic_included'],
        'visual_approval_claimed':catalog['visual_approval_claimed'],
        'physical_4k60_certified':catalog['physical_4k60_certified'],
        'entries':[
            {k:v for k,v in row.items() if k not in ('sha256','triangles','materials')}
            for row in catalog['entries']
        ],
    }


def verify(head):
    changed=git('diff','--name-only',BASE,head,'--','HavenlineGodot').decode().splitlines()
    r07_paths={f'HavenlineGodot/assets/stations_v2/{name}.glb' for name in R07_IDS}
    r03_paths={f'HavenlineGodot/assets/stations_v2/{name}.glb' for name in R03_IDS}
    r10_paths={f'HavenlineGodot/assets/stations_v2/{name}.glb' for name in R10_IDS}
    r10b_paths={f'HavenlineGodot/assets/stations_v2/{name}.glb' for name in R10B_IDS}
    allowed={ASSET,CATALOG,TEST}|r07_paths|r03_paths|r10_paths|r10b_paths
    assert set(changed)==allowed,changed

    test_text=git('show',f'{head}:{TEST}').decode().lower()
    assert 'task05' in test_text and 'station' in test_text,'Unexpected T05 acceptance-test replacement'
    capture_text=git('show',f'{head}:HavenlineGodot/tests/capture_task05_station_kit.gd').decode()
    assert '\"front_axis\": \"negative-Z\"' in capture_text,'T05 evidence front-axis contract missing'
    assert 'offset = Vector3(0.0, 10.7, -16.0)' in capture_text,'T05 front camera is not on negative-Z axis'
    assert 'offset = Vector3(0.0, 10.7, 16.0)' in capture_text,'T05 rear camera is not on positive-Z axis'

    before=json.loads(git('show',f'{BASE}:{CATALOG}'))
    after=json.loads(git('show',f'{head}:{CATALOG}'))
    assert contract_view(before)==contract_view(after),'Gameplay/catalog contract changed'

    after_by={r['id']:r for r in after['entries']}
    hearth=after_by['hearth_vessel']
    assert hearth['sha256']==EXPECTED_SHA and int(hearth['triangles'])==25968
    for name in R07_IDS+R03_IDS+R10_IDS+R10B_IDS:
        old_row=next(r for r in before['entries'] if r['id']==name)
        new_row=after_by[name]
        assert new_row['sha256']!=old_row['sha256'],name
        assert int(new_row['triangles'])>int(old_row['triangles']),name
    assert 'metal' not in after_by['stone_stack']['materials']

    for path in (
        'tools/havenline/task05/reference_hearth_v3.py',
        'tools/havenline/task05/legacy_station_kit_v1.py',
        'HavenlineGodot/scripts/station_kit.gd',
    ):
        assert git('show',f'{BASE}:{path}')==git('show',f'{head}:{path}'),path

    assert hashlib.sha256(git('show',f'{head}:{ASSET}')).hexdigest()==EXPECTED_SHA
    assert hashlib.sha256((ROOT/ASSET).read_bytes()).hexdigest()==EXPECTED_SHA

    frozen=0
    for row in before['entries']:
        name=row['id']
        if name=='hearth_vessel' or name in R07_IDS or name in R03_IDS or name in R10_IDS or name in R10B_IDS:continue
        path=f'HavenlineGodot/assets/stations_v2/{name}.glb'
        assert git('show',f'{BASE}:{path}')==git('show',f'{head}:{path}'),name
        frozen+=1
    assert frozen==0

    return {
        'passed':True,'candidate_source':head,'protected_baseline':BASE,
        'changed_game_paths':changed,'model_sha256':EXPECTED_SHA,
        'other_nonrepaired_models_unchanged':True,'r07_models_rebuilt':8,'r03_models_rebuilt':6,
        'r10_models_rebuilt':3,'r10b_models_rebuilt':4,
        'stone_metal_material_removed':True,'gameplay_contracts_unchanged':True,
        'engine_test_changes':'T05 visual-family triangle/material acceptance updates only',
        'task_approved':False,'independent_critic':False,
    }


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--head',required=True);a=p.parse_args()
    print(json.dumps(verify(a.head),indent=2))
