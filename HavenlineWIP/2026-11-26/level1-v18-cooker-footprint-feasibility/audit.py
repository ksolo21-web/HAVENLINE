from pathlib import Path
from hashlib import sha256
import json, math
from PIL import Image
P=Path(__file__).resolve().parent; H=P.parent
prev=H/'hvn-l1-t05-cooker-same-asset-intake-v1'
stock=H/'hvn-l1-owner-gate-33035-v4-native-preflight-v1'
project=stock/'staged/HavenlineLevel1'
ref=H/'t05-fresh-v18-stage/32441.png'
def sha(p):return sha256(p.read_bytes()).hexdigest()
assert sha(prev/'SHA256SUMS')=='aa3dc3b4a22aeb3150b213c1c406d00aeb261502e9ad317515fae39a2060dce5'
for s in (prev/'SHA256SUMS').read_text().splitlines():
 a,b=s.split(maxsplit=1);assert sha(prev/b)==a
old=json.loads((prev/'result.json').read_text())
assert old['cooker_exact_sha256']=='1173994824998d02c1d2cfa86ac4f0f7c88381eddc1715d81680a11c68cdcbba'
assert sha(project/'layout.json')==old['current_level1_exact_checked_source']['layout.json']
layout=json.loads((project/'layout.json').read_text())
script=(project/'previews/integrated_opening.gd').read_text()
assert 'cylinder.radius = .85' in script and 'model(HEARTH, vessel_root, 1.8)' in script
assert layout['actor_radius']==.31 and layout['actor_height']==1.75 and layout['furnace_xz']==[0,0]
assert layout['furnace_cost']=={'wood':3}
assert sha(stock/'graphics-evidence.cklm7tMU/paid-first-frame.png')=='d5c5055af8a02d6d67fcd82110f408ae2af3b3e4a12b4eade41bcbbcba2fb4ca'
with Image.open(ref) as im:assert im.size==(1536,903)
# Plausibility-only coordinates: L1 logical layout-local, preserve original cardinal transfer axis and nominal fit.
x,z=-2.75,-1.45
w,h,d=old['scale_comparisons']['historical_fit']['world_xyz_m']
assert d<=2.300001
xmin,xmax=x-w/2,x+w/2; zmin,zmax=z-d/2,z+d/2
def dist_rect(point,box):
 a,b=point; l,q,r,s=box
 return math.hypot(max(l-a,a-r,0),max(q-b,b-s,0))
# Conservative transfer END-point approach reserve outside nominal ±1.35 positions.
# It is a feasibility corridor, not an actual socket or actor route authority.
approach=.45
end_n,end_s=z-1.35-approach,z+1.35+approach
tube=(x-.31,end_n-.31,x+.31,end_s+.31)
box=(xmin,zmin,xmax,zmax)
room=[-5+.15,-4+.15,5-.15,4-.15]
def interior_slack(r):
 return min(r[0]-room[0],r[1]-room[1],room[2]-r[2],room[3]-r[3])
assert interior_slack(box)>1 and interior_slack(tube)>.25
hearth=dist_rect((0,0),box)-.85
assert hearth>1.30
points=[[0.,3.30],[0.,2.4],[0.,2.],[0.,6.],[2.,1.9],[3.,0.],[7.,0.]]
assert min(dist_rect(tuple(p),box)-.31 for p in points)>1.9
assert all(a>0 for a in [(-1.2)-xmax, abs(x-.0)-w/2-.31])
# Calibrated ortho metric using known V4 hinges (human/foot-apex height only, not posed silhouette).
phase=(stock/'graphics-evidence.cklm7tMU/write.log').read_text()
import re
r=next(json.loads(s) for s in re.findall(r'^OWNER33035_DRAW_BOUND (.+)$',phase,re.M) if '"phase":"paid-first-frame"' in s)
p=r['gates']['gate-south']['projected_hinge_verticals_px'][0]
y=(p[1]-p[3])/1.35
assert math.isclose(y,720/13*math.sqrt(1-121/291),abs_tol=1e-4)
# Manual exact-reference observation bounds exclude smoke: full rear plate and equipment from about (109,123) to (1428,797).
# Give ±7px each side, and no linear-scale inference from isolated reference art.
rlo=(674-14)/(1319+14);rhi=(674+14)/(1319-14)
assert rlo<h/d<rhi
def coords(dx,dz):
 s=math.sqrt(170);n=math.sqrt(291)
 return [(720/13)*(11*dx-7*dz)/s,(720/13)*11*(7*dx+11*dz)/(s*n)]
hc=coords(x,z)
assert hc[0]<-80 and hc[1]<-85
print(json.dumps({'interpretation':'One plausible plan envelope, no approved origin/site/socket/route or rendered result',
'geometry_exact_source':old['cooker_exact_sha256'],'normal_actual_desktop_paid_control_hash':sha(stock/'graphics-evidence.cklm7tMU/paid-first-frame.png'),
'reference_sha256':sha(ref),'reference_height_over_platform_approx_band': [rlo,rhi],
'equipment_height_over_legacy_transfer_axis_depth':h/d,'normal_camera_vertical_pixels_per_meter':y,
'orthographic_measured_axis_height_only_px':{'candidate_v18':h*y,'same_actual_hero_height_datum':1.75*y,'protected_hearth_height_datum':1.8*y},
'analytic_fixture_local_xz_only':[x,z],'physical_xz_aabb':box,'legacy_connector_plane_radius_m':1.35,
'computed_actor_access_tube_not_real_sockets':tube,'wall_inner_edge_slack_m':[interior_slack(box),interior_slack(tube)],
'hearth_surface_axis_plan_clearance_m':hearth,'nearest_sampled_ordinary_route_points_capsule_edge_clearance_m':min(dist_rect(tuple(p),box)-.31 for p in points),
'camera_screen_x_y_offset_from_hearth_assuming_level_ground_px':hc,'ground_elevation_and_support_unmeasured':True},indent=2))
