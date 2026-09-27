#!/usr/bin/env python3
"""Deterministic T05 source audit, retaining all existing contracts and outward-topology tests."""
from __future__ import annotations
import hashlib,json,struct,subprocess,sys
from pathlib import Path
import numpy as np
import legacy_station_kit_v1 as legacy

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
    assert sum(int(row['triangles']) for row in entries)==49160
    storage=sum((ASSET_DIR/(row['id']+'.glb')).stat().st_size for row in entries)
    assert storage==1673036 and storage<=15*1024*1024
    palette={m for row in entries for m in row['materials']}
    assert palette=={'snow','cream','wood','wood_light','metal','blue','cyan','orange','yellow','green','red','dark'}
    assert catalog['performance_contract']=={
        'triangles_max':180000,'draw_calls_max':48,'visible_materials_max':12,
        'texture_memory_mib_max':96,'storage_delta_mib_max':15,
        'active_physics':0,'skeletons':0,'animations':0,'population':0,
    }
    by_id={r['id']:r for r in entries}
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
    triangles={'camp':37108,'lakeshore':9456};surfaces={'camp':12,'lakeshore':10}
    for name,placements in arrangements.items():
        assert len({r['id'] for r in placements})==len(placements)
        assert sum(by_id[r['id']]['triangles'] for r in placements)==triangles[name]
        assert len({m for r in placements for m in by_id[r['id']]['materials']})==surfaces[name]
        assert surfaces[name]<=catalog['performance_contract']['draw_calls_max']
    from test_reference_hearth_v4 import verify
    topology=verify()
    report={'suite':'T05_station_kit_source_integrity','passed':True,'asset_count':22,
            'triangles':49160,'storage_bytes':storage,'deterministic_files':len(first),
            'opposite_winding_triangles':0,'nominal_batched_draw_calls':surfaces,
            'reference_hearth_topology':topology,'independent_critic':False,'physical_4k60_verified':False}
    print(json.dumps(report,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
