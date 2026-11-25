from pathlib import Path
import hashlib,json,subprocess,sys,re,math,runpy,io,contextlib
import numpy as np
from scipy.optimize import linprog
base=Path('..'); repo=Path(sys.argv[1]); pin='11c14a1c41971067c7dc97db69375f720a408f68'
def git(f):return subprocess.check_output(['git','-C',repo,'show',pin+':HavenlineLevel1/'+f])
def hash_(x):return hashlib.sha256(x).hexdigest()
def manifest(p,s):
 assert hash_((p/'SHA256SUMS').read_bytes())==s
 subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
layout=json.loads(git('layout.json'))
active=git('previews/integrated_opening.gd')
for fragment in [b'CAMP_SHIFT := Vector2(-3.25, 5.80)',b'cylinder.radius = .85',b'floor.position.y = .012',b'block(camp_built, Vector3(float(row[2]), .95, float(row[3]))']:
 assert fragment in active
assert layout['camp_rect_xz']==[-5,-4,5,4] and layout['actor_radius']==.31 and layout['furnace_xz']==[0,0]
assert [x['center_xz'] for x in layout['gates']]==[[0,4],[5,0]]
shade=git('previews/integrated_camp_floor.gdshader')
assert b'terrain_xz.x < bounds.x' in shade and b'discard' in shade
gate=git('technical_gate.gd').decode()
def gc(k):return float(re.search('const '+k+r' := ([.0-9]+)',gate)[1])
R=layout['actor_radius']
gm=R+gc('SAFETY_MARGIN')+.5*gc('LEAF_DEPTH'); sx=gc('HALF_SPAN')+gm
# Parent's baseline input driver and prior funded passed route. Use corridors for
# exact segments waypoints, not pretend actual continuous native trajectories.
test=git('tests/test_integrated_opening.gd').decode()
for frag in ['[0.0, 2.0], [0.0, 6.0]', '[3.0, 0.0], [7.0, 0.0]','[2.0, 1.9]']:assert frag in test
# Local coordinates before +(-3.25, 5.80), inner west wall x=-4.85, south z=3.85.
boxes=[('wall'+str(i),np.array([x-w/2,z-d/2,x+w/2,z+d/2])) for i,(x,z,w,d) in enumerate(layout['walls_xz'])]
# Exact code's conservative pair sweep occupancy rectangles, already including actor radius/safety.
boxes.extend([('south_sweep',np.array([-sx,4-gc('LEAF_LENGTH')-gm,sx,4+gm])),
 ('east_sweep',np.array([5-gc('LEAF_LENGTH')-gm,-sx,5+gm,sx]))])
f=base/'havenline-l1-fence-counter-fit-v1'
manifest(f,'c052cce25e3acaa82cf955df52d57f7c4decc68c1f46099d9499b8a2eb5fe5f2')
assert '3.65 m' in (f/'HANDOFF.md').read_text()
# Separate hypothetical customer reservation. Wider than bay by one actor radius
# an edge; conservatively keep through z=-2.15 for detached inward worker pose.
boxes.append(('detached_counter_reserve',np.array([-1.825-R,-4.48,1.825+R,-2.15])))
p=base/'hvn-l1-storage-reference-scale-v1'
manifest(p,'a142a105af37cdc3c81d988f4afa2af717870b04108b3fdd74879ff63da9a431')
# Evidence-conservative known nominal paths; keep extra radius for thumb-driven path error.
paths={'south_inner_to_out':[([0,2],[0,6])],'east_inner_to_out':[([3,0],[7,0])],
 'south_to_east_interior':[([0,2],[2,1.9]),([2,1.9],[3,0])],
 'paid_pad_to_south':[([0,2.4],[0,2])]}
# Prove an entire centre rectangle for near-quarter-turn placements by bounding
# the rotated projected rectangle over 89–91°, corners included. This isn't a placement.
W,D=2.886,2.270; slo=np.array([-2.96,-.06]);shi=np.array([-2.80,-.03]);th=np.radians(1.)
hx=(W*np.sin(th)+D*np.cos(th))/2
hz=(W*np.cos(th)+D*np.sin(th))/2
edge=np.array([hx,hz]); lo=slo-edge;hi=shi+edge
def bd(a,b,c,d):
 return float(np.linalg.norm(np.maximum(np.maximum(a-d,c-b),0)))
def distpoint(lo,hi,v):return float(np.linalg.norm(np.maximum(np.maximum(lo-v,v-hi),0)))
# For these polylines, AABB branch containment yields a conservative lower clearance,
# even if actual operator cuts slightly inside chords. Preserve a full .62m width.
routes={k:min(bd(lo,hi,np.minimum(a,b),np.maximum(a,b)) for a,b in c)-.41 for k,c in paths.items()}
gaps={n:bd(lo,hi,b[:2],b[2:]) for n,b in boxes}
gaps['hearth']=distpoint(lo,hi,np.zeros(2))-.85
gaps['purchase_plot_and_full_reach']=distpoint(lo,hi,np.array(layout['pad_xz']))-.72
assert all(gaps[n]>(0 if n.endswith("_sweep") else .62) for n in gaps) and min(routes.values())>.62
shift=np.array([-3.25,5.80]);be=lo+shift; en=hi+shift
# Reuse source-mirrored indexed terrain and verify bytes before using functions.
with contextlib.redirect_stdout(io.StringIO()):
 t=runpy.run_path(str(base/'havenline-buy-plot-footprint-study-v8/project.py'))
for f0 in ('accepted_t02_surface.gd','river_geometry.gd','terrain_source.gd'):
 assert git(f0)==(t['pin']/f0).read_bytes()
def terrain_points(L,H):
 coords=[]
 for i in range(math.floor(L[0]*4),math.ceil(H[0]*4)):
  for j in range(math.floor(L[1]*4),math.ceil(H[1]*4)):
   a,b,c,d=[(i/4+x,j/4+z) for x,z in [(0,0),(.25,0),(0,.25),(.25,.25)]]
   for seg in [[a,b,c],[b,d,c]]:
    for axis,bnd,keep_high in [(0,L[0],True),(0,H[0],False),(1,L[1],True),(1,H[1],False)]:
     seg=t['clip'](seg,axis,bnd,keep_high)
    if len(seg)>=3:coords+=seg
 pts=np.array(sorted(set(coords)))
 hs=np.array([t['height'](*q) for q in pts])
 return pts,hs
points,y=terrain_points(be,en)
mid=((slo+shi)/2)+shift; tight=np.array([D,W])/2
mp,my=terrain_points(mid-tight,mid+tight)
cl=np.array([-3.75,-1.25]); ch=np.array([-2.,1.22])
maxe=np.maximum(shi-cl,ch-slo)
diag=maxe+np.sin(th)*maxe[::-1]
# Interior reserve .13m exceeds the proposed uniform-XZ scaled .028m
# source top corner radius; that guarantees this common core before carry log use.
assert np.all(diag<np.array([D,W])/2-.13)
cc,cy=terrain_points(cl+shift,ch+shift)
def planar(q,h):
 # Best worst-case affine tilt, all extrema of piecewise affine terrain-minus-plane
 # occur at clipped indexed triangle vertices, so this finite LP covers entire rectangle.
 u=np.c_[q-q.mean(0),np.ones(len(q))]
 A=np.concatenate([np.c_[u,-np.ones(len(q))],np.c_[-u,-np.ones(len(q))]],axis=0)
 ans=linprog([0,0,0,1],A_ub=A,b_ub=np.r_[h,-h],bounds=[(None,None)]*3+[(0,None)],method='highs')
 assert ans.success
 return dict(n=len(q),min_y_m=float(h.min()),max_y_m=float(h.max()),horizontal_range_m=float(np.ptp(h)),best_tilt_sup_error_m=float(ans.fun),plane_slopes_xz=ans.x[:2].tolist(),min_vertex_shore_m=min(t['shore'](*p0) for p0 in q))
report={'pin':pin,'audit_source_blob_sha256':{k:hash_(git(k)) for k in ('layout.json','technical_gate.gd','previews/integrated_opening.gd','previews/integrated_camp_floor.gdshader','accepted_t02_surface.gd','river_geometry.gd')},
 'proposed_outer_W_D_height_m':[W,D,.008],'center_envelope_pre_shift_xz_m':[slo.tolist(),shi.tolist()],
 'rotation_range_deg':[89,91],'whole_footprint_envelope_relative_xz_m':[lo.tolist(),hi.tolist()],
 'south_east_static_keepouts_m':{k:v.tolist() for k,v in boxes if 'sweep' in k},'lower_plan_separations_m':gaps,'lower_plan_clearance_outside_preserved_route_corridors_m':routes,
 'terrain_common_core_all_orientations_and_centers':planar(cc,cy), 'common_core_pre_shift_xz_m':[cl.tolist(),ch.tolist()], 'terrain_entire_candidate_union_aabb':planar(points,y),'terrain_single_midpoint_90deg_diagnostic_no_placement':planar(mp,my),
 'actor_diameter_m':2*R,'counter_reserve_is_future':True,'no_world_binding':True}
print(json.dumps(report,indent=2,sort_keys=True))
