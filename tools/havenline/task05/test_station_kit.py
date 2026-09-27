#!/usr/bin/env python3
"""Deterministic T05 source audit, retaining all existing contracts and outward-topology tests."""
from __future__ import annotations
import hashlib,json,struct,subprocess,sys
from pathlib import Path
import numpy as np
import legacy_station_kit_v1 as legacy
import reference_resource_props_v2 as resource_v2
import reference_station_families_v3 as station_v3
import reference_utility_stations_v3 as utility_v3
# T05_SCOPE_NOTE: R01 hearth plus R07/R03/R10/R10B families are independently gated; no stale legacy utility freeze remains.

ROOT=Path(__file__).resolve().parents[3]
ASSET_DIR=ROOT/'HavenlineGodot/assets/stations_v2'
CATALOG=ASSET_DIR/'catalog.json'
GENERATOR=ROOT/'tools/havenline/task05/generate_station_kit.py'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def glb_document(path):
    raw=path.read_bytes()
    magic,version,length=struct.unpack_from('<4sII',raw,0)
    assert magic==b'glTF' and version==2 and length==len(raw),path
    size,kind=struct.unpack_from('<I4s',raw,12)
    assert kind==b'JSON'
    document=json.loads(raw[20:20+size]);offset=20+size
    binary_length,binary_type=struct.unpack_from('<I4s',raw,offset)
    assert binary_type==b'BIN\0'
    blob=raw[offset+8:offset+8+binary_length]
    assert len(blob)==binary_length
    return document,blob


def accessor(document,blob,index):
    row=document['accessors'][index];view=document['bufferViews'][row['bufferView']]
    offset=int(view.get('byteOffset',0))+int(row.get('byteOffset',0))
    components={'SCALAR':1,'VEC3':3,'VEC4':4}[row['type']]
    dtype={5125:'<u4',5126:'<f4'}[int(row['componentType'])]
    return np.frombuffer(blob,dtype=dtype,count=int(row['count'])*components,offset=offset).reshape((-1,components))


def winding_failures(path):
    document,blob=glb_document(path);failures=0
    for primitive in document['meshes'][0]['primitives']:
        p=accessor(document,blob,primitive['attributes']['POSITION'])
        n=accessor(document,blob,primitive['attributes']['NORMAL'])
        f=accessor(document,blob,primitive['indices']).reshape((-1,3))
        assert np.isfinite(p).all() and np.isfinite(n).all()
        geometric=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
        authored=n[f].sum(axis=1)
        failures+=int((np.einsum('ij,ij->i',geometric,authored)<-1e-8).sum())
    return failures


def snapshot():
    return {p.name:digest(p) for p in sorted(ASSET_DIR.glob('*.glb'))}|{'catalog.json':digest(CATALOG)}


def main():
    subprocess.run([sys.executable,str(GENERATOR)],cwd=ROOT,check=True,capture_output=True,text=True)
    first=snapshot()
    subprocess.run([sys.executable,str(GENERATOR)],cwd=ROOT,check=True,capture_output=True,text=True)
    assert first==snapshot(),'generator output is not byte deterministic'
    catalog=json.loads(CATALOG.read_text())
    assert catalog['authority_id']=='T05-station-kit-v1'
    for flag in ('runtime_logic_included','visual_approval_claimed','physical_4k60_certified'):
        assert catalog[flag] is False
    assert catalog['requirements']==[f'T05-R{i:02d}' for i in range(1,13)]
    entries=catalog['entries'];ids=[row['id'] for row in entries]
    assert len(entries)==len(set(ids))==22
    assert set(ids)==set(legacy.METADATA)
    by_id={r['id']:r for r in entries}
    total_triangles=sum(int(row['triangles']) for row in entries)
    assert 49160 < total_triangles <= int(catalog['performance_contract']['triangles_max'])
    storage=sum((ASSET_DIR/(row['id']+'.glb')).stat().st_size for row in entries)
    assert 1673036 < storage <= 15*1024*1024
    palette={m for row in entries for m in row['materials']}
    # R07 replaces the generic red jerrycan with a Havenline blue/orange
    # canister. Red was used nowhere else, so the active palette intentionally
    # contracts from 12 slots to 11 while the hard ceiling remains 12.
    assert palette=={'snow','cream','wood','wood_light','metal','blue','cyan','orange','yellow','green','dark'}
    assert len(palette)==11 and int(catalog['performance_contract']['visible_materials_max'])==12

    # R07 reference rebuild gate. These exact legacy hashes are forbidden so a
    # future regeneration cannot silently restore the primitive pickup props.
    legacy_resource_hashes={
        'cargo_crate':'b524e93f6ebc56750c55b67f7e7747c599d956a37f66c4e6368d4314b01c2cf2',
        'cooked_food_stack':'d235f82290045a02a7fb0200ab95d19192ff0784ef05185bcbe095516567f2f6',
        'fish_crate':'6834b98ae6bb37cbca712676326e2c7f8b82ab557d0cffb5ad76712b5bd59320',
        'fuel_canister':'4f12ab4c8bd7e6a282cbfe797bcebc11b638d4a458f7ad19661e76e6e12f70e5',
        'metal_stack':'44e3467f16ee777878b7881b0a76fc2b41d87cbf199cc2731831a9c881490338',
        'money_stack':'564be7e8e5ba47f36f96ab7d7851d4c905f8f005510a0a7b1948dbda5d975864',
        'stone_stack':'4fda08c4b117ba6c3c72212cfe02fbed9519dba1a74345f2c2c04bc548d554c7',
        'wood_stack':'5d5707cc5ecc05a2c586b6a933d15075510a9d091defdd63a42bca693658320b',
    }
    legacy_resource_triangles={
        'cargo_crate':864,'cooked_food_stack':1764,'fish_crate':1512,'fuel_canister':640,
        'metal_stack':1404,'money_stack':2596,'stone_stack':1116,'wood_stack':1404,
    }
    resource_report=resource_v2.quality_report()
    assert resource_report['stone_uses_metal'] is False
    assert set(resource_report['asset_ids'])==set(legacy_resource_hashes)
    assert set(resource_report['material_slots'])<=palette
    for asset_id in resource_report['asset_ids']:
        row=by_id[asset_id]
        assert row['sha256']!=legacy_resource_hashes[asset_id],asset_id
        assert int(row['triangles'])==int(resource_report['triangles'][asset_id]),asset_id
        assert int(row['triangles'])>legacy_resource_triangles[asset_id],asset_id
        assert row['materials']==resource_report['materials'][asset_id],asset_id
        assert len(row['materials'])>=4,asset_id
    assert 'metal' not in by_id['stone_stack']['materials']

    # R10 station-family rebuild gate. The hearth freeze intentionally excludes
    # these three assets, so bind them here to the exact authored v3 builders
    # instead of weakening byte-identity proof globally.
    station_assets=station_v3.build_station_families()
    legacy_station_triangles={'service_counter':1476,'processing_counter':2052,'defense_platform':1632}
    assert set(station_assets)==set(legacy_station_triangles)
    for asset_id,builder in station_assets.items():
        row=by_id[asset_id]
        assert int(row['triangles'])==builder.triangle_count(),asset_id
        assert row['materials']==sorted(builder.surfaces),asset_id
        assert int(row['triangles'])>legacy_station_triangles[asset_id],asset_id
    assert 'cyan' in by_id['service_counter']['materials']

    # R10B binds the four remaining legacy utility silhouettes to authored,
    # reference-driven replacements without changing their gameplay metadata.
    utility_assets=utility_v3.build_utility_stations()
    legacy_utility_triangles={
        'fishing_rack':1276,'intake_machine':760,
        'cooker_processor':1188,'conveyor_straight':1216,
    }
    legacy_utility_hashes={
        'fishing_rack':'56c190ec2abb6efb8b0e21656071ffb7f532941fe3b5a4ca069da3bf23b192bf',
        'intake_machine':'df4a7e95f92b1ebff291506a4bd1eabf989e82cb8feec5efcce87a0eb01ab647',
        'cooker_processor':'6c7820c06c20ed481e4f55b1e9d186f54b1a8e215f337b6a6bdbbe4d703c9688',
        'conveyor_straight':'89bbeb9f7c38744497deefb414eb0456ed28100a07d4ae6bce47aa85cf40bb15',
    }
    assert set(utility_assets)==set(legacy_utility_triangles)
    for asset_id,builder in utility_assets.items():
        row=by_id[asset_id]
        assert row['sha256']!=legacy_utility_hashes[asset_id],asset_id
        assert int(row['triangles'])==builder.triangle_count(),asset_id
        assert int(row['triangles'])>legacy_utility_triangles[asset_id],asset_id
        assert row['materials']==sorted(builder.surfaces),asset_id
        assert {'snow','wood','wood_light','blue'}<=set(row['materials']),asset_id
        assert len(row['materials'])>=6,asset_id
        # Source-side footprint guard: catch authored mesh overhangs before the
        # Godot placement/collision suite. This is intentionally stricter than
        # a visual-only review because frozen gameplay footprints must match art.
        footprint=legacy.METADATA[asset_id][0]
        xs=[p[0] for surface in builder.surfaces.values() for p in surface.positions]
        zs=[p[2] for surface in builder.surfaces.values() for p in surface.positions]
        assert max(xs)-min(xs) <= float(footprint[0])+.03,(asset_id,'footprint_x',max(xs)-min(xs),footprint[0])
        assert max(zs)-min(zs) <= float(footprint[1])+.03,(asset_id,'footprint_z',max(zs)-min(zs),footprint[1])
    assert catalog['performance_contract']=={
        'triangles_max':180000,'draw_calls_max':48,'visible_materials_max':12,
        'texture_memory_mib_max':96,'storage_delta_mib_max':15,
        'active_physics':0,'skeletons':0,'animations':0,'population':0,
    }
    variants=[by_id['pad_'+kind]['visual_variant'] for kind in ('build','upgrade','input','output','stock','payment')]
    assert len({r['silhouette'] for r in variants})==6
    assert len({r['icon'] for r in variants})==6
    assert [r['trim'] for r in variants]==['yellow','orange','cyan','blue','cream','green']
    for row in entries:
        path=ASSET_DIR/(row['id']+'.glb')
        assert path.exists() and row['asset']=='res://assets/stations_v2/'+path.name
        assert row['sha256']==digest(path)
        doc,blob=glb_document(path)
        assert {m['name'].removeprefix('HL_') for m in doc['materials']}==set(row['materials'])
        assert all(m['name'].startswith('HL_') for m in doc['materials'])
        assert all(m.get('doubleSided') is False for m in doc['materials'])
        assert winding_failures(path)==0,row['id']
        assert row['sockets'] and all(len(v)==3 for v in row['sockets'].values())
        assert all(float(v)>0 for v in row['footprint'])
        footprint,requirement,later_task,sockets=legacy.METADATA[row['id']]
        assert row['footprint']==list(footprint)
        assert row['clearance']==.55 and row['requirement']==requirement and row['later_task']==later_task
        assert row['sockets']=={k:list(v) for k,v in sockets.items()}
        if row['id']=='hearth_vessel':
            assert row['triangles']==25968
            assert doc['asset']['generator']=='HAVENLINE reference sculpt v4'
            for material in doc['materials']:
                key=material['name'].removeprefix('HL_')
                color,metallic,roughness=legacy.MATERIALS[key]
                assert material['pbrMetallicRoughness']=={'baseColorFactor':list(color),'metallicFactor':metallic,'roughnessFactor':roughness}
                assert 'emissiveFactor' not in material
            for prim in doc['meshes'][0]['primitives']:
                colors=accessor(doc,blob,prim['attributes']['COLOR_0'])
                assert np.isfinite(colors).all() and (colors>=0).all() and (colors<=1).all()
    arrangements=catalog['arrangements']
    assert {name:len(rows) for name,rows in arrangements.items()}=={'camp':11,'lakeshore':10}
    assert arrangements=={name:[{'id':i,'position':list(p),'rotation_y':r} for i,p,r in rows] for name,rows in legacy.ARRANGEMENTS.items()}
    triangle_floors={'camp':37108,'lakeshore':9456};surfaces={'camp':11,'lakeshore':10}
    for name,placements in arrangements.items():
        assert len({r['id'] for r in placements})==len(placements)
        assert sum(by_id[r['id']]['triangles'] for r in placements)>triangle_floors[name]
        assert len({m for r in placements for m in by_id[r['id']]['materials']})==surfaces[name]
        assert surfaces[name]<=catalog['performance_contract']['draw_calls_max']
    from test_reference_hearth_v4 import verify
    topology=verify()
    report={'suite':'T05_station_kit_source_integrity','passed':True,'asset_count':22,
            'triangles':total_triangles,'storage_bytes':storage,'deterministic_files':len(first),
            'opposite_winding_triangles':0,'nominal_batched_draw_calls':surfaces,
            'reference_hearth_topology':topology,
            'r10_station_triangles':{name:builder.triangle_count() for name,builder in station_assets.items()},
            'r10_station_materials':{name:sorted(builder.surfaces) for name,builder in station_assets.items()},
            'r10b_utility_triangles':{name:builder.triangle_count() for name,builder in utility_assets.items()},
            'r10b_utility_materials':{name:sorted(builder.surfaces) for name,builder in utility_assets.items()},
            'independent_critic':False,'physical_4k60_verified':False}
    print(json.dumps(report,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
