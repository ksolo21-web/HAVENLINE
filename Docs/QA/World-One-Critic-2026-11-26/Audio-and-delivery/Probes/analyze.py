import numpy as np, scipy.signal as sig, json,pathlib,subprocess as sp,hashlib
from fractions import Fraction
from functools import lru_cache
from PIL import Image
import io
P=pathlib.Path
out=P('/workspace/shared/downloads/Havenline/critic-95/Audio-and-delivery')
base=out.parent.parent
local=P('/tmp/hl-critic-audio')
game=P('/dev/shm/havenline-world/Game')
db='/dev/shm/havenline-world/published.git'
vid=base/'world-one-mining/Metal-ore-five-second-return.mp4'
mixfile=base/'world-one/Gameplay/World-One-Gameplay.mp4'
fs=12000
def hashf(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probe(p):
 return json.loads(sp.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,codec_name,width,height,avg_frame_rate,nb_frames,duration,sample_rate,channels','-of','json',str(p)]))['streams']
def snd(p,channels=1,rate=fs):
 data=sp.check_output(['ffmpeg','-loglevel','error','-i',str(p),'-map','0:a:0','-f','f32le','-ac',str(channels),'-ar',str(rate),'-'])
 return np.frombuffer(data,dtype=np.float32).reshape(-1,channels)
def dbfs(n):return round(float(20*np.log10(max(float(n),1e-12))),3)
def levels(x):return {'peak_dbfs':dbfs(abs(x).max()),'rms_dbfs':dbfs(np.sqrt(np.mean(x*x))),'rail_samples':int((abs(x)>=.99997).sum())}
def filtered(x):return sig.sosfilt(sig.butter(3,[650,4750],btype='bandpass',fs=fs,output='sos'),x)
@lru_cache(150)
def ref(n,p):
 a=snd(game/'assets/audio'/n).ravel()
 pitched=np.interp(np.arange(0,len(a),p),np.arange(len(a)),a)
 return filtered(pitched)[:int(.12*fs)]
def search(x,y,t,left=.10,right=.15):
 t0=max(0,int((t-left)*fs))
 signal=x[t0:min(len(x),int((t+right)*fs)+len(y))]
 if len(signal)<len(y):return 0,0
 coeff=sig.correlate(signal,y,mode='valid')/np.sqrt(np.maximum(1e-12,np.convolve(signal**2,np.ones(len(y)),mode='valid')*np.sum(y*y)))
 idx=int(np.argmax(coeff));return float(coeff[idx]),round((idx+t0)/fs,5)
def metadata(c):return c if c!= 'regrow_stone' else c
roll=json.loads((local/'ore.json').read_text()); film=json.loads(vid.with_suffix('.json').read_text());trans=json.loads((local/'transitions.json').read_text())
record={}
for label,p,trim in [('fresh_replay',local/'ore.avi',0),('delivered_mining_film',vid,13)]:
 raw=snd(p,2);x=filtered(raw.mean(axis=1)); rows=[]
 for v in roll['cue_started']:
  if v['cue'] not in ('impact_stone','deplete_stone','regrow_stone','drop_stone','equip_pickaxe'):continue
  name=P(v['asset']).name
  t=(v['pframe']-trim)/30
  val,start=search(x,ref(name,v['pitch']),t,.1,.18)
  rows.append(dict(cue=v['cue'],asset=name,actual_pitch=v['pitch'],logical_seconds=round(t,5),best_sample_start_seconds=start,latency_ms=round((start-t)*1000,2),normalized_correlation=round(val,3)))
 record[label]={'sha256':hashf(p),'levels':levels(raw),'streams':probe(p),'samples':rows}
raw=snd(local/'transitions.avi',2)
frames={}
for i in (0,48,60,120,168,180,240,288,300,360,390,408,420,444,468):
 a=next(b for b in trans if b['tick']==i) if i%12==0 else min(trans,key=lambda r:abs(r['tick']-i))
 frames[str(a['tick'])]=a
record['mixer_state_fixture']={'states':frames,'states_are_requested_diagnostic_inputs':True,'levels':{k:levels(raw[int(v[0]*fs):int(v[1]*fs)]) for k,v in dict(field=(1.1,1.6),camp=(4.8,5.7),threat=(8.3,9.7),field_return=(11.4,12.7),mute=(13.3,13.8),unmute=(14.4,15.5)).items()}}
record['native_mining_telemetry']=roll
timing=json.loads((base/'world-one/Gameplay/World-One-Gameplay.json').read_text())
histevent=json.loads((base/'world-one/Gameplay/Evidence/Full-game-events.json').read_text())
mx=filtered(snd(mixfile,2).mean(axis=1)); old=[]
for name in ('impact_wood','impact_stone','purchase','gate','gate_latch','tower_fire','enemy_attack','boss_arrival','equip_pickaxe','spend_wood','step_snow','step_camp'):
 matches=[]
 for ch in timing['chapters']:
  if ch['originating_run']!='film-e978a44b':continue
  t0=ch['source_start_s']; t1=t0+ch['frames']/24
  for ev in histevent:
   if ev['event']!=name or not t0+.1<ev['t']<t1-.16:continue
   t=ev['t']-t0+ch['reel_start_s']
   for f in (game/'assets/audio').glob(name+'*.wav'):
    for pitch in (1,.968,1.026):
     v,at=search(mx,ref(f.name,pitch),t,.55,.35);matches.append((v,at,f.name,pitch,ch['title'],round(t,3)))
 if matches:old.append(dict(zip(['peak_match','film_time','asset','pitch','chapter','approx_subject_time'],max(matches))))
record['historical_world_earliest_main']={'commit':'e978a44b1b112bb598f9ec1724b3616ec80e6970','samples':old,'method':'For each cue with an in-cut gameplay event, report strongest bank-template match across candidate imported variants in the nearby film. This establishes sampled sound identities, not independent editing quality.'}
refdir=base/'field-loop/References/Locked-sequences';led=json.loads((refdir/'source-ledger.json').read_text())
refrows=[]
for c in led['clips']:
 p=refdir/c['mp4'];ss=sp.check_output(['git','--git-dir='+db,'show',c['file_at_commit']])
 assert hashlib.sha256(ss).hexdigest()==c['sheet_sha256']
 assert hashf(p)==c['sha256']
 im=Image.open(io.BytesIO(ss)).convert('RGB')
 for e in c['samples']:
  x,y=e['sheet_cell_xy']; cell=im.crop((x,y,x+260,y+340))
  assert hashlib.sha256(cell.tobytes()).hexdigest()==e['sheet_cell_RGB_sha256']
 refrows.append(dict(file=p.name,streams=probe(p),file_sha256=hashf(p),cells=len(c['samples']),original_sha256=c['video_source_sha256']))
record['locked_refs']=refrows
record['source_film_streams']={str(p.relative_to(base)):probe(p) for p in [vid,mixfile,base/'gait-ultra/Havenline-Gait-Ultra-4K60.mp4']}
(out/'Audio-footage-and-reference-audit.json').write_text(json.dumps(record,indent=2)+'\n')
