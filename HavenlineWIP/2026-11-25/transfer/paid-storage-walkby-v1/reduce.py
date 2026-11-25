import json,sys,math
from pathlib import Path
log=Path(sys.argv[1]).read_text().splitlines()
def numbered(prefix):return [json.loads(s[len(prefix):]) for s in log if s.startswith(prefix)]
S,=numbered('WALK_SUM ')
G=numbered('WALK_GEOM ')
O=numbered('WALK_OBSTRUCTION ')
assert len(G)==S['camera_geometric_samples'] and len(O)==S['obstructed_ticks']
assert not any('ERROR' in s or 'WARNING' in s for s in log)
C=[s for s in log if s.startswith('FAIL ')]
assert len(C)==S['failures']
v=(math.hypot(r['motion'][0],r['motion'][2]) for r in G)
def hull_delta(a,b):return max(a[0]-b[2],a[1]-b[3],b[0]-a[2],b[1]-a[3])
motion=[]
for r,v in zip(G,v):
 r['requested_world_horizontal_native_speed_m_s']=v
 r['occlusion_conservative_separations_native_units']=[[hull_delta(a,b) for b in [r['skin_rect']]+r['carry_rects']] for a in r['target_rects']]
 if r['animation'].endswith('/run') and r['anim_t']>1e-5 and v>.65:
  motion.append(r)
summ={}
for phase in dict.fromkeys(r['phase'] for r in G):
 gr=[r for r in G if r['phase']==phase]
 mr=[r for r in motion if r['phase']==phase]
 summ[phase]=dict(total_observed=len(gr),geometrically_open=sum(r['both_conservative_open'] for r in gr),
   genuine_nonzero_phase_run=len(mr),geometrically_open_run=sum(r['both_conservative_open'] for r in mr))
assert {'near_edge_approach','along_west_departure'}<=summ.keys()
near=next(r for r in G if r['phase']=='near_edge_approach' and r['tick']==1333)
assert near['both_conservative_open'] and near['world'][0]<-6.
disk=lambda r:[r[j] for j in [0,2]]
print(json.dumps({'native_summary':S,'failure':['conservative swept carry check did not clear' for s in C],
 'camera_phase_counts':summ,'min_actor_local_back_skin_gap_in_samples_m':min(r['actor_local_back_gap_m'] for r in G),
 'near_waypoint_origin_error_xz_m':math.dist(disk(near['world']),[-6.125,6.95]),'near_waypoint_sample':near,
 'sampled_scene_vertex_rays_blocked':sum(sum(r['scene_rays_blocked']) for r in G),
 'sampled_scene_vertex_rays_total':sum(sum(r['scene_rays_total']) for r in G),
 'walk_geometry_samples':G,'obstructions':O},sort_keys=True,indent=2))
