import json,hashlib,types
from pathlib import Path
import numpy as np
def seal(p,x):
 assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()==x
 for ln in (p/'SHA256SUMS').read_text().splitlines():
  h,k=ln.split();assert hashlib.sha256((p/k).read_bytes()).hexdigest()==h
ref=Path('../hvn-c1-shoulder-torso-jacobian-v1.ulS8v6')
seal(ref,'d17972b3aeb10b21aa2c59da04320347100f9bee7f58567798e3ade641384eeb')
auth=Path('../hvn-c1-coupled-shoulder-open-v1.Ik28DQ')
seal(auth,'0c711d29f9589f4625097e580ed60d8356503c27e4df3431d9e6838b17360c1e')
code=(auth/'audit.py').read_text().split('# Full posed character')[0].replace('def evaluated_side(side):','maps={}\ndef evaluated_side(side):').replace(' after=dqsk(new)',' maps[side]=(transform,new)\n after=dqsk(new)')
d=types.SimpleNamespace()
exec(compile(code,str(auth/'audit.py'),'exec'),vars(d))
S=json.loads((auth/'result.json').read_text());R=json.loads((ref/'result.json').read_text())
for key,label in [('source_positions','original_52j_candidate_positions_sha256'),('right_positions','right_patch_candidate_positions_sha256')]:
 assert hashlib.sha256(np.ascontiguousarray(getattr(d,key)).tobytes()).hexdigest()==S[label]
# Local scalar-first Hamilton derivative. No geometric perturbation or finite
# difference: substitute left-trivialized rigid joint generator directly.
def H(q):
 w,x,y,z=q; return np.array([[w,-x,-y,-z],[x,w,-z,y],[y,z,w,-x],[z,-y,x,w]])
J=np.array([1.,-1.,-1.,-1.])
def qmul(a,b):
 w,x,y,z=np.moveaxis(a,-1,0); W,X,Y,Z=np.moveaxis(b,-1,0)
 return np.stack([w*W-x*X-y*Y-z*Z,w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W],axis=-1)
def derivative(rows, frames, pivot, descendants):
 cols=np.flatnonzero(np.any(d.Rsource[rows]>0,axis=0)); w0=d.Rsource[rows][:,cols]
 U=[];Z=[]
 for c in cols:
  r,t=frames[int(c)]
  q=d.Rotation.from_matrix(r).as_quat()[[3,0,1,2]]
  U.append(q);Z.append(.5*H(np.r_[0.,t])@q)
 U=np.array(U); Z=np.array(Z)
 w=w0*np.sign(U[np.argmax(w0>0,axis=1)]@U.T)
 a=w@U; b=w@Z
 L=np.linalg.norm(a,axis=1)[:,None]
 q=a/L; z=b/L
 product=np.c_[np.zeros(len(rows)),d.P[rows]]
 m=np.isin(cols,descendants)
 ans=[]
 for axis in np.eye(3):
  G=H(np.r_[0.,axis])*.5
  Gt=H(np.r_[0.,-np.cross(axis,pivot)])*.5
  da=w[:,m]@(U[m]@G.T)
  db=w[:,m]@(Z[m]@G.T+U[m]@Gt.T)
  ll=(q*da).sum(1)[:,None]
  dq=(da-q*ll)/L; dz=(db-z*ll)/L
  px=(qmul(qmul(dq,product),q*J)+qmul(qmul(q,product),dq*J)+2*(qmul(dz,q*J)+qmul(z,dq*J)))[:,1:]
  ans.append(px.reshape(-1))
 return np.column_stack(ans)
res={}
for side in ('L','R'):
 rows=np.asarray(d.mix0[side]); probes=[]
 shoulder=np.array(d.J['sides'][side]['shoulder'])
 descendant=d.rids[side][1:]
 assert not (d.Rsource[rows][:,descendant]>0).any()
 for k,aff in enumerate(d.maps[side]):
  jac=derivative(rows,aff,shoulder,d.rids[side])
  jd=derivative(rows,aff,np.array(d.J['sides'][side]['elbow']),descendant)
  assert np.count_nonzero(jd)==0
  gram=jac.T@jac; s=np.sqrt(np.linalg.eigvalsh(gram)[::-1])
  own=np.array(R['fits'][side][k]['SVD_raw_m_per_rad'][:3])
  assert np.max(abs(s-own))<1e-8
  probes.append({'step_free_xyz_shoulder_singular_m_per_rad':s.tolist(),'max_diff_to_producer_fd':float(max(abs(s-own))),
   'all_three_elbow_rotation_columns_zero':True,'protected_rows':len(rows),'gram_determinant':float(np.linalg.det(gram))})
 res[side]=probes
f=d.F[[556546,674738]]; W=d.Rsource[f]
assert not np.any(W[:,:,d.rids['L'][1:]]) and np.all(W[1,:,d.ix['upper_arm.L']]==1)
print(json.dumps({'analytic_controls':res,'named_pair_elbow_independent_even_if_three_axes_instead_of_hinge':True,'held_and_open_exact_hashes_verified':True},indent=2,sort_keys=True))
