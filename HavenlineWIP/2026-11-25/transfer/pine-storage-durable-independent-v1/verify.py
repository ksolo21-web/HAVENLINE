from pathlib import Path
from tempfile import TemporaryDirectory
import os,sys,hashlib,subprocess,selectors,signal,json
p=Path(__file__).resolve().parent.parent/'hvn-l1-pine-storage-durable-backend-v1'
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='c52e1ccf7bd332724d16569a270929f14c9e2994f5ab07c0fc7da401b99132bb'
subprocess.run(['sha256sum','--check','--status','SHA256SUMS'],cwd=p,check=True)
sys.dont_write_bytecode=True;sys.path.insert(0,str(p))
from backend import Store,record,MARK,PREFIX
ids=['wood-b','wood-c','wood-a']; receipt={'offer':'center-hearth','grant':'center-hearth','typed_debit':{'wood':3},'revision':1}
def initial(n):
 d=dict(version=2 if n else 1,collected=ids,stock={'wood':n},receipt=receipt)
 if n:d['pine_occurrences']=n
 raw=json.dumps(d,indent=2); return json.dumps(dict(version=1,payload=raw,sha256=hashlib.sha256(raw.encode()).hexdigest())).encode()
def put(p,b):
 with open(p,'wb',opener=lambda path,f:os.open(path,f,0o600)) as o:o.write(b)
def profile(d,n):
 d=Path(d);put(d/'fixture.marker',MARK); put(d/'fixture.primary',initial(n));return str(d)
def child(d,*a):
 return subprocess.Popen([sys.executable,'-B',str(p/'child.py'),d,*a],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def read(c,name):
 with selectors.DefaultSelector() as sel:
  sel.register(c.stdout,selectors.EVENT_READ); assert sel.select(5)
 l=c.stdout.readline()
 assert l; e=json.loads(l);assert e['pid']==c.pid and e['event']==name; return e
def state(x):
 v=x.v3(); assert v['receipt']==receipt and v['collected']==ids
 return [x.harvested,x.carried,x.stored,x.deposited]
def next_from_new(d,expected,nextstate):
 with child(d,'next') as c:
  z=read(c,'boot'); assert z['state']==expected
  f=read(c,'new'); assert f['state']==nextstate
  assert c.wait(timeout=5)==0
  return z['epoch']
def deposit(s):return s.stage_trusted('deposit',1,sink=s.test_sink)
for n in [0,2]:
 with TemporaryDirectory(prefix=PREFIX,dir='/tmp') as d:
  d=profile(d,n)
  with Store(d) as s:
   assert record(s.read('fixture.primary'))[0]==0
   q=s.boot(); assert q.epoch==1 and state(q.state)==[n,n,0,0]
out={}
for stop in ['before','after']:
 with TemporaryDirectory(prefix=PREFIX,dir='/tmp') as d:
  d=profile(d,2)
  with child(d,'crash',stop,'deposit') as c:
   try:
    boot=read(c,'boot');step=read(c,stop);assert c.poll() is None and step['live_state']==[2,2,0,0]
    with Store(d) as s:
     try:s.boot()
     except BlockingIOError:pass
     else:raise AssertionError('child lock not held')
    expected=[2,2,0,0] if stop=='before' else [2,1,1,1]
    assert step['durable_state']==expected
    assert (boot['identity']==step['primary_identity'])==(stop=='before')
   finally:
    # Only this Popen-owned child, no signal to the workspace or another process.
    if c.poll() is None:c.kill()
   assert c.wait(timeout=5)==-signal.SIGKILL
  post=list(expected);post[0]+=1;post[1]+=1
  assert next_from_new(d,expected,post)==boot['epoch']+1
  out[stop]=[expected,post]
with TemporaryDirectory(prefix=PREFIX,dir='/tmp') as d:
 d=profile(d,2)
 with Store(d) as s:
  a=s.boot(); a_t=deposit(a); assert a_t
  # Same ledger bytes logically, new durable boot epoch on a live explicit session.
  with child(d,'read') as c:
   b=read(c,'boot');assert c.wait(timeout=5)==0
  assert b['epoch']==a.epoch+1 and b['state']==state(a.state)
  assert a.publish(a_t)=='denied-stale'
  # Isolate byte-content predicate under identical epoch and logically identical state.
  q=s.boot(); q_t=deposit(q); prior=s.read('fixture.primary'); equivalent=prior+b' '
  assert record(prior)==record(equivalent)
  with s.writer():
   s.stage(equivalent);s.promote()
  assert q.publish(q_t)=='denied-stale' and s.read('fixture.primary')==equivalent
print(json.dumps(dict(detached_posix_owned_child_SIGKILL=True,verified_legacy=[1,2],stages=out,
 unchanged_ledger_new_epoch_rejects_old_pending=True,same_epoch_same_state_different_exact_bytes_rejects_old_pending=True,
 actual_held_flock_refuses_second_writer=True,device_power_failure=False,actual_Godot_save=False),indent=2))
