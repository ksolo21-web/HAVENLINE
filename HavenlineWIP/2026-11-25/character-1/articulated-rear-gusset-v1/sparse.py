import os
import numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parent; A=np.load(P/'gusset.npz')
T=A['tri']; kind=A['labels']; active=A['scope']; norm=lambda x:np.linalg.norm(x)
def unit(v):return v/norm(v)
def normal(u):return unit(np.cross(u[1]-u[0],u[2]-u[0]))
def bary(P,A):
 y=P-A[0]; m=(A[1:]-A[0]).T
 d=np.linalg.lstsq(m,y,rcond=None)[0]
 return np.r_[1-d.sum(),d]
def segtri(p,q,T):
 t=normal(T); a=(p-T[0])@t; b=(q-T[0])@t
 if a*b>0 or abs(a-b)<1.e-14:return None
 x=p+(q-p)*a/(a-b); y=bary(x,T)
 if y.min()>=-1e-10:return x
def hits(A,B):
 c=[]
 for p,q in ((A,B),(B,A)):
  for i in range(3):
   x=segtri(p[i],p[(i+1)%3],q)
   if x is not None and all(norm(x-y)>1.e-10 for y in c):c.append(x)
 return c
def segment_dist(P,Q,R,S):
 u=Q-P;v=S-R;w=P-R
 a=u@u;b=u@v;c=v@v;d=u@w;e=v@w
 z=[]
 for x in (0.,1.):
  y=np.clip((e+x*b)/c,0,1);z.append(norm(w+x*u-y*v))
 for y in (0.,1.):
  x=np.clip((y*b-d)/a,0,1);z.append(norm(w+x*u-y*v))
 D=a*c-b*b
 if D>1e-30:
  x=(b*e-c*d)/D;y=(a*e-b*d)/D
  if 0<=x<=1 and 0<=y<=1:z.append(norm(w+x*u-y*v))
 return min(z)
def point_face(x,t):
 y=x-((x-t[0])@normal(t))*normal(t)
 return norm(y-x) if bary(y,t).min()>=-1e-10 else float('inf')
def tri(A,B):
 hit=hits(A,B)
 sd=[point_face(x,B) for x in A]+[point_face(x,A) for x in B]
 sd.extend(segment_dist(A[i],A[(i+1)%3],B[j],B[(j+1)%3]) for i in range(3) for j in range(3))
 return dict(intersections=len(hit),edge_cross_points_mm=[(x*1000).tolist() for x in hit],crossing_span_mm=0 if len(hit)<2 else max(norm(x-y) for x in hit for y in hit)*1000,true_distance_mm=0 if hit else min(sd)*1000,dihedral_normal_angle_deg=float(np.degrees(np.arccos(np.clip(normal(A)@normal(B),-1,1)))),leg_A_signed_to_B_mm=(((A-B[0])@normal(B))*1000).tolist(),leg_B_signed_to_A_mm=(((B-A[0])@normal(A))*1000).tolist())
focus=np.flatnonzero(active)
record=[]
for name,X in [('neutral_3D',A['v']),('exact_0ms_mechanical_prediction',A['native0'])]:
 V=X[T]; lo=V.min(1);hi=V.max(1)
 candidates=[]
 # Separate piece triangle-to-triangle witness, excluding deliberately sewn same vertices.
 low=np.flatnonzero(kind=='shin');higher=np.flatnonzero(kind=='thigh')
 gap=float('inf');hit=[];n=0
 for i in low:
  for j in higher:
   if np.isin(T[i],T[j]).any():continue
   q=tri(V[i],V[j]);n+=1
   gap=min(gap,q['true_distance_mm'])
   if q['intersections']:hit.append([int(i),int(j),q['crossing_span_mm']])
 for i in focus:
  js=np.flatnonzero(((lo<=hi[i]+1.e-11)&(hi>=lo[i]-1.e-11)).all(1))
  for j in js:
   if i==j or (active[j] and j<i) or np.isin(T[i],T[j]).any():continue
   r=hits(V[i],V[j])
   if r:candidates.append([int(i),int(j)])
 report={'label':name,'lower_upper_pair_count':n,'strict_predicted_shin_thigh_min_mm':gap,'crosses':hit,'scoped_nonadjacent_pairs_count':len(candidates),'scoped_pairs':candidates}
 record.append(report);print(report,flush=True)
(P/'sparse.json').write_text(json.dumps(record,indent=2,default=lambda v:v.item()))
