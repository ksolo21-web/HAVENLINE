from copy import deepcopy
import hashlib,json
from pathlib import Path
from validate import propose_pair,WitnessStream,SCHEMA,READBACK
prior=Path('../hvn-l1-owner-gate-33035-v4-native-preflight-v1')
pins={'tty_capture.sh':'d8c8c5b3893c4ee7589d059b2f12b5cb02a69d97266ffc3a347730cc406bb4ff',
 'staged/draw-source.sha256':'9d81dd5397ac81d932dda03bfc64a7e5eb275bde73a0ac8d29186cfa3f82ee1d',
 'staged/HavenlineLevel1/tests/hvn_l1_active_close.gd':'71d24ff0dd9c31c26be1e7364bf6887c02aec9b3fa73a1afcedf42a9c503784b',
 'staged/HavenlineLevel1/tests/hvn_l1_combined_route.gd':'d2a5ca5397d6ecee56ad95afce9bf75a5353f2b8ceb1478a95f280be7899552a',
 'staged/HavenlineLevel1/tests/test_integrated_opening.gd':'b5e01fe68711c73e8067332a454050e1ff97877c4f5bf88bbb4846acd6a8477d',
 'graphics-evidence.cklm7tMU/active-close-evidence.json':'ebd4554a1a12aaba5b70dcecaf167f7a2cf9d3ac4d75198a62cd5a3275e47e4d'}
for f,h in pins.items():assert hashlib.sha256((prior/f).read_bytes()).hexdigest()==h
S=lambda suffix:(prior/('staged/HavenlineLevel1/'+suffix)).read_text()
L=(prior/'tty_capture.sh').read_text()
assert '--script res://tests/hvn_l1_active_close.gd' in L and '--audio-driver Dummy' in L
C=S('tests/hvn_l1_active_close.gd')
assert 'press(KEY_E)\n\tawait tick(52)' in C and 'await super.tick(1)\n\t\tif closing_index<0:' in C
assert 'await physics_frame\n\t\ttick_count += 1' in S('tests/test_integrated_opening.gd')
assert 'step_technical_gates(dt)' in S('previews/integrated_opening.gd')
assert 'gate.advance(dt, actor.global_position, float(layout.actor_radius))' in S('opening.gd')
assert 'angle = move_toward(angle, wanted, clampf(dt, 0.0, .02) * SWING_SPEED)' in S('technical_gate.gd')
W=json.loads((prior/'graphics-evidence.cklm7tMU/active-close-evidence.json').read_text())
assert [W['inherited_route_checks'],W['active_close_checks'],W['actual_close_delta_ticks']]==[67,11,[41,41]]
R={'offer':'center-hearth','grant':'center-hearth','typed_debit':{'wood':3},'revision':1}
def packet(gate,i):
    common={'scene_epoch':'synthetic-a','gate_id':gate,'instance_id':i}
    frame={**common,'route_tick':100,'engine_physics_counter':810,'active':True,'target_open':False,'held':False,'angle_rad':.012,'receipt':R,'restored':False}
    return {'schema':SCHEMA,'phase':'writer','readback_hook':READBACK,**common,'previous':frame,'current':{**frame,'route_tick':101,'engine_physics_counter':811,'angle_rad':0.0}}
p=packet('gate-east',2351); q=packet('gate-south',2760)
assert propose_pair(p).gate_id=='gate-east' and propose_pair(q).gate_id=='gate-south'
from math import pi
from validate import STEP,TOL
assert '--fixed-fps 60' in L
assert 'physics_ticks_per_second' not in S('project.godot')
def trace(seed, start=100, cycle_count=1):
 g=deepcopy(seed['previous'])
 frames=[]
 def row(open_,angle):
  t=start+len(frames)
  frames.append({**deepcopy(g),'route_tick':t,'engine_physics_counter':t+710,'target_open':open_,'angle_rad':angle})
 row(False,0.0)
 for _ in range(cycle_count):
  for n in range(1,43):row(True,min(pi/2,n*STEP))
  for n in range(1,43):row(False,max(0.0,pi/2-n*STEP))
 return [{**seed,'previous':a,'current':b} for a,b in zip(frames,frames[1:])]
def fresh():return WitnessStream('synthetic-a',{'gate-east':2351,'gate-south':2760},710)
def found(w,packets):return [e for x in packets if (e:=w.observe(x))]
w=fresh()
east=trace(p,cycle_count=2); south=trace(q)
assert len(found(w,east))==2 and len(found(w,south))==1
edge=next(x for x in east if propose_pair(x))
assert w.observe(edge) is None
attack=deepcopy(edge)
for k in ('previous','current'):attack[k]['route_tick']+=999
assert propose_pair(attack) and w.observe(attack) is None
assert fresh().observe(edge) is None
def check_bad(edit):
 bad=deepcopy(east); index=10; edit(bad[index]); assert not found(fresh(),bad[index:index+1])
 w=fresh(); assert not found(w,bad[:index]); assert w.observe(bad[index]) is None
check_bad(lambda p:p.update(scene_epoch='synthetic-b'))
check_bad(lambda p:p.update(instance_id=7))
w=fresh(); assert not found(w,east[:30]); assert not found(w,east[31:])
w=fresh(); assert not found(w,east[:11])
fake=deepcopy(east[10]); fake.update(accepted_close=True,reopened=True)
assert w.observe(fake) is None
wide=deepcopy(p);wide['previous']['angle_rad']=.040
assert propose_pair(wide) is None
near=deepcopy(p);near['previous']['angle_rad']=STEP+TOL*.999
assert propose_pair(near)
for target in (STEP+TOL*1.001,.046):
 outside=deepcopy(p); outside['previous']['angle_rad']=target
 assert propose_pair(outside) is None
negative=[('phase','cold'),('readback_hook','post-draw'),('current.route_tick',102),('current.engine_physics_counter',812),('current.instance_id',True),('current.instance_id',2760),('current.gate_id','gate-south'),('current.scene_epoch','synthetic-b'),('previous.angle_rad',0),('previous.angle_rad',.050),('current.angle_rad',.001),('current.held',True),('previous.active',False),('current.active',False),('current.target_open',True),('previous.target_open',True),('previous.receipt',None),('current.receipt',0),('current.restored',True),('previous.restored',True)]
for key,value in negative:
 t=deepcopy(p)
 if '.' in key: a,b=key.split('.');t[a][b]=value
 else:t[key]=value
 assert propose_pair(t) is None,key
print(json.dumps({'synthetic_positive_both_gates':2,'synthetic_direct_negatives':len(negative),'repeated_packet_suppression':True,
 'instance_swap_suppression':True,'genuine_later_cycle_synthetic':True,'route_relabel_same_engine_clock_rejected':True,'fixed_60hz_step_rad':STEP,'float_tolerance_rad':TOL,'gap_or_unbound_progression_rejected':True,'static_shell_and_exact_78_metadata':True,'actual_adjacent_records':0,'engine_audio_application':False},indent=2))
