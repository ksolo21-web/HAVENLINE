"""Static headless witness using actual exported posed/imported triangles (not capsules)."""
import json,sys,hashlib
from collections import defaultdict
from itertools import product
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
p=Path(sys.argv[1]); world_tol=2e-7
def emit(q):
    return json.loads(q.read_text())
def surfaces(q):
    out=[]
    for x in q:
        v=np.array(x['positions'],dtype=float); i=np.array(x['triangles'],dtype=int).reshape(-1,3)
        out.append((int(x['surface']),v[i],x))
    return out
def norm(t):
    n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
    deg=np.linalg.norm(n,axis=1)
    return n/np.where(deg[:,None]>1e-14,deg[:,None],1),deg
def section(t,d,tol=world_tol):
    pts=[v for v,x in zip(t,d) if abs(x)<=tol]
    for j,k in ((0,1),(1,2),(2,0)):
        if min(abs(d[j]),abs(d[k]))>tol and d[j]*d[k]<0:
            pts.append(t[j]+(t[k]-t[j])*(d[j]/(d[j]-d[k])))
    return np.asarray(pts)
def noncoplanar_intersection(a,b,n,m):
    # Require both surfaces to have strictly opposing-side vertices; exclude touch/graze.
    d=(a-b[0])@m; e=(b-a[0])@n
    if not(d.min()<-world_tol and d.max()>world_tol and e.min()<-world_tol and e.max()>world_tol):
        return None
    u=np.cross(n,m); z=np.linalg.norm(u)
    if z<1e-10:return None
    u/=z
    sa=section(a,d);sb=section(b,e)
    xa=sa@u;xb=sb@u
    l=max(xa.min(),xb.min());h=min(xa.max(),xb.max())
    if h-l<=2*world_tol:return None
    return float(h-l),sa[0]+(float((l+h)*.5)-(sa[0]@u))*u
raw=surfaces(emit(p/'counter.json')); work=[]; allcounter=[]
for surf,t,meta in raw:
    w=np.zeros(len(t),dtype=bool)
    if surf in (2,3):
        # 10 micrometre bucketing closes split normal corners from the native
        # vertex stream. Whole-components, not loose ranges, identify planks.
        _,corners=np.unique(np.round(t.reshape(-1,3),5),axis=0,return_inverse=True)
        corners=corners.reshape(-1,3)
        _,group=connected_components(coo_matrix((np.ones(3*len(t),bool),(corners.ravel(),corners[:,[1,2,0]].ravel()))),directed=False)
        labels=group[corners[:,0]]
        for label in np.unique(labels):
            ids=np.flatnonzero(labels==label)
            if len(ids)!=528: continue
            lo,hi=t[ids].min((0,1)),t[ids].max((0,1))
            if np.allclose([lo[0],hi[0],lo[1],hi[1]],[-1.58,1.58,.915,1.085],atol=.00008,rtol=0):
                assert abs((hi-lo)[2]-.25)<.00008
                w[ids]=True
    for j in range(len(t)):allcounter.append((surf,j,bool(w[j]),t[j]))
    work.extend(t[w])
print('donor surfaces',[(s,len(t)) for s,t,_ in raw],'worktop triangles',len(work))
assert len(work)==5*528,len(work)
donor=np.array([x[-1] for x in allcounter]); dstn,ds=norm(donor); dmin,dmax=donor.min(1),donor.max(1)
def bins(lo,hi):
    C=np.floor((np.stack([lo,hi])+np.array([-world_tol,world_tol])[:,None])/.08).astype(int)
    return product(*(range(a,b+1) for a,b in zip(*C)))
cells=defaultdict(set)
for n0,(a,b) in enumerate(zip(dmin,dmax)):
    if ds[n0]>1e-14:
        for k in bins(a,b):cells[k].add(n0)

def check_hero(file):
    h=surfaces(emit(file)); summary=[]
    strongest=[]
    for hs,hero,meta in h:
        hint=[]
        own,As=norm(hero); lo,hi=hero.min(1),hero.max(1)
        idx=np.flatnonzero((hi>=dmin.min(0)-world_tol).all(1)&(lo<=dmax.max(0)+world_tol).all(1)&(As>1e-14))
        work_count=0
        for j in idx:
            b0=np.array(sorted(set().union(*(cells[k] for k in bins(lo[j],hi[j])))),dtype=int)
            b=b0[(hi[j]>=dmin[b0]-world_tol).all(1)&(lo[j]<=dmax[b0]+world_tol).all(1)]
            for k in b:
                r=noncoplanar_intersection(hero[j],donor[k],own[j],dstn[k])
                if r:
                    s,g,w,_=allcounter[k]
                    hint.append((float(r[0]),hs,int(j),s,g,w,r[1].tolist()))
                    work_count+=int(w)
        strongest.extend(hint)
        summary.append({'hero_surface':hs,'hero_tris':len(hero),'skin_bind_matrixes':meta['matrixes'],'weights':meta['weights'],'posed_differences':meta['vertices_with_pose_delta'],'max_weight_sum_delta':meta['max_weight_sum_delta'],'all_counter_intersections':len(hint),'worktop_intersections':work_count})
    hits=sorted(strongest,reverse=True)
    return {'surfaces':summary,'longest_worktop_hits_m_with_triangle_ids_and_contact_point':[x for x in hits if x[5]][:8], 'longest_other_hits':[x for x in hits if not x[5]][:8], 'all_hits':hits}
z={s:check_hero(p/('center-'+s+'-hard-stop.json')) for s in ('inboard','outboard')}
print(json.dumps(z,indent=2))
