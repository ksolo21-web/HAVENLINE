import hashlib,json,pathlib,sys
import numpy as np
p=pathlib.Path(sys.argv[1])
assert hashlib.sha256(p.read_bytes()).hexdigest()=='367931fb80e9d4060488bd621d77aa6c8001dc6a1d6ffc72a96f9ac0bbf88580'
D=np.load(p,allow_pickle=False)
out={}
for side in 'RL':
 f=D[side+'_intact_tool_face']; E=(f[1:]-f[0]).T
 inv=np.linalg.pinv(E)
 n=np.cross(E[:,0],E[:,1]);n/=np.linalg.norm(n)
 for name in ('palm','web'):
  q=D[f'{side}_{name}_segments']; z=(q-f[0])@n
  valid= z[:,0]*z[:,1]<0
  m=q[valid]; v=z[valid]
  p=m[:,0]+(m[:,1]-m[:,0])*(v[:,0]/(v[:,0]-v[:,1]))[:,None]
  uv=(p-f[0])@inv.T
  strict=((uv>1e-7).all(axis=1)&(uv.sum(1)<1-1e-7))
  out[side+'_'+name]={'strict_crossings_infinite_plane':len(m),'strict_crossings_single_assigned_finite_facet':int(strict.sum())}
print(json.dumps(out,sort_keys=True,indent=2))
