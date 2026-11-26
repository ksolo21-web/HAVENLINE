"""Read-only physical support axle admission; no candidate asset emission."""
from pathlib import Path
import hashlib,sys,json,math
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
h=Path(__file__).resolve().parent
src=Path(sys.argv[3]).resolve()
assert hashlib.sha256((src/'SHA256SUMS').read_bytes()).hexdigest()=='02cdf3d01600e6a102f77ff1b9025572b429d2a0573af45a46f7536c0fd1cac4'
for lin in (src/'SHA256SUMS').read_text().splitlines():
 s,f=lin.split(maxsplit=1);assert hashlib.sha256((src/f).read_bytes()).hexdigest()==s
sys.path.insert(0,str(src))
import author as A,stock as S
faces=S.get(S.mesh['indices']).reshape(-1,3)
V=S.v
weld=np.unique(V,axis=0,return_inverse=True)[1]
beam={}
for role in ('left','right'):
 j=A.foot_ids[role];f,t=A.w(j[2]),A.w(j[3])
 low=(V[:,1]<=.009)&(V[:,2]>=.058)&((f+t)>.999995)
 sub=np.flatnonzero(low[faces].all(1))
 M={}
 for i in sub:
  canon=weld[faces[i]]
  for x in canon:M.setdefault(int(x),[]).append(int(i))
 work=set(map(int,sub));parts=[]
 while work:
  x=work.pop();last=[x];group=[x]
  while last:
   for c in weld[faces[last.pop()]]:
    for a in M[c]:
     if a in work:work.remove(a);last.append(a);group.append(a)
  parts.append(group)
 failure=16557 if role=='left' else 14606
 obs=np.flatnonzero(np.any(weld[faces]==weld[failure],axis=1))
 sel=next(p for p in parts if set(p)&set(obs))
 rows=np.unique(faces[sel]);assert np.max(t[rows])>.1 and np.min(t[rows])<.1
 lo,hi=V[rows,0].min(),V[rows,0].max();d=hi-lo
 beam[role]=(rows, np.array(sel), lo+.30*d, hi-.30*d, d, failure)

out=[]
def candidate(q,t,ss,G,role,pitch,roll,dy):
 th,cal,fo,to=A.foot_ids[role]
 q=q.copy()
 R=Rotation.from_euler('xz',[pitch,roll],degrees=True).as_matrix()
 Gp={i:R@G[i,:3,:3] for i in (fo,to)}
 a,b=np.linalg.norm(S.T[cal]),np.linalg.norm(S.T[fo])
 x=G[fo,:3,3]+np.array([0.,dy/A.scale,0.]);H=G[th,:3,3]
 leng=np.linalg.norm(x-H);dir=(x-H)/leng
 pole=np.array([(-.015 if role=='right' else .015),0,1.]);pole=A.unit(pole-dir*(dir@pole))
 li=(a*a+leng*leng-b*b)/(2*leng)
 if li**2>=a*a:return None,None
 k=H+li*dir+pole*math.sqrt(a*a-li*li)
 transform={th:A.rot(A.G0[cal,:3,3]-A.G0[th,:3,3],k-H)@A.G0[th,:3,:3],
         cal:A.rot(A.G0[fo,:3,3]-A.G0[cal,:3,3],x-k)@A.G0[cal,:3,:3], **Gp}
 for i,M in transform.items():A.assign_q(t,q,ss,i,S.evaluate(t,q,ss),M)
 g=S.evaluate(t,q,ss)
 assert np.max(abs(g[39]-G[39]))<1e-12
 assert np.max(abs(g[fo,:3,3]-x))<1e-9
 return q, g
for role,idx in [('left',39),('right',72)]:
 po,qo,so,req,actor=A.motion(idx/72);G=S.evaluate(po,qo,so);W=(S.skin(po,qo,so)+A.offset)*A.scale+actor
 rows,sub,left_bound,right_bound,B,oldbad=beam[role]
 # Guaranteed rigid under common Foot+Toe world rotation for pure combined
 # skin rows, even in the real weight-transition belt. Others checked in
 # the exact final per-bone solve after choosing the physical axle.
 skinrows=A.feet[role]['rows']; names=A.foot_ids[role]
 pure=skinrows[((A.w(names[2])+A.w(names[3]))[skinrows])>.999995]
 choose=np.unique(np.r_[rows,pure]); assert oldbad in choose
 sign=-1 if role=='left' else 1
 med=rows[V[rows,0]<left_bound];lat=rows[V[rows,0]>right_bound]
 worldankle=(G[names[2],:3,3]+A.offset)*A.scale+actor
 def evaluate(p,l,full=False):
  m=Rotation.from_euler('xz',[p,l],degrees=True).as_matrix()
  pos=(W[choose]-worldankle)@m.T+worldankle
  domain=(np.searchsorted(choose,lat),np.searchsorted(choose,med))
  e=pos[:,1]-A.ground_batch(pos)
  low=e.min()
  berth=max(float(e[ix].min()-low) for ix in domain)
  if not full:return berth
  q,newG=candidate(qo,po,so,G,role,p,l,.0001-low)
  if q is None:return {'ik_unreachable':True}
  W1=(S.skin(po,q,so)+A.offset)*A.scale+actor
  E=W1[skinrows,1]-A.ground_batch(W1[skinrows])
  allE=np.full(len(V),np.nan);allE[skinrows]=E
  physical=rows[(allE[rows]>=-.001)&(allE[rows]<=.002)]
  hull=W1[physical][:,[0,2]]
  lsup=sum(V[physical,0]<left_bound);rsup=sum(V[physical,0]>right_bound)
  area=ConvexHull(hull).volume*1e6 if len(hull)>=3 and np.linalg.matrix_rank(hull-hull.mean(0))==2 else 0.
  return {'pitch_deg':p,'lateral_roll_deg':l,'minimum_sole_mm':float(E.min()*1000),'support_rows':len(physical),
          'supports_each_outer_30pct':[int(lsup),int(rsup)],'hull_area_mm2':float(area),
          'patch_width_mm':float(np.ptp(hull[:,0])*1000) if len(hull) else 0.,
          'normalized_y_mm':float((.0001-low)*1000),
          'ankle_xz_preserved':True,
          'relative_signed_flex_change_deg':float(Rotation.from_matrix((newG[names[2],:3,:3].T@newG[names[3],:3,:3]).T@(G[names[2],:3,:3].T@G[names[3],:3,:3])).magnitude()*180/math.pi)}
 # Choose one angle pair from the predeclared bounded grid based solely on
 # real connected medial/lateral face-bearing height envelope.
 best=(1e10,0.,0.)
 for p in np.arange(-8.,8.01,.5):
  for l in np.arange(-6.,6.01,.5):
   cost=evaluate(float(p),float(l))
   best=min(best,(cost,float(p),float(l)))
 out.append(dict(role=role,failing_frame=idx,source_blended_rows=len(rows), source_connected_triangle_count=len(sub),
                 whole_forefoot_static_patch_width_mm=float(B*A.scale*1000),
                 near_side_rows=[len(med),len(lat)],
                 worst_end_minimum_height_after_rigid_clearance_mm=float(best[0]*1000),
                 method="bounded common pitch +/-8deg/ lateral +/-6deg, 0.5deg spacing only; selected one matched actual full solve",
                 underlying_signed_relative_flex_deg=req[role]['foot_pitch_deg']-req[role]['ball_pitch_deg'],
                 exact_selected_full_skin=evaluate(*best[1:],True)))
print(json.dumps(out,indent=2))

# The exact same fixed-decision procedure is evaluated at every native 120 Hz
# comparison knot before any output animation can be considered. Sliding
# snapshots are diagnostics only: no new pose/clip file is emitted here.
extra=[]
for role in ('left','right'):
 j=A.foot_ids[role];f,w=A.w(j[2]),A.w(j[3])
 low=(V[:,1]<=.009)&(V[:,2]<=.023)&((f+w)>.999995)
 sub=np.flatnonzero(low[faces].all(1))
 M={}
 for i in sub:
  for x in weld[faces[i]]:M.setdefault(int(x),[]).append(int(i))
 root=A.feet[role]['heel'];work=list(set(M[int(weld[root])]))
 used=set(work)
 while work:
  f0=work.pop()
  for v0 in weld[faces[f0]]:
   for f1 in M[v0]:
    if f1 not in used:used.add(f1);work.append(f1)
 Hrows=np.unique(faces[sorted(used)])
 BRows=beam[role][0]
 roots=A.feet[role]['rows']
 classified=(f+w)>.999995
 stat=[]
 for key in range(73):
  t,q,ss,rr,actor=A.motion(key/72); r=rr[role]
  if not r['plant']:
   continue
  W=(S.skin(t,q,ss)+A.offset)*A.scale+actor;G=S.evaluate(t,q,ss)
  ww=(G[j[2],:3,3]+A.offset)*A.scale+actor
  patch=Hrows if r['type']=='heel' else BRows
  lo=np.min(V[patch,0]);hi=np.max(V[patch,0]);w0=hi-lo
  D=np.unique(np.r_[roots[classified[roots]],patch])
  lw=np.searchsorted(D,patch[V[patch,0]<=lo+.30*w0])
  rw=np.searchsorted(D,patch[V[patch,0]>=hi-.30*w0])
  best=(1.e12,0.,0.,0.)
  for pp in range(-8,9,2):
   for ll in range(-6,7):
    z=(W[D]-ww)@Rotation.from_euler('xz',[pp,ll],degrees=True).as_matrix().T+ww
    e=z[:,1]-A.ground_batch(z); mn=e.min()
    err=max(e[lw].min(),e[rw].min())-mn
    # If both ends would qualify, prefer smooth small correction over
    # chasing mathematically flatter exact lowest point.
    v=(max(0,err-.0018),abs(pp)+abs(ll)*1.1,err)
    if v<best[:3]:best=(*v,pp,ll,mn)
  err=best[2]
  stat.append(dict(k=key,phase=float(r['alpha']),class_=r['type'],pitch=best[3],roll=best[4],raw_lower_bound_excess_mm=float(err*1000)))
 extra.append(dict(role=role,heel_connected_triangle_count=len(used),heel_source_rows=len(Hrows),frames=stat))
(h/'stance-screen.json').write_text(json.dumps(extra,indent=2)+'\n')
