"""Derive one conservative capsule-aware convex guard from the sealed owner-asset test.
Coordinates are metres in the actual counter-local XZ frame; no game writes.
"""
import sys, hashlib, json, math
from pathlib import Path
import numpy as np
EXPECTED='5596825cc730f97e3b4a84fd89f3ad0b5e5ae5f68e993db3d277540ad63caf58'
R=.310
ROBUST=.010
FOOT_GAP=.030
Z_INC=.005
OLD_BRIDGE_X_HALF=1.865
OLD_BRIDGE_Z_HALF=.150

def clip(poly,n,c):
    output=[]
    prev=poly[-1]
    old=prev@n-c
    for cur in poly:
        delta=cur@n-c
        if (delta>0)!=(old>0):
            output.append(prev+(cur-prev)*(old/(old-delta)))
        if delta<=0:output.append(cur)
        prev,old=cur,delta
    return np.array(output)
def from_axes(normal,support):
    poly=np.array([[-10.,-10.],[10.,-10.],[10.,10.],[-10.,10.]])
    for n,c in zip(normal,support):
        poly=clip(poly,n,c)
        assert len(poly)>=3
    # Only duplicate adjacent points can occur after equal adjacent supports.
    return np.array([q for j,q in enumerate(poly) if np.linalg.norm(q-poly[j-1])>1e-9])
def polygon_distance(x,poly):
    if all(np.cross(np.append(q-p,0),np.append(x-p,0))[2]>=-1e-11 for p,q in zip(poly,np.roll(poly,-1,axis=0))):
        return 0.
    p=poly; v=np.roll(p,-1,axis=0)-p
    s=np.clip(np.sum((x-p)*v,axis=1)/np.sum(v*v,axis=1),0.,1.)
    return float(np.linalg.norm(x-(p+s[:,None]*v),axis=1).min())
def z_bounds(poly,x):
    return sorted(float(z0+(z1-z0)*(x-a)/(b-a))
      for (a,z0),(b,z1) in zip(poly,np.roll(poly,-1,axis=0)) if abs(a-b)>1e-9 and min(a,b)<=x<=max(a,b))

p=Path(sys.argv[1])
assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED
old=json.loads(p.read_text())['support_contour']
normals=np.array(old['support_axes_xz']);h=np.array(old['max_outward_support_m'])
k=np.array(old['vertices_xz'])
# Numeric search is not a physics retune. It chooses the least scalar
# offset in this fixed-support family with a full polygon distance proof.
def trial(extra):
    q=from_axes(normals,h-R+extra)
    reach=max(polygon_distance(v,q) for v in k)
    return reach,q
a,b=0.,.1
for _ in range(40):
    m=(a+b)/2
    reach,_=trial(m)
    if reach<=R-ROBUST: b=m
    else: a=m
offset=math.ceil(b/.001)*.001
worst,shape=trial(offset)
assert worst<=R-ROBUST
xlo,zlo=shape.min(0);xhi,zhi=shape.max(0)
# Use the worst global support, not just the height line at X=0.
# Full capsule disc Minkowski reaches these upper/lower extrema.
calc_z=lambda v:math.ceil(v/Z_INC)*Z_INC
target_i=calc_z(zhi+R+FOOT_GAP)
target_o=-calc_z(-zlo+R+FOOT_GAP)
# Crosscheck the unchanged bridge has true area (not a one-point join).
overlap=shape
for n,u in [([1,0],OLD_BRIDGE_X_HALF),([-1,0],OLD_BRIDGE_X_HALF),([0,1],OLD_BRIDGE_Z_HALF),([0,-1],OLD_BRIDGE_Z_HALF)]:
    overlap=clip(overlap,np.array(n),u)
assert len(overlap)>2
w=np.roll(overlap,-1,axis=0)
area=abs(.5*np.sum(overlap[:,0]*w[:,1]-overlap[:,1]*w[:,0]))
print(json.dumps(dict(
    purpose='detached hypothetical proof only; no marker or interaction changes',
    original_marker_z=[1.35,-1.45],
    conservative_captured_pose_hull_sha256=EXPECTED,
    conditional_targets_xz={'inboard':[0,target_i],'outboard':[0,target_o]},
    extra_target_setback={'inboard':target_i-1.35,'outboard':-target_o-1.45},
    additional_motion_target_buffer_m=FOOT_GAP,
    actual_horizontal_capsule_radius_m=R,
    min_family_contour_extra_support_m=b,
    chosen_family_extra_support_m=offset,
    actual_worst_prior_hull_vertex_to_guard_m=worst,
    capsule_minus_worst_hull_distance_m=R-worst,
    robust_requested_envelope_overlap_m=ROBUST,
    guard_height_y_m=[0,.95],
    guard_vertices_xz=shape.tolist(),
    guard_x_minmax_m=[xlo,xhi],guard_z_minmax_m=[zlo,zhi],
    guard_capsule_envelope_z_minmax_m=[zlo-R,zhi+R],
    seam_center_actor_x_m=[-1.825,1.825],
    old_bridge_overlap={'x_range':sorted([float(overlap[:,0].min()),float(overlap[:,0].max())]),
                        'minimum_robust_X_reach_beyond_original_guard_end_1p5m':min(-xlo,xhi)-1.5,
                        'positive_XZ_area_sq_m':area,'unchanged_original_half_extent_x':OLD_BRIDGE_X_HALF},
    initial_shape_inboard_ray_at_x0=z_bounds(shape,0)
),indent=2))
