#!/usr/bin/env python3
"""Detached pure Level 1 accounting model; not a Godot adapter or save format release."""
from dataclasses import dataclass,replace
import hashlib,json,math
STARTERS=("wood-a","wood-b","wood-c")
OFFER="center-hearth"
MAX=2147483647
RECEIPT={"offer":OFFER,"grant":OFFER,"revision":1,"typed_debit":{"wood":3}}

def whole(x,lo=0,hi=MAX):
    if type(x) not in (int,float) or (type(x) is float and (not math.isfinite(x) or not x.is_integer())):
        raise ValueError("typed whole count")
    if not lo<=x<=hi:raise ValueError("count range")
    return int(x)

def keys(x,k):
    if type(x) is not dict or set(x)!=set(k.split()):raise ValueError("schema")
def read_receipt(x):
    if type(x) is not dict:raise ValueError("receipt type")
    if not x:return False
    keys(x,"offer grant revision typed_debit")
    keys(x["typed_debit"],"wood")
    if x["offer"]!=OFFER or x["grant"]!=OFFER or whole(x["revision"],1,1)!=1 or whole(x["typed_debit"]["wood"],3,3)!=3:
        raise ValueError("protected original receipt")
    return True

def typed(d):
    keys(d,"wood")
    return whole(d["wood"])

@dataclass(frozen=True)
class State:
    ids: tuple
    paid: bool
    harvested: int
    carried: int
    stored: int
    deposited: int

    def assert_conserved(self):
        if any(type(x) is not str or x not in STARTERS for x in self.ids) or len(set(self.ids))!=len(self.ids):
            raise ValueError("starter IDs")
        for x in (self.harvested,self.carried,self.stored,self.deposited):whole(x)
        if self.paid and set(self.ids)!=set(STARTERS):raise ValueError("paid original three")
        if not self.paid and (self.harvested or self.stored or self.deposited):raise ValueError("unpaid")
        if not 0<=self.deposited<=self.stored or (self.deposited==0)!=(self.stored==0):
            raise ValueError("deposit highwater")
        if self.carried+self.stored+(3 if self.paid else 0)!=len(self.ids)+self.harvested:
            raise ValueError("conservation")
        return self

    def v3(self):
        self.assert_conserved()
        return {"version":3,"collected":list(self.ids),"receipt":json.loads(json.dumps(RECEIPT)) if self.paid else {},
                "harvest_through":self.harvested,"deposit_through":self.deposited,
                "carried":{"wood":self.carried},"stored":{"wood":self.stored}}

def decode(d):
    if type(d) is not dict:raise ValueError("payload")
    version=whole(d.get("version"),1,3)
    src=d.get("collected")
    if type(src) is not list:raise ValueError("starter collection")
    paid=read_receipt(d.get("receipt"))
    if version==1:
        keys(d,"version collected receipt stock"); q=State(tuple(src),paid,0,typed(d["stock"]),0,0)
    elif version==2:
        keys(d,"version collected receipt stock pine_occurrences")
        q=State(tuple(src),paid,whole(d["pine_occurrences"],1),typed(d["stock"]),0,0)
    else:
        keys(d,"version collected receipt harvest_through deposit_through carried stored")
        q=State(tuple(src),paid,whole(d["harvest_through"]),typed(d["carried"]),typed(d["stored"]),whole(d["deposit_through"]))
    return q.assert_conserved()

def wire(d):
    p=json.dumps(d,sort_keys=True,separators=(",",":"),allow_nan=False)
    return json.dumps({"version":1,"payload":p,"sha256":hashlib.sha256(p.encode()).hexdigest()},sort_keys=True,separators=(",",":")).encode()

def _no_duplicates(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError("duplicate JSON field")
        d[k]=v
    return d

def load(w):
    if type(w) is not bytes or len(w)>8192:raise ValueError("bound")
    d=json.loads(w,object_pairs_hook=_no_duplicates)
    keys(d,"version payload sha256")
    whole(d["version"],1,1)
    p=d["payload"]
    if type(p) is not str or hashlib.sha256(p.encode()).hexdigest()!=d["sha256"]:raise ValueError("checksum")
    return decode(json.loads(p,object_pairs_hook=_no_duplicates))

class ColdStop(Exception):pass
class MemoryMedium:
    """One authoritative writer in the model; not a filesystem implementation."""
    def __init__(self,primary):
        self.primary=primary;self.stage=None
    def cold_boot(self):
        self.stage=None
        return Process(self)

class Process:
    def __init__(self,medium):
        self.medium=medium;self.published=medium.primary;self.live=load(self.published)
        self._issued=None; self._retired=False;self._sink=object()
    @property
    def blank_test_sink(self):return self._sink
    def snapshot(self):return self.live.v3()
    def harvest_id(self):return self.live.harvested+1
    def deposit_id(self):return self.live.deposited+1

    def _trusted_harness_issue(self,kind,action_id,material,units,origin=None,sink=None,first_paid=False,settled=False):
        """Test observer models trusted scene/event provenance; no public ingress or slot policy."""
        if kind not in ("harvest","deposit") or self._retired:return None
        if (self._issued is not None or not self.live.paid or type(material) is not str or material!="wood"
            or type(action_id) is not int or not 0<action_id<=MAX or type(units) is not int or not 0<units<=MAX):return None
        if kind=="harvest":
            if origin!="wood-a" or sink is not None or not (first_paid is True and settled is True) or units!=1 or action_id!=self.harvest_id():return None
        else:
            if origin is not None or sink is not self._sink or action_id!=self.deposit_id() or units>self.live.carried:return None
        ticket=object()
        self._issued=(ticket,kind,action_id,material,units,self.published,sink)
        return ticket

    def apply(self,ticket,stage_break=None):
        if self._retired or self._issued is None or ticket is not self._issued[0]:return False
        if stage_break not in (None,"before","after"):return False
        _,kind,action_id,row,units,prior,sink=self._issued
        self._issued=None
        if prior!=self.medium.primary or row!="wood":return False
        if kind=="harvest":
            if action_id!=self.harvest_id():return False
            new=replace(self.live,harvested=action_id,carried=self.live.carried+units)
        else:
            if sink is not self._sink or action_id!=self.deposit_id() or units>self.live.carried:return False
            new=replace(self.live,deposited=action_id,carried=self.live.carried-units,stored=self.live.stored+units)
        try:
            raw=wire(new.v3()); assert load(raw)==new
        except ValueError:
            return False
        self.medium.stage=raw
        if stage_break=="before":
            self._retired=True
            raise ColdStop("before atomic promotion")
        # Promotion is modeled by one ownership assignment, not fsync claims.
        self.medium.primary=self.medium.stage
        self.medium.stage=None
        if stage_break=="after":
            self._retired=True
            raise ColdStop("after atomic promotion, before process publication")
        self.live=new
        self.published=raw
        return True
