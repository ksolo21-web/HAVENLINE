"""One exact pelvis-only t0 adjustment, no output pose/animation or engine."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from scipy.spatial import ConvexHull
P=Path(__file__).resolve().parent.parent
B=P/'hvn-l1-c1-double-support-t0-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B/'SHA256SUMS')=='9a37f48906fd7360a541306ad2985bab88034a220188986aa8b755df67ca6ecb'
for row in (B/'SHA256SUMS').read_text().splitlines():
 h,p=row.split(maxsplit=1);assert sha(B/p)==h
prior=json.loads((B/'result.json').read_text()); assert prior['status']=='HOLD_IN_FIXED_T0_SCOPE'
best=max(prior['failed_pair_controls'],key=lambda r:r['signed_inside_margin_mm'])
assert abs(best['signed_inside_margin_mm']+39.5411457)<1e-6
# Only one computed diagnostic translation: nearest excluding edge's inward
# normal × exact distance plus fixed 5 mm safety target. No orientation search.
geq=np.array(best['nearest_excluding_edge_equation_world_zx'])
normal=geq[:2];assert abs(np.linalg.norm(normal)-1)<1e-12
world_zx=-normal*(-best['signed_inside_margin_mm']/1000+.005)
worldxyz=np.array([world_zx[1],0.,world_zx[0]])
assert .04<np.linalg.norm(worldxyz)<.05
exec((B/'solve.py').read_text().split('opt={}')[0])
# Same signed polygon minima, with exact limiting source face/point provenance.
funcs=funcs.replace('faces=A.F[np.isin(A.F,full).all(1)]','source_faces=np.flatnonzero(np.isin(A.F,full).all(1)); faces=A.F[source_faces]')
funcs=funcs.replace('whole_min=np.inf','whole_min=np.inf; limiting=None')
funcs=funcs.replace('whole_min=min(whole_min,min(map(g,m)))',
 'pick=min(m,key=g)\n     if g(pick)<whole_min:\n      whole_min=g(pick); limiting={"face":int(source_faces[idx]),"rows":faces[idx].tolist(),"point_scene_xyz":pick[:3].tolist()}')
funcs=funcs.replace("'sample_hull_world_zx':p[", "'limiting_ground_contact':limiting,'sample_hull_world_zx':p[")
exec(funcs)
from copy import deepcopy
ta0=t.copy(); hip0=g0.copy()
choices={}
for role,orientation in zip(role_names,best['orientations_deg']):
 row,=[z for z in prior['tested_exact_region_per_leg'][role]['exact_tests'] if [z['pitch_deg'],z['roll_deg']]==orientation]
 choices[role]=row
def full(qbase):
 results={};qwork=qbase.copy()
 for role in role_names:
  c=choices[role]
  r,k=solve(role,np.array(c['ankle_origin']),c['pitch_deg'],c['roll_deg'],qwork)
  if r is None:return None,None
  results[role]={'forward_mm':1000*k}
 for role in role_names:
  ids=patch[role]['ids'];gs=to_world(A.skin(r,ids)); th,ca,f,to,*_=A.roledata[role]
  measures=triangle(None,ids,gs,role,'flat',None)
  lim=measures.get('limiting_ground_contact')
  if lim:
   lim['skin_weights_by_face_vertex']=[[(S.N[int(S.jp[int(j)])]['name'],float(w)) for j,w in zip(S.J[row],S.W[row]) if w>0] for row in lim['rows']]
  ankle_err=np.linalg.norm(to_world(r[f,:3,3])-np.array(choices[role]['ankle_world_m']))*1000
  Gf=A.polar(G[f,:3,:3]).T@A.polar(G[to,:3,:3]); Hf=A.polar(r[f,:3,:3]).T@A.polar(r[to,:3,:3])
  results[role]|={'measures':measures,'ankle_world_residual_mm':float(ankle_err),
    'toe_relative_delta_deg':float(R.from_matrix(Gf.T@Hf).magnitude()*180/math.pi),
    'foot_world_zx_aabb_m':[gs[:,[2,0]].min(0).tolist(),gs[:,[2,0]].max(0).tolist()],
    'lowest_vertices_shape_identity_sha256':hashlib.sha256(gs.astype('<f8').tobytes()).hexdigest()}
 return results,r
raw_before,pose_before=full(q)
assert raw_before and pose_before is not None
for k,v in raw_before.items():
 for m in ('max_connect_width_mm','support_length_foreaft_mm','min_signed_mm','convex_hull_mm2'):
  assert abs(v['measures'][m]-best['whole_combined_patches'][k][m])<1e-8
# Amend actual shared hip translation (in tracked parent basis at original scale).
canon=(R90.T@worldxyz)/A.sc
t[23]+=np.linalg.solve(G[S.P[23],:3,:3],canon)
g0=S.evaluate(t,q,ss)
raw_after,pose_after=full(q)
status='HOLD_DUAL_REACH'
pinfo={}
if raw_after:
 actual_move=to_world(pose_after[23,:3,3])-to_world(pose_before[23,:3,3])
 assert np.max(abs(actual_move-worldxyz))<1e-10
 both=True
 for role,u in raw_after.items():
  s=u['measures']
  both=both and s['max_connect_width_mm']>=100 and s['min_signed_mm']>=-.025 and s['convex_hull_mm2']>=1000 and u['forward_mm']>0 and u['ankle_world_residual_mm']<.02 and u['toe_relative_delta_deg']<.001
 polys=[np.array(x['measures']['sample_hull_world_zx']) for x in raw_after.values()]
 pinfo={'actual_pelvis_translation_world_xyz_mm':(actual_move*1000).tolist(),
  'actual_before_proxy_world_zx_m':to_world(pose_before[23,:3,3])[[2,0]].tolist(),
  'actual_after_proxy_world_zx_m':to_world(pose_after[23,:3,3])[[2,0]].tolist()}
 after_margin=None
 if all(len(x)>2 for x in polys):
  points=np.concatenate(polys); hull=ConvexHull(points); c=to_world(pose_after[23,:3,3])[[2,0]]
  margins=-(hull.equations[:,:2]@c+hull.equations[:,2])
  after_margin=float(margins.min()*1000)
  pinfo['actual_after_signed_support_hull_margin_mm']=after_margin
  pinfo['actual_after_limiting_hull_equation_zx']=hull.equations[int(np.argmin(margins))].tolist()
 status=('T0_CONTACT_AND_CENTER_FEASIBLE_ONLY' if after_margin is not None and after_margin>0 and both else
         'HOLD_REAL_PLANTED_FOOT_CONTACT' if not both else 'HOLD_ACTUAL_CENTER_STILL_OUTSIDE')
 # Lower-region mutual footprint is a cheap separation witness only, not a whole-body pose acceptance.
 L=np.array(raw_after['left']['foot_world_zx_aabb_m']); Rr=np.array(raw_after['right']['foot_world_zx_aabb_m'])
 pinfo['between_boots_lateral_aabb_gap_mm']=float(max(L[0,0]-Rr[1,0],Rr[0,0]-L[1,0])*1000)
print(json.dumps(dict(status=status,exact_owner_sha256=sha(owner),t0_fixture_checked=True,
 frozen_left_right_exact_world_ankles_and_both_foot_toe_angles=True,origin_world_xyz=origin.tolist(),prescribed_exact_world_shift_mm=(worldxyz*1000).tolist(),
 no_more_center_variants=True,before_original_reperformed_bilateral=raw_before,after_same_ankles_recomputed_bilateral=raw_after,
 center=pinfo,full_limb_garment_and_between_step_safety_approved=False,pose_or_timing_export=False,engine_run=False),indent=2))
