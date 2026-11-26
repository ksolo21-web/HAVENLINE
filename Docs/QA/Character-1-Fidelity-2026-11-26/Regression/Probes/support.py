"""Probe vertical component clearance between each first packet and actual support triangles."""
from pathlib import Path
import json
import os
import numpy as np

root = Path(os.environ['HAVENLINE_GEAR_GEOMETRY'])
output = Path(os.environ['HAVENLINE_PROBE_RESULTS'])
families = ('wood','stone','meat','coal','slate','metal')

def mesh_vertices(where, key):
    return np.fromfile(where/(key+'-v'),np.float32).reshape(-1,3)

def sample(where, family):
    vertices = mesh_vertices(where,family+'0')
    bottom = vertices[vertices[:,1] < vertices[:,1].min() + .055]
    best = 10.0
    points_covered=set()
    closest_mesh=None
    closest_signed=None
    for fn in [where/'rack-v',*sorted(where.glob('divider-*-v'))]:
        tag=fn.name[:-2]
        vertices=mesh_vertices(where,tag)
        faces=np.fromfile(where/(tag+'-f'),np.int32).reshape(-1,3)
        a,b,c=vertices[faces].transpose(1,0,2)
        u=b-a; v=c-a
        den=u[:,0]*v[:,2]-v[:,0]*u[:,2]
        nonzero=np.abs(den)>1e-8
        den=np.where(nonzero,den,1)
        for index,(x,y,z) in enumerate(bottom):
            s=((x-a[:,0])*v[:,2]-v[:,0]*(z-a[:,2])) / den
            t=(u[:,0]*(z-a[:,2])-(x-a[:,0])*u[:,2]) / den
            h=a[:,1]+s*u[:,1]+t*v[:,1]
            intersects=nonzero&(s>=0)&(t>=0)&(s+t<=1)&(h<=y+.04)
            if intersects.any():
                points_covered.add(index)
                distances=y-h[intersects]
                signed=float(distances[np.argmin(np.abs(distances))])
                if abs(signed)<best:
                    best=abs(signed); closest_mesh=tag; closest_signed=signed
    return dict(underside_samples=len(bottom),rays_over_rack=len(points_covered),
                min_vertical_surface_distance_m=round(best,6) if closest_mesh else None,
                signed_gap_at_closest_m=round(closest_signed,6) if closest_mesh else None,
                closest_support_mesh=closest_mesh)

mixed={k:sample(root,k) for k in families}
single={k:sample(root/('single-'+k),k) for k in families}
report=dict(method='Vertical rays through every real imported underside vertex within 55 mm of the lowest vertex. Each candidate support mesh is tested at its in-game world transform. Positive signed distances are air gaps. Geometry within 40 mm above a vertex can represent partial embedment.',mixed=mixed,single_family=single)
(output/'Rack-support.json').write_text(json.dumps(report,indent=2)+'\n')
print({load:{k:v['min_vertical_surface_distance_m'] for k,v in family.items()} for load,family in [('mixed',mixed),('single',single)]})
