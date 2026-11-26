"""Single protected-row admission test: analytic derivative, no changed pose/weights."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Rot
p,bind=map(Path,sys.argv[1:])
def h(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert h(p)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
assert h(bind)=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
D=np.load(p,allow_pickle=False)
w=D['weights'];rest=D['rest'].astype(float); ids=D['edgeR'];pairs=D['E'][ids]
assert list(D['weight_names'][4:])==['thigh.R','shin.R','foot.R','toe.R']
def mul(a,b):
 av,aw=np.asarray(a)[...,:3],np.asarray(a)[...,3:4];bv,bw=np.asarray(b)[...,:3],np.asarray(b)[...,3:4]
 return np.concatenate((aw*bv+bw*av+np.cross(av,bv),aw*bw-(av*bv).sum(axis=-1,keepdims=True)),axis=-1)
def conj(q):return q*np.array([-1,-1,-1,1])
scale=float(D['scale']); origin=D['source_origin'].astype(float)
target_id=164224; es=D['E'][target_id];assert list(es)==[59329,59331]
WT=w[es,4:].astype(float); point=rest[es]/scale+origin
assert np.all(w[es,:4]==0) and np.allclose(WT.sum(1),1,atol=1e-7) and np.all(WT[:,3]>0)
pt=np.c_[point,np.zeros(2)]
dp=lambda x:np.c_[x,np.zeros(len(x))]
def signed_basis(M):
 q=Rot.from_matrix(M[:,:3,:3]).as_quat()
 t=M[:,:3,3]
 d=.5*mul(dp(t),q)
 return q,t,d
rows=[]
for i,(f,M) in enumerate(zip(D['frames'],D['bones'][:,1])):
 f=f.astype(float); e=lambda z:np.linalg.norm(z[pairs[:,1]]-z[pairs[:,0]],axis=1)
 ratio=e(f)/e(rest); found=(ratio<.5)|(ratio>2.)
 locked=found&(w[pairs,7]>0).all(1)
 q,t,d=signed_basis(M)
 first=np.argmax(WT>0,axis=1); signs=np.sign(q[first]@q.T); signed=WT*signs
 # Infinitesimal world-X relative toe rotation about its current evaluated pivot.
 # Source gait toe rotation is rotate(pitch+toe); this calculation does not instantiate an altered pose.
 u=np.array([1.,0.,0.]); toe_raw=D['joints'][1,3]/scale+origin
 toe_now=M[3,:3,:3]@toe_raw+t[3]
 qprime=np.zeros_like(q);qprime[3]=.5*mul(np.r_[u,0.],q[3])
 tprime=np.cross(u,t[3]-toe_now)
 dprime=np.zeros_like(d);dprime[3]=.5*(mul(np.r_[tprime,0.],q[3])+mul(np.r_[t[3],0.],qprime[3]))
 aq,ad=signed@q,signed@d; dQ,dD=signed@qprime,signed@dprime
 length=np.linalg.norm(aq,axis=1)[:,None]; change=(aq*dQ).sum(1)[:,None]/length
 aq,ad=aq/length,ad/length
 dQ,dD=(dQ-aq*change)/length,(dD-ad*change)/length
 base=mul(mul(aq,pt),conj(aq))+2*mul(ad,conj(aq))
 response=mul(mul(dQ,pt),conj(aq))+mul(mul(aq,pt),conj(dQ))+2*(mul(dD,conj(aq))+mul(ad,conj(dQ)))
 repro_err=np.linalg.norm((base[:,:3]-origin)*scale-f[es],axis=1)
 assert repro_err.max()<1e-6
 rates=np.linalg.norm(response[:,:3],axis=1)*scale*1000*np.pi/180
 assert np.min(rates)>1e-4
 k=int(np.flatnonzero(ids==target_id)[0]);assert locked[k]
 rows.append(dict(ms=[0,75,150][i],failed_right=int(found.sum()),both_endpoints_toe_driven_failed_right=int(locked.sum()),locked_edge_ratio=float(ratio[k]),uncorrected_exact_model_repro_max_mm=float(repro_err.max()*1000),native_axis_first_order_sensitive_mm_per_deg=rates.tolist()))
print(json.dumps(dict(status='STOP_NO_AUTHORIZED_VARIANT_CLEARS_FIXED_EDGE',exact_protected_edge=target_id,endpoints=es.tolist(),toe_fractions=WT[:,3].tolist(),keys=rows),indent=2))
