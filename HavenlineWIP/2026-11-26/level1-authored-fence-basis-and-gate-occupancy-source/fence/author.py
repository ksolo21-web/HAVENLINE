from pathlib import Path
import numpy as np,hashlib,json,sys
from collections import defaultdict,Counter
R=Path(__file__).resolve().parent
S=R.parent/'hvn-l1-fence-33036-rooted-emboss-module-v1'
sha=lambda x:hashlib.sha256(x).hexdigest()
assert sha((S/'SHA256SUMS').read_bytes())=='cfe4449f40ff684aafe5565490d19de17684f9b2ebcd7e55180a291b66365c1d'
for row in (S/'SHA256SUMS').read_text().splitlines():
 h,n=row.split(maxsplit=1); assert sha((S/n).read_bytes())==h
P=[];UV=[];Fs=[];G=[];M=[]
for line in (S/'RootedEmbossedFence_SourceOnly.obj').read_text().splitlines():
 w=line.split()
 if not w:continue
 if w[0]=='o':g=w[1]
 if w[0]=='usemtl':m=w[1]
 if w[0]=='v':P.append(tuple(map(float,w[1:])))
 if w[0]=='vt':UV.append(tuple(map(float,w[1:])))
 if w[0]=='f':Fs.append([tuple(int(i)-1 for i in j.split('/')) for j in w[1:]]);G.append(g);M.append(m)
F=np.array(Fs);p=np.array(P)[F[:,:,0]];uv=np.array(UV)[F[:,:,1]]
assert len(p)==11952
A=p[:,1]-p[:,0];B=p[:,2]-p[:,0];NR=np.cross(A,B);N0=NR/np.linalg.norm(NR,axis=1)[:,None]
links=np.arange(p.size//3)
def top(i):
 while i!=links[i]:
  links[i]=links[links[i]]
  i=links[i]
 return int(i)
def union(i,j):
 a,b=top(i),top(j)
 if a!=b:links[max(a,b)]=min(a,b)
edges=defaultdict(list); cap={}
for i,tri in enumerate(p):
 cap[i]=G[i].startswith(('rail_','rear_')) and np.ptp(tri[:,0])==0. and abs(N0[i,0])>.999999
 for j in range(3):
  k=(j+1)%3; a,b=tuple(tri[j]),tuple(tri[k])
  edges[G[i],*sorted((a,b))].append((i,j,k,a<b))
hard=Counter()
for key,E in edges.items():
 if len(E)!=2 or E[0][-1]==E[1][-1]:
  hard['non_two_opposed_edge']+=1;continue
 (i,j,k,s),(f,l,m,_)=E
 assert np.array_equal(p[i,j],p[f,m]) and np.array_equal(p[i,k],p[f,l])
 if cap[i]!=cap[f]:
  hard['end_cap_rim']+=1;continue
 if N0[i]@N0[f]<(0.30 if (G[i].startswith(('rail_','rear_')) and not cap[i]) else .78):
  hard['crease']+=1;continue
 union(i*3+j,f*3+m);union(i*3+k,f*3+l)
K=np.array([top(j) for j in range(3*len(p))]).reshape(-1,3)
W=np.empty(K.shape); weights=defaultdict(lambda:np.zeros(3))
for j in range(3):
 E=np.roll(p,-1,axis=1)[:,j]-p[:,j];H=np.roll(p,1,axis=1)[:,j]-p[:,j]
 W[:,j]=np.arctan2(np.linalg.norm(np.cross(E,H),axis=1),np.einsum('ij,ij->i',E,H))
 for i in range(len(p)):weights[K[i,j]]+=W[i,j]*N0[i]
N=np.array([[weights[k]/np.linalg.norm(weights[k]) for k in row] for row in K])
assert np.isfinite(N).all()
a=uv[:,1]-uv[:,0];b=uv[:,2]-uv[:,0]
D=a[:,0]*b[:,1]-a[:,1]*b[:,0]
T=np.zeros((*K.shape,4)); sums=defaultdict(lambda:np.zeros(3))
atlas=[i for i,m in enumerate(M) if m=='emboss_atlas']
assert len(atlas)==3200 and np.all(D[atlas]>.0012)
for i in atlas:
 t=(A[i]*b[i,1]-B[i]*a[i,1])/D[i]
 for j in range(3):sums[(K[i,j],*uv[i,j])]+=W[i,j]*t/np.linalg.norm(t)
dots=[]
for i in atlas:
 b0=(-A[i]*b[i,0]+B[i]*a[i,0])/D[i];b0/=np.linalg.norm(b0)
 for j in range(3):
  t=sums[(K[i,j],*uv[i,j])];nt=N[i,j];t=t-nt*(nt@t);t=t/np.linalg.norm(t)
  dot=float(np.cross(nt,t)@b0); dots.append(dot)
  T[i,j]=[*t,np.sign(dot)]
assert min(dots)>.25 and np.isfinite(T).all()
alignment=np.einsum('ijk,ik->ij',N,N0)
assert alignment.min()>0
assert np.max(np.abs(np.einsum('ijk,ijk->ij',N[atlas],T[atlas,:,:3])))<1e-10
# Atlas boundary geometry remains one normal fan at actual neighbors even though
# the tangent table and texture slots remain consciously material-separated.
atlas_cross=0
for E in edges.values():
 if len(E)!=2:continue
 (i,j,k,s),(f,l,m,t)=E
 if G[i].startswith('rail_') and M[i]!=M[f] and s!=t:
  if K[i,j]==K[f,m] and K[i,k]==K[f,l]:atlas_cross+=1
res={'status':'detached provisional explicit basis; further independent profile and native admission required',
 'faces':len(p),'position_and_uv_signed_source_corner_index_sha256':sha(F.tobytes()),'whole_position_sha256_f64':sha(p.tobytes()),'whole_uv_sha256_f64':sha(uv.tobytes()),'normal_sha256_f64':sha(N.tobytes()),'source_space_tangent_sha256_f64':sha(T.tobytes()),'normal_fans':len(weights),'hard_edges':dict(hard),'smooth_atlas_wood_joint_edges':atlas_cross,'min_winding_vs_authored_corner_normal_dot':float(alignment.min()),'min_atlas_positive_v_alignment':min(dots),
 'texture_pins':{q:sha((S/q).read_bytes()) for q in ('RopeFiberBaseColor.png','RopeFiberNormal.png')}}
if len(sys.argv)==2:
 dest=Path(sys.argv[1]).resolve();assert dest.is_relative_to(R) and not dest.exists();dest.mkdir()
 np.savez(dest/'ExplicitSourceBasis.npz',position=p,source_uv=uv,normal=N,tangent_source=T,faces_source=F,material=np.array(M),group=np.array(G),normal_fan=K)
print(json.dumps(res,indent=2))
