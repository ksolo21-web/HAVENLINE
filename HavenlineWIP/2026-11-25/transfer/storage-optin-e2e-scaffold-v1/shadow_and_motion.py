#!/usr/bin/env python3
"""Portable offline acceptance vectors: no native import, no filesystem persistence."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation,Slerp
root=Path(__file__).resolve().parent.parent
def bound(name,expected):
 p=root/name
 raw=(p/'SHA256SUMS').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==expected
 for line in raw.decode().splitlines():
  h,n=line.split()
  assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h
 return p
a=bound('hvn-l1-pine-storage-ledger-composition-v1','392db89ab0985fa2c9464ff28807096aa4951bdad3ce22e178cd6927b45aba06')
native=bound('hvn-l1-wood-paid-two-piece-candidate-v1','2dbde03441fe996bab357c37291ee9cbe229bf7a4fbdaf0885313f90cac2c8f5')
walk=bound('hvn-l1-paid-storage-walkby-v1','ac4a8d52a510abd6b657872fc6f73f45d043115152ce943576c365b0d4cccd80')
r=bound('hvn-l1-wood-storage-near-row-v1','b8f6061ab8f7b685beda4629ade265407b7bd5e5dfc649b2197a9b902b8767d6')
sys.dont_write_bytecode=True
sys.path.insert(0,str(a))
from oracle import MemoryMedium, wire, RECEIPT, STARTERS
k=json.loads((walk/'result.json').read_text())
assert k['native_summary']['obstructed_ticks']==2
o=k['near_waypoint_sample']
assert o['both_conservative_open'] and o['motion']==[0,0,0]
pi=json.loads((native/'native-result.json').read_text())['samples'][0]['stock_on_real_actor']
starts_local=np.array([p['local'] for p in pi])
destination=json.loads((r/'result.json').read_text())['detached_log_transforms']
# Oracle behavior expected of the NATIVE shadow seeded from exact verified live
# in-memory v2 snapshot. This fixture vector is explicitly not a native replay.
initial=dict(version=2,collected=list(STARTERS),stock={'wood':2},receipt=RECEIPT,pine_occurrences=2)
medium=MemoryMedium(wire(initial))
p=medium.cold_boot()
b4=p.snapshot()
assert p._trusted_harness_issue('deposit',1,'wood',2,sink=object()) is None
assert p._trusted_harness_issue('deposit',1,'stone',2,sink=p.blank_test_sink) is None
assert p._trusted_harness_issue('deposit',1,'wood',3,sink=p.blank_test_sink) is None
x=p._trusted_harness_issue('deposit',1,'wood',2,sink=p.blank_test_sink)
assert x is not None and p.snapshot()==b4
assert p.apply(x) and not p.apply(x)
after=p.snapshot()
assert after['receipt']==b4['receipt'] and after['collected']==b4['collected']
assert after['harvest_through']==2 and after['deposit_through']==1 and after['carried']=={'wood':0} and after['stored']=={'wood':2}
z=MemoryMedium(wire(dict(version=1,collected=list(STARTERS),stock={'wood':3},receipt={}))).cold_boot()
assert z._trusted_harness_issue('deposit',1,'wood',2,sink=z.blank_test_sink) is None
assert p._trusted_harness_issue('deposit',1,'wood',1,sink=p.blank_test_sink) is None

# ONE motion policy only. Absolute launch orientation/position MUST be read
# from live reached mount. Preview orientation below is route-heading estimate,
# not native near-pose transform or physics proof.
obs_actor=np.array(o['world'])
heading=Rotation.from_euler('y',math.atan2(-1.275,-1.10)).as_matrix()
side_mag=.94
pace_cap=4.4
# Cubic ease derivative bounded by 1.5; time snapped UP to 60Hz.
def phase_ticks(distance,angle=0.):
 return math.ceil(60*max(.30,1.5*distance/pace_cap,1.5*angle/math.radians(160)))
def plan(B,src,e,R):
 d=src-.94*B[:,0]
 h=e.copy();h[1]=src[1]
 k=[src,d,h,e]
 angular=np.linalg.norm(Rotation.from_matrix(R@B.T).as_rotvec())
 durations=[phase_ticks(np.linalg.norm(b-a),angular if j==1 else 0)
  for j,(a,b) in enumerate(zip(k,k[1:]))]
 return k,durations
res=[]; t0=0
for c,row in enumerate(destination):
 end=np.array(row['t_source_to_source_world']); basis=np.array(row['R_source_to_source_world'])
 src=obs_actor+heading@starts_local[c]
 k,dt=plan(heading,src,end,basis)
 dif=np.linalg.norm(np.diff(k,axis=0),axis=1)
 assert max(1.5*d/t*60 for d,t in zip(dif,dt))<=pace_cap and min(dt)>=18
 # Format/cadence guard only; geometry is not inferred from estimated pose.
 times=np.r_[0,np.cumsum(dt)]+t0
 res.append({'piece':c+1,'estimated_only_anchor_world_m':src.tolist(),'ticks':times.tolist(),
   'key_positions_m':[z.tolist() for z in k],
   'max_speed_each_phase_m_s':[1.5*d/t*60 for d,t in zip(dif,dt)],
   'certified_world_geometry':False})
 t0=int(times[-1])+6
print(json.dumps({'claims':'Independent exact v3 oracle vector and one TEST pace/shape calculation only; no native motion or geometry admission',
 'transaction_before':b4,'transaction_after':after,'halt_reasons':['original walk carries conservatively obstructed at ticks 1306 and 1353','native mount matrix/whole obstacle certificate for proposed transfer absent'],
 'design_test_speed_cap_m_s':pace_cap,'poses':res,'tail_time_s':res[-1]['ticks'][-1]/60},indent=2,sort_keys=True))
