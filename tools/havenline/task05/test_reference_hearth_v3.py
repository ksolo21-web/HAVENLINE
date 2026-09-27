"""Topology and identity checks for the reference-hearth replacement, not art approval."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import numpy as np
from reference_hearth_v3 import Model,furnace
import legacy_station_kit_v1 as legacy
import reference_resource_props_v2 as resource_v2
import reference_ground_pads_v2 as pads_v2
import reference_station_families_v2 as station_v2


def component_errors(vertices,faces):
    errors=[]
    if not np.isfinite(vertices).all():return ['nonfinite vertices']
    vertices,indices=np.unique(np.round(vertices,8),axis=0,return_inverse=True)
    faces=indices[np.asarray(faces)]
    edges=np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]])
    ordered=np.sort(edges,axis=1)
    _,inverse,counts=np.unique(ordered,axis=0,return_inverse=True,return_counts=True)
    balance=np.bincount(inverse,weights=np.where(edges[:,0]<edges[:,1],1,-1))
    if not np.all(counts==2):errors.append('surface is not closed manifold')
    if not np.all(balance==0):errors.append('surface winding is inconsistent')
    p=vertices[faces]
    cross=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
    if np.any(np.linalg.norm(cross,axis=1)<1e-12):errors.append('degenerate triangle')
    volume=float(np.einsum('ij,ij->i',p[:,0],np.cross(p[:,1],p[:,2])).sum()/6)
    if volume<=1e-12:errors.append('nonpositive outward volume')
    return errors


def verify():
    model=furnace()
    assert len(model.parts)==184
    assert sum(len(p.faces) for p in model.parts)==19680
    for p in model.parts:
        assert not component_errors(p.vertices,p.faces),(p.name,component_errors(p.vertices,p.faces))
        assert np.isfinite(p.normals).all()
        assert np.allclose(np.linalg.norm(p.normals,axis=1),1,atol=1e-6)
    bounds=np.concatenate([p.vertices for p in model.parts])
    assert bounds[:,0].min()>=-1.3 and bounds[:,0].max()<=1.3
    assert bounds[:,2].min()>=-1.125 and bounds[:,2].max()<=1.125
    assert -.09<=bounds[:,1].min()<=.01
    # Negative controls are tested directly; they cannot be auto-corrected by Model.add.
    probe=Model('hostile');p=probe.bevel_box('box','metal',(1,1,1))
    assert not component_errors(p.vertices,p.faces)
    assert component_errors(p.vertices,p.faces[:-1])
    assert component_errors(p.vertices,p.faces[:,[0,2,1]])
    mixed=p.faces.copy();mixed[0]=mixed[0,::-1]
    assert component_errors(p.vertices,mixed)
    snow_cases=0
    for segments in (12,16,20):
        for rings in (4,5,7):
            for seed in (0,.37,2.3):
                snow=Model('snow');part=snow.snow('powder',(0,0,0),(.28,.12,.18),seed,segments,rings)
                assert not component_errors(part.vertices,part.faces)
                snow_cases+=1
    # R01 still freezes every non-hearth asset that is not deliberately owned
    # by the separately tested R07 resource-prop rebuild.
    root=Path(__file__).resolve().parents[3]
    assets=root/'HavenlineGodot/assets/stations_v2'
    rebuilt=set(resource_v2.RESOURCE_IDS)
    rebuilt_pads=set(pads_v2.PAD_IDS)
    rebuilt_stations=set(station_v2.STATION_IDS)
    unchanged=0
    with tempfile.TemporaryDirectory() as tmp:
        for name,builder in legacy.asset_specs().items():
            if name=='hearth_vessel' or name in rebuilt or name in rebuilt_pads or name in rebuilt_stations:continue
            path=Path(tmp)/(name+'.glb');legacy.pack_glb(builder,path)
            assert path.read_bytes()==(assets/path.name).read_bytes(),name
            unchanged+=1
    assert unchanged==4 and len(rebuilt)==8 and len(rebuilt_pads)==6 and len(rebuilt_stations)==3
    return {'passed':True,'closed_outward_components':184,'hostile_controls_rejected':3,
            'snow_topology_cases':snow_cases,'unchanged_nonhearth_nonresource_nonpad_assets':unchanged,
            'intentionally_rebuilt_r07_assets':len(rebuilt),
            'intentionally_rebuilt_r03_assets':len(rebuilt_pads),
            'intentionally_rebuilt_r10_assets':len(rebuilt_stations),
            'visual_approval':False,'independent_critic':False}


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
