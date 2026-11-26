from pathlib import Path
from hashlib import sha256
import json,re
root=Path(__file__).resolve().parent.parent
stage=root/'hvn-l1-owner-gate-33035-v4-native-preflight-v1/staged'
src=stage/'HavenlineLevel1'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def verify(p,s):
 f=p/'SHA256SUMS'; assert sha(f)==s
 for line in f.read_text().splitlines():
  h,n=line.split('  ',1); assert sha(p/n)==h
first=root/'hvn-l1-south-hold-x11-approach104-wall360-v4/functional-only.fx67FvME'
second=root/'hvn-l1-east-hold-x11-runtime-v1/functional-only.HRc4IOeH'
assert sha(stage/'draw-source.sha256')=='9d81dd5397ac81d932dda03bfc64a7e5eb275bde73a0ac8d29186cfa3f82ee1d'
sources={Path(n):h for h,n in (x.split('  ',1) for x in (stage/'draw-source.sha256').read_text().splitlines())}
files=['technical_gate.gd','opening.gd','previews/integrated_opening.gd','previews/clearance_gate/clearance_gate_view.gd']
content={}
for f in files:
 assert sha(src/f)==sources[Path(f)]
 content[f]=(src/f).read_text()
assert not re.search(r'(?m)^\s*signal\s|\bemit_signal\(|\.emit\(',content['technical_gate.gd'])
assert 'gate.advance(dt, actor.global_position, float(layout.actor_radius))' in content['opening.gd']
assert 'actor.move_and_slide()' in content['previews/integrated_opening.gd'] and 'step_technical_gates(dt)' in content['previews/integrated_opening.gd']
out={}
for label,d,pin in [('south',first,'519024ff4fdda219d9f186679f70dedc52392812496dab32a1a81400c1731a9c'),('east',second,'518523f6c6bef81acf78339a4d0dbb21f2b7058121d2172d6eeaedba2875de39')]:
 verify(d,pin)
 actual=json.loads((d/(label+'-hold-joined.json')).read_text())
 assert (actual['writer_prefix_settled'],actual['additional_settled'],actual['cold_settled'],actual['save_preserved'])==(4,0,0,True)
 rows=actual[label+'_occupied_samples']
 assert len(rows)==6 and len({r['angle'] for r in rows})==1 and all(r['held'] and r['grounded'] and not r['leaf_contact'] for r in rows)
 assert [r['target_open'] for r in rows]==[False]*3+[True]*3
 assert (d/'writer.snapshot').read_bytes()==(d/'cold.snapshot').read_bytes()
 out[label]={'archive':pin,'test_only_settled_close_proposals':4,'occupancy_tail_proposals':0,'cold_proposals':0,'same_angle_adjacent_held_rows':6}
assert actual['south_idle_paired_tail_rows']==371
verify(root/'hvn-l1-gate-latch-adjacent-witness-v2','c43511e62477ab704aa138cc1e823b4b5e69d6c259ac33c62f1e80c4fbca341c')
print(json.dumps({'results':out,'south_idle_during_east_adjacent_rows':371,'native_runtime_gate_publisher_exists':False,'missing_representation':'read-only runtime-owned post-advance ordered transition event; offline test consumers only','T54':'LOCKED'},indent=2))
