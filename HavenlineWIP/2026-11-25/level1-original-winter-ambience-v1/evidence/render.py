from pathlib import Path
import json, subprocess, wave
import numpy as np
P=Path(__file__).resolve().parent
config=json.loads((P/'recipe.json').read_text())
fs=config["sample_rate_hz"]
n=config["layer_seconds"]*fs
rng=np.random.default_rng(config["seed"])
t=np.arange(n,dtype=float)/fs
phase=2*np.pi*t/config["layer_seconds"]
fr=np.fft.rfftfreq(n,1/fs)
def colored(lo,hi):
    f=np.maximum(fr,1.)
    band=(1+(lo/f)**6)**-.5*(1+(f/hi)**8)**-.5*(1+f/550)**-.63
    band[0]=0.
    return np.fft.irfft(np.fft.rfft(rng.standard_normal(n))*band,n)
def norm(x,peak):
    y=x-x.mean()
    return y*(10**(peak/20))/np.abs(y).max()
wind=norm(colored(*config["wind"]["band_hz"])*(.75+.13*np.cos(phase+.2)+.065*np.sin(2*phase+1.3)+.04*np.cos(3*phase+.8)),config["wind"]["target_peak_dbfs"])
crack=.35*colored(*config["hearth"]["band_hz"])*(.85+.09*np.cos(phase-1.2)+.04*np.sin(3*phase+1.6))
def gate(x):
    return .5-.5*np.cos(np.pi*np.clip(x,0.,1.))
# No discontinuous impulses: all local grains have zero-amplitude edge, band-limited
# carrier uses only original oscillators; last event wraps over boundary on purpose.
for at,gain in [(0.51,.26),(1.18,.49),(1.62,.23),(2.24,.33),(2.29,.15),(3.12,.43),
                (3.87,.28),(4.98,.36),(5.64,.41),(5.984,.15)]:
    start=int(round(fs*at))
    j=np.arange(int(fs*.065))
    dt=j/fs
    f=float(rng.uniform(290,590))
    p=float(rng.uniform(0,2*np.pi))
    v=(np.sin(2*np.pi*dt*f+p)+.45*np.sin(2*np.pi*dt*(2.41*f)+p/2)
       +.18*np.sin(2*np.pi*dt*(3.8*f)-p)) * gate(dt/.0025)*np.exp(-dt/.013)*gate((.065-dt)/.011)
    crack[(start+j)%n]+=gain*v
crack=norm(crack,config["hearth"]["target_peak_dbfs"])
cfg=config["transition"]
j=np.arange(round(cfg["audition_seconds"]*fs))
tt=j/fs
gap_begin=cfg["first_segment_end_s"]
cold_start=cfg["cold_paid_start_s"]
first=gate(tt/.26)*gate((gap_begin-tt)/.30)
cold=gate((tt-cold_start)/cfg["cold_fade_seconds"])*gate((cfg["audition_seconds"]-tt)/.28)
phase_idx=(j+fs//3)%n
cold_idx=(j-round(cold_start*fs)+2*fs)%n
earned=gate((tt-cfg["earned_crossfade_start_s"])/cfg["earned_crossfade_seconds"])
w_preview=(first*wind[phase_idx]+cold*wind[cold_idx])*.86
h_preview=(first*earned*crack[phase_idx]+cold*crack[cold_idx])*.79
demo=w_preview+h_preview
assert np.all(h_preview[tt<cfg["earned_crossfade_start_s"]]==0)
assert np.all(demo[(tt>=gap_begin)&(tt<=cold_start)]==0)
assert np.max(np.abs(wind)+np.abs(crack)) < .26
def db(v):
    return round(float(20*np.log10(max(v,1e-15))),2)
def put(name,vals,loop):
    q=np.rint(vals*32767).astype("<i2")
    data=q.tobytes()
    with wave.open(str(P/name),'wb') as dst:
        dst.setparams((1,2,fs,len(q),'NONE','not compressed'))
        dst.writeframes(data)
    cmd=["ffmpeg","-nostdin","-v","error"]
    if loop: cmd+=["-stream_loop","2"]
    cmd+=["-i",str(P/name),"-f","s16le","-acodec","pcm_s16le","pipe:1"]
    b=subprocess.check_output(cmd)
    assert b==data*(3 if loop else 1)
    result={"seconds":len(vals)/fs,"peak_dbfs":db(np.max(np.abs(q.astype(float)))/32768),
            "rms_dbfs":db(np.sqrt(np.mean(vals**2))),"verified_exact_pcm_repeats":3 if loop else 1}
    if loop:
        d=np.abs(np.diff(q.astype(int)))
        wrap=abs(int(q[0])-int(q[-1]))
        local=np.concatenate((d[-40:],d[:40]))
        assert wrap <= local.max()
        result.update({"wrap_step_pcm":wrap,"neighbor_max_step_pcm":int(local.max()),"internal_max_step_pcm":int(d.max())})
    return result
items={name:put(name,x,loop) for name,x,loop in [
    ("Havenline-Winter-Air-Loop.wav",wind,True),
    ("Havenline-Earned-Hearth-Crackle-Loop.wav",crack,True),
    ("Havenline-Ambience-Fresh-Earned-Restore-Test.wav",demo,False)]}
res={"files":items,"layer_pair_peak_ceiling_linear":round(float(max(np.abs(wind))+max(np.abs(crack))),5),
     "demo_pre_earn_hearth_samples_nonzero":int(np.count_nonzero(h_preview[tt<cfg["earned_crossfade_start_s"]])),
     "demo_silence_gap_samples_nonzero":int(np.count_nonzero(demo[(tt>=gap_begin)&(tt<=cold_start)])),
     "build_success_asset_used":False,"gameplay_bind":False}
(P/"measurements.json").write_text(json.dumps(res,indent=2)+"\n")
print(json.dumps(res,indent=2))
