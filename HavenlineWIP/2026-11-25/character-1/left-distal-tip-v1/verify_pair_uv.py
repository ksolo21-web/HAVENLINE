import os
import numpy as np,json
from collections import Counter
from pathlib import Path
p=Path(__file__).parent
prev=np.load(Path(os.environ['C1_LEFT_SIDE_DATA']))
new=np.load(p/'editable_distal_tip.npz')
def edges(F,U):
 c=Counter();out={}
 for f,u in zip(F,U):
  for i,j in ((0,1),(1,2),(2,0)):
   e=(int(f[i]),int(f[j]));c[e]+=1;out[e]=(u[i],u[j])
 return c,out
F=prev['combined_tri']; UV=prev['corner_uv']; G=new['combined_tri']; TX=new['corner_uv']
assert np.array_equal(F,G[:len(F)]) and np.array_equal(UV,TX[:len(F)])
c,w=edges(F,UV);d,o=edges(G,TX)
rail=new['author_boundary'];n=0
for a,b in zip(rail,np.roll(rail,-1)):
 assert not c[a,b] and c[b,a]==d[b,a]==d[a,b]==1
 assert np.array_equal(o[a,b][0],w[b,a][1]) and np.array_equal(o[a,b][1],w[b,a][0])
 n+=1
assert n==8
results={}
for stage in ('open','bind'):
 P=new[stage];a=P[G[82]];b=P[G[116]]
 assert not np.isin(G[82],G[116]).any()
 def direction(X):
  q=np.cross(X[1]-X[0],X[2]-X[0]); return q/np.linalg.norm(q)
 na=direction(a);nb=direction(b)
 i0=(b-a[0])@na;i1=(a-b[0])@nb
 pts=[]
 for X,Y,N in [(a,b,nb),(b,a,na)]:
  for q,r in zip(X,np.roll(X,-1,axis=0)):
   dp=(q-Y[0])@N;dr=(r-Y[0])@N
   if dp*dr>0:continue
   Q=q+dp/(dp-dr)*(r-q)
   c0=np.linalg.pinv((Y[1:]-Y[0]).T)@(Q-Y[0])
   if min(c0)>=-1e-8 and c0.sum()<=1+1e-8 and all(np.linalg.norm(v-Q)>1e-7 for v in pts):pts.append(Q)
 assert len(pts)>=2
 results[stage]={'a_vertices':G[82].tolist(),'b_vertices':G[116].tolist(),'b_to_a_plane_mm':(i0*1000).tolist(),'a_to_b_plane_mm':(i1*1000).tolist(),
 'normal_separation_deg':float(np.degrees(np.arccos(np.clip(na@nb,-1,1)))),'crossing_segment_mm':float(1000*np.linalg.norm(pts[0]-pts[1]))}
print('8/8 opposing directed shared edges; 16/16 exact inherited seam-corner UV values.')
print(json.dumps(results,indent=2))
