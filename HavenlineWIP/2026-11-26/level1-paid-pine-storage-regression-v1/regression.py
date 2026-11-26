"""Off-engine transcription of exact paid-pine restore/commit decision order."""
from pathlib import Path
from hashlib import sha256
from copy import deepcopy
import json,math,re
root=Path(__file__).resolve().parent.parent
stage=root/'hvn-l1-e2e-paid-pine-v1/staged/HavenlineLevel1'
pins={'opening_ledger.gd':'a65fa1f6fdfa9f304550fe923cc5c14f3d79e6f7b38d59d8441a194caff28e90','opening_save.gd':'e07e922708c473b291c46fac87ebdc5a2e26d89617f741c4a8ae91bec5aa5f55'}
def digest(data):return sha256(data).hexdigest()
s={}
for n,h in pins.items():
 b=(stage/n).read_bytes(); assert digest(b)==h;s[n]=b.decode()
ledger=s['opening_ledger.gd']; save=s['opening_save.gd']
def literal(source,key):
 return json.loads(re.search(r'(?m)^const '+key+r' := (.*)$',source)[1])
cost=literal(ledger,'COST'); known=literal(ledger,'KNOWN_WOOD'); offer=literal(ledger,'OFFER')
cap=literal(ledger,'MAX_PINE_OCCURRENCES'); max_bytes=literal(save,'MAX_BYTES')
assert 'remaining += occurrence_count' in ledger and 'not _whole(incoming_stock.get("wood"), remaining)' in ledger and '_whole(stock.get("wood"), pine_occurrences)' in ledger
assert 'if not ledger.restore(JSON.parse_string(payload)):' in save and 'return ERR_INVALID_DATA' in save
receipt={'offer':offer,'grant':offer,'typed_debit':cost,'revision':1}
def whole(x,n):return type(x) in (float,int) and x==n
def gid(raw):
 if type(raw) is not bytes:return None
 try:return json.loads(raw,parse_int=float)
 except (ValueError,UnicodeError):return None
def restore(data):
 if type(data) is not dict:return None
 occ=0
 if len(data)==5 and whole(data.get('version'),2):
  count=data.get('pine_occurrences')
  if type(count) not in (int,float) or not math.isfinite(count) or not 1<=count<=cap or count!=math.floor(count):return None
  occ=int(count)
 elif len(data)!=4 or not whole(data.get('version'),1):return None
 a,b,c=(data.get(k) for k in ('collected','stock','receipt'))
 if type(a) is not list or type(b) is not dict or len(b)!=1 or type(c) is not dict:return None
 verified=[]
 for x in a:
  if type(x) is not str or x not in known or x in verified:return None
  verified.append(x)
 remaining=len(verified)
 if c:
  d=c.get('typed_debit')
  if len(c)!=4 or c.get('offer')!=offer or c.get('grant')!=offer or not whole(c.get('revision'),1) or type(d) is not dict or len(d)!=1 or not whole(d.get('wood'),cost['wood']):return None
  remaining-=cost['wood']
 if remaining<0 or (occ>0 and not c):return None
 remaining+=occ
 if not whole(b.get('wood'),remaining):return None
 out={'version':2 if occ else 1,'collected':verified,'stock':{'wood':remaining},'receipt':deepcopy(receipt) if c else {}}
 if occ:out['pine_occurrences']=occ
 return out
def encode(state):
 p=json.dumps(state,separators=(',',':'),sort_keys=True)
 return json.dumps({'version':1,'payload':p,'sha256':digest(p.encode())},separators=(',',':'),sort_keys=True).encode()
def decode(data):
 if type(data) is not bytes or len(data)>max_bytes:return None
 o=gid(data)
 if type(o) is not dict or len(o)!=3 or not whole(o.get('version'),1):return None
 p=o.get('payload')
 if type(p) is not str or digest(p.encode())!=o.get('sha256'):return None
 return restore(gid(p.encode()))
def commit_candidate(prior,candidate):
 next_=restore(candidate)
 if next_ is None:return 'ERR_INVALID_DATA',prior
 if prior is not None and decode(prior) is None:return 'ERR_FILE_CORRUPT',prior
 return 'OK',encode(next_) # decision model only, not filesystem/transaction proof
def cold(data,existing):
 if data is None:return 'ERR_FILE_NOT_FOUND',existing
 next_=decode(data)
 return ('ERR_FILE_CORRUPT',existing) if next_ is None else ('OK',next_)
def has_exact_paid(data):
 return data['receipt']==receipt and len(data['collected'])==len(known) and all(k in data['collected'] for k in known) and whole(data['stock']['wood'],data['pine_occurrences'])
def snapshot(carried,occ=1):
 return {'version':2,'collected':['wood-b','wood-c','wood-a'],'stock':{'wood':carried},'receipt':deepcopy(receipt),'pine_occurrences':occ}
actual_result=root/'hvn-l1-paid-pine-storage-custody-contract-v1/result.json'
assert json.loads(actual_result.read_text())['archived_verified']=={'writer_checks':57,'cold_checks':10,'no_deposit':True}
control=snapshot(1)
payload=encode(control)
target={'sentinel_do_not_mutate':True}
assert cold(payload,target)==('OK',control) and has_exact_paid(control)
assert digest(payload)=='832e3f09cb5718634de49d89e1e358b70cc5789464612b2ca48ec6dab43bc415'
checks=[]
for name,state in [('deposit_undercarry',snapshot(0)),('overcarry_without_custody',snapshot(2)),('next_repeat_still_one_stored',snapshot(1,2)),('negative_carry',snapshot(-1)),('boolean_carry',snapshot(True)),('fractional_carry',snapshot(1.25))]:
 assert restore(state) is None and commit_candidate(payload,state)==('ERR_INVALID_DATA',payload)
 assert cold(encode(state),target)==('ERR_FILE_CORRUPT',target)
 assert not has_exact_paid(state)
 checks.append({'name':name,'restore':False,'commit':'ERR_INVALID_DATA','cold':'ERR_FILE_CORRUPT','no_in_memory_state_change':True})
assert commit_candidate(encode(snapshot(0)),control)==('ERR_FILE_CORRUPT',encode(snapshot(0)))
assert cold(payload+b'garbage',target)==('ERR_FILE_CORRUPT',target)
assert cold(None,target)==('ERR_FILE_NOT_FOUND',target)
# Closed modeled slice only: paid carry plus admitted durable storage must account for earned units.
# This arithmetic is deliberately not a new authority/coercion path.
def covers(earned,carry,stored):
 return all(type(x) is int and x>=0 for x in (earned,carry,stored)) and carry+stored==earned
assert all(covers(*x) for x in [(1,1,0),(1,0,1),(2,1,1)])
assert not any(covers(*x) for x in [(2,1,0),(2,2,1),(1,True,0)])
print(json.dumps({'scope':'pinned source transcription and in-memory bytes only','pinned_sources':pins,'synthetic_control_sha256_matches_real_archived_digest':digest(payload),'cold_positive':True,'negative_matrix':checks,'existing_corrupt_primary_refuses_replacement':True,'hash_invalid_and_missing_controls':True,'receiver_or_engine_or_real_save':False},indent=2))
