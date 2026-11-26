"""Binary custody check for exact ordered framebuffer bytes, no conversion."""
import hashlib,re
SIZES={"rgb8":1280*720*3,"rgba8":1280*720*4}
def verify_native_raw(raw,*,fmt,n,worker,expected):
 assert fmt in SIZES and isinstance(n,int) and 0<n<=180
 b=SIZES[fmt]
 assert (worker['accepted'],worker['written'],worker['outstanding'],worker['bytes_per_frame'],worker['reason'])==(n,n,0,b,'')
 assert 1<=worker['peak']<=8
 assert re.fullmatch(r'[a-f0-9]{64}',expected)
 assert raw.is_file() and not raw.is_symlink() and raw.stat().st_size==n*b
 assert len(worker['hashes'])==n and all(re.fullmatch(r'[a-f0-9]{64}',x) for x in worker['hashes'])
 whole=hashlib.sha256()
 hashes=[]
 with raw.open('rb') as f:
  for _ in range(n):
   data=f.read(b);assert len(data)==b
   whole.update(data)
   hashes.append(hashlib.sha256(data).hexdigest())
  assert f.read(1)==b''
 assert hashes==worker['hashes'], 'worker and host per-frame hash or order mismatch'
 assert whole.hexdigest()==expected
 return hashes
