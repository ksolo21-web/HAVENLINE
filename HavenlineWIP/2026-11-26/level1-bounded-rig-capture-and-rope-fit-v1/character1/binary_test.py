"""Actual binary-file fault controls using invented deterministic framebuffer bytes."""
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
from copy import deepcopy
from raw_verify import SIZES,verify_native_raw
b=SIZES['rgba8'];a=b'\x00'*b;c=b'\x2a'*b
h=lambda x:sha256(x).hexdigest()
r={'accepted':2,'written':2,'outstanding':0,'bytes_per_frame':b,'reason':'','peak':1,'hashes':[h(a),h(c)]}
with TemporaryDirectory() as d:
 f=Path(d)/'native.rgb'
 def t(content,worker=r,sig=h(a+c),passes=False):
  f.write_bytes(content)
  try:result=verify_native_raw(f,fmt='rgba8',n=2,worker=worker,expected=sig)
  except AssertionError:assert not passes
  else:assert passes and result==r['hashes']
 t(a+c,passes=True)
 t(c+a,sig=h(c+a)) # whole hash alone would pass, per-frame order cannot
 t(a+a,sig=h(a+a)) # replayed frame
 t(a+c[:-1]);t(a+c+b'x');t(a+c,sig=h(a))
 for k,v in [('peak',9),('outstanding',1),('written',1),('accepted',1),('reason','short-write')]:
  q=deepcopy(r);q[k]=v;t(a+c,q)
print('Binary file controls: exact 2 full-size frames pass; order, duplicate, shortage, append, whole-hash, slot/accounting and write-error negatives denied. Synthetic only.')
