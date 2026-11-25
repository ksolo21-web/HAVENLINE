import hashlib,json,types
from pathlib import Path
import numpy as np
p=Path('../hvn-c1-coupled-shoulder-open-v1.Ik28DQ')
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='0c711d29f9589f4625097e580ed60d8356503c27e4df3431d9e6838b17360c1e'
for line in (p/'SHA256SUMS').read_text().splitlines():
 sig,name=line.split(); assert hashlib.sha256((p/name).read_bytes()).hexdigest()==sig
d=types.SimpleNamespace()
exec(compile((p/'audit.py').read_text().split('# Full posed character')[0],str(p/'audit.py'),'exec'),vars(d))
S=json.loads((p/'result.json').read_text())
assert hashlib.sha256(np.ascontiguousarray(d.source_positions).tobytes()).hexdigest()==S['original_52j_candidate_positions_sha256']
assert hashlib.sha256(np.ascontiguousarray(d.right_positions).tobytes()).hexdigest()==S['right_patch_candidate_positions_sha256']
V,F,P,A=d.V,d.F,d.P,d.source_positions
def common_line_length(f,g):
 n=np.cross(f[1]-f[0],f[2]-f[0]);n/=np.linalg.norm(n)
 v=np.cross(g[1]-g[0],g[2]-g[0]);v/=np.linalg.norm(v)
 m=np.cross(n,v)
 if np.linalg.norm(m)<=1e-10:return 0.0
 m/=np.linalg.norm(m)
 def clip(z,origin,plane):
  a=(z-origin)@plane
  if min(a)>=-1e-10 or max(a)<=1e-10:return None
  cross=[]
  for i,j in ((0,1),(1,2),(2,0)):
   if abs(a[i])<=1e-10: cross.append(z[i]@m)
   elif a[i]*a[j]<-1e-20:cross.append((z[i]+(z[j]-z[i])*a[i]/(a[i]-a[j]))@m)
  if len(cross)<2:return None
  return min(cross),max(cross)
 a,b=clip(f,g[0],v),clip(g,f[0],n)
 return 0. if a is None or b is None else max(0.,min(a[1],b[1])-max(a[0],b[0]))
R=np.array(S['rig_two_hands']['R']['rotation'])
e=np.array(d.J['sides']['R']['shoulder'])
checks=[]
for t in json.loads((p/'controls.json').read_text())['explicit_body_pair_controls']:
 f,g=t['source_faces']; ix=F[[f,g]]
 b=common_line_length(*V[ix]); a=common_line_length(*A[ix])
 c={'source_faces':[f,g],'baseline_strict_overlap_mm':1e3*b,'whole_arm_strict_overlap_mm':1e3*a}
 assert b==0.
 if a==0:
  c['common_subtree_rigid_error_m']=float(np.linalg.norm((V[ix]-e)@R.T+e-A[ix],axis=2).max())
  assert c['common_subtree_rigid_error_m']<2e-7
 else:assert a>1e-7
 assert (a>0)==t['strict_candidate']
 checks.append(c)
# Independent replay of old chest-author non-arm selection directly from pinned
# v1 source, not a claim about semantic membership of every garment pixel.
old_dom=np.asarray(d.names)[np.argmax(d.W,axis=1)].astype(str)
auth_arm=np.array([x.split('.')[0] in {'upper_arm','forearm','hand','clavicle'} for x in old_dom])
allbody_ids=np.flatnonzero((~auth_arm[F]& (abs(P[F,0])<=.48)).all(1)); rows=np.unique(F[allbody_ids])
assert len(rows)==len(d.frozen_body_rows) and np.array_equal(rows,d.frozen_body_rows)
guard=rows[(V[rows]!=A[rows]).any(1)]
assert len(guard)==2291
metrics={}
for side,mask in [('R',P[guard,0]<0),('L',P[guard,0]>0)]:
 ids=guard[mask]; ww=d.Rsource[ids][:,d.rids[side]].sum(1)
 assert all(ww>0)
 metrics[side]={'n':len(ids),'min_max_positive_arm_subtree_weight':[float(ww.min()),float(ww.max())],
  'min_max_abs_rest_x_m':[float(abs(P[ids,0]).min()),float(abs(P[ids,0]).max())]}
core=np.flatnonzero(abs(P[:,0])<.175)
assert len(core)==229322 and np.array_equal(V[core],A[core])
assert np.array_equal(V[P[:,2]<-.2],A[P[:,2]<-.2])
delta=np.linalg.norm(V[guard]-A[guard],axis=1)
stats=S['body_self_clearance']
assert stats['original_strict_pairs_relative_faces']-stats['cleared_strict_pairs']+stats['new_strict_pairs']==stats['candidate_strict_pairs_relative_faces']
print(json.dumps({'independent_named_pair_controls':checks,'pinned_torso_guard_faces':len(allbody_ids),
 'untouched_central_rows':len(core),'changed_nondominant_chart_rows':len(guard),'change_by_side':metrics,'most_chart_motion_mm':float(1000*delta.max()),
 'body_counts_producer_custody_only':{k:stats[k] for k in ('original_strict_pairs_relative_faces','candidate_strict_pairs_relative_faces','new_strict_pairs','cleared_strict_pairs')}},indent=2,sort_keys=True))
