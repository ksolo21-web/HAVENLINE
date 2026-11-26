"""Read one exact sealed key; no pose microvariants, only planar target feasibility."""
import contextlib,io,os,sys,json,hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

here=Path.cwd(); key=Path('../stage').resolve()
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=key/'KEY-INPUT-SHA256SUMS'
assert digest(manifest)=='5c33d2c33255195e23f0ee632514a2a375e89be4a1872b4d113c3da83d25f7fe'
for line in manifest.read_text().splitlines():
 h,n=line.split();assert digest(key/n)==h
sys.path.insert(0,str(key));os.chdir(key)
with contextlib.redirect_stdout(io.StringIO()) as q:
 import stage as f
assert json.loads(q.getvalue())==json.loads((key/'result.json').read_text())
os.chdir(here)
def dist(i):
 P=f.P[i]
 return float(P[1]-f.ground(*P[[0,2]]))
witness={}
for s in 'LR':
 b=f.bounds[s];distances=np.array([dist(i) for i in np.flatnonzero(b['physical'])])
 ids=np.flatnonzero(b['physical']); assert b['anchor'] in ids
 ids=ids[(distances>=-.001)&(distances<=.002)]
 nearest=int(ids[np.linalg.norm(f.P[ids][:,[0,2]]-f.P[b['anchor'],[0,2]],axis=1).argmin()])
 witness[s]=dict(representative_source_row=int(b['anchor']),representative_gap_mm=dist(b['anchor'])*1000,
   physical_contact_vertices=len(ids),nearest_real_in_band_source_row=nearest,nearest_real_in_band_gap_mm=dist(nearest)*1000,
   representative_to_nearest_real_in_band_xz_mm=float(np.linalg.norm(f.P[nearest,[0,2]]-f.P[b['anchor'],[0,2]])*1000))

A,B=f.hull.equations[:,:2],f.hull.equations[:,2]
center=f.center
ankles={s:f.ankle(s,d) for s,d in zip('LR',f.drops)}
hip={s:f.at(s+'Hip')+np.array([0,f.pelvis/f.S,0]) for s in 'LR'}
seg={s:sum(np.linalg.norm(f.at(s+a)-f.at(s+b)) for a,b in [('Hip','Shin'),('Shin','Heel')])*f.S for s in 'LR'}
basehip={s:(hip[s]-ankles[s])*f.S for s in 'LR'}
def margins(x):
 return np.array([seg[s]-np.linalg.norm(basehip[s]+np.array([x[0],0,x[1]])) for s in 'LR'])
def inside(x):return float(-np.max(A@(center+x)+B))
def response(target):
 # Disabled near-threshold tolerance lowering. Feasibility in a convex reach-
 # and support-intersection, horizontal pelvis only, fixed y and fixed ankles.
 res=minimize(lambda x:.5*(x@x), np.array([0.,-.04]), jac=lambda x:x,
    constraints=[dict(type='ineq',fun=lambda x:-(A@(center+x)+B)-target,jac=lambda x:-A),
                 dict(type='ineq',fun=lambda x:margins(x)-.011)], method='SLSQP',
    options={'ftol':1e-14,'maxiter':100})
 opt=res.x;ok=bool(res.success and inside(opt)>=target-1e-9 and np.min(margins(opt))>=.011-1e-9)
 return dict(status='FEASIBLE_STATIC_CONSTRAINTS_ONLY' if ok else 'NO_FEASIBLE_POINT_FOUND',
             support_target_margin_mm=target*1000,xy_in_xz_delta_m=opt.tolist(),shift_mm=float(np.linalg.norm(opt)*1000),
             actual_center_inside_margin_mm=inside(opt)*1000,fixed_height_reach_reserve_mm=dict(zip('LR',margins(opt)*1000)),
             fixed_ankles=True,exact_source_mesh_pose_not_evaluated_for_this_target=True)
result=dict(exact_held_key_manifest_sha256='b536ff68c3f9a116bce12acbf8c0004c7ba6a1917cc7fb01aa2625532427e18c',physical_vs_marker= witness,
    exact_old_center_inside_margin_mm=inside([0.,0.])*1000,
    near_center_targets=[response(x) for x in [0.,.003]],
    original_actor_root_terrain_camera_unchanged=True,
    screen_prefers_measured_contacts_over_anchor_renaming=True,
    gait_or_integration_pass=False)
print(json.dumps(result,indent=2))
