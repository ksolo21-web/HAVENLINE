"""Read-only two loaded-key envelope solve. Does not write pose or clip."""
from pathlib import Path
import math,hashlib,json
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation as Rot
import author as A,stock as S
h=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(h/'SHA256SUMS')=='02cdf3d01600e6a102f77ff1b9025572b429d2a0573af45a46f7536c0fd1cac4'
for l in (h/'SHA256SUMS').read_text().splitlines():
 k,n=l.split(maxsplit=1);assert sha(h/n)==k
pts=[]
unit=A.unit
for sample,role in [(39,'left'),(72,'right')]:
 t,oq,ss,r,actor=A.motion(sample/72)
 G=S.evaluate(t,oq,ss)
 th,cal,fo,to=A.foot_ids[role]
 fixed_ankle=G[fo,:3,3].copy()
 fixed_q={fo:G[fo,:3,:3].copy(),to:G[to,:3,:3].copy()}
 H=G[th,:3,3]
 rows=A.feet[role]['rows']
 marker=r[role]['row']
 # A simultaneous new lower tension candidate is not emitted. At each lift
 # solve the same stock bone lengths, unchanged signed sole and ToeBase
 # world rotations, exact original ankle XZ/pelvis, only Y as the variable.
 def measure(dy):
  q=oq.copy();T=fixed_ankle+[0.,dy/A.scale,0.]
  a,b=np.linalg.norm(S.T[cal]),np.linalg.norm(S.T[fo])
  length=np.linalg.norm(T-H)
  d=(T-H)/length;p=np.array([.015 if role=='left' else -.015,0.,1.])
  orth=unit(p-d*(p@d));s=(a*a+length*length-b*b)/(2*length)
  assert a*a>s*s
  knee=H+d*s+orth*math.sqrt(a*a-s*s)
  n0=A.rot(A.G0[cal,:3,3]-A.G0[th,:3,3],knee-H)@A.G0[th,:3,:3]
  n1=A.rot(A.G0[fo,:3,3]-A.G0[cal,:3,3],T-knee)@A.G0[cal,:3,:3]
  for i,N in [(th,n0),(cal,n1),(fo,fixed_q[fo]),(to,fixed_q[to])]:
   A.assign_q(t,q,ss,i,S.evaluate(t,q,ss),N)
  G1=S.evaluate(t,q,ss);world=(S.skin(t,q,ss)+A.offset)*A.scale+actor
  assert np.linalg.norm(G1[fo,:3,3]-T)<1e-6
  assert all(np.max(abs(G1[i,:3,:3]-fixed_q[i]))<1e-9 for i in (fo,to))
  assert np.max(abs(G1[39]-G[39]))<1e-10
  dev=world[rows,1]-A.ground_batch(world[rows])
  return dev,world,float(math.degrees(math.acos(np.clip(unit(knee-H)@unit(T-knee),-1,1))))
 old0,w0,k0=measure(0)
 lo,hi=0.,.030
 assert old0.min()<-.007 and measure(hi)[0].min()>.0001
 for _ in range(16):
  mid=(lo+hi)*.5
  if measure(mid)[0].min()>=.0001:hi=mid
  else:lo=mid
 new,w1,k1=measure(hi)
 r0=rows[(old0>=-.001)&(old0<=.002)]
 r1=rows[(new>=-.001)&(new<=.002)]
 def hull(w,ro):
  X=w[ro][:,[0,2]];X=np.unique(np.round(X,8),axis=0)
  if len(X)<3:return dict(count=len(ro),unique=len(X),hull_mm2=0,extent_mm=np.ptp(X,axis=0).tolist() if len(X) else [])
  return dict(count=len(ro),unique=len(X),hull_mm2=ConvexHull(X).volume*1e6,extent_mm=(np.ptp(X,axis=0)*1000).tolist())
 pts.append(dict(role=role,sample=sample,required_ankle_Y_mm=hi*1000,post_minimum_snow_clearance_mm=float(new.min()*1000),
                 signed_foot_vs_Toe_roll_unchanged_deg=r[role]['foot_pitch_deg']-r[role]['ball_pitch_deg'],
                 knee_bend_before_after_deg=[k0,k1],anchor_row=marker,
                 pure_ball_height_change_mm=float((w1[marker,1]-w0[marker,1])*1000),
                 old_support_hull_around_1mm2mm=hull(w0,r0),new_support_hull_around_1mm2mm=hull(w1,r1),
                 new_pure_ToeBase_support_rows=int(np.isin(r1,A.feet[role]['ball_rows']).sum()),
                 min_raw_support_row=int(rows[np.argmin(new)]),
                 loaded_contact_center_offset_from_pure_ball_anchor_XZ_mm=((w1[rows[np.argmin(new)]]-w0[marker])[[0,2]]*1000).tolist()))
print(json.dumps(dict(scope='read-only correction feasibility on two failed keys, not candidate clip or retest',results=pts),indent=2))
