from pathlib import Path
import hashlib,json,numpy as np, math
R=Path(__file__).resolve().parent;Q=R.parent/'hvn-l1-fence-33036-owner-sized-seam-admission-v1'
assert hashlib.sha256((Q/'SHA256SUMS').read_bytes()).hexdigest()=='b1f68c0676013b7ada505c040c02ff02befbef23ca49093659b348b81c750e2e'
src=(Q/'section.py').read_text(); n={'__file__':str(Q/'section.py')}
exec(src[:src.index('results={}')],n)
O,A,spec=n['O'],n['A'],n['spec']
pins=json.loads((Q/'result.json').read_text())['joins']
out={}
for nb,(run,pk,rem,(ra,rb),ax,sign) in spec.items():
 trans=2 if ax==0 else 0
 # Outward world axis for genuine SOUTH (Z+) or WEST (X-), independently of tangent.
 outward=1 if nb=='SW1' else -1
 line=9.8 if nb=='SW1' else -8.25
 old=O[run+'/'+pk]
 next_owner=(run+'/post7' if nb=='SW1' else run+'/post2')
 inward_neighbor=O[next_owner]
 outward_neighbor=A[nb][0][ra:rb+1]
 # Protected existing decorative post centerline, not an invisible reanchor.
 postcen=(old.min((0,1))+old.max((0,1)))*.5
 roots=float(outward*(postcen[trans]-line))
 pairs={k:float(np.min(sign*u[:,:,ax].ravel())-sign*postcen[ax]) for k,u in [('outward_neighbor',outward_neighbor),('inward_neighbor',inward_neighbor)]}
 inward_edge=float(sign*postcen[ax]-np.max(sign*inward_neighbor[:,:,ax].ravel()))
 outward_edge=float(np.min(sign*outward_neighbor[:,:,ax].ravel())-sign*postcen[ax])
 centers=[float(outward*(d['existing_owner_rail_depth_center_m']-line)) for d in pins[nb]]
 rawrail=max(centers)+.05655
 # Exact scope upper housing of all original colored physical hemp on agreed arm.
 # Full span is conservative vs a local phase redesign, rejects if showing a claimed equivalent.
 ropes=[t for k,t in O.items() if k.startswith(run+'/') and 'return' in k]
 def clipped_axis(tris, a, b):
  out=[]
  for t in tris:
   if t[:,ax].max()<a or t[:,ax].min()>b:continue
   for v in t:
    if a<=v[ax]<=b:out.append(v)
   for u,v in zip(t,np.roll(t,-1,axis=0)):
    for q in (a,b):
     if (u[ax]-q)*(v[ax]-q)<0:out.append(u+(v-u)*(q-u[ax])/(v[ax]-u[ax]))
  return np.asarray(out)
 local=[clipped_axis(t,postcen[ax]-.13,postcen[ax]+.13) for t in ropes]
 outer_hemp=float(max((outward*(t[:,trans]-line)).max() for t in local if t.size))
 full=float(max((outward*(t[:,:,trans]-line)).max() for t in ropes))
 near_rail_hemp_out=max(rawrail,outer_hemp)
 seat_guard=.002;roof=1.02
 need=near_rail_hemp_out+seat_guard
 centered_radius_for_regular_20=need/math.cos(math.pi/20)
 center_held_symmetric=(need-roots)/math.cos(math.pi/20)
 # envelope supports asymmetric oval/trapezoid if actual appearance and loop tolerances permit;
 # these numbers are absolute best-case outer strips at original root, not designed geometry.
 positive_axis_budget=min(inward_edge,outward_edge)
 foot={
  'protected_lane_half_width_m':.15,'optional_prior_art_half_width_m':.14742,'advertised_owner_neutral_round_timber_radius_m':.142,'advertised_neutral_icing_radius_m':.14484,
  'same_root_world_xyz_bbox_center_m':postcen.tolist(),'root_transverse_outward_relative_to_lane_m':roots,
  'clear_axial_half_shell_between_unchanged_timbers_m':positive_axis_budget,
  'inward_outward_axial_limits_m':[inward_edge,outward_edge],
  'required_low_upper_world_vertical_rail_crown_intervals_m':[[d['exact_owner_tip_plane_xyz_m'][1]-.064,d['exact_owner_tip_plane_xyz_m'][1]+.064] for d in pins[nb]],
  'terminal_hemp_transport_outer_m':outer_hemp,'max_whole_owner_hemp_transport_outer_m':full,'full_rail_outward_extent_m':rawrail,
  'absolute_required_outer_extent_with_guard_m':need,
  'symmetric_stock_root_round_post_required_radius_m':center_held_symmetric,
  'symmetric_stock_root_round_cap_outward_and_inward_extent_relative_lane_m':[roots+roof*center_held_symmetric,roots-roof*center_held_symmetric],
  'lane_centered_round_20facet_requirement_m':centered_radius_for_regular_20,
  'lane_centered_crown_projected_extent_m':roof*centered_radius_for_regular_20,
  'lane_centered_only_radial_margin_to_150mm_m':.15-roof*centered_radius_for_regular_20,
  'old_root_geometry_must_not_translate':True}
 out[nb]=foot
(R/'result.json').write_text(json.dumps(dict(scope='exact fixed-root rectangular world envelope and accepted owner-family thickness sensitivity, NOT geometry/mesh/collider test',joins=out),indent=2)+'\n')
