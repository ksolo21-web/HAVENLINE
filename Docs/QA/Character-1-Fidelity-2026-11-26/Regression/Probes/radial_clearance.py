"""Conservative all-angle horizontal separation certificate for rigid orbit/cargo solids."""
from pathlib import Path
import os,json
import numpy as np

root=Path(os.environ['HAVENLINE_GEAR_GEOMETRY']); out=Path(os.environ['HAVENLINE_PROBE_RESULTS'])
d=json.loads((root/'transforms.json').read_text())
placements={}
for group in [root]+sorted(p for p in root.iterdir() if p.is_dir()):
    origins=json.loads((group/'root-origins.json').read_text())
    label='mixed' if group==root else group.name
    limits={}
    settled={}
    underside={}
    for verts in group.glob('*-v'):
        key=verts.name[:-2]
        if key in ('axe','pickaxe','body'): continue
        xyz=np.fromfile(verts,np.float32).reshape(-1,3).astype(float)
        v=xyz[:,[0,2]]
        settled[key]=float(np.linalg.norm(v,axis=1).max())
        underside[key]=float(xyz[:,1].min())
        if key=='rack' or key.startswith('divider-'):
            radius=np.linalg.norm(v,axis=1).max()
        else:
            anchor=np.asarray(origins[key])[[0,2]]
            # All authored tier yaws and arbitrary interpolation rotations lie inside this cylinder.
            radius=np.linalg.norm(v-anchor,axis=1).max()+np.linalg.norm(anchor)
        limits[key]=float(radius)
    max_key=max(limits,key=limits.get)
    placements[label]=dict(limiting_solid=max_key,maximum_radius_bound_m=limits[max_key],
                           largest_installed_vertex_radius_m=max(settled.values()),lowest_installed_vertex_m=min(underside.values()))
reach=max(q['maximum_radius_bound_m'] for q in placements.values())
installed=max(q['largest_installed_vertex_radius_m'] for q in placements.values())
underside=min(q['lowest_installed_vertex_m'] for q in placements.values())
axes=d['orbit_geometry']
a,b=axes['side_radius'],axes['depth_radius']
direction=np.asarray(axes['near_direction_xz'])
results={}
for k in ('axe','pickaxe'):
    t, *coeff=d['samples'][k+'1'][0]
    assert t==0 and a<=b and axes['upgraded_radius_multiplier']>=1
    m=np.asarray(coeff).reshape(3,4)
    vs=np.fromfile(root/(k+'-v'),np.float32).reshape(-1,3)
    f=np.fromfile(root/(k+'-f'),np.int32).reshape(-1,3)
    xyz=vs@m[:,:3].T+m[:,3]
    v=xyz[:,[0,2]]-(b-a)*direction
    assert np.min(v@direction)>0
    tri=v[f]; start=tri.reshape(-1,2);end=np.roll(tri,-1,axis=1).reshape(-1,2)
    delta=end-start;den=(delta*delta).sum(1);span=np.zeros_like(den)
    np.divide(-(start*delta).sum(1),den,out=span,where=den>1e-15)
    distance=np.linalg.norm(start+np.clip(span,0,1)[:,None]*delta,axis=1).min()
    results[k]=dict(minimum_tool_radius_m=float(distance),minimum_horizontal_gap_m=float(distance-reach),
                    guarantees_separation=bool(distance>reach),
                    all_phase_settled_horizontal_gap_m=float(distance-installed),
                    all_phase_gap_above_steady_tool_m=float(underside-xyz[:,1].max()),
                    settled_separation_proven=bool(distance>installed or underside>xyz[:,1].max()))
report=dict(method='For the starter ellipse every triangle of a tool lies in the forward half-plane, and the held orientation follows the instantaneous orbit radius. Horizontal distance is minimal at the minor radius. Closest projected triangle edges give the inner solid radius. Upgraded orbits stay farther out. The conservative radius bound allows arbitrary tier spin around its mount. The additional settled result measures every actual installed vertex and allows arbitrary character yaw. Both methods cover every phase between samples. Vertical gaps assume the fully reached tool height.',loads=placements,results=results)
(out/'Continuous-clearance.json').write_text(json.dumps(report,indent=2)+'\n')
