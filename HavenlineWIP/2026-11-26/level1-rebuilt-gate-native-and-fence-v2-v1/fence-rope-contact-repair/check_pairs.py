from pathlib import Path
import json,sys,numpy as np
def read(p):
 v=[];f={}
 for l in p.read_text().splitlines():
  a=l.split()
  if not a:continue
  if a[0]=='v':v.append([float(x) for x in a[1:]])
  if a[0]=='usemtl':m=a[1];f[m]=[]
  if a[0]=='f':f[m].append([int(s.split('/')[0])-1 for s in a[1:]])
 v=np.array(v); return {k:v[x] for k,x in f.items()}
def norm(T):
 n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);return n/np.linalg.norm(n,axis=1)[:,None]
def witnesses(A,B,same=False):
 if not(len(A) and len(B)):return []
 n,m=norm(A),norm(B);out=[]
 al,ah=A.min(1),A.max(1);bl,bh=B.min(1),B.max(1)
 ii,jj=np.where(np.all((ah[:,None,:]>=bl[None,:,:]-1e-8)&(bh[None,:,:]>=al[:,None,:]-1e-8),axis=-1))
 def sec(a,d,w):
  xs=[a[i]@w for i in range(3) if abs(d[i])<=2e-8]
  for i,j in [(0,1),(1,2),(2,0)]:
   if min(abs(d[i]),abs(d[j]))>2e-8 and d[i]*d[j]<0:xs.append((a[i]+(a[j]-a[i])*d[i]/(d[i]-d[j]))@w)
  return min(xs),max(xs)
 for i,j in zip(ii,jj):
  if same and (i>=j or len(set(map(tuple,A[i])) & set(map(tuple,B[j])))):continue
  d=(A[i]-B[j,0])@m[j];e=(B[j]-A[i,0])@n[i]
  if not(d.min()<-2e-8<2e-8<d.max() and e.min()<-2e-8<2e-8<e.max()):continue
  w=np.cross(n[i],m[j]);nrm=np.linalg.norm(w)
  if nrm<1e-8:continue
  w/=nrm
  a,b=sec(A[i],d,w);c,q=sec(B[j],e,w); ov=min(b,q)-max(a,c)
  if ov>4e-8:out.append([int(i),int(j),float(ov)])
 return out
before,after=map(lambda x:read(Path(x)),sys.argv[1:3])
out=[]
for k in range(20):
 i=k//2;wood=after['amber_timber'][i*180:(i+1)*180]
 s=slice(k*128,(k+1)*128)
 a,b=before['cream_hemp'][s],before['warm_hemp'][s]
 A,B=after['cream_hemp'][s],after['warm_hemp'][s]
 assert np.array_equal(before['amber_timber'],after['amber_timber'])
 assert np.array_equal(before['draped_snow'],after['draped_snow'])
 old=witnesses(a,b);new=witnesses(A,B)
 wood_pairs0=witnesses(a,wood)+witnesses(b,wood);wood_pairs1=witnesses(A,wood)+witnesses(B,wood)
 assert wood_pairs1==wood_pairs0, (k,len(wood_pairs0),len(wood_pairs1))
 assert not old and new
 assert not witnesses(A,A,True) and not witnesses(B,B,True)
 faces={sign: [r for r in new if sign*A[r[0],:,2].min()>0] for sign in (1,-1)}
 assert sum(map(len,faces.values()))==len(new) and all(faces.values())
 out.append(dict(post=i,band=k%2,strict_pairs_per_face=[len(faces[z]) for z in (1,-1)],largest_intersection_segment_mm=max(r[2] for r in new)*1000,wood_strict_pairs_unchanged=len(wood_pairs1)))
print(json.dumps(out,indent=2))
