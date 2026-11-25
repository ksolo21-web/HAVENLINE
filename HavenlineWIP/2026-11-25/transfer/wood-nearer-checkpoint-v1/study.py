from pathlib import Path
import contextlib,hashlib,io,json,math,runpy,subprocess,sys
import numpy as np
from scipy.spatial.transform import Rotation
root=Path(__file__).resolve().parent.parent
repo=Path(sys.argv[1]); mesh=Path(sys.argv[2]); raw_hero=Path(sys.argv[3])
pin='11c14a1c41971067c7dc97db69375f720a408f68'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def packet(n,h):
    p=root/n
    assert sha(p/'SHA256SUMS')==h
    subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
    return json.loads((p/('native-result.json' if (p/'native-result.json').exists() else 'result.json')).read_text())
native=packet('hvn-l1-wood-paid-two-piece-candidate-v1','2dbde03441fe996bab357c37291ee9cbe229bf7a4fbdaf0885313f90cac2c8f5')
carry=packet('hvn-l1-wood-paid-carry-capture-v1','af819aeb459d6835f43f1f5f015d78abc6916a561b3c3cd7190dfe08eb6a1b98')
end=packet('hvn-l1-wood-storage-near-row-v1','b8f6061ab8f7b685beda4629ade265407b7bd5e5dfc649b2197a9b902b8767d6')
assert sha(mesh)=='31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554'
tris,_=runpy.run_path(str(root/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](mesh)
V=np.unique(tris.reshape(-1,3),axis=0); assert len(V)==834
radius=float(np.linalg.norm(V,axis=1).max())
def src(x):return subprocess.check_output(['git','-C',repo,'show',pin+':HavenlineLevel1/'+x])
layout=json.loads(src('layout.json'))
opening=src('previews/integrated_opening.gd').decode()
assert all(s in opening for s in ['cylinder.radius = .85','floor.position.y = .012','for row in layout.walls_xz'])
with contextlib.chdir(root/'hvn-l1-wood-storage-near-row-v1'),contextlib.redirect_stdout(io.StringIO()):
    t=runpy.run_path(str(root/'havenline-buy-plot-footprint-study-v8/project.py'))
for x in ('accepted_t02_surface.gd','river_geometry.gd','terrain_source.gd'):
    assert src(x)==(t['pin']/x).read_bytes()
H=t['height']
record=native['samples'][0]; old=carry['native']; assert native['pass_count']==20 and native['failures']==0
assert record['actor_world']==old['actor_world']['origin'] and record['tick']==old['tick']==1277
assert record['anim']==old['settled_animation'] and record['anim_t']==old['settled_animation_time']
B=np.array(old['carry_root_world']['basis_cols']).T; q=np.array(record['actor_world'])
assert np.linalg.norm(B.T@B-np.eye(3),ord=np.inf)<1e-5
radius*=max(1.,float(np.linalg.norm(B,ord=2)))
starts=[np.array(d['world']) for d in record['stock_on_real_actor']]
assert all(abs(B@d['local']+q-a).max()<1e-6 for d,a in zip(record['stock_on_real_actor'],starts))
reshaped=Path(root/'hvn-l1-wood-paid-two-piece-candidate-v1/paid_piece_methods.gdfrag').read_text()
assert 'source_crown.transform != Transform3D.IDENTITY' in reshaped
# Source child identity: only a local origin is set. Basis comes from the
# paired original-run mount capture, not exported in the two-piece capture.
assert 'crown.position = centers[i]' in reshaped and 'crown.basis' not in reshaped
caps=old['actor_collisions'][0]
c=np.array(caps['world']['origin']); rad=caps['radius']; height=caps['height']
caps_box=np.stack([c-np.array([rad,height/2,rad]),c+np.array([rad,height/2,rad])])
body=np.array(carry['world_cpu_skin_bounds'])
actor_box=np.stack([np.minimum(body[0],caps_box[0]),np.maximum(body[1],caps_box[1])])
# Local AABB combines native CPU-skinned whole-body bounds and an enclosing
# prism of the actual vertical capsule, not a visual proxy for either alone.
body_local=np.array(carry['actor_relative_cpu_skin_bounds'])
cz=np.linalg.solve(B,c-q)
actor_local_box=np.stack([np.minimum(body_local[0],cz-[rad,height/2,rad]),np.maximum(body_local[1],cz+[rad,height/2,rad])])
shift=np.array([-3.25,5.80]); hearth=np.array(layout['furnace_xz'])+shift
def slab(x):return np.stack([x.min(0),x.max(0)])
def xz(x):return x[..., [0,2]]
boxes={}
for gate in old['gates']:
    for leaf in gate['leaf_boxes']:
        assert leaf['layer']==1
        R=np.array(leaf['shape_world']['basis_cols']).T
        p=np.array(leaf['shape_world']['origin'])
        d=np.abs(R)@(.5*np.array(leaf['size']))
        boxes[gate['gate_id']+'-'+leaf['hinge']]=xz(np.stack([p-d,p+d]))
for k,(x,z,w,d) in enumerate(layout['walls_xz']):
    p=np.array([x,z])+shift; size=np.array([w,d])/2
    boxes['wall-'+str(k)]=np.stack([p-size,p+size])
def maxgap(a,b):return float(np.max(np.maximum(b[0]-a[1],a[0]-b[1])))
def pbox_gap(p,a):return float(np.linalg.norm(np.maximum(np.maximum(a[0]-p,p-a[1]),0)))
def world(V,B,p):return V@B.T+p
def terrain_bound(box):
    # Affine floor patches on the exact quarter-metre grid are bounded by
    # their vertices; include every grid cell incident on this rectangle.
    ll,hh=xz(box)
    return max(H(i/4,j/4) for i in range(math.floor(ll[0]*4),math.ceil(hh[0]*4)+1)
              for j in range(math.floor(ll[1]*4),math.ceil(hh[1]*4)+1))+.012
dest=[(np.array(x['R_source_to_source_world']),np.array(x['t_source_to_source_world'])) for x in end['detached_log_transforms']]
parks=[slab(world(V,R,e)) for R,e in dest]; startbox=[slab(world(V,B,a)) for a in starts]
from scipy.spatial import ConvexHull
from collections import defaultdict
def bounds_of(p):return np.stack((p.min(0),p.max(0)))
safe=packet('hvn-l1-wood-storage-camp-fit-v1','af1d5e7ed9f9043b6b1becb008bdff5a1e6196e1ed5b779b5d9d6ef039ee2548')
entry=packet('hvn-l1-wood-storage-entry-route-v1','31fd140a463973a16141bcabd78957165dcbcc3d52f51549c22b254a8d2be5b7')
ind=packet('hvn-l1-wood-paid-handoff-independent-v1.h4wAS6','07709d6c43953379330032d881e68730bdcc7f8f823b1afe49757ccc81dea870')
run=packet('hvn-l1-wood-paid-two-piece-independent-v1.XTDZvo','ccbaf423bbca4c1e90ac373b58364731fda7734eaf4b39c23071d344cbd2be25')
assert len(run['ordinary_run_seconds'])==4 and run['min_skin_plane_mm']>60
assert sha(raw_hero)==carry['local_raw_cpu_pose_sha256']=='6b05599d7bc7d0563a568572d1af4e35ed627d8c746dfc6c5c7ca4824683a266'
Rint=np.linalg.inv(B)
hero=json.loads(raw_hero.read_text())
G0=np.concatenate([np.asarray(z['positions'])[np.unique(z['triangles'])] for z in hero])
assert sum(len(z['triangles']) for z in hero)//3==96001
assert np.allclose(bounds_of(G0),body,atol=1e-6)
body_actor=(G0-q)@Rint.T
log_act=[V+np.array(d['local']) for d in record['stock_on_real_actor']]
envelope=np.asarray(safe['whole_footprint_envelope_relative_xz_m'])+shift
boxes['reserved_detached_counter']=np.array([[-2.135,-4.48],[2.135,-2.15]])+shift
guard_boxes={name:np.asarray(ext).reshape(2,2)+shift for name,ext in safe['south_east_static_keepouts_m'].items()}
# Predeclare one source-derived east-side inspection aisle point. No receiver/trigger.
local=np.array([-.98,1.27])
first=q[[0,2]].copy(); bend=np.array([local[0],first[1]-shift[1]])+shift; target=local+shift
height_bias=float(q[1]-H(*first))
qy=H(*target)+height_bias
qin=np.array([target[0],qy,target[1]])
route_waypoints=np.array([first,bend,target])
assert np.all(np.abs(route_waypoints)<=np.array([14.2,16.2])-.31)
# Exact finite terrain grid expanded by inspected body/capsule/held support.
worst_r=max(np.linalg.norm(xz(v),axis=1).max() for v in [body_actor]+log_act)
RADIUS=float(worst_r)
def segment_point_gap(a,c,p):
 d=c-a
 if d@d==0:return float(np.linalg.norm(p-a))
 return float(np.linalg.norm(a+np.clip((p-a)@d/(d@d),0,1)*d-p))
# Waveform: first ordinary westward input, then ordinary northward input.
# At bends the finite global radial envelope bounds any yaw of the exact
# source pose, independent of which turn interpolation is used. No new pose.
def perp_clear(body,a,c,yaw):
 rg=np.array([[math.cos(yaw),0,math.sin(yaw)],[0,1,0],[-math.sin(yaw),0,math.cos(yaw)]])
 seq=xz(body@rg.T)
 return np.stack((seq.min(0)+np.minimum(a,c),seq.max(0)+np.maximum(a,c)))
rigid_union=np.concatenate([body_actor,*log_act])
approach=[]
for i,(a,c) in enumerate(zip(route_waypoints[:-1],route_waypoints[1:])):
 yaw=(-math.pi/2,-math.pi)[i]
 A=perp_clear(rigid_union,a,c,yaw)
 sep={name:maxgap(A,bx) for name,bx in boxes.items()}
 sep['hearth']=pbox_gap(hearth,A)-.85
 turn={name:pbox_gap(a,bx)-RADIUS for name,bx in boxes.items()}
 turn['hearth']=np.linalg.norm(a-hearth)-.85-RADIUS
 # Transition over a low paint region is plan-screened for the actor capsule
 # against the full no-placement envelope (not asserting it is a physical slab).
 cap=np.stack([np.minimum(a,c)-.31,np.maximum(a,c)+.31])
 sep['actor_capsule_to_complete_unplaced_west_envelope']=maxgap(cap,envelope)
 for name,g0 in guard_boxes.items():
  # Existing actor freeze boxes already include the real capsule/safety. Only
  # nominal foot centerline is considered, no collision state is edited.
  sep[name+'_nominal_foot']=maxgap(np.stack([np.minimum(a,c),np.maximum(a,c)]),g0)
 lo=cap[0];hi=cap[1]
 xy=[(x/4,z/4) for x in range(math.floor(4*lo[0]),math.ceil(4*hi[0])+1) for z in range(math.floor(4*lo[1]),math.ceil(4*hi[1])+1)]
 heights=np.array([H(*g) for g in xy]); shores=[t['shore'](*g) for g in xy]
 slopes=[]
 for ix in range(math.floor(4*lo[0]),math.ceil(4*hi[0])):
  for iz in range(math.floor(4*lo[1]),math.ceil(4*hi[1])):
   a0,z0=ix/4,iz/4
   h0,hx,hz,he=[H(a0+u,z0+v) for u,v in ((0,0),(.25,0),(0,.25),(.25,.25))]
   slopes.extend([math.hypot(4*(hx-h0),4*(hz-h0)),math.hypot(4*(he-hz),4*(he-hx))])
 approach.append({'terrain_max_exact_grid_triangle_slope_deg':float(np.degrees(np.arctan(max(slopes)))) ,'exact_rigid_paid_mesh_yawed_corridor_min_gaps_m':sep,'turn_origin_radial_min_gaps_m':turn,
    'source_capsule_grid_dry_shore_min_m':float(min(shores)),'finite_capsule_ground_height_extrema_m':[float(heights.min()),float(heights.max())]})
# Nominal entire copy/pose is translated to the diagnostic stance; original
# raw mesh is unmodified and this is explicitly not a real sampled arrival.
Frot=np.array([[-1.,0,0],[0,1,0],[0,0,-1.]])
natives=body_actor@Frot.T+qin
blend_caps=np.array([-.31,0,-.31]),np.array([.31,1.785,.31])
AB=bounds_of(np.vstack([natives,*[q2+qin for q2 in blend_caps]]))
aLocal=bounds_of(np.vstack([body_actor,*blend_caps]))
Afirst=[qin+Frot@np.array(d['local']) for d in record['stock_on_real_actor']]
starts_boxes=[bounds_of(V@Frot.T+a) for a in Afirst]
motions=[]
# Both sequential geometric candidates preserve the reference earlier recipe
# geometry (same fixed lateral 1.23m, turn then pure vertical descent), no duration.
for i,(a,(R,e)) in enumerate(zip(Afirst,dest)):
 side=a+1.23*Frot[:,0]; hover=e.copy();hover[1]=a[1]
 Qs=[V@Frot.T+a,V@Frot.T+side,V@R.T+hover,V@R.T+e]
 vols=[bounds_of(np.vstack(Qs[:2])),np.stack([np.minimum(side,hover)-radius,np.maximum(side,hover)+radius]),bounds_of(np.vstack(Qs[2:]))]
 rec=[]
 for c,vol in enumerate(vols):
  metrics={name:maxgap(xz(vol),bx) for name,bx in boxes.items()}
  metrics['hearth']=pbox_gap(hearth,xz(vol))-.85
  metrics['hero']=maxgap(vol,AB)
  if c==0:
   sep_loc=bounds_of((np.vstack(Qs[:2])-qin)@Frot)
   metrics['hero']=maxgap(sep_loc,aLocal)
   if i==0:metrics['paired_still_owned_piece']=maxgap(sep_loc,bounds_of(log_act[1]))
  if 'paired_still_owned_piece' not in metrics:metrics['paired_still_owned_piece']=maxgap(vol,starts_boxes[1] if i==0 else parks[0])
  if c<2:metrics['above_source_visible_terrain']=float(vol[0,1]-terrain_bound(vol))
  else:
   assert end['terrain_support_and_full_mesh'][i]['visible_seat_min_full_convex_envelope_m']==0
   metrics['above_source_visible_terrain']=0.
  rec.append(metrics)
 knots=[a,side,hover,e]; L=sum(np.linalg.norm(v-u) for u,v in zip(knots,knots[1:]))
 motions.append({'sequence':i+1,'length_m':float(L),'old_m':ind['motions'][i]['path_m'],'symbolic_shortening_fraction':1-float(L)/ind['motions'][i]['path_m'],
                 'no_duration_or_speed_assumed':True,'source_offline_spatial_bounds_m':rec,'knots':knots,'key_mesh':Qs})
def sat2(A,B):
 # Exact convex-hull separation only.
 A=A[ConvexHull(A).vertices];B=B[ConvexHull(B).vertices]
 best=-float('inf')
 for points in (A,B):
  edges=np.roll(points,-1,axis=0)-points
  n=edges[:,[1,0]]*[-1,1];n/=np.linalg.norm(n,axis=1)[:,None]
  g=A@n.T;h=B@n.T
  best=max(best,float(np.max(np.maximum(h.min(0)-g.max(0),g.min(0)-h.max(0)))))
 return best
camera=np.array([7.,11.,11.]);camera/=np.linalg.norm(camera)
xdir=np.cross([0.,1.,0.],camera);xdir/=np.linalg.norm(xdir)
ydir=np.cross(camera,xdir)
def proj(a):return (a@np.array([xdir,ydir]).T)*(720/13)
def depth_screen(a):
 return np.concatenate((proj(a),a@camera[...,None]),axis=-1)
actor_raw_tri=np.concatenate([((np.asarray(z['positions'])-q)@Rint.T@Frot.T+qin)[np.asarray(z['triangles']).reshape(-1,3)] for z in hero])
ATR=depth_screen(actor_raw_tri)
def ray_mask(mesh_a,mesh_b):
 def plan(t):
  p=t[:,:,:2]
  lo,hi=p.min(1),p.max(1)
  a=p[:,1]-p[:,0];b=p[:,2]-p[:,0]
  det=a[:,0]*b[:,1]-a[:,1]*b[:,0]
  return lo,hi,a,b,det
 def dmax(P,T,Q):
  lo,hi,a,b,det=Q
  j=np.flatnonzero((lo<P).all(1)&(hi>P).all(1)&(abs(det)>1e-12))
  c=P-T[j,0,:2]
  u=(c[:,0]*b[j,1]-c[:,1]*b[j,0])/det[j]
  v=(a[j,0]*c[:,1]-a[j,1]*c[:,0])/det[j]
  keep=(u>=0)&(v>=0)&(u+v<=1)
  dz=T[j,0,2]+u*(T[j,1,2]-T[j,0,2])+v*(T[j,2,2]-T[j,0,2])
  return max(dz[keep],default=-float('inf'))
 apr=plan(mesh_a)
 lo,hi=apr[0].min(0),apr[1].max(0)
 m=(mesh_b[:,:,:2].min(1)<=hi).all(1)&(mesh_b[:,:,:2].max(1)>=lo).all(1)
 b=mesh_b[m];bpr=plan(b)
 hits, blocked=0,0; gaps=[]
 for x in np.arange(math.floor(lo[0]*4)/4+.125,hi[0],.25):
  for y in np.arange(math.floor(lo[1]*4)/4+.125,hi[1],.25):
   p=np.array([x,y]);v=dmax(p,mesh_a,apr)
   if not math.isfinite(v):continue
   hits+=1
   u=dmax(p,b,bpr)
   if u>v+1e-7:
    blocked+=1;gaps.append(u-v)
 return {'crown_ray_hits':hits,'body_nearer_ray_hits':blocked,'body_nearer_ray_fraction':blocked/hits if hits else None,
         'minimum_positive_depth_lead_m':min(gaps) if gaps else None,'projection_ray_pitch_px':.25,'raw_raster_claim':False}
vis=[]
PH=proj(natives)
for m in motions:
 S=m.pop('key_mesh')
 i=m['sequence']-1; a,si,h,e=m['knots']; R,_=dest[i]
 vis.append({'convex_screen_gaps_vs_hero_px':{tag:sat2(PH,proj(v)) for tag,v in zip(['mounted','clear_side','at_hover','parked'],S)},
             'parked_depth_test':ray_mask(depth_screen(tris@R.T+e),ATR),
             'hover_depth_test':ray_mask(depth_screen(tris@R.T+h),ATR)})
 m['knots']=[k.tolist() for k in m['knots']]
assert all(min(p['exact_rigid_paid_mesh_yawed_corridor_min_gaps_m'].values())>0 and min(p['turn_origin_radial_min_gaps_m'].values())>0 for p in approach)
assert all(all(v>=0 for row in m['source_offline_spatial_bounds_m'] for v in row.values()) for m in motions)
assert all(v['hover_depth_test']['body_nearer_ray_hits']==0 for v in vis)
assert vis[1]['parked_depth_test']['body_nearer_ray_fraction']==1
print(json.dumps(dict(status='HOLD_NEARER_SOURCE_FITS_PLAN_BUT_LOSES_PARKED_VISIBILITY',approach=approach,trial_local_xz=local.tolist(),ordinary_nominal_waypoints_pre_shift_xz_m=(route_waypoints-shift).tolist(),
 head_pose_note='Exact old idle source body and original two-crown pair rigidly translated/yawed only; no new phase measured.',
 normal_camera_hull_samples=vis,
 raw_source_hash=sha(raw_hero),followup_source_cut_ground_height_bias_m=height_bias,
 pressure_site_adopted=False,receiver_defined=False,actual_arrival_turn_or_render_proven=False,geometric_trial_paths=motions),indent=2,sort_keys=True))
