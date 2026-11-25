"""Offline denial controls mirror strict wire law only; no Godot parse or scene claim."""
from pathlib import Path
from copy import deepcopy
import json
p=Path(__file__).resolve().parent
baseline=json.loads((p/'expected.json').read_text())
live={'source':True,'finished':False,'fault':False,'ticks':list(range(1278,1424)),
      'record':baseline,'mount':True,'failures':1,'gate_drift':0,'body_contact':0}
def allowed(x):
 return (x['source'] and not x['finished'] and not x['fault'] and x['mount']
     and len(x['ticks'])==146 and x['ticks'][-1]==1423
     and all(j-i==1 for i,j in zip(x['ticks'],x['ticks'][1:]))
     and x['record']==baseline and x['failures']==1 and not x['gate_drift'] and not x['body_contact'])
def edit(x, idx, f, key='frames'):
 v=json.loads(x['record'][key][idx]); f(v); x['record'][key][idx]=json.dumps(v,sort_keys=True,separators=(',',':'))
cases={
 'wrong_actor_yaw':lambda x:edit(x,1,lambda v:v['actor'][1].__setitem__(2,.999)),
 'wrong_source_time':lambda x:edit(x,1,lambda v:v.__setitem__('anim_t',.1)),
 'wrong_mesh_mount':lambda x:edit(x,1,lambda v:v['crowns'][0]['mounted_local'][0].__setitem__(0,.5)),
 'altered_previous_position':lambda x:edit(x,1,lambda v:v['crowns'][0]['previous'][0].__setitem__(0,0)),
 'altered_current_yaw':lambda x:edit(x,4,lambda v:v['crowns'][0]['current'][1].__setitem__(2,.5)),
 'changed_heading':lambda x:edit(x,4,lambda v:v['velocity'].__setitem__(2,.5)),
 'wrong_phase':lambda x:edit(x,4,lambda v:v.__setitem__('phase','near_edge_approach')),
 'wrong_shape_node':lambda x:edit(x,1,lambda v:v['crowns'][0]['midpoint_enclosing_shape_hits'][0].__setitem__('shape_node','changed')),
 'wrong_shape_identity':lambda x:edit(x,1,lambda v:v['crowns'][0]['midpoint_enclosing_shape_hits'][0].__setitem__('body','changed')),
 'wrong_leaf_transform':lambda x:edit(x,1,lambda v:v['crowns'][0]['midpoint_enclosing_shape_hits'][0]['transform'][0].__setitem__(2,12)),
 'altered_warning_tick':lambda x:edit(x,0,lambda v:v.__setitem__('tick',1307),'warnings'),
 'extra_obstruction':lambda x:x['record']['warnings'].append(x['record']['warnings'][0]),
 'missing_1353':lambda x:x['record']['warnings'].pop(),
 'missing_1354':lambda x:x['record']['frames'].pop(),
 'stale_preflight_reused_same_instance':lambda x:x.__setitem__('finished',True),
 'wrong_source_digest':lambda x:x.__setitem__('source',False),
 'other_route_failure':lambda x:x.__setitem__('failures',2),
 'same_run_identity_fault':lambda x:x.__setitem__('fault',True),
 'missing_mount':lambda x:x.__setitem__('mount',False),
 'gate_movement':lambda x:x.__setitem__('gate_drift',1),
 'character_contact':lambda x:x.__setitem__('body_contact',1),
 'broken_continuous_sample_order':lambda x:x['ticks'].__setitem__(10,x['ticks'][11]),
 'settled_at_1333_not_complete':lambda x:x['ticks'].__delitem__(slice(56,None)),
}
states={'frozen_fixture_full_route':allowed(live)}
assert states['frozen_fixture_full_route']
for name,bad in cases.items():
 x=deepcopy(live); bad(x); states[name]=not allowed(x); assert states[name],name
scaffold=(p.parent/'hvn-l1-storage-optin-e2e-scaffold-v1'/'examiner.gd').read_text()
states['original_examiner_denies_invalid_callable']= 'if not verifier.is_valid():\n\t\treturn false' in scaffold
assert states['original_examiner_denies_invalid_callable']
print(json.dumps({'stage':'offline protocol mirror plus frozen examiner static check; never native', 'cases':states,'passed':sum(states.values())},sort_keys=True,indent=2))
