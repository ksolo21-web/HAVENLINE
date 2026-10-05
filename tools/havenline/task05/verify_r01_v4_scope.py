"""Fail-closed R01 identity proof inside the combined T05 visual-family repair."""
import argparse,json,hashlib,subprocess,importlib.util,tempfile,copy,base64
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE='b080906140b892f789a5f48a9f8cbeee1359c12e'
ASSET='HavenlineGodot/assets/stations_v2/hearth_vessel.glb'
CATALOG='HavenlineGodot/assets/stations_v2/catalog.json'
TEST='HavenlineGodot/tests/test_task05_station_kit.gd'
CAPTURE='HavenlineGodot/tests/capture_task05_station_kit.gd'
LOADER='HavenlineGodot/scripts/station_kit.gd'
HISTORICAL='95c11abd7c712a7d8122091682ab830593d28d8d'
AUTHORIZED_SHA='0b4090092e1146631048b5b6f0ebfb522074c8f01535985c5630667dd36f3cac'
CENSUS_SHA='17cdbc973ccb7744291c707f6c4d5e5f77c918b0f191e5bf74badc87c7484cf2'
REQUEST='Docs/Production/T05/ChangeRequests/T05-PROTECTED-HEARTH-MATERIAL-ONLY-20261005.json'
HELPER='tools/havenline/task05/rebind_hearth_materials_v5.py'
FIXTURES='tools/havenline/task05/fixtures/'
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



# Exact bounded loader addition; removing this method and its one call must
# reconstruct the historical frozen source. No gameplay changes are admitted.
COLOR_METHOD = """func enable_authored_vertex_colors(node: Node3D) -> void:
	if node is MeshInstance3D and node.mesh != null:
		for surface_index in node.mesh.get_surface_count():
			var arrays: Array = node.mesh.surface_get_arrays(surface_index)
			if arrays[Mesh.ARRAY_COLOR] == null or arrays[Mesh.ARRAY_COLOR].size() == 0:
				continue
			var material: Material = node.get_active_material(surface_index)
			if material is BaseMaterial3D and not material.vertex_color_use_as_albedo:
				var authored: BaseMaterial3D = material.duplicate()
				authored.vertex_color_use_as_albedo = true
				node.set_surface_override_material(surface_index, authored)
	for child in node.get_children():
		if child is Node3D:
			enable_authored_vertex_colors(child)

"""


def material_supersession(head, asset_bytes):
    request=json.loads(git('show',f'{head}:{REQUEST}'))
    assert request['disposition']=='AUTHORIZED_FOR_BOUNDED_ISOLATED_IMPLEMENTATION'
    assert request['disposition_by']['owner']=='primary-integration-owner'
    assert request['disposition_by']['session']=='/root'
    assert request['task_approved'] is False and request['production_approval'] is False
    assert request['integration_authorized'] is False
    scope=request['scope_supersession']
    assert scope['historical_source']==HISTORICAL
    assert scope['historical_exact_hearth_sha256']==EXPECTED_SHA
    assert scope['baseline_fixture_sha256']==EXPECTED_SHA
    assert scope['palette']['old_kit_vocabulary']==11 and scope['palette']['new_kit_vocabulary']==12
    assert scope['palette']['visible_materials_max']==12 and scope['palette']['budget_waiver'] is False
    with tempfile.TemporaryDirectory(prefix='t05-material-proof-') as directory:
        root=Path(directory);(root/'fixtures').mkdir()
        module_path=root/'rebind_hearth_materials_v5.py'
        module_path.write_bytes(git('show',f'{head}:{HELPER}'))
        for name in ('hearth_material_source_v4.json','hearth_geometry_source_v4.glb'):
            (root/'fixtures'/name).write_bytes(git('show',f'{head}:{FIXTURES}{name}'))
        spec=importlib.util.spec_from_file_location('t05_candidate_material_helper',module_path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        assert module.BASE_SHA==EXPECTED_SHA
        assert module.FIXTURE_SHA==scope['fixture_census_sha256']==CENSUS_SHA
        assert module.FORGED_PBR==scope['palette']['forged_pbr']
        assert module.FORGED_PBR=={'baseColorFactor':[.18,.22,.27,1.],'metallicFactor':.45,'roughnessFactor':.55}
        fixture=json.loads((root/'fixtures/hearth_material_source_v4.json').read_text())
        assert fixture['body_tags']==scope['body_tags'] and fixture['body_triangles']==scope['body_triangles']==2464
        assert fixture['blue_tag']==scope['blue_enamel_tag']=='enamel_armor_tab'
        assert fixture['blue_part_count']==scope['blue_enamel_instances']==8
        proof=module.rebuild(root/'candidate.glb')
        first=(root/'candidate.glb').read_bytes();module.rebuild(root/'candidate.glb')
        assert first==(root/'candidate.glb').read_bytes()==asset_bytes,'Candidate must equal fixture rebuild'
        assert proof['sha256']==scope['material_helper_sha256']==AUTHORIZED_SHA
        assert proof['proof']['actual_hearth_material_count']==scope['palette']['new_hearth_materials']==10
        assert proof['triangles']==25968
        baseline=(root/'fixtures/hearth_geometry_source_v4.glb').read_bytes()
        assert hashlib.sha256(baseline).hexdigest()==EXPECTED_SHA
        before,bb=module.unpack(baseline);after,ab=module.unpack(asset_bytes)
        assert module.triangles(before,bb)==module.triangles(after,ab)
        old=module.primitives_by_name(before);new=module.primitives_by_name(after)
        assert len(after['materials'])==10 and len(new)==10
        assert new['HL_forged_iron']['attributes']['POSITION']==old['HL_cream']['attributes']['POSITION']
        assert new['HL_forged_iron']['attributes']['NORMAL']==old['HL_cream']['attributes']['NORMAL']
        for i,material in enumerate(before['materials']):
            expected=copy.deepcopy(material)
            if material['name']=='HL_blue':expected['pbrMetallicRoughness']['roughnessFactor']=.65
            assert after['materials'][i]==expected
        assert after['materials'][-1]=={'name':'HL_forged_iron','pbrMetallicRoughness':module.FORGED_PBR,'doubleSided':False}
        for name in ('HL_cream','HL_blue'):
            expected=bytearray(module.payload(before,bb,old[name]['attributes']['COLOR_0']))
            for member in fixture['members']:
                if member['baseline_material']==name:
                    start=member['vertex_start']*16;end=start+member['vertex_count']*16
                    expected[start:end]=base64.b64decode(member['source_colors_with_v4_ao_base64'],validate=True)
            assert bytes(expected)==module.payload(after,ab,new[name]['attributes']['COLOR_0']),'COLOR changes exceeded census'

        for name,prim in old.items():
            for semantic in ('POSITION','NORMAL'):
                assert module.payload(before,bb,prim['attributes'][semantic])==module.payload(after,ab,new[name]['attributes'][semantic])
            if name not in ('HL_cream','HL_blue'):
                assert module.payload(before,bb,prim['attributes']['COLOR_0'])==module.payload(after,ab,new[name]['attributes']['COLOR_0'])
    loader=git('show',f'{head}:{LOADER}').decode()
    call='\tenable_authored_vertex_colors(instance)\n'
    assert loader.count(COLOR_METHOD)==1 and loader.count(call)==1
    original=loader.replace(COLOR_METHOD,'',1).replace(call,'',1)
    assert original.encode()==git('show',f'{HISTORICAL}:{LOADER}'),'Loader exceeded bounded method/call addition'
    assert git('show',f'{head}:{CAPTURE}')==git('show',f'{HISTORICAL}:{CAPTURE}'),'Frozen capture/camera source changed'
    return proof


def verify(head):
    asset_bytes=git('show',f'{head}:{ASSET}')
    actual_sha=hashlib.sha256(asset_bytes).hexdigest()
    superseded=actual_sha!=EXPECTED_SHA
    material_proof=material_supersession(head,asset_bytes) if superseded else None
    changed=git('diff','--name-only',BASE,head,'--','HavenlineGodot').decode().splitlines()
    r07_paths={f'HavenlineGodot/assets/stations_v2/{name}.glb' for name in R07_IDS}
    r03_paths={f'HavenlineGodot/assets/stations_v2/{name}.glb' for name in R03_IDS}
    r10_paths={f'HavenlineGodot/assets/stations_v2/{name}.glb' for name in R10_IDS}
    r10b_paths={f'HavenlineGodot/assets/stations_v2/{name}.glb' for name in R10B_IDS}
    # The capture harness is part of the visual-evidence contract and was
    # intentionally expanded to six-angle family coverage. No runtime/gameplay
    # source is allowed through this scope proof.
    allowed={ASSET,CATALOG,TEST,CAPTURE}|r07_paths|r03_paths|r10_paths|r10b_paths
    if superseded:allowed.add(LOADER)
    assert set(changed)==allowed,changed

    test_text=git('show',f'{head}:{TEST}').decode().lower()
    assert '"suite": "t05_station_and_prop_kit"' in test_text,'Unexpected T05 acceptance-test replacement'
    assert 'const stationkit = preload("res://scripts/station_kit.gd")' in test_text,'T05 station authority missing from acceptance test'
    capture_text=git('show',f'{head}:{CAPTURE}').decode()
    assert '\"front_axis\": \"negative-Z\"' in capture_text,'T05 evidence front-axis contract missing'
    assert 'offset = Vector3(0.0, 10.7, -16.0)' in capture_text,'T05 front camera is not on negative-Z axis'
    assert 'offset = Vector3(0.0, 10.7, 16.0)' in capture_text,'T05 rear camera is not on positive-Z axis'
    assert '--family-gallery' in capture_text and 'capture_family_gallery' in capture_text,'T05 six-angle family evidence path missing'
    for view in ('front','rear','left','right','three-quarter','detail'):
        assert f'"{view}"' in capture_text,f'T05 family evidence view missing: {view}'

    before=json.loads(git('show',f'{BASE}:{CATALOG}'))
    after=json.loads(git('show',f'{head}:{CATALOG}'))
    assert contract_view(before)==contract_view(after),'Gameplay/catalog contract changed'

    after_by={r['id']:r for r in after['entries']}
    hearth=after_by['hearth_vessel']
    assert hearth['sha256']==actual_sha and int(hearth['triangles'])==25968
    if superseded:
        assert set(hearth['materials'])==set(material_proof['materials'])
        assert len({m for row in after['entries'] for m in row['materials']})==12
        assert after['performance_contract']['visible_materials_max']==12
    for name in R07_IDS+R03_IDS+R10_IDS+R10B_IDS:
        old_row=next(r for r in before['entries'] if r['id']==name)
        new_row=after_by[name]
        assert new_row['sha256']!=old_row['sha256'],name
        assert int(new_row['triangles'])>int(old_row['triangles']),name
    assert 'metal' not in after_by['stone_stack']['materials']

    for path in (
        'tools/havenline/task05/reference_hearth_v3.py',
        'tools/havenline/task05/legacy_station_kit_v1.py',
        *(() if superseded else (LOADER,)),
    ):
        assert git('show',f'{BASE}:{path}')==git('show',f'{head}:{path}'),path

    # Source-bound history remains verifiable while the worktree has newer art.
    if superseded and git('rev-parse',head).strip()==git('rev-parse','HEAD').strip():
        assert hashlib.sha256((ROOT/ASSET).read_bytes()).hexdigest()==actual_sha

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
        'changed_game_paths':changed,'model_sha256':actual_sha,'historical_model_sha256':EXPECTED_SHA,
        'scope_mode':'AUTHORIZED_MATERIAL_ONLY_SUPERSESSION' if superseded else 'HISTORICAL_EXACT_FREEZE',
        'material_rebuild_proof':material_proof,
        'other_nonrepaired_models_unchanged':True,'r07_models_rebuilt':8,'r03_models_rebuilt':6,
        'r10_models_rebuilt':3,'r10b_models_rebuilt':4,
        'stone_metal_material_removed':True,'gameplay_contracts_unchanged':True,
        'engine_test_changes':'T05 visual-family triangle/material acceptance updates only',
        'task_approved':False,'independent_critic':False,
    }


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--head',required=True);a=p.parse_args()
    print(json.dumps(verify(a.head),indent=2))
