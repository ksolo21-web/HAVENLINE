import numpy as np,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
S=P.parent/'hvn-l1-c1-newer-knee-flex-v1'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(S/'poses.npz')=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
assert sha(S/'rejected-material-arrays.npz')=='bce54417d8b2340277ecbb2f60c7681f5bc76a7ff04ddbd3a9472fa185f051fe'
a=np.load(S/'poses.npz'); old=a['frames']; v=a['rest'].astype(float); E=a['E']; W=a['weights']; z=v[:,2]
repaired=np.load(S/'rejected-material-arrays.npz')['xyz']
_, rep, welded=np.unique(np.rint(v/1e-6).astype('int64'),axis=0,return_index=True,return_inverse=True)
n=lambda u:np.linalg.norm(u,axis=-1)
len0=n(v[E[:,1]]-v[E[:,0]])
result={}
for k,s in enumerate('LR'):
 ii=a['edge'+s]; e=E[ii]
 Hip,Knee,Ankle,Toe=a['joints'][k]
 # A genuine limb scope from ankle to hip; conservative fixed distal
 # precaution includes at least ALL source boot classifier and Foot/Toe material.
 fixed_exact=(z<=.05)|(W[:,4*k+2:4*k+4].sum(1)>.99999)
 fixed_exact[a['footprint'+s]]=True
 fixed_boot=fixed_exact.copy();fixed_boot[a['boot'+s]]=True
 own=W[:,4*k:4*k+4].sum(1);both=np.zeros(len(v),bool)
 both[own>.85]=True
 zmax=float(Hip[2]); zmin=float(Ankle[2])
 sig=np.array([1,-1])[k]
 definition=(z>zmin)&(z<zmax)&(v[:,0]*sig>.025)&both
 # Group raw seam twins by source rest. Ambiguous/fixed twins cannot receive
 # a different material transform on the partner side.
 guard_fixed=np.zeros(len(rep),bool);guard_fixed[welded[fixed_boot|~definition]]=True
 eligible=definition & ~guard_fixed[welded]
 case=[]
 for j in range(3):
  x=old[j].astype(float)
  rat=n(x[e[:,1]]-x[e[:,0]])/len0[ii]
  bad=(rat<.5)|(rat>2)
  d=np.max(np.abs(repaired[j]-x),axis=1)
  unaffected=bad&np.all(d[e]<1e-9,axis=1)
  edge_region=np.any(eligible[e],axis=1)
  spans={}
  for key,which in [('all_failed',bad),('prior_unaffected',unaffected),('unreachable_new',bad&~edge_region)]:
   pos=v[e[which]]
   spans[key]={'num':int(which.sum()),'z_bounds_mm':None if len(pos)==0 else (np.array([pos[...,2].min(),pos[...,2].max()])*1000).tolist(),'both_fixed_exact':int(np.sum(which&fixed_exact[e].all(1))),'both_fixed_boot_mask':int(np.sum(which&fixed_boot[e].all(1))),'relevant_max_foot_toe':float(W[e[which],4*k+2:4*k+4].sum(-1).max()) if np.any(which) else None,'exact_ids':ii[which].tolist()}
  case.append(spans)
  print(s,j,[(a0,v0['num'],v0['z_bounds_mm'],v0['both_fixed_exact'],v0['both_fixed_boot_mask'],v0['relevant_max_foot_toe']) for a0,v0 in spans.items()])
 result[s]={'joint_points':a['joints'][k].tolist(),'eligible_vertex_count':int(sum(eligible)), 'angles_not_modified':True,'keys':case}
(P/'coverage.json').write_text(json.dumps(result,indent=2))
