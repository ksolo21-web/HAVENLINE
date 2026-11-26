"""Continuous conservative angular exclusion over actual terrain for the worst heel keys."""
from pathlib import Path
import hashlib,sys,json,math
import numpy as np
from scipy.spatial.transform import Rotation
src=Path(sys.argv[3]).resolve()
assert hashlib.sha256((src/'SHA256SUMS').read_bytes()).hexdigest()=='02cdf3d01600e6a102f77ff1b9025572b429d2a0573af45a46f7536c0fd1cac4'
for lin in (src/'SHA256SUMS').read_text().splitlines():
 s,f=lin.split(maxsplit=1);assert hashlib.sha256((src/f).read_bytes()).hexdigest()==s
sys.path.insert(0,str(src))
import author as A,stock as S
h=Path(__file__).resolve().parent
faces=S.get(S.mesh['indices']).reshape(-1,3);v=S.v
canon=np.unique(v,axis=0,return_inverse=True)[1]
proof=[]
for role,k in [('left',72),('right',38)]:
 j=A.foot_ids[role];wt=A.w(j[2])+A.w(j[3]); pure=(wt>.9999995)
 low=(v[:,1]<=.009)&(v[:,2]<=.023)&pure
 sub=np.flatnonzero(low[faces].all(1))
 g={}
 for fi in sub:
  for vert in canon[faces[fi]]:g.setdefault(int(vert),[]).append(int(fi))
 stack=list(set(g[int(canon[A.feet[role]['heel']])]))
 sel=set(stack)
 while stack:
  for vert in canon[faces[stack.pop()]]:
   for f in g[vert]:
    if f not in sel:sel.add(f);stack.append(f)
 heel=np.unique(faces[sorted(sel)])
 low=heel[v[heel,0]<=v[heel,0].min()+.3*np.ptp(v[heel,0])]
 high=heel[v[heel,0]>=v[heel,0].max()-.3*np.ptp(v[heel,0])]
 t,q,s,req,actor=A.motion(k/72)
 G=S.evaluate(t,q,s)
 o=(G[j[2],:3,3]+A.offset)*A.scale+actor
 w=(S.skin(t,q,s)+A.offset)*A.scale+actor
 full=A.feet[role]['rows'];D=np.unique(np.r_[full[pure[full]],heel])
 X=w[D]-o;r=float(np.max(np.linalg.norm(X,axis=1)))
 segments=[np.searchsorted(D,zone) for zone in [low,high]]
 u=(np.floor((o[[0,2]]-r)*4).astype(int),np.ceil((o[[0,2]]+r)*4).astype(int))
 slopes=[]
 for i in range(u[0][0],u[1][0]+1):
  for z in range(u[0][1],u[1][1]+1):
   a,b,c,d=[A.vertex(x*.25,y*.25)[0] for x,y in [(i,z),(i+1,z),(i,z+1),(i+1,z+1)]]
   slopes.extend([4*math.hypot(b-a,c-a),4*math.hypot(d-c,d-b)])
 lip_per_degree=2*math.hypot(1,max(slopes))*r*math.pi/180
 def f(p,l):
  y=X@Rotation.from_euler('xz',[p,l],degrees=True).as_matrix().T+o
  e=y[:,1]-A.ground_batch(y)
  return float(max(e[z].min() for z in segments)-e.min())
 cells=[(-8.,8.,-6.,6.)];n=0;tested_min=1.;smallest=1.;insufficient=[];target=.0019
 while cells:
  a,b,c,d=cells.pop();p,l=(a+b)*.5,(c+d)*.5
  y=f(p,l);n+=1;tested_min=min(tested_min,y)
  lb=y-lip_per_degree*((b-a+d-c)*.5)
  # Margin includes a 0.025mm tolerance for pure-weight rounding and numeric reconstruction.
  if lb>target+0.000025:
   smallest=min(smallest,lb);continue
  if y<target+0.000025 or max(b-a,d-c)<0.0078125:
   insufficient.append([a,b,c,d,float(y*1000)]);break
  if b-a>=d-c: cells.extend([(a,p,c,d),(p,b,c,d)])
  else: cells.extend([(a,b,c,l),(a,b,l,d)])
  assert n<24000
 proof.append(dict(role=role,index=k,angular_cells_examined=n,whole_angular_box_certified=not insufficient, smallest_terminal_cell_bound_mm=smallest*1000,
                   smallest_examined_center_mm=tested_min*1000, exact_selected_heel_faces=len(sel), active_material_minmax_world_m=[o.tolist(),r],
                   lower_bound_worse_side_requirement_mm=target*1000, conservative_snow_grad=max(slopes), support_margin_lipschitz_mm_per_degree=lip_per_degree*1000,
                   unproved_first_cell=insufficient))
print(json.dumps(proof,indent=2))
