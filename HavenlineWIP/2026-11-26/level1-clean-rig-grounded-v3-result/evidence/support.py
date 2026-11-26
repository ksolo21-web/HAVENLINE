from collections import defaultdict
import numpy as np
def clip(poly,limit,positive):
 out=[]
 for v,u in zip(poly,np.roll(poly,1,axis=0)):
  a=(v[2]-limit)*(1 if positive else -1);b=(u[2]-limit)*(1 if positive else -1)
  if (a>=0)!=(b>=0):out.append(u+(v-u)*(b/(b-a)))
  if a>=0:out.append(v)
 return np.array(out)
def connected(v,tr,weld):
 a=v[tr]; m=(a[:,:,2].max(1)>=-.001)&(a[:,:,2].min(1)<=.002)
 a=a[m];tr=tr[m]
 g=defaultdict(list);areas=[];parents=[]
 def root(k):
  while k!=parents[k]:k=parents[k]
  return k
 for pts,row in zip(a,tr):
  poly=clip(pts,-.001,True)
  if len(poly)<3:continue
  poly=clip(poly,.002,False)
  if len(poly)<3:continue
  x,y=poly[:,:2].T; area=abs(float(x@np.roll(y,1)-y@np.roll(x,1)))*.5
  if area<=1e-12:continue
  n=len(areas);areas.append(area);parents.append(n)
  for j in range(3):
   k=(j+1)%3
   # Only actual shared non-point support interval in the clipped region connects faces.
   lo,hi=sorted((float(pts[j,2]),float(pts[k,2])))
   if (hi>lo and min(hi,.002)-max(lo,-.001)<=1e-10) or (hi==lo and not -.001<=lo<=.002):continue
   pair=tuple(sorted((int(weld[row[j]]),int(weld[row[k]]))))
   if pair[0]==pair[1]:continue
   for old, edge in g[pair]:
    # Refuse seam connections that have separated when posed.
    cur=pts[[j,k]]; order=[0,1] if weld[row[j]]<weld[row[k]] else [1,0]; cur=cur[order]
    if np.max(np.abs(cur-edge))<1e-6:parents[root(old)]=root(n)
   cur=pts[[j,k]]; order=[0,1] if weld[row[j]]<weld[row[k]] else [1,0]
   g[pair].append((n,cur[order]))
 comp=defaultdict(list)
 for n,a in enumerate(areas):comp[root(n)].append(a)
 best=max(comp.values(),key=sum,default=[])
 return {'largest_face_count':len(best),'largest_projected_face_area_sum_mm2':round(sum(best)*1e6,4),'components':len(comp)}
