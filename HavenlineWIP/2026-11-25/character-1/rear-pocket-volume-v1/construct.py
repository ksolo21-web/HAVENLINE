import os
import numpy as np,hashlib,json
from pathlib import Path
from scipy.spatial.transform import Slerp,Rotation
P=Path(__file__).resolve().parent
H=Path(os.environ['C1_APPROVED_REAR_DATA'])
S=(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(H/'new-rear-panel.npz')=='023ed33af9ac04e8c6223fb6abfd2f2002d3b3b8a06c00b50dba0b581ad389bf'
assert h(S)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
a=np.load(H/'new-rear-panel.npz');ref=np.load(S)
V=a['v'];T=a['tri'];RG=a['region']; w=a['w'];S0=float(ref['scale']);O=ref['source_origin']
X=V[T[RG]][:,:,[0,2]]
raw=M=ref['bones'][0,1]; assert M.shape==(4,4,4)
# Bind two exact source material rails per panel; all lookup signed x-left
# y-back z-up. Articulated design units metre, exact approved scale.
lanes=np.array([-.151,-.136,-.121,-.105,-.089])
z0,z1=.411,.463
def witness(x,z):
 A=X[:,0];b=X[:,1]-A;c=X[:,2]-A;d=np.array([x,z])-A
 D=b[:,0]*c[:,1]-b[:,1]*c[:,0]
 u=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/D
 v=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/D
 Q=np.stack([1-u-v,u,v],1);j=int(np.argmax(Q.min(1)))
 assert Q[j].min()>-1e-9,(x,z)
 out=Q[j]@V[T[RG[j]]]
 return out,dict(face=int(RG[j]),vertex_ids=T[RG[j]].tolist(),barycentric=Q[j].tolist(), point_m=out.tolist())
src={}
rails={}
for name,rows in [('shin',(.397,.404,.41075)),('thigh',(.46325,.470,.478)),('attachment',(.411,.463))]:
 p=[];k=[]
 for zz in rows:
  q=[witness(xx,zz) for xx in lanes]
  p.append([x[0] for x in q]); k.append([x[1] for x in q])
 src[name]=np.array(p);rails[name]=k
def apply(x,R,t):
 p=np.asarray(x)/S0+O
 return ((p@R.T)+t-O)*S0
def rigid(s):
 R=np.array([Slerp([0,1],Rotation.from_matrix(np.array([np.eye(3),f[:3,:3]])))([s]).as_matrix()[0] for f in M])
 tt=M[:,:3,3]*s
 return R,tt
def slab_grid(top,bottom):
 # ordered grid consistent; top and lower layer plus all side walls closed.
 ny,nx=top.shape[:2]; n=nx*ny
 assert np.min(np.linalg.norm(top-bottom,axis=-1))>1e-4
 u=np.concatenate((top.reshape(-1,3),bottom.reshape(-1,3)))
 f=[]
 for j in range(ny-1):
  for i in range(nx-1):
   a=j*nx+i; b=a+1;c=b+nx;d=c-1
   f.extend(((a,b,c),(a,c,d),(a+n,c+n,b+n),(a+n,d+n,c+n)))
 rim=list(range(nx))+[j*nx+nx-1 for j in range(1,ny)]+[(ny-1)*nx+i for i in range(nx-2,-1,-1)]+[j*nx for j in range(ny-2,0,-1)]
 for i,j in zip(rim,rim[1:]+rim[:1]):
  f.extend(((j,i,i+n),(j,i+n,j+n)))
 f=np.array(f)
 vol=np.sum(np.einsum('ij,ij->i',u[f][:,0],np.cross(u[f][:,1],u[f][:,2])))/6
 if vol<0:f=f[:,[0,2,1]];vol=-vol
 return u,f,float(vol)
poses=[]; topology={}; intervals=np.linspace(0,1,17)
for q in intervals:
 R,tt=rigid(float(q));X=[]
 old_raw=V/S0+O
 native=(np.einsum('nbi,nb->ni',np.einsum('bij,nj->nbi',R,old_raw)+tt,w)-O)*S0
 r0,r1=[apply(r,R[i],tt[i]) for r,i in zip(src['attachment'],(1,0))]
 for tag,i in [('shin',1),('thigh',0)]:
  rw=src[tag].copy();top=rw+np.array([0.,-.00135,0.]); bottom=rw+np.array([0.,-.00210,0.])
  uv,ft,vol=slab_grid(apply(top,R[i],tt[i]),apply(bottom,R[i],tt[i]))
  X.append(uv);topology.setdefault(tag,{'f':ft,'v':len(uv),'vol_m3':vol,'spec':'0.750mm finite thickness, 1.350mm inset from measured exterior anchor'})
 # Rolling return explicitly spans actual paired rails. Attachment tips
 # end short of rigid slab edges, no nominal shared surface contact in test.
 caps=[];bots=[]
 for mu in np.linspace(.025,.975,9):
  Q=(1-mu)*r0+mu*r1
  # Measure bands in both neutral and held, no forced limb stretching:
  # return bounds sine shape with fixed shallow inward pocket and loaded extra slack.
  fm=Slerp([0,1],Rotation.from_matrix(R[[1,0]]))([mu]).as_matrix()[0]
  inward=fm@np.array([0.,-1.,0.]); wave=np.sin(np.pi*mu)
  d=.00135+.00240*wave
  caps.append(Q+inward*d);bots.append(Q+inward*(d+.00065))
 uv,ft,vol=slab_grid(np.array(caps),np.array(bots))
 X.append(uv);topology.setdefault('return',{'f':ft,'v':len(uv),'vol_m3':vol,'spec':'0.650mm thick, bounded 2.4mm additional inset, normalized swing .025–.975'})
 poses.append((X,native))
out={'exact_stock_transforms':True,'exact_sweep':'lambda=q from neutral->held; shortest proper rotations and linear exact translation per bone; frozen authored geometrical layers, not walk time','thickness_mm':{'shin':.75,'thigh':.75,'return':.65},'rail_material_relations':rails,'frames':intervals.tolist()}
(P/'construction.json').write_text(json.dumps(out,indent=2))
np.savez_compressed(P/'pocket-solids.npz',shin=np.array([v[0][0] for v in poses]),thigh=np.array([v[0][1] for v in poses]),roll=np.array([v[0][2] for v in poses]),shin_tri=topology['shin']['f'],thigh_tri=topology['thigh']['f'],roll_tri=topology['return']['f'],retained=np.array([v[1] for v in poses],dtype=np.float32),shell_tri=T)
for k,j in [('neutral',0),('held',-1)]:
 with (P/f'proof-pocket-{k}.obj').open('w') as f:
  off=1
  for i,(n,z) in enumerate(topology.items()):
   V0=poses[j][0][i]
   f.write('o '+n+'\n')
   for v in V0:f.write('v '+' '.join('%.10f'%x for x in v)+'\n')
   for t in z['f']:f.write('f '+' '.join(str(off+x) for x in t)+'\n')
   off+=len(V0)
print([(k,z['v'],len(z['f']),z['vol_m3']) for k,z in topology.items()],flush=True)
