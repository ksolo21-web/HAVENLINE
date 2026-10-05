"""Fail-closed R01-only source boundary and exact model identity proof."""
import argparse,json,hashlib,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE='b080906140b892f789a5f48a9f8cbeee1359c12e'
ASSET='HavenlineGodot/assets/stations_v2/hearth_vessel.glb'
CATALOG='HavenlineGodot/assets/stations_v2/catalog.json'
TEST='HavenlineGodot/tests/test_task05_station_kit.gd'
EXPECTED_SHA='6d32499229dd22dde1ee32940bb1b0a506a0647ea911a4787b3bce83fe60a8e7'


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def verify(head):
    changed=git('diff','--name-only',BASE,head,'--','HavenlineGodot').decode().splitlines()
    assert set(changed)=={ASSET,CATALOG,TEST},changed
    old=git('show',f'{BASE}:{TEST}').decode()
    expected=old.replace('== 42872','== 49160').replace('== 30820','== 37108')
    assert expected!=old
    assert git('show',f'{head}:{TEST}').decode()==expected,'Unrelated test change'
    before=json.loads(git('show',f'{BASE}:{CATALOG}'))
    after=json.loads(git('show',f'{head}:{CATALOG}'))
    row=next(r for r in before['entries'] if r['id']=='hearth_vessel')
    row['sha256']=EXPECTED_SHA;row['triangles']=25968
    assert before==after,'Gameplay catalog metadata changed'
    for path in ('tools/havenline/task05/reference_hearth_v3.py','tools/havenline/task05/legacy_station_kit_v1.py','HavenlineGodot/scripts/station_kit.gd','HavenlineGodot/tests/capture_task05_station_kit.gd'):
        assert git('show',f'{BASE}:{path}')==git('show',f'{head}:{path}'),path
    assert hashlib.sha256(git('show',f'{head}:{ASSET}')).hexdigest()==EXPECTED_SHA
    assert hashlib.sha256((ROOT/ASSET).read_bytes()).hexdigest()==EXPECTED_SHA
    return {'passed':True,'candidate_source':head,'protected_baseline':BASE,'changed_game_paths':changed,
            'model_sha256':EXPECTED_SHA,'other_21_models_unchanged':True,
            'gameplay_contracts_unchanged':True,'engine_test_changes':'two exact triangle-accounting assertions only',
            'task_approved':False,'independent_critic':False}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--head',required=True);a=p.parse_args()
    print(json.dumps(verify(a.head),indent=2))
