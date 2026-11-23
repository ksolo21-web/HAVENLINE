import hashlib,json,math,os,struct,tempfile,unittest
from pathlib import Path
from checker import check,ORDER,MANIFEST
# Separate expected digests derive from this test's fixed synthetic records
# before the on-disk manifest is created; never taken from the checker input
# files after writer mutation. No production generator imports or audio.
def wav(frames,sample):
 pcm=struct.pack('<h',sample)*frames
 return struct.pack('<4sI4s4sIHHIIHH4sI',b'RIFF',36+len(pcm),b'WAVE',b'fmt ',16,1,1,22050,44100,2,16,b'data',len(pcm))+pcm
def sha(b):return hashlib.sha256(b).hexdigest()
class TestWav(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent,prefix=".synthetic-")
  self.addCleanup(self.temp.cleanup)
  self.path=Path(self.temp.name)
  self.original={n:wav(frames,i+1) for i,(n,secs,frames) in enumerate(ORDER)}
  self.expected={n:sha(value) for n,value in self.original.items()}
  self.m={'origin':'original deterministic synthesis','listening_review':'not certified',
   'files':[{'file':n,'seconds':secs,'sample_rate':22050,'peak':(i+1.25)/32767,'sha256':self.expected[n]}
    for i,(n,secs,frames) in enumerate(ORDER)]}
  for n,v in self.original.items():(self.path/n).write_bytes(v)
  self.save()
 def save(self):(self.path/MANIFEST).write_text(json.dumps(self.m))
 def test_bounded_valid_and_scope(self):
  assert check(self.path)['level']=='FORMAT_AND_SELF_MANIFEST_ONLY'
  result=check(self.path,self.expected)
  assert result['external_named_reference_match'] and not result['label_identity_verified_by_checker'] and not result['audible_playback_verified']
 def test_misleading_header_and_self_rehash_truncation(self):
  short=self.original['wood.wav'][:-2]
  (self.path/'wood.wav').write_bytes(short);self.m['files'][2]['sha256']=sha(short);self.save()
  with self.assertRaisesRegex(ValueError,'physical length'):check(self.path)
 def test_same_length_named_swap_detected_by_reference_only(self):
  a,b=self.original['wind.wav'],self.original['fire.wav'];assert len(a)==len(b) and a!=b
  (self.path/'wind.wav').write_bytes(b);(self.path/'fire.wav').write_bytes(a)
  self.m['files'][0]['sha256']=sha(b);self.m['files'][1]['sha256']=sha(a)
  self.m['files'][0]['peak'],self.m['files'][1]['peak']=self.m['files'][1]['peak'],self.m['files'][0]['peak'];self.save()
  assert check(self.path)['level']=='FORMAT_AND_SELF_MANIFEST_ONLY'
  with self.assertRaisesRegex(ValueError,'independent named digest'):check(self.path,self.expected)
 def test_duplicate_row(self):
  self.m['files'][1]=self.m['files'][0];self.save()
  with self.assertRaisesRegex(ValueError,'duplicate'):check(self.path)
 def test_duplicate_json_keys(self):
  p=self.path/MANIFEST;p.write_text(p.read_text().replace('"file": "fire.wav"','"file": "fire.wav", "file": "fire.wav"'))
  with self.assertRaisesRegex(ValueError,'duplicate JSON key'):check(self.path)
 def test_traversal_in_row(self):
  self.m['files'][1]['file']='../fire.wav';self.save()
  with self.assertRaisesRegex(ValueError,'unsafe'):check(self.path)
 def test_symlink_rejected(self):
  name=self.path/'fire.wav';name.unlink();name.symlink_to(self.path/'wind.wav')
  with self.assertRaises(OSError):check(self.path)
 def test_tampered_manifest_peak_with_unchanged_wav_and_reference(self):
  for peak,reason in [(.98,'generator peak'),(.25,'actual signed PCM'),(0,'generator peak'),(0.0,'generator peak')]:
   self.m['files'][2]['peak']=peak;self.save()
   with self.assertRaisesRegex(ValueError,reason):check(self.path,self.expected)
 def test_signed_max_and_narrow_integer_boundary(self):
  n,_,frames=ORDER[2]
  b=bytearray(wav(frames,100))
  # Positive sample 100, negative sample -257: only unsigned/positive-only
  # or average metrics can miss the absolute signed maximum.
  struct.pack_into('<h',b,44,-257)
  (self.path/n).write_bytes(b)
  self.m['files'][2]['sha256']=sha(b)
  for pcm_peak in (257.18,math.nextafter(257.,0.)):
   self.m['files'][2]['peak']=pcm_peak/32767;self.save()
   self.assertEqual(check(self.path)['files'][n]['signed_abs_pcm_peak'],257)
  self.m['files'][2]['peak']=256.999/32767;self.save()
  with self.assertRaisesRegex(ValueError,'actual signed PCM'):check(self.path)
 def test_sub_lsb_peak_can_quantize_to_zero(self):
  n,_,frames=ORDER[2];b=wav(frames,0)
  (self.path/n).write_bytes(b);self.m['files'][2]['sha256']=sha(b)
  self.m['files'][2]['peak']=.25/32767;self.save()
  self.assertEqual(check(self.path)['files'][n]['signed_abs_pcm_peak'],0)
 def test_header_type_not_self_attested(self):
  p=self.path/'stone.wav';b=bytearray(p.read_bytes());b[22]=2;p.write_bytes(b)
  self.m['files'][3]['sha256']=sha(b);self.save()
  with self.assertRaisesRegex(ValueError,'header'):check(self.path)
if __name__=='__main__':unittest.main()
