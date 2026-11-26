from hashlib import sha256
from pathlib import Path
base=Path(__file__).resolve().parent.parent
s=base/'hvn-l1-owner-gate-33035-v4-native-preflight-v1'/'staged/HavenlineLevel1'
pins={'technical_gate.gd':'e3483ca3ff564693280783bdea689a1ebcb2231abd1d2b645180dba7ba3d1ad4',
'tests/hvn_l1_active_close.gd':'71d24ff0dd9c31c26be1e7364bf6887c02aec9b3fa73a1afcedf42a9c503784b',
'tests/hvn_l1_combined_route.gd':'d2a5ca5397d6ecee56ad95afce9bf75a5353f2b8ceb1478a95f280be7899552a',
'tests/hvn_l1_combined_draw.gd':'c7dbd6f1dea4f281de5796e9589751f2a3c412449d85352b14f4dad510cddb19'}
for path,h in pins.items(): assert sha256((s/path).read_bytes()).hexdigest()==h
assert sha256((base/'hvn-l1-gate-latch-adjacent-witness-v2/SHA256SUMS').read_bytes()).hexdigest()=='c43511e62477ab704aa138cc1e823b4b5e69d6c259ac33c62f1e80c4fbca341c'
cl=(s/'tests/hvn_l1_active_close.gd').read_text()
assert 'await super.tick(1)\n\t\tif closing_index<0:' in cl
assert cl.count('not await _one_close(')==2 and 'await RenderingServer.frame_post_draw' in cl
rt=(s/'tests/hvn_l1_combined_route.gd').read_text()
assert rt.count('await gate_cross(')==2 and 'await cold_route(primary)' in rt
print('Pinned shell, V2 contract and first-open/single-close/cold topology verified; observer GDScript not parsed or run.')
