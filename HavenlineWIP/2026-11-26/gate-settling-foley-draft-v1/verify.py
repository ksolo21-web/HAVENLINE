from hashlib import sha256
from pathlib import Path
from math import log10,sqrt
import json,struct,subprocess,tempfile,wave,sys
here=Path(__file__).resolve().parent
p=here/'gate-settle-draft.wav'
def sig(data):return sha256(data).hexdigest()
h=here.parent/'hvn-l1-gate-cue-handoff-contract-v1/SHA256SUMS'
assert sig(h.read_bytes())=='165dbc683955748869ac323b41f98fa0db5b49282e3307f1f66f322883c0d2e1'
with wave.open(str(p),'rb') as f:
 assert (f.getnchannels(),f.getframerate(),f.getsampwidth(),f.getnframes())==(1,48000,2,15360)
 raw=f.readframes(15360)
s=struct.unpack('<15360h',raw); active=[i for i,x in enumerate(s) if x]
peak=max(map(abs,s)); rms=sqrt(sum(x*x for x in s)/len(s))
assert len(raw)==30720 and 0<peak<20000 and not any(s[:480]) and not any(s[-1920:]) and abs(sum(s)/len(s))<=10
ff=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','a','-show_entries','stream=codec_name,sample_rate,channels,duration','-of','json',str(p)]))['streams'][0]
assert ff=={'codec_name':'pcm_s16le','sample_rate':'48000','channels':1,'duration':'0.320000'}
decoded=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(p),'-f','s16le','-acodec','pcm_s16le','-'])
assert raw==decoded
with tempfile.TemporaryDirectory() as d:
 out=Path(d)/'regen.wav'
 subprocess.run([sys.executable,str(here/'synth.py'),str(out)],check=True)
 assert p.read_bytes()==out.read_bytes()
print(json.dumps({'scope':'standalone original offline procedural dry foley draft','duration_s':.32,'format':ff,'file_sha256':sig(p.read_bytes()),'bytes':p.stat().st_size,'decoded_pcm_sha256':sig(raw),'sample_peak_dbfs':20*log10(peak/32768),'duration_rms_dbfs':20*log10(rms/32768),'dc_average_lsb':sum(s)/len(s),'clipped_samples':sum(abs(x)>=32767 for x in s),'first_nonzero_s':active[0]/48000,'last_nonzero_s':active[-1]/48000,'separately_decoded_and_reproduced_byte_exact':True,'listened':False,'mixed_or_wired':False,'approved':False},indent=2))
