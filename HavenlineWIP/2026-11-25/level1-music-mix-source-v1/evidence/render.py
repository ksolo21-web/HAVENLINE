from pathlib import Path
from array import array
import json, math, sys, wave
p=Path(__file__).resolve().parent
score=json.loads((p/'score.json').read_text())
fs=48000
seconds_per_beat=60/score['bpm']
n=round(fs*seconds_per_beat*score['beats'])
out=[0.]*n
tau=2*math.pi
freq=lambda m: 440*2**((m-69)/12)
def envelope(t, span, a, rel):
    if t<=0 or t>=span: return 0.
    if t<a: return (0.5-0.5*math.cos(math.pi*t/a))
    if t>span-rel: return (0.5-0.5*math.cos(math.pi*(span-t)/rel))
    return 1.
def note(beat, length, midi, gain, instrument):
    duration=seconds_per_beat*length
    start=round(seconds_per_beat*fs*beat)
    f=freq(midi)
    if instrument=='keys':
        a=.024; release=.23; span=duration+.17
        partials=((1,.74),(2,.23),(3.003,.052),(4.07,.019))
    else:
        a=.52; release=.64; span=duration+.54
        partials=((1,.87),(2,.22),(3,.034))
    for j in range(round(span*fs)):
        t=j/fs
        env=envelope(t,span,a,release)
        w=tau*f*t
        if instrument=='keys':
            env*=math.exp(-t/.40)
            v=sum(level*math.sin(ratio*w) for ratio,level in partials)
        else:
            v=sum(level*math.sin(ratio*w+.13*math.sin(tau*.81*t)) for ratio,level in partials)
            env*=.91+.09*math.cos(tau*.62*t)
        out[(start+j)%n]+=v*gain*env
for beat,length,chord in score['pad']:
    for i,m in enumerate(chord):
        note(beat,length,m,[.105,.064,.049][i],'pad')
for beat,length,midi,velocity in score['keys']:
    note(beat,length,midi,.250*velocity,'keys')
# Add phase-locked quiet air motion; Hz are multiples of 1/duration.
for j in range(n):
    t=j/fs
    out[j]+=.0054*sum(a*math.sin(tau*h*t) for h,a in ((294.,.5),(440.1,.23),(610.3,.14)))*(.55+.45*math.cos(tau*.3*t))
mean=sum(out)/n
out=[v-mean for v in out]
scale=(10**(-13/20))/max(map(abs,out))
q=[round(v*scale*32767) for v in out]
pcm=array('h',q)
if sys.byteorder!='little':
    pcm.byteswap()
with wave.open(str(p/'Havenline-Snow-Between-Embers-Loop.wav'),'wb') as w:
    w.setparams((1,2,fs,n,'NONE','not compressed'))
    w.writeframes(pcm.tobytes())
db=lambda v:20*math.log10(max(v,1e-15))
d=[abs(q[i]-q[i-1]) for i in range(1,n)]
print(f'duration_s={n/fs:.6f} sample_peak_dbfs={db(max(map(abs,q))/32768):.2f} rms_dbfs={db(math.sqrt(sum(v*v for v in q)/n)/32768):.2f}')
print(f'seam sample_delta={abs(q[0]-q[-1])} local_deltas={d[-5:]+d[:5]} cue_internal_max_delta={max(d)}')
print(f'loop duration{n}, no reset/fade; end envelopes wrap and air Hz exactly periodic')
assert abs(q[0]-q[-1]) <= max(d[-5:]+d[:5])
assert max(map(abs,q)) < 32767
