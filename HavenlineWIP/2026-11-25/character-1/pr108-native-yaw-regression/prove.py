import json,numpy as np
R=np.diag([-1.,1.,-1.])
F=np.array([0.,0.,-1.]);Right=np.array([1.,0.,0.])
norm=lambda a:a/np.linalg.norm(a)
def placement(l,r):
 y=norm(l-r)
 x=np.cross(y,F); fallback=np.linalg.norm(x)<.001
 if fallback: x=np.cross(y,Right)
 x=norm(x);z=norm(np.cross(x,y))
 basis=np.stack([x,y,z],axis=1)
 units=.95/.70;mid_y=(-.34-.08)/2
 t=(l+r)*.5-y*mid_y*units+.08*x
 bands=[t+y*b*units for b in (-.34,-.08)]
 return basis,t,np.array(bands),fallback
rng=np.random.default_rng(108)
axes=np.r_[rng.normal(size=(512,3)),[[0,0,-1],[1e-5,1e-5,-1],[0,0,1],[0,1,0]]]
seen=0; oo=[]
for axis in axes:
 r=rng.normal(size=3);l=r+norm(axis)*.28
 B,t,p,x=placement(l,r)
 C,u,q,y=placement(R@l,R@r)
 assert x==y
 seen+=x
 e=(R@u)-t
 oo.append([np.max(abs(R@C-B@R)),np.linalg.norm(e+.16*B[:,0]),np.max(abs((q@R)-p-e))])
out=np.max(oo,axis=0)
assert np.max(out)<1e-12
print(json.dumps({'poses':len(axes),'fallback_poses':int(seen),'actor_local_basis_max_abs_error_to_expected_flip':out[0],'actor_local_axis_offset_error_m':out[1],'actor_local_bands_delta_error_m':out[2],'expected_actor_local_shift_m':.16,'expected_actor_local_roll_degrees':180},sort_keys=True,indent=2))
