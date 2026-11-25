import json,sys,hashlib,numpy as np
from collections import Counter
from pathlib import Path
root=Path.cwd(); p=Path(sys.argv[1]); Q=np.load(p/'exact_native_shell.npz')
F=Q['faces']; region=set(Q['region'].tolist()); assert len(region)==147
approved=root/'hvn-l1-c1-approved-rear-fold-v1.kD1WNv'; A=np.load(approved/'new-rear-panel.npz'); B=json.loads((approved/'build.json').read_text())
assert np.array_equal(F,A['tri']) and set(A['region'])==region
R={}
for t in F[sorted(region)]:
 for u,v in zip(t,np.roll(t,-1)):
  k=tuple(sorted((u,v))); R[k]=R.get(k,0)+1
rim={e for e,count in R.items() if count==1};assert len(rim)==41 and {i for e in rim for i in e}==set(A['boundary'])
carrier={tuple(sorted(e)) for e in B['outline_carrier_edges']};assert len(carrier)==16
ret=np.flatnonzero(~np.isin(np.arange(len(F)),list(region))); assert len(ret)==42393
M=e=1.e-8
def cuts(V):
 T=V[F[ret]]; TL,TH=T.min(1),T.max(1)
 out=[]
 for i,j in sorted(rim|carrier):
  a,b=V[[i,j]].astype(float); d=b-a
  use=(TL<=np.maximum(a,b)+e).all(1)&(TH>=np.minimum(a,b)-e).all(1)
  ids=np.flatnonzero(use); L=T[ids].astype(float)
  n=np.cross(L[:,1]-L[:,0],L[:,2]-L[:,0]); N=np.linalg.norm(n,axis=1)
  n/=np.maximum(N,1e-30)[:,None]; d0=np.einsum('ij,ij->i',a-L[:,0],n); d1=np.einsum('ij,ij->i',b-L[:,0],n)
  for k in np.flatnonzero(((d0<-e)&(d1>e)|(d0>e)&(d1<-e))&(N>1e-14)):
   z=d0[k]/(d0[k]-d1[k]); X=a+d*z; tt=L[k];w=np.linalg.lstsq((tt[1:]-tt[0]).T,X-tt[0],rcond=None)[0]
   bc=np.r_[1-w.sum(),w]
   if min(bc)>1e-6 and e<z<1-e:
    out.append({'edge':[int(i),int(j)],'on_approved_stitch_rim':(i,j) in rim,'on_locked_outline_carrier_path':(i,j) in carrier,'retained_face':int(ret[ids[k]]),'t':float(z),'bary':bc.tolist(),'xyz_m':X.tolist(),'edge_coordinates_m':[a.tolist(),b.tolist()],'native_triangle_m':tt.tolist()})
 return out
def seg(A,B):
 def norm(t):
  v=np.cross(t[1]-t[0],t[2]-t[0]);return v/np.linalg.norm(v)
 A,B=np.asarray(A,float),np.asarray(B,float);m,no=norm(A),norm(B);t=np.cross(m,no);t/=np.linalg.norm(t)
 def l(A,B,n0):
  d=(A-B[0])@n0
  return [(A[i]+(A[j]-A[i])*(-d[i])/(d[j]-d[i]))@t for i,j in ((0,1),(1,2),(2,0)) if d[i]*d[j]<0],d
 x,dx=l(A,B,no);y,dy=l(B,A,m)
 return {'strict_overlap_span_mm':1000*max(0,min(max(x),max(y))-max(min(x),min(y))) if len(x) and len(y) else 0.,'signed_plane_distances_m':[dx.tolist(),dy.tolist()],'triangle_a':A.tolist(),'triangle_b':B.tolist()}
summary={}
for pose in ('bind','held'):
 V=Q[pose]; candidate=cuts(V)
 summary[pose]={'triangle_pairs':{f'{a}:{b}':seg(V[F[a]],V[F[b]]) for a,b in ((27920,42401),(28093,42401),(28093,28305),(27920,28305))},'all_protected_edge_crossings':candidate}
 print(pose,'strict crossings',len(candidate),[(a['edge'],a['retained_face'],a['on_approved_stitch_rim'],a['on_locked_outline_carrier_path']) for a in candidate],file=sys.stderr)
print(json.dumps({'frozen_geometry_scope':'exact native seated 0ms and neutral; line/triangle interior only; not full non-self intersection','all_pose_faces':len(F),'retained_faces':len(ret),'protected_rim_edges':len(rim),'outline_carrier_edges':len(carrier),'native_full_sha256':hashlib.sha256((p/'exact_native_shell.npz').read_bytes()).hexdigest(),'results':summary},indent=2))
