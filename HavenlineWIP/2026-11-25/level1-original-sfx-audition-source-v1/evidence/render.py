import array, math, random, sys, wave
from pathlib import Path

FS=48000
PI=math.pi
ROOT=Path(__file__).resolve().parent

def voice(samples, delay, modes, decay, attack, gain, noise_gain=0, seed=0):
    r=random.Random(seed)
    start=round(delay*FS)
    low=0.
    slower=0.
    for i in range(start, len(samples)):
        t=(i-start)/FS
        u=(1-math.exp(-t/attack))*math.exp(-t/decay)
        f=sum(weight*math.sin(2*PI*(freq*t+drift*(1-math.exp(-t/.032)))) for freq,weight,drift in modes)
        white=r.uniform(-1,1)
        low=.64*low+.36*white
        slower=.94*slower+.06*low
        samples[i]+=gain*u*f + noise_gain*(low-slower)*(1-math.exp(-t/.0015))*math.exp(-t/.013)

def cue(duration):
    return [0.]*round(duration*FS)

def write(name,samples):
    pcm=array.array('h',(round(32767*v) for v in samples))
    assert len(pcm) and max(map(abs,pcm)) < 32767
    if sys.byteorder!='little':
        pcm.byteswap()
    with wave.open(str(ROOT/name),'wb') as w:
        w.setparams((1,2,FS,len(pcm),'NONE','not compressed'))
        w.writeframes(pcm.tobytes())
    q=[round(v*32767)/32768 for v in samples]
    dB=lambda v: 20*math.log10(max(v,1e-12))
    print(f'{name} {len(q)/FS:.3f}s {dB(max(map(abs,q))):.2f}dBFS peak {dB(math.sqrt(sum(v*v for v in q)/len(q))):.2f}dBFS RMS')

def shape(samples, targetpeak):
    last=round(.025*FS)
    for j in range(last):
        samples[-last+j]*=.5+.5*math.cos(PI*(j+1)/last)
    f=targetpeak/max(map(abs,samples))
    return [x*f for x in samples]

# Dry bevel-on-wood knock followed by a short, lower landing/deadened rustle.
pickup=cue(.186)
voice(pickup,.008,[(478,.84,-.40),(778,.29,-.25),(1292,.21,-.16),(2057,.08,-.15)],.026,.0025,.57,.11,38)
voice(pickup,.052,[(386,.86,-.24),(689,.23,-.03),(1567,.07,-.17)],.018,.0018,.20,.08,55)
pickup=shape(pickup,.31)

# A short mechanical seat, then an original warm three-note rising resonance.
furnace=cue(.684)
voice(furnace,.008,[(246,.70,-.28),(491,.39,-.19),(951,.41,-.26),(1668,.27,-.33)],.041,.0024,.43,.13,67)
voice(furnace,.096,[(392,.79,0),(784,.24,0),(1182,.13,.04),(1574,.045,0)],.080,.010,.22,.018,42)
voice(furnace,.174,[(493.88,.77,0),(987.76,.20,0),(1478,.13,.035)],.092,.014,.23,.010,16)
voice(furnace,.267,[(587.33,.80,0),(1174.66,.23,0),(1759,.11,.025)],.111,.012,.25,.013,75)
furnace=shape(furnace,.48)

write('Wood-Pickup.wav',pickup)
write('Furnace-Earned.wav',furnace)
# Audition at representative repeat intervals, then one build, with no loudness compensation.
mix=cue(2.800)
for offset,data in [(0.10,pickup),(.42,pickup),(.74,pickup),(1.55,furnace)]:
    i=round(offset*FS)
    mix[i:i+len(data)]=data
write('Havenline-Level-1-SFX-Audition.wav',mix)
