import sys,struct,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Rot
p=Path(sys.argv[1])
data=p.read_bytes();l=struct.unpack_from('<I',data,12)[0];d=json.loads(data[20:20+l]);raw=data[l+28:]
N=d['nodes'];P={k:i for i,j in enumerate(N) for k in j.get('children',[])}
def get(i):
 a=d['accessors'][i]; b=d['bufferViews'][a['bufferView']]; n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 return np.frombuffer(raw,{5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']],count=n*a['count'],offset=b.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
jp=d['skins'][0]['joints'];mesh=d['meshes'][0]['primitives'][0];v,J,W=[get(mesh['attributes'][k]) for k in ('POSITION','JOINTS_0','WEIGHTS_0')]
I=get(d['skins'][0]['inverseBindMatrices']).reshape((-1,4,4)).transpose((0,2,1))
T=np.array([j.get('translation',[0,0,0]) for j in N]);Q=np.array([j.get('rotation',[0,0,0,1]) for j in N])
S=np.array([j.get("scale",[1,1,1]) for j in N])
def evaluate(t,q,ss=S):
 out={}
 def M(i):
  if i not in out:
   a=np.eye(4);a[:3,:3]=Rot.from_quat(q[i]).as_matrix()*ss[i];a[:3,3]=t[i];out[i]=M(P[i])@a if i in P else a
  return out[i]
 return np.array([M(i) for i in range(len(N))])
def skin(t,q,ss=S):
 G=evaluate(t,q,ss)
 B=(G[jp]@I)[J]
 return ((np.einsum('mkij,mj->mki',B,np.c_[v,np.ones(len(v))]))*W[:,:,None]).sum(1)[:,:3]
if __name__=='__main__':
 G=evaluate(T,Q); print('aabb',v.min(0),v.max(0)); print('baseposed',skin(T,Q).min(0),skin(T,Q).max(0))
 for i in [42,40,39,16,7,4,1,0,15,14,11,10]:
  print(i,N[i]['name'],G[i,:3,3], 'first-axis',G[i,:3,0])
 for i in [0,1,10,11]:
  r=np.where(J==jp.index(i),W,0).sum(1)
  a=v[r>.999]
  y=a[:,1].min()
  print(i,len(a),a.min(0),a.max(0),'lowest10',a[np.argsort(a[:,1])[:10]])
def anim(name,phase):
 a=next(v for v in d['animations'] if v['name']==name)
 end=max(float(get(s['input'])[-1,0]) for s in a['samplers'])
 tt=end*phase
 t=T.copy();q=Q.copy();ss=S.copy()
 for ch in a['channels']:
  s=a['samplers'][ch['sampler']]; times=get(s['input'])[:,0];y=get(s['output'])
  ix=int(np.clip(np.searchsorted(times,tt,side='right')-1,0,len(times)-1))
  if ix+1<len(times):
   z=float(np.clip((tt-times[ix])/(times[ix+1]-times[ix]),0,1));u=y[ix+1]
   if y.shape[1]==4 and u@y[ix]<0:u=-u
   a0=y[ix]*(1-z)+u*z
  else:a0=y[ix]
  i=ch['target']['node'];k=ch['target']['path']
  if k=='translation':t[i]=a0
  elif k=='rotation':q[i]=a0/np.linalg.norm(a0)
  elif k=='scale':ss[i]=a0
  else:raise ValueError(k)
 return t,q,ss,end
