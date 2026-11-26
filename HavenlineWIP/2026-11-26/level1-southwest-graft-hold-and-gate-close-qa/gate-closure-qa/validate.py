"""Pure schema and same-record pairing; does not read engine state or play."""
from pathlib import Path
import runpy,hashlib
from copy import deepcopy
from math import isfinite,pi
previous=Path(__file__).parent.parent/'hvn-l1-settled-gate-latch-cue-contract-v1'
assert hashlib.sha256((previous/'SHA256SUMS').read_bytes()).hexdigest()=='cb3975fecd64f0e2eb735d33b277d384b9d86b2fcc6228445e6dbd74c8f649b5'
for row in (previous/'SHA256SUMS').read_text().splitlines():
    hash,name=row.split('  '); assert hashlib.sha256((previous/name).read_bytes()).hexdigest()==hash
base=runpy.run_path(str(previous/'contract.py'))
CLOSE=base['CloseProbe']; SNAPSHOT=base['Snapshot']
SCHEMA='havenline.l1.gate-latch-adjacent-witness/v2'
READBACK='last-completed-physics-before-next'
PACKET=frozenset(('schema','phase','scene_epoch','gate_id','instance_id','previous','current','readback_hook'))
FIELDS=frozenset(('route_tick','engine_physics_counter','scene_epoch','gate_id','instance_id','active','target_open','held','angle_rad','receipt','restored'))
GATES={'gate-east','gate-south'}
def token(v):return type(v) is str and bool(v) and v==v.strip()
def pn(v):return type(v) is int and 0<=v
STEP=2.3/60
TOL=1e-6

def rows_for(p):
    if type(p) is not dict or set(p)!=PACKET or p['schema']!=SCHEMA or p['phase'] not in ('writer','cold') or p['readback_hook']!=READBACK:return None
    if type(p['gate_id']) is not str or p['gate_id'] not in GATES or not token(p['scene_epoch']) or not pn(p['instance_id']) or p['instance_id']==0:return None
    if type(p['previous']) is not dict or type(p['current']) is not dict:return None
    rows=(p['previous'],p['current'])
    for r in rows:
        if set(r)!=FIELDS or any(r[k]!=p[k] for k in ('gate_id','instance_id','scene_epoch')):return None
        if not pn(r['route_tick']) or not pn(r['engine_physics_counter']) or type(r['instance_id']) is not int or type(r['restored']) is not bool:return None
    a,b=rows
    if b['route_tick']-a['route_tick']!=1 or b['engine_physics_counter']-a['engine_physics_counter']!=1 or p['phase']!='writer':return None
    for r in rows:
        if any(type(r[k]) is not bool for k in ('active','held','target_open','restored')):return None
        x=r['angle_rad']
        if type(x) not in (int,float) or not isfinite(x) or not 0<=x<=pi/2+TOL:return None
        if r['receipt'] is not None and not base['earned_receipt'](r['receipt']):return None
    if abs(b['angle_rad']-a['angle_rad'])>STEP+TOL:return None
    return rows

def propose_pair(p):
    rows=rows_for(p)
    if rows is None:return None
    validate=CLOSE(p['scene_epoch'])
    for r in rows:
        outcome=validate.observe(SNAPSHOT(r['gate_id'],r['scene_epoch'],r['route_tick'],r['active'],r['target_open'],r['held'],r['angle_rad'],r['receipt'],r['restored']))
    return outcome

class WitnessStream:
    """One trusted detached writer. Bind from actual scene/hook once, not packet fields."""
    def __init__(self,epoch,instances,phase_offset):
        if not token(epoch) or type(instances) is not dict or set(instances)!=GATES or not all(pn(i) and i>0 for i in instances.values()) or len(set(instances.values()))!=2 or type(phase_offset) is not int:
            raise ValueError('exact epoch, distinct bound native instances and measured phase offset required')
        self._epoch=epoch
        self._instances=dict(instances)
        self._offset=phase_offset
        self._prev={}
        self._state={}
        self._broken=set()
    def observe(self,p):
        rows=rows_for(p)
        if rows is None:return None
        a,b=rows
        g=p['gate_id']
        if (g in self._broken or p['scene_epoch']!=self._epoch or p['instance_id']!=self._instances[g] or
            any(r['engine_physics_counter']-r['route_tick']!=self._offset for r in rows)):return None
        old=self._prev.get(g)
        if old is not None:
            if any(b[k]<=old[k] for k in ('route_tick','engine_physics_counter')):return None
            if a!=old:
                # Missing/contradictory chronology invalidates the rest of this gate's epoch.
                self._broken.add(g)
                return None
        elif a['target_open'] or a['angle_rad']!=0 or a['held'] or a['restored']:
            self._broken.add(g)
            return None
        self._prev[g]=deepcopy(b)
        st=self._state.get(g,'closed')
        delta=b['angle_rad']-a['angle_rad']
        if (b['held'] and abs(delta)>TOL) or (b['target_open'] and delta < -TOL) or (not b['target_open'] and delta>TOL):
            self._broken.add(g)
            return None
        if not all(r['active'] and base['earned_receipt'](r['receipt']) and not r['restored'] for r in rows):
            self._state[g]='closed'
            return None
        if not a['target_open'] and b['target_open']:
            st='opening' if a['angle_rad']==0 else 'unarmed'
        if st=='opening' and b['target_open'] and not b['held'] and abs(b['angle_rad']-pi/2)<=TOL and delta>TOL:
            st='opened'
        if a['target_open'] and not b['target_open']:
            st='closing' if st=='opened' and a['angle_rad']>0 else 'unarmed'
        if st=='closing' and b['angle_rad']==0:
            self._state[g]='closed'
            # Reject an endpoint on the same tick as the target edge; there is no
            # preceding close-target/positive readback for this scoped witness.
            return propose_pair(p)
        self._state[g]=st
        return None
