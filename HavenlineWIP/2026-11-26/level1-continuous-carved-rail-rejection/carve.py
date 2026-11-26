from pathlib import Path
import json,hashlib,numpy as np,itertools
from scipy.interpolate import PchipInterpolator
R=Path(__file__).resolve().parent;P=R.parent
E=P/'hvn-l1-fence-33036-continuous-run-envelope-v1'
assert hashlib.sha256((E/'SHA256SUMS').read_bytes()).hexdigest()=='05b2c988c45e439ab0d1c4df715ec44bbfdbbc138c1c9614df5d6587d5f5064f'
source=json.loads((E/'result.json').read_text())
from math import pi
C={'__file__':str(E/'envelope.py')};txt=(E/'envelope.py').read_text();exec(txt[:txt.index('for k,d in world.items():')],C)
terrain=C['ctx']['height'];norms=C['ctx']['norms'];span=C['ctx']['span'];old=.066885
RS=.013455;RY=.0235; RD=.05655; HH=.064
Y=np.linspace(-HH,HH,25)
flipped=[-1,1]
def tube(rows):
 T=[]
 for a,b in zip(rows,rows[1:]):
  for k in range(len(a)):
   j=(k+1)%len(a);T += [(a[k],a[j],b[j]),(a[k],b[j],b[k])]
 for i,last in [(0,False),(-1,True)]:
  q=rows[i];c=q.mean(0)
  for k in range(len(q)):
   j=(k+1)%len(q);T.append((c,q[k],q[j]) if last else (c,q[j],q[k]))
 T=np.asarray(T)
 d=np.einsum('ij,ij->i',T[:,0],np.cross(T[:,1],T[:,2])).sum()
 return T if d>0 else T[:,::-1]
def strict(a,b):
 # 3D bounding search in run/local axial coordinate. Full strict positive crossings.
 xlo,xhi=a.min(1),a.max(1);ylo,yhi=b.min(1),b.max(1);nb=norms(b);na=norms(a);total=0;length=0;pair=None
 for i in range(len(a)):
  idx=np.flatnonzero(np.all((xlo[i]<=yhi)&(xhi[i]>=ylo),axis=1))
  for j in idx:
   k=span(a[i],b[j],na[i],nb[j])
   if k>4e-7:
    total+=1
    if k>length:length=k;pair=[i,int(j)]
 return [total,length*1000,pair]
def local_shell(z,t):
 b=.050*np.cos(2*pi*z/.36);margin=np.clip((abs(b)-.025)/.030,0,1);m=margin*margin*(3-2*margin)
 centers=[(-b,.1313),(b,.101+(.0303*m))]
 R0=[(old+RD*np.sqrt(max(0,1-(v/HH)**2)),v) for v in Y]
 fac=[]
 for d,v in R0:
  # Near-lower slot gets a proper curved undercut in Y, broadened by 5mm to
  # cover true coarse angle ribbons; at crossing preserve a clean wood shoulder.
  for off,dep in centers:
   s=np.clip((abs(v-off)-(RY+.004))/.011,0,1)
   s=s*s*(3-2*s)
   limit=dep-RS-.0028
   d=min(d,limit+(d-limit)*s) if d>limit else d
  fac.append([z,t+v,d])
 # Machinable front triangular-strip relief; closed rear half unchanged circular envelope.
 tail=[[z,t+v,old-RD*np.sqrt(max(0,1-(v/HH)**2))] for v in Y[-2:0:-1]]
 return np.array(fac+tail),centers
def section(k):
 a=source['run_bare_terrain_bounds_and_grade'][k]
 lo,hi=a['protected_run_study_endpoints_m']
 # Continuous footprint bounds plus grade headroom. Raise with smooth station intervals,
 # conservatively derive both end stations to cover neighbor terrain extrema.
 S=np.array([v['s_range'][0] for v in a['all_segment_extrema']]+[hi])
 raw=np.array([v['exact_indexed_terrain_y_minmax'][1] for v in a['all_segment_extrema']])
 heights=np.maximum(np.r_[raw[0],raw],np.r_[raw,raw[-1]])+.073
 f=PchipInterpolator(S,heights)
 # Aligned same axial samples enforce real indexed section surfaces globally.
 X=np.unique(np.r_[np.linspace(lo,hi,round((hi-lo)/.022)+1),S]);X=np.sort(X)
 D={i:[] for i in ['wood','front_clear','front_warm','rear']}
 for z in X:
  yy=float(f(z)); Q,centers=local_shell(z-lo,yy)
  Q[:,0]+=lo
  D['wood'].append(Q)
  for j,k2 in enumerate(['front_clear','front_warm']):
   y,depth=centers[j]
   th=np.arange(12)*2*pi/12
   D[k2].append(np.c_[np.repeat(z,len(th)),yy+y+RY*np.cos(th),depth+RS*np.sin(th)])
  th=np.arange(10)*2*pi/10
  D['rear'].append(np.c_[np.repeat(z,len(th)),yy+.003*np.cos((z-lo)*2*pi/.36)+.010*np.cos(th),-.128+.01248*np.sin(th)])
 T={t:tube(np.array(v)) for t,v in D.items()}
 # Retains positive shape and full owner width context; stock projected normal check is numeric only.
 widths=[float(np.max(v[:,2])) for v in D['wood']]
 narrow=np.mean(np.asarray(widths)>=.119)
 joints={}
 for (p,u),(q,v) in itertools.combinations(T.items(),2):
  z=strict(u,v)
  if z[0]:joints[p+'/'+q]=z
 # Audit group closed consistency in exact scope.
 from collections import Counter
 def closure(t):
  cc=Counter();dd=Counter()
  for f in np.round(t,8):
   ccorners=list(map(tuple,f))
   for a,b in zip(ccorners,ccorners[1:]+ccorners[:1]):
    k=tuple(sorted((a,b)));cc[k]+=1;dd[k]+=1 if a==k[0] else -1
  return all(n==2 and dd[k]==0 for k,n in cc.items())
 assert all(closure(tt) for tt in T.values())
 # All terrain maxima under the most permissive full visual strip, not just shaft width.
 # Exact reference indexed terrain extrema used; art min Y is affine per loft slab.
 ctr=source['study_bound_geometry_not_move_permission'][k]['center']
 ia=source['study_bound_geometry_not_move_permission'][k]['ax']
 cbox=C['corners']; strip=[]
 for lo1,hi1 in zip(S[:-1],S[1:]):
  for label,face in T.items():
   uv=face[(face[:,:,0].min(1)<=hi1)&(face[:,:,0].max(1)>=lo1)]
   vv=cbox(ia,lo1,hi1,ctr-.14742,ctr+.14742)
   if len(uv):strip.append([float(uv[:,:,1].min()-vv[:,2].max()),label,float(lo1),float(hi1)])
  Q=dict(samples=len(X),part_faces={nm:len(t) for nm,t in T.items()},crossings=joints,
    positive_design_margin_to_14742_mm=float((.14742-max(t[:,:,2].max() for t in T.values()))*1000),
    whole_strip_conservative_terrain_gap_min_m_label_interval=min(strip),directed_weld_closure_all=True,full_nose_fraction_retained_stock_center=narrow,grade_derivative_peak=float(max(np.abs(f.derivative()(X)))),
    raised_y_ranges=[float(f(X).min()),float(f(X).max())],
    scope_caps='analytically closed welded end disks; true concealment within rooted terminals not assessed')
 return T,Q
allm={};rv={}
for run in ('South','West'):
 allm[run],rv[run]=section(run)
(R/'result.json').write_text(json.dumps(rv,indent=2)+'\n')
print(json.dumps(rv))
# Non-admitted math diagnostic actual whole-length lower section. No private textures.
v=['# HOLD carved lower section source witness. Not a game asset.'];n=1
for k,T in allm.items():
 for p,Tri in T.items():
  v.append('o '+k+'_'+p)
  for f in Tri:
   for pt in f:v.append('v '+' '.join(f'{n:.9f}' for n in pt))
   v.append(f'f {n} {n+1} {n+2}');n+=3
(R/'CarvedWholeGrade_HOLD.obj').write_text('\n'.join(v)+'\n')
