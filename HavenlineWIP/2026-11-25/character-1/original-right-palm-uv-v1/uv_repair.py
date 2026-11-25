from boundary import *
from collections import defaultdict,Counter
from scipy.optimize import minimize
old=np.load('reauthored-review-LOCAL.npz',allow_pickle=False)
pgeom=old['vertices']; Tn=old['faces']; olduv=old['uv']; ow=old['weights']; drop=old['removed']
N=len(uv); U=np.vstack([uv,olduv]).astype(float)
eps=1e-12
def det2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def signed(X):return det2(X[:,1]-X[:,0],X[:,2]-X[:,0])
a0=signed(U[Tn]); bad=np.flatnonzero(a0>=-eps)
assert bad.tolist()==[810,851,852,853,854,855,856,1067,1427,1432,1458,1747,1751,1756]
# Immutable rows include every source ID; recoloring, materials, exact seam
# endpoints and exact UV aliases are forbidden.
seed=np.unique(Tn[bad]); active=seed[seed>=N]
for _ in range(2):
 rows=np.flatnonzero(np.isin(Tn,active).any(1)); nodes=np.unique(Tn[rows]); active=nodes[nodes>=N]
rows=np.flatnonzero(np.isin(Tn,active).any(1)); rs=Tn[rows]
col={v:i for i,v in enumerate(active)}
table=np.array([[col.get(v,-1) for v in t] for t in rs]); valid=table>=0
fixed=np.unique(rs[~valid])
# Exact sign preflight before authoring: fixed-only faces must already meet
# the expected sign and each directed perimeter loop must be simple with
# correct orientation, proven pairwise on source atlas coordinates.
edges=Counter(tuple(sorted((int(a),int(b)))) for t in Tn for a,b in zip(t,np.roll(t,-1)))
B={k for k,v in edges.items() if v==1}
adj=defaultdict(list)
for a,b in B:adj[a].append(b);adj[b].append(a)
loops=[]
remain=set(adj)
while remain:
 i=min(remain); chain=[i]; prev=-1
 while True:
  k=min(v for v in adj[i] if v!=prev)
  if k==chain[0]:break
  assert k not in chain
  chain.append(k); prev=i;i=k
 remain.difference_update(chain);loops.append(chain)
dirs={tuple(sorted((int(a),int(b)))):(int(a),int(b)) for t in Tn for a,b in zip(t,np.roll(t,-1)) if tuple(sorted((int(a),int(b)))) in B}
def cross0(a,b,c,d):
 e=b-a; f=d-c; den=det2(e,f)
 if abs(den)<1e-15:return False
 u=det2(c-a,f)/den;v=det2(c-a,e)/den
 return min(u,v,1-u,1-v)>1e-9
loopqc=[]
for li in loops:
 if tuple(li[:2])!=dirs[tuple(sorted(li[:2]))]:li.reverse()
 P0=U[li]; P1=np.roll(P0,-1,axis=0)
 clear=not any(cross0(P0[i],P1[i],P0[j],P1[j]) for i in range(len(P0)) for j in range(i+1,len(P1)))
 loopqc.append({'number_vertices':len(li),'signed_area':float(det2(P0,P1).sum()/2),'strictly_simple':clear})
assert all(l['strictly_simple'] and l['signed_area']<0 for l in loopqc)
# Optimize one same-topology chart mask. Disk geometry is read-only.
uvunit=1000.
x0=(uvunit*U[active]).ravel(); constant=uvunit*U[rs]
def corners(x):
 p=constant.copy()
 p[valid]=x.reshape(-1,2)[table[valid]]
 return p
# Per triangle guard against nearly collapsing a corrected chart sliver:
# minimum twice-area is 10% of the old absolute value, with 1e-11
# normalized floor. This is a diagnostic guard, not visual approval.
area_floor=np.maximum(1.e-11,.10*np.abs(a0[rows]))
def constraints(x):
 return -signed(corners(x))-area_floor*uvunit**2
def jac(x):
 p=corners(x); e0=p[:,1]-p[:,0];e1=p[:,2]-p[:,0]
 d1=np.c_[e1[:,1],-e1[:,0]]; d2=np.c_[-e0[:,1],e0[:,0]]; d0=-d1-d2
 out=np.zeros((len(rs),len(x)))
 for k,g in enumerate((d0,d1,d2)):
  i=np.flatnonzero(valid[:,k]); j=table[i,k]*2
  out[i,j]=-g[i,0];out[i,j+1]=-g[i,1]
 return out
result=minimize(lambda x:.5*((x-x0)**2).sum(),x0,jac=lambda x:x-x0,
               constraints=[{'type':'ineq','fun':constraints,'jac':jac}],method='SLSQP',
               options={'maxiter':100,'ftol':1e-11})
trial=U.copy(); trial[active]=result.x.reshape(-1,2)/uvunit
vals=signed(trial[Tn]); source=F[drop]
srcdir=signed(U[source])
assert set(np.flatnonzero(vals!=a0)).issubset(set(rows))
assert np.array_equal(U[:N],trial[:N])
report={'status':'HOLD','source_inputs':expected,'base_perturbed_uv_reversed_count':len(bad),
 'loop_material_preflight':loopqc,'original_solver':str(result.message),'trial_changed_ids':active[np.any(trial[active]!=U[active],axis=1)].tolist(),
 'trial_reversed_or_degenerate_ids':np.flatnonzero(vals>=-eps).tolist(),'original_face_min_twice_unsigned_UV_area':float(abs(srcdir).min()),
 'trial_face_min_twice_unsigned_UV_area':float(abs(vals).min()),'changed_loop_triangles':len(rows)}

# For same connected disk, fixed directed simple boundary and strictly
# oriented, nondegenerate faces imply a degree-one map of its polygon:
# chart coverage and source padding are unchanged. Replay triangle collision
# too, including the other disk and actual nearby original atlas triangles.
def clip_triangle(A,B):
 p=list(A)
 s=np.sign(det2(B[1]-B[0],B[2]-B[0]))
 for b,c in zip(B,np.roll(B,-1,axis=0)):
  q=[]
  for r,t in zip(p,p[1:]+p[:1]):
   u=s*det2(c-b,r-b);v=s*det2(c-b,t-b)
   if u>=-1e-17:q.append(r)
   if (u< -1e-17)!=(v< -1e-17):q.append(r+(t-r)*u/(u-v))
  p=q
 if len(p)<3:return 0.
 p=np.array(p);return abs(det2(p-p[0],np.roll(p,-1,axis=0)-p[0]).sum())*.5
change=np.flatnonzero(vals!=a0)
Tuv=trial[Tn]; all_min=Tuv.min(1); all_max=Tuv.max(1)
new_overlap=[]; old_overlap=[]
dirs_all=defaultdict(list)
for t in Tn:
 for a,b in zip(t,np.roll(t,-1)):dirs_all[tuple(sorted((int(a),int(b))))].append((int(a),int(b)))
assert all(len(x)==1 or len(x)==2 and x[0]==x[1][::-1] for x in dirs_all.values())
assert np.array_equal(trial[np.unique(list(adj))],U[np.unique(list(adj))])
component_boxes=[(U[l].min(0),U[l].max(0)) for l in loops]
patchbounds=np.array([U[np.unique(list(adj))].min(0),U[np.unique(list(adj))].max(0)])
out=np.setdiff1d(np.arange(len(F)),drop)
origtris=U[F[out]]
neighbor=((origtris.min(1)<patchbounds[1]).all(1)&(origtris.max(1)>patchbounds[0]).all(1))
neighbor_ids=out[neighbor]; neighbors=origtris[neighbor]
qmin=neighbors.min(1);qmax=neighbors.max(1)
for i in range(len(Tuv)):
 lo=all_min[i];hi=all_max[i]
 jrows=np.flatnonzero((all_min<hi).all(1)&(all_max>lo).all(1)&(np.arange(len(Tuv))>i))
 for j in jrows:
  area=clip_triangle(Tuv[i],Tuv[j])
  if area>1e-14:new_overlap.append((int(i),int(j),area))
 for j in np.flatnonzero((qmin<hi).all(1)&(qmax>lo).all(1)):
  area=clip_triangle(Tuv[i],neighbors[j])
  if area>1e-14:old_overlap.append((int(i),int(neighbor_ids[j]),area))
old_src_overlap=[]
for i,A0 in zip(drop,U[F[drop]]):
 for j in np.flatnonzero((qmin<A0.max(0)).all(1)&(qmax>A0.min(0)).all(1)):
  area=clip_triangle(A0,neighbors[j])
  if area>1e-14:old_src_overlap.append((int(i),int(neighbor_ids[j]),area))
def h(t):
 return hashlib.sha256(np.ascontiguousarray(t).tobytes()).hexdigest()
oldarr={k:h(old[k]) for k in old.files}
assert oldarr=={
 'faces':'c68dad9d175c99d9cfa40e913c3f649760a24c4a1d85e2fa4a5eab7b73cfc771',
 'removed':'b70fef22110c7c31348d7ee2d93fa1bf9985d41d60d9377da2a4839962060c4b',
 'uv':'551b2fff98e90949a95ed83e66a5cdf53e01e533ed1082e90fbffdea400f1b66',
 'vertices':'8b17525d8728a8f0280ab65aeb3dcb3cdd41277aa2be14419bf4e699a9dcff57',
 'weights':'a96abf08caa7940e63c8590a3fe4b71a6ae8a491c6dfc97298a4f743addfb190'}
bline=np.unique(np.concatenate(loops))
geometry_proof={k:h(v) for k,v in {'vertices':pgeom,'faces':Tn,'weights':ow,'removed':drop}.items()}
assert all(geometry_proof[k]==oldarr[k] for k in geometry_proof)
# Exact normalized box is chart identity, not sufficient for texel padding;
# unchanged material boundary + matching interior measure is decisive.
disp=np.linalg.norm((trial[active]-U[active])*np.array(I.shape[1::-1]),axis=1)
report.update({'candidate_patch_coverage_area':float(-vals.sum()/2),'original_patch_coverage_area':float(-srcdir.sum()/2),
 'fixed_boundary_source_uv_id_digest':h(trial[bline]), 'unchanged_geometry_arrays_SHA256':geometry_proof,
 'base_local_candidate_array_SHA256':oldarr,'candidate_uv_array_SHA256':h(trial[N:]),
 'vertex_move_max_texels':float(disp.max()),'fold_free_min_area_ratio_for_guard_mask':float(np.min(-vals[rows]/area_floor)),
 'new_internal_strict_positive_uv_overlap':new_overlap,'new_uv_vs_retained_strict_positive_overlap':old_overlap,
 'original_pressure_uv_vs_retained_overlap':old_src_overlap, 'atlas_retained_broadphase_faces':len(neighbors),
 'geometry_and_all_source_uvs_bitidentical':True,'incident_faces_in_solver_mask':len(rows),'actual_changed_face_orientations':len(change),'numerical_overlap_twice_area_guard':2.e-14,'all_2445_face_UVs_have_expected_negative_sign':bool((vals< -eps).all())})
report['status']='UV_ONLY_NUMERIC_PASS__INDEPENDENT_MATERIAL_REVIEW_PENDING' if (not report['trial_reversed_or_degenerate_ids'] and not new_overlap and not old_overlap and abs(report['candidate_patch_coverage_area']-report['original_patch_coverage_area'])<1e-12) else 'HOLD'
print(json.dumps(report,indent=2,sort_keys=True))
