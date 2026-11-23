"""Strict readback for the archival Havenline audio generator layout."""
import hashlib,json,math,os,re,stat,struct

ORDER=(('wind.wav',12.0,264600),('fire.wav',12.0,264600),
 ('wood.wav',.28,6174),('stone.wav',.32,7056),('transfer.wav',.22,4851),
 ('upgrade.wav',1.65,36382))
RATE=22050
PEAK_MAX=.72 + 2*math.ulp(.72)
PEAK_PRODUCT_ULPS=4
MANIFEST='bake-manifest.json'
NAMES=tuple(x[0] for x in ORDER)

def need(ok,why):
 if not ok:raise ValueError(why)
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(v):return type(v) is str and re.fullmatch('[0-9a-f]{64}',v) is not None
def pairs(raw):
 out={}
 for key,value in raw:
  need(key not in out,'duplicate JSON key')
  out[key]=value
 return out
def reject_constant(v):raise ValueError('nonfinite JSON number')
def bounded_child(root_fd,name,limit,exact=None):
 fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=root_fd)
 with os.fdopen(fd,'rb') as f:
  q=os.fstat(f.fileno())
  need(stat.S_ISREG(q.st_mode) and q.st_nlink==1 and 0<q.st_size<=limit,'unsafe file or size: '+name)
  if exact is not None:need(q.st_size==exact,'WAV physical length mismatch: '+name)
  b=f.read(limit+1);after=os.fstat(f.fileno())
  need(len(b)==q.st_size==after.st_size and (q.st_mtime_ns,q.st_ctime_ns)==(after.st_mtime_ns,after.st_ctime_ns),'member changed during read')
  return b
def check(root,expected_sha256_by_name=None):
 # Reference values must arrive from independently attested custody by the
 # caller, not be constructed from the emitted manifest or examined WAVs.
 if expected_sha256_by_name is not None:
  need(type(expected_sha256_by_name) is dict and set(expected_sha256_by_name)==set(NAMES) and all(map(sha,expected_sha256_by_name.values())),'invalid reference digests')
 root_fd=os.open(root,os.O_DIRECTORY|os.O_NOFOLLOW|os.O_RDONLY)
 try:
  names={MANIFEST,*NAMES}
  need(set(os.listdir(root_fd))==names,'unexpected/missing pre-import audio members')
  mf=json.loads(bounded_child(root_fd,MANIFEST,8192).decode('utf-8'),
                object_pairs_hook=pairs,parse_constant=reject_constant)
  need(type(mf) is dict and set(mf)=={'origin','listening_review','files'} and mf['origin']=='original deterministic synthesis' and mf['listening_review']=='not certified','manifest format')
  rows=mf['files']
  need(type(rows) is list and len(rows)==len(ORDER),'wrong file row count')
  result={}
  for row,(name,secs,frames) in zip(rows,ORDER):
   need(type(row) is dict and set(row)=={'file','seconds','sample_rate','peak','sha256'} and row['file']==name,'unknown, unsafe, duplicate or unordered manifest filename')
   need(type(row['seconds']) in (int,float) and row['seconds']==secs and type(row['sample_rate']) is int and row['sample_rate']==RATE and sha(row['sha256']),'bad manifest metadata')
   peak=row['peak']
   need(type(peak) is float and math.isfinite(peak) and 0<peak<=PEAK_MAX,'invalid generator peak metadata')
   size=2*frames
   b=bounded_child(root_fd,name,44+size,44+size)
   # Reject aliases, unknown or extended chunks, inconsistent block alignment,
   # advertised/truncated payload, and trailing bytes. Matches this generator's
   # specific ordinary PCM layout, not arbitrary otherwise valid WAV.
   canonical=struct.pack('<4sI4s4sIHHIIHH4sI',b'RIFF',36+size,b'WAVE',b'fmt ',16,1,1,RATE,2*RATE,2,16,b'data',size)
   need(b[:44]==canonical,'WAV header or frame metadata mismatch: '+name)
   # Source first computes peak * gain in floating point then independently
   # applies the same gain per sample and truncates signed PCM toward zero.
   # At the expected max no .98 clipping can occur. Permit only last-bit
   # floating rounding at an integer boundary, not a one-count tolerance
   # elsewhere. struct's <h reads signed little-endian, including -32768.
   measured=max(abs(x) for (x,) in struct.iter_unpack('<h',memoryview(b)[44:]))
   intended=peak*32767
   uncertainty=PEAK_PRODUCT_ULPS*math.ulp(intended)
   need(int(max(0.,intended-uncertainty))<=measured<=int(intended+uncertainty),
        'manifest peak does not reconcile with actual signed PCM peak: '+name)
   actual=digest(b)
   need(actual==row['sha256'],'manifest/file digest mismatch: '+name)
   if expected_sha256_by_name is not None:
    need(actual==expected_sha256_by_name[name],'independent named digest mismatch: '+name)
   result[name]={'frames':frames,'sha256':actual,'signed_abs_pcm_peak':measured}
  need(set(os.listdir(root_fd))==names,'audio member set changed during read')
 finally:os.close(root_fd)
 return {'level':'FORMAT_AND_SELF_MANIFEST_ONLY' if expected_sha256_by_name is None else 'MATCHED_SUPPLIED_REFERENCE_DIGESTS',
  'label_identity_verified_by_checker':False,
  'external_named_reference_match':expected_sha256_by_name is not None,
  'requires_independent_reference_provenance':True,'audible_playback_verified':False,'files':result}
