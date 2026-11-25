"""Same sealed geometry intake, independent world-space Moller-Trumbore predicate."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
input_packet=Path(sys.argv[1]).resolve()
script=input_packet/'measure.py'
s=script.read_text()
assert hashlib.sha256(script.read_bytes()).hexdigest() == dict(reversed(line.split('  ',1)) for line in (input_packet/'SHA256SUMS').read_text().splitlines())['measure.py']
ctx={'__file__':str(script)}
prefix=s.split('def blocked(T,P,direction):',1)[0]
assert len(prefix)<len(s)
exec(compile(prefix,str(script),'exec'),ctx)
oc=json.loads((input_packet/'result.json').read_text())
name='facing-inboard-+0'
T,yaw=ctx['get_pose'](name)
def world_ray_counts(T,P,n):
    # Broad phase conservative geometric ray-cylinder test, not final predicate.
    along=T@n
    Tproj=T-along[:,:,None]*n[None,None,:]
    Pproj=P-(P@n)[:,None]*n[None,:]
    select=((Tproj.min(1)<=Pproj.max(0)+1e-7)&(Tproj.max(1)>=Pproj.min(0)-1e-7)).all(1)
    t=T[select]
    a=t[:,1]-t[:,0]; b=t[:,2]-t[:,0]
    p=np.cross(n,b); det=np.sum(a*p,axis=1)
    keep=abs(det)>1e-14
    t=t[keep];a=a[keep];b=b[keep];p=p[keep];det=det[keep]
    result=np.zeros(len(P),dtype=bool)
    for i in range(0,len(t),256):
        sl=slice(i,i+256)
        q=P[None,:,:]-t[sl,0,None,:]
        inv=(1/det[sl])[:,None]
        u=np.sum(q*p[sl,None,:],axis=2)*inv
        cross=np.cross(q,a[sl,None,:])
        v=np.sum(cross*n[None,None,:],axis=2)*inv
        dist=np.sum(cross*b[sl,None,:],axis=2)*inv
        result|=((u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(dist>1e-8)).any(axis=0)
    return [int(result.sum()),len(result)]
out={}
for label,h,side in [('V6',11,.8),('RC2',20.3,1.4),('near_nadir',75,1.4),('overhead_86deg',math.hypot(7,11)*math.tan(math.radians(86)),1.4)]:
    d=np.array([7,h,11]); d=d/np.linalg.norm(d)
    for sn,row in ctx['south'].items():
        if label=='overhead_86deg' and sn!='05-south-090cm':continue
        body=np.array(ctx['ctx']['tuplef'](row['actor_global']))
        posed=ctx['rotate_y'](T,row['actor_yaw_rad']-yaw)+body
        origin=np.array([ctx['ctx'][k] for k in ('X','Y','Z')])
        for g,mask in ctx['masks'].items():
            points=np.array([ctx['ctx']['vector'](u,v,side) for u,v in mask])+origin
            actual=world_ray_counts(posed,points,d)
            expected=oc['checks'][label][sn][name][g]
            assert actual==expected,(label,sn,g,actual,expected)
            out.setdefault(label,{}).setdefault(sn,{})[g]=actual
print(json.dumps({'world_ray_match_cases':len([a for b in out.values() for s in b.values() for a in s]),'checks':out},indent=2,sort_keys=True))
