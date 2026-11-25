from pathlib import Path
import re,json,math,hashlib,subprocess,runpy
import numpy as np
B=Path(__file__).resolve().parent.parent
p=B/'hvn-l1-paid-walkby-turn-precision-v1'
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='d8c52a7404a4690d0cd35e5f4cb1b01c37ff28fb8b30ee68c70190518047e594'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
original=(B/'hvn-l1-paid-storage-walkby-v1/native.log').read_text().splitlines()
test=(p/'native.txt').read_text().splitlines()
tags=('WALK_OBSTRUCTION ','WALK_SUM ')
assert [l for l in original if l.startswith(tags)]==[l for l in test if l.startswith(tags)]
frames={g['tick']:g for l in test if l.startswith('TURN_DETAIL ') for g in [json.loads(l[len('TURN_DETAIL '):])]}
assert sorted(frames)==[1305,1306,1307,1352,1353,1354]
tri,_=runpy.run_path(str(B/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](B/'havenline-rendered-wood-ab-verified/project/assets/studio/starter_ground_wood_lod.glb')
v=np.unique(tri.reshape(-1,3),axis=0); assert len(v)==834
def pose(x): return np.array(x[0]),np.array(x[1:]).T
def Ry(t):
 c,s=np.cos(t),np.sin(t)
 return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def yaw(M):return math.atan2(M[0,2],M[2,2])
def g(lo,hi,h):return float(np.max(np.maximum(lo-h,-h-hi)))
pin='11c14a1c41971067c7dc97db69375f720a408f68'; repo=B/'havenline-tree-regrow.IVOMrj/repo'
def source(f):return subprocess.check_output(['git','-C',str(repo),'show',pin+':HavenlineLevel1/'+f]).decode()
code=source('previews/integrated_opening.gd')
assert code.index('actor.move_and_slide()')<code.index('actor.rotation.y = atan2(flat.x, flat.z)')
layout=json.loads(source('layout.json'))
assert [-5.0,0.0,.3,8.] in layout['walls_xz']
rows=[]
for k in [1306,1353]:
 f0,f1=frames[k-1],frames[k]; p0,R0=pose(f0['mount']);p1,R1=pose(f1['mount'])
 a=yaw(R0); d=math.remainder(yaw(R1)-a,2*math.pi)
 resid=max(np.linalg.norm(R0-Ry(a),2),np.linalg.norm(R1-Ry(a+d),2)); assert abs(d)<math.pi and resid<1e-5
 for i,q in enumerate(f1['crowns']):
  b,=q['midpoint_enclosing_shape_hits'];bp,br=pose(b['transform']); inv=np.linalg.inv(br)
  assert b['class']=='BoxShape3D'
  if k==1306:
   assert '/gate-south/HingeLeft/' in b['body'] and np.allclose(b['size'],[1.18,1.35,.14]) and abs(float(br[0,0]))<1e-6
  else:
   assert 'StaticBody3D' in b['body'] and np.allclose(b['size'],[.30,.95,8]) and np.allclose(bp[[0,2]],[-8.25,5.80])
  pL,rL=pose(q['mounted_local'])
  for pp,RR,key in [(p0,R0,'previous'),(p1,R1,'current')]:
   pC,rC=pose(q[key]);assert np.max(abs(pp+RR@pL-pC))<2e-6 and np.max(abs(RR@rL-rC))<2e-6
  vv=v@rL.T+pL; r=float(np.hypot(vv[:,0],vv[:,2]).max())
  P=np.stack([p0,p1]); P=(P-bp)@inv.T; tmin=P.min(0);tmax=P.max(0)
  # Decouple shortest yaw parameter and straight segment translation parameter entirely.
  # Thus independent advance rates or either sequential order are conservatively covered.
  h=np.array(b['size'])/2
  bounds=[]; N=96
  chord=2*r*math.sin(abs(d)/(4*N)); pad=chord*np.linalg.norm(inv,axis=1)+22e-6+resid*np.linalg.norm(vv,axis=1).max()*np.linalg.norm(inv,axis=1)
  for j in range(N):
   local=vv@Ry(a+d*(j+.5)/N).T@inv.T
   bounds.append(g(local.min(0)+tmin-pad,local.max(0)+tmax+pad,h))
  assert min(bounds)>0
  rows.append(dict(native_tick=k,crown=i,capped_shortest_yaw_degrees=math.degrees(abs(d)),min_decoupled_axis_gap_mm=1000*min(bounds)))
print(json.dumps(dict(box_matches=True,proxy_summary_unchanged=True,pair_of_intervals_only=True,subdivisions=96,finite_bound_all_yaw_translation_progress_combinations=True,not_arbitrary_off_segment_or_yaw=True,rows=rows),indent=2))
