#!/usr/bin/env python3
"""Disposable POSIX proof adapter for a sealed Level 1 accounting oracle."""
import contextlib,fcntl,hashlib,json,os,re,stat,sys
from dataclasses import replace
from pathlib import Path
P=Path(__file__).resolve().parent.parent/"hvn-l1-pine-storage-ledger-composition-v1"
def sha(x):return hashlib.sha256(x).hexdigest()
m=(P/"SHA256SUMS").read_bytes()
assert sha(m)=="392db89ab0985fa2c9464ff28807096aa4951bdad3ce22e178cd6927b45aba06"
for line in m.decode().splitlines():
    h,name=line.split()
    assert sha((P/name).read_bytes())==h
sys.dont_write_bytecode=True
sys.path.insert(0,str(P))
from oracle import MAX,State,load,wire,whole,keys
PREFIX="hvn-pine-store-fsfixture-"
MARK=b"HAVENLINE-PINE-STORE-BACKEND-TEST-V1\n"
NAMES={"fixture.marker","fixture.lock","fixture.primary","fixture.stage"}
def stable(d):
    return json.dumps(d,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
def encode(epoch,state):
    led=wire(state.v3()).decode()
    plain=dict(epoch=epoch,ledger=led,fixture_format=1)
    return stable(dict(payload=plain,sha256=sha(stable(plain))))
def strict_pairs(items):
    out={}
    for k,v in items:
        if k in out:raise ValueError("duplicate fields")
        out[k]=v
    return out
def record(raw):
    if len(raw)>8192:raise ValueError("profile file bound")
    d=json.loads(raw,object_pairs_hook=strict_pairs)
    if "payload" in d and type(d["payload"]) is str:
        return 0,load(raw)
    keys(d,"payload sha256")
    p=d["payload"];keys(p,"epoch ledger fixture_format")
    whole(p["fixture_format"],1,1)
    epoch=whole(p["epoch"],1)
    if type(p["ledger"]) is not str or sha(stable(p))!=d["sha256"]:
        raise ValueError("ledger/epoch integrity")
    return epoch,load(p["ledger"].encode())

class Store:
    def __init__(self,p):
        leaf=Path(p).name
        if p!="/tmp/"+leaf or not re.fullmatch(PREFIX+r"[a-zA-Z0-9_-]{8,64}",leaf):
            raise ValueError("dedicated disposable profile")
        base=os.open("/tmp",os.O_RDONLY|os.O_DIRECTORY)
        try:self.df=os.open(leaf,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=base)
        finally:os.close(base)
        try:
            fs=os.fstat(self.df)
            if fs.st_uid!=os.geteuid() or fs.st_mode&0o077:raise ValueError("private directory required")
            if self.read("fixture.marker")!=MARK:raise ValueError("fixture marker")
        except BaseException:
            os.close(self.df);raise
    def __enter__(self):return self
    def __exit__(self,*exc):os.close(self.df)
    def fd(self,name,flags):
        assert name in NAMES
        f=os.open(name,flags|os.O_NOFOLLOW|os.O_NONBLOCK,0o600,dir_fd=self.df)
        fs=os.fstat(f)
        if not stat.S_ISREG(fs.st_mode) or fs.st_nlink!=1 or fs.st_uid!=os.geteuid() or fs.st_mode&0o077:
            os.close(f);raise ValueError("unowned/linked/public profile file")
        return f
    def read_no(self,name):
        f=self.fd(name,os.O_RDONLY)
        with os.fdopen(f,"rb") as data:return data.read(8193)
    def read(self,name):
        return self.read_no(name)
    @contextlib.contextmanager
    def writer(self):
        f=self.fd("fixture.lock",os.O_RDWR|os.O_CREAT)
        try:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield
        finally:os.close(f)
    def stage(self,raw):
        # Dispose an uncommitted stage only while holding the writer lock.
        try:old=self.fd("fixture.stage",os.O_RDONLY)
        except FileNotFoundError:pass
        else:
            os.close(old)
            os.unlink("fixture.stage",dir_fd=self.df)
        f=self.fd("fixture.stage",os.O_WRONLY|os.O_CREAT|os.O_EXCL)
        with os.fdopen(f,"wb") as out:
            out.write(raw);out.flush();os.fsync(out.fileno())
        assert self.read("fixture.stage")==raw
        self._last_stage=raw
    def promote(self):
        if self.read("fixture.stage")!=self._last_stage:raise ValueError("changed staged identity")
        os.replace("fixture.stage","fixture.primary",src_dir_fd=self.df,dst_dir_fd=self.df)
        os.fsync(self.df)
    def boot(self):
        with self.writer():
            e,s=record(self.read("fixture.primary"))
            if not e<MAX:raise ValueError("epoch exhausted")
            raw=encode(e+1,s)
            self.stage(raw)
            self.promote()
        return Session(self,e+1,s,sha(raw))

class Session:
    def __init__(self,store,generation,state,identity):
        self.store=store;self.epoch=generation;self.state=state;self.expected=identity
        self._pending=None;self.test_sink=object()
    def stage_trusted(self,kind,i,source=None,first_paid=False,settled=False,sink=None,material="wood",units=1):
        """Test harness trust seam, not real player ingress or a receiver."""
        s=self.state
        if self._pending is not None or not s.paid or material!="wood" or type(i) is not int or not 0<i<=MAX or type(units) is not int or units!=1:return None
        if kind=="deposit":
            # Bounded to ONE fixture deposit, no policy about actual deposit volume.
            if i!=1 or i!=s.deposited+1 or s.carried<1 or sink is not self.test_sink or source is not None:return None
            n=replace(s,deposited=1,carried=s.carried-1,stored=s.stored+1)
        elif kind=="harvest":
            if source!="wood-a" or first_paid is not True or settled is not True or sink is not None or i!=s.harvested+1:return None
            n=replace(s,harvested=i,carried=s.carried+1)
        else:return None
        n.assert_conserved()
        token=object();self._pending=(token,self.epoch,self.expected,n)
        return token
    def publish(self,token,barrier=None):
        if self._pending is None or token is not self._pending[0]:return "denied-token"
        _,epoch,prior,new=self._pending
        try:
            with self.store.writer():
                cur=self.store.read("fixture.primary")
                persisted_epoch,s=record(cur)
                if persisted_epoch!=epoch or sha(cur)!=prior or s!=self.state:
                    self._pending=None;return "denied-stale"
                raw=encode(epoch,new)
                self.store.stage(raw)
                if barrier:barrier("before")
                self.store.promote()
                if barrier:barrier("after")
                self.state=new;self.expected=sha(raw); self._pending=None
        except BlockingIOError:
            return "denied-held-lock"
        return "committed"
