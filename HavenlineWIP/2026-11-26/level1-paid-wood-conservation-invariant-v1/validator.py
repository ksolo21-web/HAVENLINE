"""Offline conservation validator only, not a receiver or a persistence authority."""
from pathlib import Path
from hashlib import sha256
import json,re
root=Path(__file__).resolve().parent.parent
ORIGIN='58f708b44d04ebeec91590f8b4cdd609e3575bb7'
PINS={'opening_ledger.gd':'a65fa1f6fdfa9f304550fe923cc5c14f3d79e6f7b38d59d8441a194caff28e90','opening_save.gd':'e07e922708c473b291c46fac87ebdc5a2e26d89617f741c4a8ae91bec5aa5f55'}
old=root/'hvn-l1-paid-pine-storage-regression-v1'
assert sha256((old/'SHA256SUMS').read_bytes()).hexdigest()=='7071566ebf07a8e148fdf4ccf1eb18d849af9bd5ae515c332bbb86e833d06c63'
for h,n in (x.split('  ',1) for x in (old/'SHA256SUMS').read_text().splitlines()):
 assert sha256((old/n).read_bytes()).hexdigest()==h
src=root/'hvn-l1-e2e-paid-pine-v1/staged/HavenlineLevel1'
for n,h in PINS.items():assert sha256((src/n).read_bytes()).hexdigest()==h
source=(src/'opening_ledger.gd').read_text()
def literal(k):return json.loads(re.search(r'(?m)^const '+k+r' := (.*)$',source).group(1))
MAX=literal('MAX_PINE_OCCURRENCES')
STARTERS=frozenset(literal('KNOWN_WOOD'))
OFFER=literal('OFFER')
COST=literal('COST')
def exact_receipt():
 return {'offer':OFFER,'grant':OFFER,'typed_debit':dict(COST),'revision':1}
NAMESPACE='havenline.detached.paid-pine-conservation.v1'
MIGRATION_INTENT='explicit-offline-seed-known-fixture-only'
OLD_FIXTURE_SHA='832e3f09cb5718634de49d89e1e358b70cc5789464612b2ca48ec6dab43bc415'
FIELDS={'schema','starter_ids','hearth_receipt','earned','carried_wood','credited_wood','credits'}
CREDIT_FIELDS={'ticket','source_unit','material','units'}
TICKET=r'[a-z0-9-]{1,64}'
class Reject(ValueError):pass
def need(ok,why):
 if not ok:raise Reject(why)
def integer(x):return type(x) is int and 0<=x<=MAX
def receipt_is_exact(x):
 return type(x) is dict and x==exact_receipt() and type(x.get('revision')) is int and type(x['typed_debit']['wood']) is int
def validate(state, *, independently_admitted_pairs=frozenset()):
 """Validate a closed snapshot. Optional evidence is caller-supplied upstream certification,
 not derived here; a tuple is isomorphic to one receipt, not a runtime inventory instruction."""
 need(type(state) is dict and set(state)==FIELDS and state.get('schema')==NAMESPACE,'unmigrated or unknown detached schema')
 ids=state['starter_ids']
 need(type(ids) is list and all(type(s) is str for s in ids) and len(ids)==3 and frozenset(ids)==STARTERS and receipt_is_exact(state['hearth_receipt']),'wrong paid hearth authority')
 earned,carried,credited=(state[k] for k in ('earned','carried_wood','credited_wood'))
 need(all(integer(x) for x in (earned,carried,credited)),'negative, mistyped, or overflowing count')
 need(type(independently_admitted_pairs) is frozenset,'no mutable evidence pool')
 need(all(type(k) is tuple and len(k)==2 and type(k[0]) is str and re.fullmatch(TICKET,k[0]) and integer(k[1]) and 1<=k[1]<=earned for k in independently_admitted_pairs),'malformed independent evidence')
 need(type(state['credits']) is list and len(state['credits'])<=earned,'invalid credit list')
 receipts=set(); consumed=set(); found=set()
 for r in state['credits']:
  need(type(r) is dict and set(r)==CREDIT_FIELDS,'invalid credit row')
  ticket,s=r['ticket'],r['source_unit']
  need(type(ticket) is str and re.fullmatch(TICKET,ticket) and integer(s) and 1<=s<=earned and r['material']=='wood' and type(r['units']) is int and r['units']==1,'invalid typed one-unit evidence')
  need(ticket not in receipts and s not in consumed,'reused receipt or earned unit')
  need((ticket,s) in independently_admitted_pairs,'no affirmed external evidence for credit')
  receipts.add(ticket); consumed.add(s);found.add((ticket,s))
 need(found==independently_admitted_pairs,'missing affirmed evidence unit')
 need(credited==len(found),'credit count not evidenced')
 need(credited<=earned and carried==earned-credited,'balance not conserved')
 return (earned,carried,credited)

def seed_known_fixture(raw, *, intent):
 """One explicit bridge from audited 326-byte test fixture, creates an in-memory dict only."""
 need(intent==MIGRATION_INTENT and type(raw) is bytes and len(raw)==326 and sha256(raw).hexdigest()==OLD_FIXTURE_SHA,'not explicitly authorized known test fixture')
 o=json.loads(raw); p=json.loads(o['payload'])
 need(o['version']==1 and sha256(o['payload'].encode()).hexdigest()==o['sha256'] and p['version']==2 and p['stock']=={'wood':1} and p['pine_occurrences']==1 and p['collected']==['wood-b','wood-c','wood-a'] and receipt_is_exact(p['receipt']),'mismatched fixture')
 s={'schema':NAMESPACE,'starter_ids':p['collected'],'hearth_receipt':p['receipt'],'earned':1,'carried_wood':1,'credited_wood':0,'credits':[]}
 validate(s)
 return s
