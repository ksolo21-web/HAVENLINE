#!/usr/bin/env python3
"""Generate the T05 kit with bounded reference-driven visual overrides.

R01 keeps the approved reference-hearth replacement. R07 replaces only the eight
pickup/storage resource props whose legacy geometry/material treatment remains
visibly primitive against the user's supplied HAVENLINE renders. IDs, footprints,
sockets, arrangements, gameplay metadata and the existing 12-slot palette remain
authoritative.
"""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
import legacy_station_kit_v1 as legacy
from reference_hearth_v4 import build_legacy
from reference_resource_props_v2 import build_resource_props

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'HavenlineGodot/assets/stations_v2'
EXPECTED_HEARTH_SHA256='6d32499229dd22dde1ee32940bb1b0a506a0647ea911a4787b3bce83fe60a8e7'


def preserve_shared_palette(path):
    """Keep named material definitions compatible with the unchanged batcher.

    The shipping scene owns heat lighting. A shared HL_orange/HL_yellow material
    must not make unrelated stations glow merely because the furnace is first.
    Vertex colors retain the furnace's paint/stone detail; geometry is untouched.
    """
    raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
    document=json.loads(raw[20:20+size]);binary_chunk=raw[20+size:]
    document['asset']['generator']='HAVENLINE reference sculpt v4'
    for material in document['materials']:
        material.pop('emissiveFactor',None)
    encoded=json.dumps(document,sort_keys=True,separators=(',',':')).encode()
    encoded+=b' '*((-len(encoded))%4)
    result=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(binary_chunk))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+binary_chunk
    path.write_bytes(result)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assets=legacy.asset_specs()
    assets.update(build_resource_props())
    assets['hearth_vessel']=build_legacy(legacy.MeshBuilder)
    expected={asset_id+'.glb' for asset_id in assets}
    for path in OUT.glob('*.glb'):
        if path.name not in expected:raise RuntimeError('Unexpected authored asset; refusing deletion: '+str(path))
    entries=[]
    for asset_id in sorted(assets):
        builder=assets[asset_id];path=OUT/(asset_id+'.glb')
        if asset_id=='hearth_vessel':
            # R01-V4 is already source-bound and visually repaired. R07 does
            # not own it, so never re-export the furnace on another CI host:
            # tiny cross-host floating differences must not mutate approved art.
            # Fail closed if the exact approved bytes are absent or altered.
            if not path.exists():
                raise RuntimeError('Missing approved R01-V4 hearth_vessel.glb')
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            if actual!=EXPECTED_HEARTH_SHA256:
                raise RuntimeError(f'R01-V4 hearth bytes drifted: {actual}')
        else:legacy.pack_glb(builder,path)
        footprint,requirement,later_task,sockets=legacy.METADATA[asset_id]
        entry={'id':asset_id,'asset':'res://assets/stations_v2/'+path.name,
               'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
               'requirement':requirement,'later_task':later_task,
               'footprint':list(footprint),'clearance':0.55,
               'sockets':{name:list(value) for name,value in sockets.items()},
               'triangles':builder.triangle_count(),'materials':sorted(builder.surfaces)}
        if asset_id in legacy.PAD_VISUAL_VARIANTS:entry['visual_variant']=legacy.PAD_VISUAL_VARIANTS[asset_id]
        entries.append(entry)
    catalog={'schema_version':1,'authority_id':'T05-station-kit-v1',
             'generator':'tools/havenline/task05/generate_station_kit.py',
             'art_language':'reference-driven sculpted winter production kit; chunky readable forms, layered timber/metal, snow loading and blue/orange/yellow Havenline identity',
             'requirements':[f'T05-R{i:02d}' for i in range(1,13)],'entries':entries,
             'arrangements':{name:[{'id':i,'position':list(p),'rotation_y':r} for i,p,r in rows] for name,rows in legacy.ARRANGEMENTS.items()},
             'performance_contract':{'triangles_max':180000,'draw_calls_max':48,'visible_materials_max':12,'texture_memory_mib_max':96,'storage_delta_mib_max':15,'active_physics':0,'skeletons':0,'animations':0,'population':0},
             'runtime_logic_included':False,'visual_approval_claimed':False,'physical_4k60_certified':False}
    (OUT/'catalog.json').write_text(json.dumps(catalog,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'assets':len(entries),'triangles':sum(x['triangles'] for x in entries),'catalog':str((OUT/'catalog.json').relative_to(ROOT))},indent=2))


if __name__=='__main__':main()
