from pathlib import Path
import hashlib,json,math,numpy as np
from functools import lru_cache
R=Path(__file__).resolve().parent;P=R.parent
q=P/'hvn-l1-fence-33036-full-perimeter-repair-bound-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(q/'SHA256SUMS')=='45c8b73f0463f8158b1985b58ae0fa8f852799c0d57911de41f2e9e0e8a8c845'
ac=P/'hvn-l1-fence-33036-continuous-terminal-footprint-v1'
assert sha(ac/'SHA256SUMS')=='910141edea3f1e3dfd6b642f60b4ac55232bd90a793d6c492d5ff1e1f35c47db'
model=P/'hvn-l1-fence-33036-bold-wrap-v3/build.py'
value=model.read_text()
assert 'ROPE_RAD_Z=.0064' in value and 'radius_z,radius_y' in value and '.0069,.0235' in value and 'rail_rz=.0290' in value and 'rail_z=.0293' in value
ctx={'__file__':str(q/'verify.py')};exec((q/'verify.py').read_text().split('seams=')[0],ctx)
h=ctx['height']
# Two real two-panel placements, excluding actual gate stop strip (no edited gate).
# Continuous screening source runs every 0.25m terrain grid breakpoint and diagonal/rectangle intersections.
world={'South':{'ax':0,'lo':-8.25,'hi':-4.575,'center':9.8,'sgn':1},
       'West':{'ax':1,'lo':4.466666666666667,'hi':9.8,'center':-8.25,'sgn':-1}}
scale=1.95;recenter=.00975;rc=recenter+.0293*scale;rd=.0290*scale
N=.14742;B=.002
width=(.0069*scale*2)
paint=.012
zones={};tol=1e-10
@lru_cache(None)
def hs(x,z):return float(h(np.array([x,z])))
def corners(ax,a,b,outlo,outhi):
 lo,hi=(np.array([a,outlo]),np.array([b,outhi])) if ax==0 else (np.array([outlo,a]),np.array([outhi,b]))
 grids=[]
 for p,q in zip(lo,hi):
  grids.append([p,*[k/4 for k in range(math.ceil(p*4),math.floor(q*4)+1) if p<k/4<q],q])
 V={(x,z) for x in grids[0] for z in grids[1]}
 for i in range(math.floor(lo[0]*4),math.ceil(hi[0]*4)):
  for j in range(math.floor(lo[1]*4),math.ceil(hi[1]*4)):
   d=(i+j+1)/4
   for k in lo[0],hi[0]:
    z=d-k
    if i/4-tol<=k<=(i+1)/4+tol and j/4-tol<=z<=(j+1)/4+tol and lo[1]-tol<=z<=hi[1]+tol:V.add((k,z))
   for k in lo[1],hi[1]:
    x=d-k
    if j/4-tol<=k<=(j+1)/4+tol and i/4-tol<=x<=(i+1)/4+tol and lo[0]-tol<=x<=hi[0]+tol:V.add((x,k))
 return np.array([(x,z,hs(x,z)) for x,z in sorted(V)])
for k,d in world.items():
 ax,start,stop,center,sgn=[d[u] for u in ('ax','lo','hi','center','sgn')]
 o=sorted([center+(rc-rd)*sgn,center+(rc+rd)*sgn])
 v=corners(ax,start,stop,*o)
 extra=.064+.002
 raw=v[:,2]+extra
 # Pure construction inequality, not selected route: minimum rail center by declared 1:6 slope at both boundaries.
 slope=1/6
 worst_a=raw-slope*(v[:,ax]-start);worst_b=raw-slope*(stop-v[:,ax])
 edges=[start,*[i*.25 for i in range(math.ceil(start*4),math.floor(stop*4)+1) if start<i*.25<stop],stop]
 masks=[]
 for lo,hi in zip(edges[:-1],edges[1:]):
  vv=corners(ax,lo,hi,*o)
  masks.append({'s_range':[lo,hi],'exact_indexed_terrain_y_minmax':[float(vv[:,2].min()),float(vv[:,2].max())]})
 zones[k]={'world_axis_x_zero_z_one':ax,'protected_run_study_endpoints_m':[start,stop],
  'fixed_wall_line_other_axis_m':center,'rail_depth_strip_xyz_mapped_xz_axis_m':o,
  'global_physical_terrain_y_minmax_m':[float(v[:,2].min()),float(v[:,2].max())],
  'clip_exact_vertex_count':len(v),'all_segment_extrema':masks,
  'unguarded_low_raw_y_center_peak_needed_m':float(max(raw)),
  'minimum_end_center_y_with_inboard_grade_bound_m':[float(max(worst_a)),float(max(worst_b))],
  'upper_lower_band_separation_reference_m':.692}
sock={
 'snow_nominal_inside_reserve_m':N-.14484,
 'simple_back_course_nominal_full_depth_m':.0064*2*scale,
 'prior_continuous_lower_raw_rear_depth_wall_relative_m':recenter+(-.0235-.0448-.0035-.0064)*scale,
 'rear_wall_relative_guarded_limit_m':-N+B,
 'front_pair_recess_floor_if_lower_half_visible_plus_2mm_strand_separation_m':(.5*width+width+.002)-(N-B-(rc+rd))}
x={'status':'HOLD exact native body/rope route not authored; continuous-run study identifies external stack cross-sectional incompatibility',
 'study_bound_geometry_not_move_permission':world,
 'normal_cross_section_m':{'owner_snow_previous_rounded_crown_radius_m':.14484,'owner_rail_front_outward_surface_m':rc+rd,'owner_profile_height_depth_m':[.128,2*rd],
 'old_conservative_visual_half_width_m':N,'new_model_containment_reserve_m':B,
 'front_rope_nominal_full_depth_m_at_true_old_scale_before_relief':width,
 'outboard_available_beyond_full_exposed_rail_with_2mm_guard_m':N-B-(rc+rd),
 'upper_limb_alone_width_deficit_even_if_lower_does_not_protrude_m':width-(N-B-(rc+rd)),
 'no_assumptions_recorded_as_accepted_clearance':True},
 'source_stage_rejection':'No wholesale repeat, no retained-stock terminals. One full-size upper old rope over untouched round nose is wider than available guarded depth even giving hidden opposing limb zero outward thickness. Need joint section with arced recessed seats or intentionally revised non-round depth maintaining projected visible pale width; save only as concept. Bounds do not rule out a genuinely reauthored combined rail+rope section.',
 'remaining_art_channel_full_profile_bounds':sock,'run_bare_terrain_bounds_and_grade':zones}
(R/'result.json').write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
