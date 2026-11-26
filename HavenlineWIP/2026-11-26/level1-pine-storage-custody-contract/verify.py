"""Static evidence and arithmetic specification examples only."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent.parent/'hvn-l1-e2e-paid-pine-v1'
stage=root/'staged'; game=stage/'HavenlineLevel1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
final=stage/'final.sha256'
files={}
for ln in final.read_text().splitlines():
 h,n=ln.split('  ',1);files[n.removeprefix('./')]=h
target=['opening_ledger.gd','opening_save.gd','previews/integrated_opening.gd','resources/typed_receiver.gd','tests/test_typed_resource_receiver.gd','tests/hvn_l1_combined_route.gd']
for n in target:assert sha(game/n)==files[n]
e=root/'evidence'; package={}
for ln in (e/'SHA256SUMS').read_text().splitlines():
 h,n=ln.split('  ',1);assert sha(e/n)==h;package[n]=h
p=json.loads((e/'result.json').read_text())
assert p['baseline']=='11c14a1c41971067c7dc97db69375f720a408f68' and p['paid_pine_patch']=='e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd'
assert (p['phases']['write']['checks'],p['phases']['cold']['checks'])==(57,10)
assert p['controlled_checkpoint']=={'byte_count':326,'outer_version':1,'payload_version':2,'primary_sha256':'832e3f09cb5718634de49d89e1e358b70cc5789464612b2ca48ec6dab43bc415','receipt_cost_wood':3,'renewals':1,'wood':1}
ledger=(game/'opening_ledger.gd').read_text()
save=(game/'opening_save.gd').read_text()
integ=(game/'previews/integrated_opening.gd').read_text()
test=(game/'tests/test_typed_resource_receiver.gd').read_text()
assert all(x in ledger for x in ['remaining += occurrence_count','not _whole(incoming_stock.get("wood"), remaining)','_whole(stock.get("wood"), pine_occurrences)','occurrence != pine_occurrences + 1'])
assert 'return ERR_INVALID_DATA' in save and 'ledger.restore(JSON.parse_string(payload))' in save
assert 'ledger.has_exact_paid_hearth()' in integ and 'plan_transfer' not in integ and 'typed_receiver.gd' not in integ
assert 'Receiver.plan_transfer' in test and '52 type-A units plan' in test
cases=[
 ('earned control', 1,1,0,True,True),('deposit one',1,0,1,False,True),
 ('cold after deposit',1,0,1,False,True),('next legitimate renewal',2,1,1,False,True),
 ('unexplained missing wood',2,1,0,False,False),('count credited twice',2,2,1,True,False),
 ('negative stock',1,-1,2,False,False)]
for _, earned, carry, storage, v2, composite in cases:
 assert (carry==earned)==v2
 assert (min(earned,carry,storage)>=0 and carry+storage==earned)==composite
print(json.dumps({'source_manifest_sha256':sha(final),'archived_evidence_manifest_sha256':sha(e/'SHA256SUMS'),'source_files':{n:files[n] for n in target},
 'archived_verified':{'writer_checks':57,'cold_checks':10,'no_deposit':True},
 'arithmetic_examples':cases,'runtime_receiver_admitted':False,'engine_or_save_tested_here':False},indent=2))
