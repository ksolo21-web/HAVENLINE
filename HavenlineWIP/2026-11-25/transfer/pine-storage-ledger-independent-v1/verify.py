from pathlib import Path
import hashlib, importlib.util,itertools,sys,json,subprocess
B=Path(__file__).resolve().parent.parent
def pin(n,h):
 p=B/n; f=p/'SHA256SUMS'; assert hashlib.sha256(f.read_bytes()).hexdigest()==h
 subprocess.run(['sha256sum','--check','--status','SHA256SUMS'],cwd=p,check=True)
 return p
p=pin('hvn-l1-pine-storage-ledger-composition-v1','392db89ab0985fa2c9464ff28807096aa4951bdad3ce22e178cd6927b45aba06')
v=pin('hvn-l1-paid-pine-renewal-v1','2939ea7d5a82461840888791619fd4ecc0eb41d6f6371cfc4170554de94d5a2f')
assert hashlib.sha256((v/'renewal.patch').read_bytes()).hexdigest()=='e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd'
spec=importlib.util.spec_from_file_location('exact_review_oracle',p/'oracle.py'); m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;sys.dont_write_bytecode=True;spec.loader.exec_module(m)
ids=['wood-c','wood-a','wood-b']; receipt={'grant':'center-hearth','revision':1,'typed_debit':{'wood':3},'offer':'center-hearth'}
def env(q):
 t=json.dumps(q,indent=2)  # source wire checks the hash of this precise string
 return json.dumps({'sha256':hashlib.sha256(t.encode()).hexdigest(),'payload':t,'version':1}).encode()
def legacy(n=0):
 d={'version':2 if n else 1,'receipt':receipt,'stock':{'wood':n},'collected':ids}
 if n:d['pine_occurrences']=n
 return d
def tup(p):
 v=p.snapshot(); assert v['receipt']==receipt and v['collected']==ids
 return [v['harvest_through'],v['carried']['wood'],v['stored']['wood'],v['deposit_through']]
def take(p,k,n,seq=None):
 if k=='D':return p._trusted_harness_issue('deposit',p.deposit_id() if seq is None else seq,'wood',n,sink=p.blank_test_sink)
 return p._trusted_harness_issue('harvest',p.harvest_id() if seq is None else seq,'wood',n,origin='wood-a',first_paid=True,settled=True)
for n in [0,1,3,2147483647]:
 s=m.load(env(legacy(n)));assert (s.harvested,s.carried,s.stored,s.deposited)==(n,n,0,0)
def rejects(w):
 try:m.load(w)
 except ValueError:return True
 raise AssertionError('unexpected accepted payload')
neg=legacy(3);neg['stock']={'wood':2}; assert rejects(env(neg))
d=m.load(env(legacy(3))).v3();d['stored']={'wood':1}; d['carried']={'wood':2};d['deposit_through']=2
assert rejects(env(d))  # conserved total, impossible two distinct positive deposits of one wood
checked=0
for steps in itertools.product(['H','D1','D2'],repeat=6):
 a=m.MemoryMedium(env(legacy(3))); p0=a.cold_boot(); H=3; bucket=[]; D=0
 for step in steps:
  before=a.primary; p=p0;k=step[0];n=int(step[1:]) if k=='D' else 1
  if k=='D' and n>H-sum(bucket):
   assert take(p,k,n) is None and a.primary==before
   continue
  t=take(p,k,n);assert t and p.apply(t) and not p.apply(t)
  if k=='H': H+=1
  else: bucket.append(n);D+=1
  assert tup(p)==[H,H-sum(bucket),sum(bucket),D] and a.primary!=before
  p0=a.cold_boot(); assert tup(p0)==tup(p) and not p0.apply(t)
  checked+=1
out={}
for phase in ('before','after'):
 a=m.MemoryMedium(env(legacy(3))); p=a.cold_boot(); old=a.primary
 t=take(p,'D',2)
 try:p.apply(t,phase)
 except m.ColdStop:pass
 else:raise AssertionError
 assert tup(p)==[3,3,0,0] and not p.apply(t)
 q=a.cold_boot();assert a.stage is None and not q.apply(t)
 expected=[3,3,0,0] if phase=='before' else [3,1,2,1]
 assert tup(q)==expected and (a.primary==old)==(phase=='before')
 out[phase]=expected
a=m.MemoryMedium(env(legacy(3))); p=a.cold_boot(); stale=take(p,'H',1); q=a.cold_boot(); now=take(q,'D',2); assert q.apply(now); good=a.primary
assert not p.apply(stale) and good==a.primary
# A mere logical boot is not process termination: no generation/fencing token was added.
a=m.MemoryMedium(env(legacy(3))); p=a.cold_boot(); pending=take(p,'D',2); q=a.cold_boot()
assert not q.apply(pending) and p.apply(pending)
print(json.dumps({'original_source_patches_verified':True,'canonical_legacy_samples':4,'independent_action_traces':729,
 'independent_successful_steps':checked,'modeled_deposit_two_unit_interruptions':out,
 'invalid_conserved_but_impossible_deposit_counter_rejected':True,'stale_writer_after_byte_change_rejected':True,
 'cold_boot_alone_does_not_revoke_old_live_reference_before_any_durable_change':True,
 'scope':'single writer, well-formed generated envelopes, modeled cold stop; not runtime persistence or ingress'},indent=2))
