from pathlib import Path
import hashlib,json,io,contextlib,runpy,sys,subprocess,re
import numpy as np
import math
base=Path('..'); repo=Path(sys.argv[1]); asset=Path(sys.argv[2])
def packet(name,d):
 p=base/name
 assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()==d
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
 return p
pre=packet('hvn-l1-transfer-actual-scene-anchor-repair-v2','db8872b992dc84c09eb146a5ef90dae0e7f0c160bc453583254bc432a725e47f')
combined=packet('hvn-l1-v5-paid-pine-combined-v1','950d1a8b9992596a7b56ec64c7c98fbe1c9d34c04e698a78fb0dfbc50db4b031')
end=packet('hvn-l1-wood-storage-near-row-v1','b8f6061ab8f7b685beda4629ade265407b7bd5e5dfc649b2197a9b902b8767d6')
packet('hvn-l1-storage-near-row-independent-v1.FHNUiw','e10f9b28b237289fd8e2258a96a10ac310f0ae746ef34009ffc25e34a7a7ae51')
pin='11c14a1c41971067c7dc97db69375f720a408f68'
def src(x):return subprocess.check_output(['git','-C',repo,'show',pin+':HavenlineLevel1/'+x])
lod,_=runpy.run_path(str(base/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](asset)
v=np.unique(lod.reshape(-1,3),axis=0)
radius=float(np.linalg.norm(v,axis=1).max())
shift=np.array([-3.25,5.80])
layout=json.loads(src('layout.json'))
gate=src('technical_gate.gd').decode()
assert 'cylinder.radius = .85' in src('previews/integrated_opening.gd').decode()
def prop(n):return float(re.search('const '+n+r' := ([.0-9]+)',gate)[1])
rad=layout['actor_radius']
margin=rad+prop('SAFETY_MARGIN')+.5*prop('LEAF_DEPTH')
s=prop('HALF_SPAN')+margin
# No gameplay transfer trigger: only geometric centerline comparisons.
boxes={'south_actor_freeze_box':np.array([-s,4-prop('LEAF_LENGTH')-margin,s,4+margin]),
 'east_actor_freeze_box':np.array([5-prop('LEAF_LENGTH')-margin,-s,5+margin,s]),
 'north_detached_counter_reserve':np.array([-2.135,-4.48,2.135,-2.15])}
p=.5*prop('LEAF_DEPTH'); L=prop('LEAF_LENGTH')
boxes.update({'south_actual_leaf_conservative_box':np.array([-prop('HALF_SPAN')-p,4-L-p,prop('HALF_SPAN')+p,4+p]),
 'east_actual_leaf_conservative_box':np.array([5-L-p,-prop('HALF_SPAN')-p,5+p,prop('HALF_SPAN')+p])})
boxes.update({f'wall_{i}':np.array([x-w/2,z-d/2,x+w/2,z+d/2]) for i,(x,z,w,d) in enumerate(layout['walls_xz'])})
def pointbox(x,b):
 return float(np.linalg.norm(np.maximum(np.maximum(b[:2]-x,x-b[2:]),0)))
def segp(a,b,q):
 d=b-a; f=float(np.clip((q-a)@d/(d@d),0,1))
 return float(np.linalg.norm(a+f*d-q))
def segbox(a,b,box):
 # Exact 2D distance via endpoints plus all box vertices, with segment
 # interval need for polygon edge intersections.
 d=b-a; l,h=0,1
 for i in range(2):
  if abs(d[i])<1e-12:
   if not box[i]<=a[i]<=box[i+2]:l,h=1,0;break
  else:
   p,q=sorted(((box[i]-a[i])/d[i],(box[i+2]-a[i])/d[i]))
   l,h=max(l,p),min(h,q)
 if l<=h:return 0.
 return min(pointbox(a,box),pointbox(b,box),*(segp(a,b,np.array([x,z])) for x in (box[0],box[2]) for z in (box[1],box[3])))
row=[json.loads(x[14:]) for x in (pre/'replay.log').read_text().splitlines() if x.startswith('ANCHOR_RESULT ')]
ref=next(q for q in row if q['scenario']=='clean'); assert (ref['checks'],ref['failures'])==(157,0)
starts=[np.asarray(q['actual'])[[0,2]]-shift for q in ref['launches'] if 'launch'in q]
assert len(starts)==2 and len(ref['surface_roles'])==2
with contextlib.redirect_stdout(io.StringIO()):
 m=runpy.run_path(str(base/'havenline-buy-plot-footprint-study-v8/project.py'))
for f in ('accepted_t02_surface.gd','river_geometry.gd','terrain_source.gd'):
 assert src(f)==(m['pin']/f).read_bytes()
H=m['height']
# Source bound named movement waypoints, not assumed no postpay dynamic actor interference.
locus=np.array([0.,2.]); late=np.array([-.40,1.72]); outer=np.array([0.,6.])
route=src('tests/test_integrated_opening.gd').decode()
assert '[0.0, 2.0], [0.0, 6.0]' in route and '[-.40, 1.72]' in (pre/'test_transfer_anchor.gd').read_text()
log=(combined/'funded.log').read_text()
assert all(c in log for c in ['PASS South gate physical outward traversal','PASS South gate physical return traversal','PASS one +1 original pine occurrence'])
# Candidate locus is an existing interior gate checkpoint. Distances below
# are center/capsule comparisons, not production input eligibility.
footrows=[]
for label,w in [('south_inner_existing_waypoint',locus),('late_step_existing_unpaid_waypoint',late),('south_outer_existing_waypoint',outer)]:
 footrows.append({'tag':label,'local_xz':w.tolist(),'world_xz':(w+shift).tolist(),
  'terrain_y':H(*(w+shift)),'west_furnace_actor_clearance_m':float(np.linalg.norm(w))-.85-rad,
  'inside_either_native_freeze_box':any(pointbox(w,box)==0 for n,box in boxes.items() if n.endswith('freeze_box')),
  'gap_to_actual_box_min_less_actor_radius_m':min(pointbox(w,b)-rad for n,b in boxes.items() if '_actual_leaf_' in n or n.startswith('wall_'))})
docs=json.loads((end/'result.json').read_text())
pairs=[]
for i,(a,tf) in enumerate(zip(starts,docs['detached_log_transforms'])):
 b=np.asarray(tf['t_source_to_source_world'])[[0,2]]-shift
 # All allowed orientations of an exact finite source mesh are bounded by
 # its actual max vertex radius about the source node origin, not a box guess.
 gaps={n:segbox(a,b,c)-radius for n,c in boxes.items()}
 hearth=segp(a,b,np.zeros(2))-.85-radius
 world_low=np.minimum(a,b)+shift-radius;world_high=np.maximum(a,b)+shift+radius
 vals=[]
 for ix in range(math.floor(world_low[0]*4),math.ceil(world_high[0]*4)+1):
  for iz in range(math.floor(world_low[1]*4),math.ceil(world_high[1]*4)+1):
   vals.append(H(ix/4,iz/4))
 topbound=max(vals)+.012
 pairs.append(dict(terrain_plus_visible_lift_upper_bound_m=topbound,pre_hover_source_origin_y_sufficient_to_clear_floor_m=topbound+radius,log_i=i,archived_unpaid_start_local_xz=a.tolist(),display_end_pose_origin_local_xz=b.tolist(),
   source_origin_sphere_radius_m=radius,hearth_clearance_m=hearth,static_plan_gaps_m=gaps,
   note='Unpaid start endpoint only; actual awaited postpay local anchor could differ. Swept sphere protects arbitrary rotations but not actor or other log without authentic state.'))
print(json.dumps(dict(source_pin=pin,origin_radius_exact_mesh_m=radius,locus_source_rows=footrows,
 archival_launch_continuity_delta_m=ref['launches'][1]['late_live_displacement_m'], plan_carry_to_hover_only=pairs),indent=2,sort_keys=True))
