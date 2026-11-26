"""Exactly one source-math pelvic-center correction, fixed original contact markers."""
import os,sys,contextlib,io,inspect,hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree,ConvexHull
p=Path.cwd(); key=Path('../stage').resolve()
cand=Path('../feasibility').resolve()
H=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
for d,n,h in [(key,'KEY-INPUT-SHA256SUMS','5c33d2c33255195e23f0ee632514a2a375e89be4a1872b4d113c3da83d25f7fe'),(cand,'CENTER-INTAKE-SHA256SUMS','8d548ff8b22cba70092632a23de1d3c1cef2a046db9e6df6f34d8191131571b4')]:
 assert H(d/n)==h
 for row in (d/n).read_text().splitlines():
  x,k=row.split();assert H(d/k)==x
item=json.loads((cand/'result.json').read_text())['near_center_targets'][1]
assert item['support_target_margin_mm']==3.
target=np.array(item['xy_in_xz_delta_m'])
sys.path.insert(0,str(key));os.chdir(key)
with contextlib.redirect_stdout(io.StringIO()) as q:import stage as f
assert json.loads(q.getvalue())==json.loads((key/'result.json').read_text())
os.chdir(p)

# Patch exactly one detached driver input from the checksummed stage.
# No scan or candidate angle changes. Reusing original algebra here avoids
# introducing a hidden difference in normalized skin, yaw or roll.
old=inspect.getsource(f.driver)
before='pelvis=pelvic(H);off=np.array([0,pelvis/S,0])'
after='pelvis=pelvic(H);off=np.array([target[0]/S,pelvis/S,target[1]/S])'
assert old.count(before)==1
ns={**f.__dict__,'target':target};exec(old.replace(before,after),ns)
P,T,pelvis,margins=ns['driver'](f.drops)
assert pelvis==f.pelvis
assert np.array_equal(T['Root'],f.Xfit['Root'])
assert np.allclose((T['Pelvis'][:3,3]-f.Xfit['Pelvis'][:3,3])*f.S,[target[0],0,target[1]],atol=1e-15)
for s in 'LR':
 for bone in ['Heel','Ball']:
  assert np.array_equal(T[s+bone],f.Xfit[s+bone])
 assert margins[s]>.011
foot={}
points=[]
for s,b in f.bounds.items():
 surf=P[:,[0,2,1]].copy();surf[b['leg'],2]=f.distance(P,b['leg'])
 sup=f.connected(surf,b['faces'],f.tags)
 actual=P[b['anchor']]
 marker=float(actual[1]-f.ground(*actual[[0,2]]))
 points.extend(P[b['physical'] & (np.abs(surf[:,2]-.0005)<=.0015)][:,[0,2]].tolist())
 foot[s]={'same_role':b['role'],'same_source_row':b['anchor'],'original_marker_gap_mm':f.out['feet'][s]['actual_marker_ground_distance_m']*1000,
          'corrected_marker_gap_mm':marker*1000,
          'protected_ankle_and_ball_frames_exact':True,
          'whole_boot_min_mm':float(surf[b['leg'],2].min()*1000),'support':sup}
hull=ConvexHull(points)
center=(T['Pelvis'][:3,3]*f.S+f.base)[[0,2]]
inside=float(-np.max(hull.equations@np.r_[center,1]))*1000
V,F=f.V,f.F
active=np.flatnonzero((V[:,1]<.32)[F].any(1))
def nn(t,a):return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
rest=V.astype(float)*f.S+f.base
nr=nn(rest[F[active]],None)
def dynamics(A,X):
 global_matrix=np.stack([X[k] for k in f.slots])@f.inv
 D=sum(global_matrix[f.J[:,i],:3,:3]*f.W[:,i,None,None] for i in range(4))
 frame=D[F[active]].mean(1)
 pred=(frame@nr[:,:,None])[:,:,0]
 actual=nn(A[F[active]],None)
 orient=(np.sum(pred*actual,axis=1)<=0)&(np.linalg.norm(nr,axis=1)>1e-12)
 return int(orient.sum())
# Independently pinned conventional triangle narrow phase: only strict
# interior contact, no coplanar/tangent false positives. Whole-source
# neighborhood connected to all 31,576 lower-triangle source IDs.
evalp=Path(os.environ['HAVENLINE_ARCHIVED_GROUND_EVALUATOR']).resolve()
assert H(evalp) == '0b33c50478530a6266535d7c4b7e286703454e04f260b12d12249c52818e8c82'
text=evalp.read_text()
st=text.index('def mesh_overlap(P):');en=text.index('\nnb=mesh_overlap',st)
code=text[st:en]
assert 'I=I[~np.isin(Weld[TR[I]],Weld[TR[i]]).any(1)]' in code
e={'np':np,'cKDTree':cKDTree,'TR':F,'Weld':f.tags,'active':active}
exec(code,e)
pairs={k:e['mesh_overlap'](X) for k,X in [('source_neutral',rest),('old_key',f.P),('corrected_key',P)]}
cross=(8794,8891); oldedge=(36861,36961)
el=lambda X:np.linalg.norm(X[oldedge[0]]-X[oldedge[1]])
olds=pairs['old_key'];news=pairs['corrected_key'];re=pairs['source_neutral']
witness={'v3_historic_faces':list(cross),'faces_in_source_neutral':cross in re,'faces_in_old_key':cross in olds,
         'faces_in_corrected_key':cross in news,'historic_edge_indices':list(oldedge),'edge_length_ratios_old_corr':[el(A)/el(rest) for A in [f.P,P]]}
stages=[('source_neutral',rest,f.G),('old_key',f.P,f.Xfit),('corrected_key',P,T)]
o={'status':'HOLD_NO_ACCEPTED_CHARACTER1_KEY','pelvis_shift_pinned_xz_mm':(target*1000).tolist(),'root_actor_camera_unchanged':True,
   'pelvis_zero_y_change':True,'fixed_rotation_and_position_heel_ball_frames':True,'full_actual_bound_skin':True,
   'author_source_prephysics_frame_not_native_validate':True,'lower_faces_scope':len(active),'same_contact_markers':foot,
   'real_support_hull_margin_after_mm':inside,'old_margin_mm':f.out['geometric_pelvis_over_contact_hull']['signed_margin_inside_m']*1000,
   'hip_extended_reach_reserve_mm':{k:v*1000 for k,v in margins.items()},
   'strict_crossing_counts':{k:len(v) for k,v in pairs.items()},'candidate_new_vs_old':len(news-olds),'old_removed':len(olds-news),
   'first_new_vs_old_pair':list(min(news-olds)) if news-olds else None,
   'conservative_transported_normal_alarm_counts':{k:dynamics(a,t) for k,a,t in stages},
   'known_v3_witness_at_this_new_key':witness,'coplanar_tangency_or_continuous_gait_validated':False,'native_or_rendered_quality_pass':False}
print(json.dumps(o,indent=2))
