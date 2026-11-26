"""Test the source boundaries and independent writer invariants, never launch."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent
P=H.parent/'hvn-l1-c1-normal-camera-stock-capture-v1'
R=H.parent/'hvn-l1-c1-normal-camera-stock-parser-import-v3/compile-only.MC0vLsj3'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(P/'SHA256SUMS')=='5f7046a5c3369d341743fdad7f5cf8c409b65f0e04b01de1d9e82864af87c7ad'
assert h(R/'SHA256SUMS')=='39a0fca0e650dbca7615aa6a118aae3e8b4e8436375f77ae029bd36fedaff58b'
assert json.loads((R/'parser-proof.json').read_text())['parser_only']
for line in (R/'SHA256SUMS').read_text().splitlines():
 digest,n=line.split('  ',1);assert h(R/n)==digest
a=(P/'observer.gd').read_text(); b=(H/'observer.gd').read_text()
for header,end in [('func _initialize()', 'func draw()'),('func draw()', '\n\tif rgb:'),('if Engine.get_physics_frames()!=phys or Engine.get_process_frames()!=proc','func run()'),('func run()', '\n\tactive=true'),('\tactive=true','\n\tif not finish_skin():')]:
 o=a[a.index(header):];n=b[b.index(header):]
 left=o.split(end,1)[0];right=n.split(end,1)[0]
 # Exact controller source held through writer startup insertion; final writer
 # completion may be inserted once END guards have already been evaluated.
 if header=='func run()':right=right.split('\n\tif rgb:',1)[0]
 if header=='\tactive=true':right=right.split('\n\tvar writer_result',1)[0]
 assert left==right, header
assert 'var images:' not in b and 'pic.convert' not in b
w=b[b.index('class NativeFrameWriter'):b.index('func fail(')]
assert 'const SLOT_LIMIT := 8' in w
assert 'reserved>=SLOT_LIMIT' in w and w.index('reserved+=1')<w.index('pending_frames.push_back')
assert 'pending_frames.pop_front()' in w and 'if serial!=pre+1' in w
assert w.index('file.store_buffer(bytes)')<w.index('rec.clear()')<w.index('bytes=PackedByteArray()')<w.index('reserved-=1')
assert 'm.try_lock()' in w and 'if file.get_error()!=OK or file.get_position()!=serial*bytes.size():' in w
assert 'worker.wait_to_finish()' in w and 'file.flush()' in w
ver=(H/'verify.py').read_text()
r=(H/'raw_verify.py').read_text()
assert "assert hashes==worker['hashes']" in r and "assert 1<=worker['peak']<=8" in r and 'assert c==a' in ver and 'hashes=verify_native_raw' in ver

# Independent state-machine test of the intended protocol. These are not Godot calls.
class Sim:
 def __init__(self):self.q=[];self.flight=None;self.n=0;self.err=False;self.done=[]
 @property
 def used(self):return len(self.q)+int(self.flight is not None)
 def push(self,n):
  if self.err or self.used>=8 or n!=self.n+1:self.err=True;return False
  self.n=n;self.q.append(n);return True
 def take(self):
  if self.err or self.flight is not None:return
  self.flight=self.q.pop(0)
 def finish(self,success=True):
  n=self.flight;self.flight=None
  if not success or n!=len(self.done)+1:self.err=True;return
  self.done.append(n)
 def valid(self):return not self.err and not self.used and self.done==list(range(1,self.n+1))
s=Sim()
for x in range(1,9):assert s.push(x)
s.take();assert s.used==8 and not s.push(9) and not s.valid() # includes flight
for n in (0,2):
 s=Sim();assert not s.push(n) and not s.valid()
s=Sim();assert s.push(1);s.take();s.finish(False);assert not s.valid() # short write
s=Sim();assert s.push(1);s.take();s.flight=2;s.finish();assert not s.valid() # reorder
s=Sim();assert s.push(1);assert not s.valid() # undrained
s=Sim()
for x in range(1,175):
 assert s.push(x)
 if x%4==0:
  for _ in range(4):s.take();s.finish()
while s.used:s.take();s.finish()
assert s.valid()
print('Bounded writer source controls exact; model accepts 174 ordered bytes slots and rejects duplicate/gap, in-flight overflow, write failure, reorder and undrained completion. Not native.')
