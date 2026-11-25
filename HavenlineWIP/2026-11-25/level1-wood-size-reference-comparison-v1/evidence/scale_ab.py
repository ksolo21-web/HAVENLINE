"""Detached normal-camera exact mesh projections + plan-only feasibility. No engine."""
import pathlib, hashlib, json, sys, runpy
import numpy as np
from scipy.spatial import ConvexHull, distance
from scipy.optimize import linprog
root=pathlib.Path.cwd()
c,m,s=map(pathlib.Path,sys.argv[1:])
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert H(c)=='31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554'
assert H(m)=='c3f34aa549171d9dde0ca6c3fdf7f7f4baf938429e2a91f368c184f9388e64aa'
assert H(s)=='51e34077a346b0f60951d9ee18c43276c82e8a9787af8f82cdf14a1a7f84c31e'
audit=runpy.run_path(str(root/'hvn-l1-transfer-crown-spacing-v1/audit.py'))
tri,_=audit['decode'](c)
v=np.unique(tri.reshape(-1,3),axis=0).astype(float)
assert len(v)==834
center=.5*(v.max(0)+v.min(0))
v-=center
tri-=center
clip=json.loads(m.read_bytes()); stage=json.loads(s.read_bytes())
verts=np.array(stage['vertices_godot']); faces=np.array(stage['faces']); marked=verts[np.unique(faces[np.array(stage['material_ids'])==1])][:,[0,2]]
markh=ConvexHull(marked)
def project(frame,T,k=1):
  o,*axes=np.array(T); P=np.array(frame['camera'])[1:3].T
  h=np.array([0.,0.,0.])
  x=k*v@np.array(axes)+o
  p=x@P*(720/13)
  return x,float(distance.pdist(p[ConvexHull(p).vertices]).max()),np.ptp(p,axis=0).tolist()
f=clip['frames'][-1]
details={str(a):[project(q,t)[1] for t in q['crowns']] for q in clip['frames'] for a in [q['age_tick']] if a in (64,172,266)}
peak=max((project(q,t)[1],q['age_tick'],i) for q in clip['frames'] for i,t in enumerate(q['crowns']))
s0=57.5/peak[0]
r=[project(f,T,s0)[0][:,[0,2]] for T in f['crowns']]
a=[project(f,T,s0)[0] for T in f['crowns']]
ab=[(x.min(0),x.max(0)) for x in r]
orig=[project(f,T,1)[0][:,[0,2]] for T in f['crowns']]
width=max(np.ptp(x[:,0]) for x in r)
span=max(x[:,0].max() for x in orig)-min(x[:,0].min() for x in orig)
center_pitch=.5*(ab[1][0][0]+ab[1][1][0]-ab[0][0][0]-ab[0][1][0])
def feasible_intersection(p,q):
  h=np.concatenate([ConvexHull(p).equations,ConvexHull(q).equations])
  z=linprog(np.zeros(p.shape[1]),A_ub=h[:,:-1],b_ub=-h[:,-1],bounds=[(None,None)]*p.shape[1],method='highs')
  return z.success
# Solve a hypothetical pair moved together into an axis-separable row.
# Keep final pose orientations, allow x offsets and shared z translation,
# preserve .02m planning-only clearance between visible x envelopes.
limits=markh.equations
A=[];B=[]
for j in range(2):
 for eq in limits:
  n=eq[:2]; coef=[0.,0.,n[1],1.]
  coef[j]=n[0]
  A.append(coef);B.append(float(-eq[2]-max(r[j]@n)))
A.append([1,-1,0,0]);B.append(float(ab[1][0][0]-ab[0][1][0]-.02))
sol=linprog([0,0,0,-1],A_ub=A,b_ub=B,bounds=[(None,None)]*4,method='highs')
need=float(ab[0][1][0]-ab[1][0][0]+.02)
shift=[np.array([-need/2,0]),np.array([need/2,0])]
def marker_reserve(p):
 return float(np.min([-q[2]-max(p@q[:2]) for q in limits]))
# True surface narrow phase; direct witness only, without coplanar or
# edge-on-plane cases. Uses source-stable triangle ordering and both final
# frame basis matrices independently, not a shared-yaw approximation.
def transformed_tri(T,k):
  o,*axes=np.array(T)
  return k*tri@np.array(axes)+o
def strict_cross(t,q):
  eps=1e-9
  section=audit['plane_section']
  def normals(p):
    n=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]); l=np.linalg.norm(n,axis=1)
    np.divide(n,l[:,None],out=n,where=l[:,None]>1e-15)
    return n,l
  nt,lt=normals(t);nq,lq=normals(q)
  lo,hi=q.min(axis=1),q.max(axis=1)
  count=0; w=None
  for i,x in enumerate(t):
    if lt[i]<=1e-15:continue
    js=np.flatnonzero(np.all(lo<=x.max(0)+eps,axis=1)&np.all(hi>=x.min(0)-eps,axis=1)&(lq>1e-15))
    d=(q[js]-x[0])@nt[i]
    for j,dj in zip(js,d):
      s=section(q[j],dj,eps)
      if s is None:continue
      u=section(x,(x-q[j,0])@nq[j],eps)
      if u is None:continue
      l=np.cross(nt[i],nq[j]);ln=np.linalg.norm(l)
      if ln<=eps:continue
      l/=ln
      a,b=sorted(s@l);c,e=sorted(u@l)
      overlap=min(b,e)-max(a,c)
      if overlap<=eps:continue
      count+=1
      if w is None or overlap>w['segment_m']:w=dict(triangle_a=i,triangle_b=int(j),segment_m=float(overlap))
  return dict(strict_crossing_pairs_lower_bound=count,strongest_segment=w)
tB=[transformed_tri(T,s0) for T in f['crowns']]
xB=strict_cross(*tB)
xA=strict_cross(*(transformed_tri(T,1.) for T in f['crowns']))
assert xB['strict_crossing_pairs_lower_bound'] and not xA['strict_crossing_pairs_lower_bound']
result={
 'mode':'OFFLINE_AB_PLAN_ONLY',
 'source_vertices':len(v),'original_projected_long_axis_px':details,
 'peak_original_projected_long_axis_px_age_slot':peak,
 'b_scale_relative_to_exact_presentation':s0,'b_target_min_center_max_px':[55,57.5,60],
 'b_projected_long_axis_px_at_seats':[project(f,T,s0)[1] for T in f['crowns']],
 'b_fixed_seat_plan_bounds_xz_m':[list(map(lambda v:v.tolist(),p)) for p in ab],
 'b_fixed_seat_x_overlap_m':float(ab[0][1][0]-ab[1][0][0]),
 'b_fixed_seat_projected_hulls_overlap':feasible_intersection(*r),
 'b_fixed_seat_3d_convex_hulls_overlap':feasible_intersection(*a),
 'actual_surface_strict_noncoplanar_collision_proof_at_terminal_age_266':{'A':xA,'B_fixed_unmodified_seats':xB},
 'exact_current_seat_pitch_by_bounding_center_x_m':float(center_pitch),
 'b_minimum_x_pitch_by_bounding_center_for_20mm_axis_gap_m':float(width+.02),
 'b_minimum_total_pair_width_x_for_20mm_axis_gap_m':float(np.ptp(r[0][:,0])+np.ptp(r[1][:,0])+.02),
 'exact_original_render_pair_width_x_m':float(span),
 'b_minimal_symmetric_spread_plan':{
  'each_outward_dx_m':need/2,
  'outline_minimum_reserve_m':[marker_reserve(q+d) for q,d in zip(r,shift)],
  'planar_hulls_overlap':feasible_intersection(r[0]+shift[0],r[1]+shift[1]),
 },
 'marker_plan_feasibility_only_with_new_draft_x_and_common_z_offsets':{
  'success':bool(sol.success),'max_convex_outline_edge_reserve_m':float(sol.x[-1]) if sol.success else None,
  'chosen_offsets_dx_L_dx_R_shared_dz_m':sol.x[:3].tolist() if sol.success else None},
 'limitations':'Geometry only; cannot certify bark appearance, contact after reseating, center icon/pad function, rotor/actor clearance, terrain support, flight path, or approved placement. Proposed scale is a detached all-axis screen-readability B test, not production mount/asset guidance.'
}
print(json.dumps(result,indent=2))
