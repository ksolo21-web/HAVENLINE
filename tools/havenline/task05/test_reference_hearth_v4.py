"""R01 V4 topology, geometry-bound bake, and immutable dependency checks.
Machine integrity only: this module never claims independent visual approval.
"""
from __future__ import annotations
import copy,json
from pathlib import Path
import numpy as np
from reference_hearth_v4 import furnace
from reference_hearth_v3 import furnace as historical_furnace
from test_reference_hearth_v3 import component_errors,verify as verify_v3
from r01_ambient_bake_v4 import apply_baked_occlusion,geometry_digest,GEOMETRY_SHA256,VERTEX_COUNT


def verify():
    preserved=verify_v3()
    model=furnace()
    assert len(model.parts)==238
    assert sum(len(p.faces) for p in model.parts)==25968
    assert sum(len(p.vertices) for p in model.parts)==VERTEX_COUNT
    assert geometry_digest(model)==GEOMETRY_SHA256
    for part in model.parts:
        assert not component_errors(part.vertices,part.faces),(part.name,component_errors(part.vertices,part.faces))
        assert np.isfinite(part.normals).all()
        assert np.allclose(np.linalg.norm(part.normals,axis=1),1,atol=1e-6)
        assert np.isfinite(part.colors).all()
        assert (part.colors>=0).all() and (part.colors<=1).all()
    bounds=np.concatenate([p.vertices for p in model.parts])
    assert bounds[:,0].min()>=-1.3 and bounds[:,0].max()<=1.3
    assert bounds[:,2].min()>=-1.125 and bounds[:,2].max()<=1.125
    assert -.09<=bounds[:,1].min()<=.01
    expected={p.name for p in model.parts}
    for name in ('forged_lower_plate_00','service_hatch_panel_0','service_hatch_cross_strap','valve_handwheel','pressure_gauge_tick_00','sculpted_flame_00','firebox_bronze_reveal'):
        assert name in expected,name
    assert not any(p.name.startswith(('lower_shell_stave_','flame_','flame_heart_')) for p in model.parts)
    # No caps/normals can be removed while satisfying the outward-closure gate.
    plate=next(p for p in model.parts if p.name=='forged_lower_plate_00')
    assert component_errors(plate.vertices,plate.faces[:-1])
    assert component_errors(plate.vertices,plate.faces[:,[0,2,1]])
    # A bake cannot silently survive changed source geometry or part identity.
    for mutation in ('position','part_name'):
        broken=copy.deepcopy(model)
        if mutation=='position':broken.parts[0].vertices[0,0]+=.01
        else:broken.parts[0].name+='-not-the-baked-component'
        try:apply_baked_occlusion(broken)
        except ValueError:pass
        else:raise AssertionError('stale bake accepted: '+mutation)
    # Model-space contracts remain frozen while every non-hearth T05 family is
    # now intentionally owned by R07/R03/R10/R10B and gated separately.
    assert preserved['unchanged_nonhearth_nonresource_nonpad_assets']==0
    assert preserved['intentionally_rebuilt_r07_assets']==8
    assert preserved['intentionally_rebuilt_r03_assets']==6
    assert preserved['intentionally_rebuilt_r10_assets']==3
    assert preserved['intentionally_rebuilt_r10b_utility_assets']==4
    return {'passed':True,'closed_outward_components':238,'hearth_triangles':25968,
            'vertex_occlusion_count':VERTEX_COUNT,'geometry_bound_bake':True,
            'new_hostile_controls_rejected':4,'preserved_v3_regression':preserved,
            'unchanged_nonhearth_nonresource_nonpad_assets':0,'intentionally_rebuilt_r07_assets':8,
            'intentionally_rebuilt_r03_assets':6,'intentionally_rebuilt_r10_assets':3,
            'intentionally_rebuilt_r10b_utility_assets':4,
            'visual_approval':False,'independent_critic':False}


if __name__=='__main__':print(json.dumps(verify(),indent=2))
