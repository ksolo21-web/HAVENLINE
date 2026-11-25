#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
from oracle import *
def h(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def pinned(folder,manifest):
    path=Path(folder)/"SHA256SUMS"
    assert h(path)==manifest
    for row in path.read_text().splitlines():
        sha,f=row.split(None,1)
        assert h(path.parent/f.strip())==sha
    return path.parent
p=pinned("../hvn-l1-paid-pine-renewal-v1","2939ea7d5a82461840888791619fd4ecc0eb41d6f6371cfc4170554de94d5a2f")
q=pinned("../hvn-l1-transfer-authority-fixture-v2","c901b967dc8774ac585eadf785a4ec2c2208f403529933b3c4c0e78e5846775b")
assert h(p/"renewal.patch")=="e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd"
assert h(q/"planner_upstream.gd")=="0ae04e267c01a0163cc29f6eabb23c1d8cc93edb635ced9e865a5452dcde9151"
old_patch=(p/"renewal.patch").read_text()
assert '"pine_occurrences"' in old_patch and '_whole(stock.get("wood"), pine_occurrences)' in old_patch
assert 'remaining += occurrence_count' in old_patch and '_whole(incoming_stock.get("wood"), remaining)' in old_patch
proof=(p/"evidence/restored_route_first.txt").read_text()
assert 'PASS deserialize actual persisted v1 envelope' in proof and 'PASS one durable occurrence and exact receipt for completed paid cut 2' in proof
assert 'PASS restart recovers two exactly, aborted cut not credited' in (p/"evidence/restored_cold.txt").read_text()
assert '953/953' in (q/"README.md").read_text()
checks=0
def ck(x):
    global checks
    assert x
    checks+=1
def err(fn):
    try:fn()
    except (ValueError,TypeError,OverflowError):ck(True)
    else:raise AssertionError("must reject")
def pkt(v,ids,carry,paid=False,z=None):
    d={"version":v,"collected":list(ids),"stock":{"wood":carry},"receipt":json.loads(json.dumps(RECEIPT)) if paid else {}}
    if z is not None:d['pine_occurrences']=z
    return d
def paid_v1():return pkt(1,("wood-b","wood-c","wood-a"),0,True)
def v2(z):return pkt(2,("wood-b","wood-c","wood-a"),z,True,z)
def fields(c):return [c.live.harvested,c.live.carried,c.live.stored,c.live.deposited]
def emit(c,k,stage=None,n=1):
    action=c.harvest_id() if k=="harvest" else c.deposit_id()
    if k=="harvest":ticket=c._trusted_harness_issue(k,action,"wood",n,origin="wood-a",first_paid=True,settled=True)
    else:ticket=c._trusted_harness_issue(k,action,"wood",n,sink=c.blank_test_sink)
    assert ticket is not None
    return c.apply(ticket,stage),ticket

# Legacy payload compatibility, with modern carried/stored strictly separate.
import itertools
for k in range(4):
    for ids in itertools.permutations(STARTERS,k):
        d=pkt(1,ids,k)
        z=load(wire(d))
        ck(z.ids==ids and z.carried==k and z.stored==0 and not z.paid)
        if k==3:
            d=pkt(1,ids,0,True)
            z=load(wire(d)); ck(z.ids==ids and z.paid and (z.harvested,z.carried,z.stored)==(0,0,0))
for i in (1,2,3,27,MAX):
    z=load(wire(v2(i))); ck((z.harvested,z.carried,z.stored,z.deposited)==(i,i,0,0))
    d=v2(i);d["version"]=2.0;d["pine_occurrences"]=float(i);d["stock"]["wood"]=float(i)
    ck(load(wire(d))==z)
    d=v2(i);d['stock']['wood']-=1
    err(lambda:load(wire(d)))
ck(load(wire(v2(2))).harvested==2)
# Godot hashes the exact payload string, not reserialized key order.
for actual_order in (paid_v1(),v2(2)):
    raw=json.dumps(actual_order,indent=1)
    envelope={"sha256":hashlib.sha256(raw.encode()).hexdigest(),"payload":raw,"version":1}
    ck(load(json.dumps(envelope).encode())==decode(actual_order))
bad=v2(2);bad["stock"]["wood"]=1
err(lambda:load(wire(bad))) # The original v2 negative after naïve deposit.
ck("stock" in bad and "stored" not in bad)
legacy=load(wire(paid_v1()))
assert (legacy.harvested,legacy.carried,legacy.stored)==(0,0,0)
gold=[fields(MemoryMedium(wire(paid_v1())).cold_boot())]
m=MemoryMedium(wire(paid_v1())); c=m.cold_boot()
ok,t1=emit(c,"harvest");ck(ok and not c.apply(t1))
ok,t2=emit(c,"harvest");ck(ok and not c.apply(t2));gold.append(fields(c))
ck(c.snapshot()["receipt"]==RECEIPT and c.snapshot()["collected"]==paid_v1()["collected"])
before=c.snapshot(); tok=c._trusted_harness_issue("deposit",1,"wood",1,sink=c.blank_test_sink)
ck(tok is not None);ck(not c.apply({"id":1,"stock":{"wood":1},"receipt":RECEIPT}))
ck(not c.apply(t1));ck(c.snapshot()==before)
ck(c.apply(tok));ck(not c.apply(tok));gold.append(fields(c))
p0=m.primary; new=m.cold_boot();gold.append(fields(new))
ck(new.snapshot()["receipt"]==RECEIPT and m.primary==p0 and new.blank_test_sink is not c.blank_test_sink)
ck(not new.apply(tok))
ck(new._trusted_harness_issue("deposit",1,"wood",1,sink=new.blank_test_sink) is None)
ok,t3=emit(new,"harvest");ck(ok and not new.apply(t3));gold.append(fields(new))
ck(gold==[[0,0,0,0],[2,2,0,0],[2,1,1,1],[2,1,1,1],[3,2,1,1]])
ck(new.snapshot()["receipt"]==RECEIPT and load(m.primary).v3()==new.snapshot())

# Cold cut at either side of atomic publish, separate old producer and deposit IDs.
cold={}
for kind in ("harvest","deposit"):
    for end in ("before","after"):
        med=MemoryMedium(wire(v2(2))); before=med.primary
        c=med.cold_boot()
        tid=c._trusted_harness_issue(kind,3 if kind=="harvest" else 1,"wood",1,
          origin="wood-a" if kind=="harvest" else None,sink=c.blank_test_sink if kind=="deposit" else None,
          first_paid=True,settled=True)
        ck(tid is not None)
        try:c.apply(tid,end)
        except ColdStop:ck(True)
        else:raise AssertionError("expected modeled process interruption")
        ck(fields(c)==[2,2,0,0] and not c.apply(tid))
        now=med.cold_boot();ck(med.stage is None and not now.apply(tid))
        target=[2,2,0,0] if end=="before" else ([3,3,0,0] if kind=="harvest" else [2,1,1,1])
        ck(fields(now)==target and (med.primary==before)==(end=="before"))
        ck(now.snapshot()["receipt"]==RECEIPT)
        cold[kind+"_"+end]=target
        # Reconciled recovery: no automatic replay on load; a new trusted action
        # uses only the current monotonic ID and acts once.
        ok,_=emit(now,kind);ck(ok)

# One stale independent process cannot clobber a durable committed generation.
med=MemoryMedium(wire(v2(2))); first=med.cold_boot();second=med.cold_boot()
stale=first._trusted_harness_issue("deposit",1,"wood",1,sink=first.blank_test_sink)
ck(stale is not None);ok,_=emit(second,"deposit");ck(ok)
prev=med.primary;ck(not first.apply(stale) and prev==med.primary)
# Wrong source/sink/material, future and replay IDs, malformed amounts, prepay and incomplete strikes.
med=MemoryMedium(wire(v2(2)));c=med.cold_boot();wrong=object()
for a in [(0,"wood",1,c.blank_test_sink),(2,"wood",1,c.blank_test_sink),(1,"food",1,c.blank_test_sink),
          (1,"wood",1,wrong),(1,"wood",0,c.blank_test_sink),(1,"wood",-1,c.blank_test_sink),(1,"wood",True,c.blank_test_sink),
          (1,"wood",1.0,c.blank_test_sink),(1,"wood",3,c.blank_test_sink),(1,"wood",MAX+1,c.blank_test_sink)]:
    ck(c._trusted_harness_issue("deposit",a[0],a[1],a[2],sink=a[3]) is None)
for k,src,start,done,total in ((3,"wood-b",True,True,1),(3,"wood-a",False,True,1),(3,"wood-a",True,False,1),
                                (2,"wood-a",True,True,1),(4,"wood-a",True,True,1),(3,"wood-a",True,True,2)):
    ck(c._trusted_harness_issue("harvest",k,"wood",total,origin=src,first_paid=start,settled=done) is None)
uc=MemoryMedium(wire(pkt(1,STARTERS,3))).cold_boot()
ck(uc._trusted_harness_issue("harvest",1,"wood",1,origin="wood-a",first_paid=True,settled=True) is None)
ck(uc._trusted_harness_issue("deposit",1,"wood",1,sink=uc.blank_test_sink) is None)
cap=MemoryMedium(wire(v2(MAX))).cold_boot()
ck(cap._trusted_harness_issue("harvest",MAX+1,"wood",1,origin="wood-a",first_paid=True,settled=True) is None)
ck(fields(c)==[2,2,0,0] and c.snapshot()["receipt"]==RECEIPT)
# Protocol malformed fixtures, including state rewrites with an otherwise valid checksum.
st=load(wire(v2(2))).v3()
for kind,value in (("carried",{"wood":1}),("stored",{"wood":0,"food":1}),("harvest_through",-1),("deposit_through",True),
                   ("deposit_through",1),("receipt",{}),("receipt",{"offer":"wrong"}),("collected",["wood-a",9,"wood-c"]),
                   ("collected",["wood-a","wood-a","wood-c"]),("collected",["wood-a","wood-b"]),("version",4)):
    d=dict(st);d[kind]=value
    err(lambda:load(wire(d)))
payload=wire(st); env=json.loads(payload)
err(lambda:load(payload+b'x'))
err(lambda:load(wire(st)+b' '*9000))
err(lambda:load(json.dumps(dict(env,sha256="invalid")).encode()))
err(lambda:load(wire(dict(st,unexpected=True))))
err(lambda:load(b'{"version":1,"version":1,"payload":"{}","sha256":"x"}'))
err(lambda:load(wire(pkt(2,STARTERS,3,False,3))))
# Broad exact accounting state matrix, independent arithmetic truth predicate.
matrix=0
for H in range(5):
 for carry in range(5):
  for stored in range(5):
   for seq in range(5):
    d=dict(st,harvest_through=H,carried={"wood":carry},stored={"wood":stored},deposit_through=seq)
    truth=H==carry+stored and 0<=seq<=stored and (seq==0)==(stored==0)
    try: x=load(wire(d))
    except ValueError:ck(not truth)
    else:ck(truth and x.v3()==d)
    matrix+=1
print(json.dumps({"pure_oracle_checks":checks,"matrix_states":matrix,"legacy_v2_stock_after_naive_deposit_rejected":True,
 "gold_fields":["harvest_highwater","carried_wood","stored_wood","deposit_highwater"],"gold_route":gold,
 "cold_controls":cold,"prior_typed_transfer_manifest":h(q/"SHA256SUMS"),"pine_patch_sha256":h(p/"renewal.patch"),
 "pine_native_author_manifest":h(p/"SHA256SUMS"),"world_slot_receiver_or_economics_defined":False,
 "production_v2_or_scene_modified":False,"simulated_atomic_promotion_only":True},indent=2,sort_keys=True))
