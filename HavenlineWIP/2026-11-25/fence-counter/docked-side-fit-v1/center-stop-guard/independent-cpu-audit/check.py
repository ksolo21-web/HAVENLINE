"""Offline validation of prior frozen source captures; no engine or transformations."""
import sys,json,hashlib
from pathlib import Path
from itertools import product
from collections import defaultdict, Counter
import numpy as np
p=Path(sys.argv[1]); raw=p/'native-v3'; receipt=json.loads((p/'native-v3-geometry.json').read_text())
digest=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
E=2e-7
def tr(file):
    Q=json.loads(file.read_text())
    O=[]
    for s in Q:
        v=np.asarray(s['positions']);f=np.asarray(s['triangles']).reshape(-1,3)
        O.append(v[f])
    return np.concatenate(O)
def vectors(T):
    cn=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); m=np.linalg.norm(cn,axis=1); return cn/np.maximum(m,1e-30)[:,None],m
def eval_batch(H,Hn,cb,a,b):
    X=H[a];Y=cb[b];G=Hn[a];M=DN[b]
    dx=np.einsum('nki,ni->nk',X-Y[:,0,None,:],M);dy=np.einsum('nki,ni->nk',Y-X[:,0,None,:],G)
    good=(dx.min(1)<-E)&(dx.max(1)>E)&(dy.min(1)<-E)&(dy.max(1)>E)
    dx,dy,X,Y,M,G,b=[z[good] for z in (dx,dy,X,Y,M,G,b)]
    axis=np.cross(G,M);norm=np.linalg.norm(axis,axis=1)
    select=norm>1e-10
    dx,dy,X,Y,axis,norm,b=[z[select] for z in (dx,dy,X,Y,axis,norm,b)]
    axis=axis/norm[:,None]
    def span(v,d):
        s=np.einsum('nki,ni->nk',v,axis)
        vals=[np.where(abs(d[:,i])<=E,s[:,i],np.nan) for i in range(3)]
        for i,j in ((0,1),(1,2),(2,0)):
            inner=(np.minimum(abs(d[:,i]),abs(d[:,j]))>E)&(d[:,i]*d[:,j]<0)
            r=np.divide(d[:,i],d[:,i]-d[:,j],out=np.zeros(len(d)),where=inner)
            vals.append(np.where(inner,s[:,i]+r*(s[:,j]-s[:,i]),np.nan))
        vals=np.stack(vals,axis=1);return np.nanmin(vals,axis=1),np.nanmax(vals,axis=1)
    xl,xh=span(X,dx);yl,yh=span(Y,dy)
    interval=np.minimum(xh,yh)-np.maximum(xl,yl)
    return b[interval>2*E],interval[interval>2*E]
def conservative_slab_min(A,side):
    a0,a1=A.min(1),A.max(1);l=A[:,:,0].min();r=A[:,:,0].max()
    clip=(DL[:,0]<=r)&(DH[:,0]>=l)
    count=100
    # Use each exact face extremum only if it intersects the given Y slab;
    # no interpolation to simplify into an optimistic bound.
    y=np.arange(-5,count)*.02
    ha=(a0[:,1][None,:]<=y[:,None]+.02)&(a1[:,1][None,:]>=y[:,None])
    ca=(DL[:,1][None,:]<=y[:,None]+.02)&(DH[:,1][None,:]>=y[:,None])&clip[None,:]
    m=ha.any(1)&ca.any(1)
    hero=np.min(np.where(ha[m],(A[:,:,2]*side).min(1)[None,:],np.inf),axis=1)
    donor=np.max(np.where(ca[m],(D[:,:,2]*side).max(1)[None,:],-np.inf),axis=1)
    return float(np.min(hero-donor))
f=raw/'counter.json';assert digest(f)==receipt['actual_donor_dump_sha256'];D=tr(f);DN,nD=vectors(D);DL,DH=D.min(1),D.max(1)
def key(lo,hi):
    a=np.floor((lo-E)/.12).astype(int);b=np.floor((hi+E)/.12).astype(int)
    return product(*(range(c,d+1) for c,d in zip(a,b)))
grid=defaultdict(set)
for i,(x,y) in enumerate(zip(DL,DH)):
    if nD[i]>1e-14:
        for k in key(x,y):grid[k].add(i)
def run(H):
    HN,nh=vectors(H);HL,HH=H.min(1),H.max(1); d0=DL.min(0); d1=DH.max(0)
    ix=np.flatnonzero((HH>=d0-E).all(1)&(HL<=d1+E).all(1)&(nh>1e-14))
    A=[];B=[]
    for k in ix:
        pre=np.array(sorted(set().union(*(grid[t] for t in key(HL[k],HH[k])))),dtype=int)
        good=pre[(DL[pre]<=HH[k]+E).all(1)&(DH[pre]>=HL[k]-E).all(1)]
        A.extend([k]*len(good));B.extend(good)
    A=np.array(A,int);B=np.array(B,int)
    d,seg=eval_batch(H,HN,D,A,B)
    return len(seg),float(max(seg,default=0))
state={}
route=(p/'native-v3-route.log').read_text().splitlines()
assert sum(s.startswith('PASS ') for s in route)==123 and not any(s.startswith('FAIL ') for s in route)
assert not (raw/'save-artifacts.txt').read_bytes()
for k,v in receipt['native_poses'].items():
    f=raw/(k+'.json');assert digest(f)==v['native_dump_sha256']
    h=tr(f); assert len(h)==96001
    signed=conservative_slab_min(h,1 if 'inboard' in k else -1)
    count,span=run(h)
    assert abs(signed-v['signed_z_conservative_gap_m_in_20mm_y_slabs'])<1e-9 and count==v['surfaces'][0]['all_counter_intersections'],k
    state[k]={'independent_strict_full_donor_count':count,'independent_conservative_slab_min_signed_m':signed,
              'independent_max_strict_full_donor_segment_m_not_depth':span}
    print(k,count,signed,span,file=sys.stderr)
print(json.dumps({'current_run_is_read_only_offline':True,'source_native_movement_positive_checks':123,
'source_native_save_files':0,'holder':'HOLD_SIDE_AND_SERVICE_APPROACH','poses':state},indent=2))
