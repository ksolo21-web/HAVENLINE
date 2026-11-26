from copy import deepcopy
from validator import *
def enc(data):return json.dumps(data,separators=(',',':'),sort_keys=True)
old={'version':2,'collected':['wood-b','wood-c','wood-a'],'stock':{'wood':1},'receipt':exact_receipt(),'pine_occurrences':1}
payload=enc(old)
raw=enc({'version':1,'sha256':sha256(payload.encode()).hexdigest(),'payload':payload}).encode()
base=seed_known_fixture(raw,intent=MIGRATION_INTENT)
assert validate(base)==(1,1,0)
assert seed_known_fixture(raw,intent=MIGRATION_INTENT)==base
positive=dict(base,carried_wood=0,credited_wood=1,credits=[{'ticket':'offline-1','source_unit':1,'material':'wood','units':1}])
ev=frozenset({('offline-1',1)})
assert validate(positive,independently_admitted_pairs=ev)==(1,0,1)
assert validate(dict(positive,earned=2,carried_wood=1),independently_admitted_pairs=ev)==(2,1,1)
assert validate(dict(base,earned=MAX,carried_wood=MAX))==(MAX,MAX,0)
names=[]
def denied(name,fn,before=None):
 copy=deepcopy(before)
 try:fn()
 except Reject:names.append(name)
 else:raise AssertionError(name)
 assert before==copy
denied('old-unmigrated-state',lambda:validate(old),old)
denied('old-unmigrated-outer',lambda:validate(json.loads(raw)))
denied('migration-without-intent',lambda:seed_known_fixture(raw,intent=None))
denied('altered-old-fixture',lambda:seed_known_fixture(raw+b' ',intent=MIGRATION_INTENT))
denied('credit-without-evidence',lambda:validate(positive),positive)
denied('missing-independent-evidence',lambda:validate(base,independently_admitted_pairs=ev),base)
def state_bad(name,e=ev,**changes):
 x={**deepcopy(positive),**changes};denied(name,lambda:validate(x,independently_admitted_pairs=e),x)
state_bad('undebited-credit',carried_wood=1)
state_bad('double-count-credit',credited_wood=2)
state_bad('negative',carried_wood=-1)
state_bad('overflow',earned=MAX+1)
state_bad('bool',credited_wood=True)
state_bad('fractional',carried_wood=.5)
state_bad('unaccounted-debit',earned=2)
r=positive['credits'][0]
state_bad('duplicate-ticket-separate-units',e=frozenset({('offline-1',1),('offline-1',2)}),earned=2,credited_wood=2,credits=[r,{**r,'source_unit':2}])
state_bad('duplicate-debit-unit-separate-tickets',e=frozenset({('offline-1',1),('offline-2',1)}),earned=2,credited_wood=2,credits=[r,{**r,'ticket':'offline-2'}])
state_bad('boolean-evidence-unit', e=frozenset({('offline-1',True)}))
state_bad('wrong-material',credits=[{**r,'material':'stone'}])
print(json.dumps({'archived_contract_commit':ORIGIN,'old_fixture_sha256':sha256(raw).hexdigest(),'positive_boundaries':4,'rejection_cases':names,'engine_or_receiver_or_save':False},indent=2))
