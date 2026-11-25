from pathlib import Path
import hashlib, json, math, struct, subprocess, wave

HERE = Path(__file__).resolve().parent
RATE = 24_000
N = RATE * 17//4
ASSETS = {
    "pickup": ("../hvn-l1-audio-original-cue-sketch-v1/Wood-Pickup.wav", "f7b3547a9e48c2c56c58f0f37fe05ffcde191034f24fcf02bcee6865f5fa22d8"),
    "hearth": ("../hvn-l1-audio-original-cue-sketch-v1/Furnace-Earned.wav", "a3fc0ca7164a5e7f459e62cc25edee485f2293740df3541c5a8d37937f11b395"),
    "music": ("../hvn-l1-music-direction-sketch-v1/Havenline-Snow-Between-Embers-Loop.wav", "db21a30c25f7b80a729a88027d5a8e33fbca76f09a89275b16c84970b266084a")
}

def command(args, data=None):
    return subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *args], input=data, stdout=subprocess.PIPE, check=True).stdout

def floats(b):
    return [x[0] for x in struct.iter_unpack("<f", b)]

def load_asset(key):
    path, expected = ASSETS[key]
    p=(HERE/path).resolve()
    assert hashlib.sha256(p.read_bytes()).hexdigest()==expected, key
    return floats(command(["-i",str(p),"-ar",str(RATE),"-ac","1","-f","f32le","pipe:1"]))

def band(x):
    return floats(command(["-f","f32le","-ar",str(RATE),"-ac","1","-i","pipe:0","-af",
                           "highpass=f=250,lowpass=f=4000","-f","f32le","pipe:1"],
                          struct.pack('<'+'f'*len(x),*x)))

def rms(a):
    return math.sqrt(sum(x*x for x in a)/len(a))

def db(x):
    return round(20*math.log10(max(x,1e-15)),2)

def raised(u):
    return .5-.5*math.cos(math.pi*max(0.,min(1.,u)))

SCHEDULE = [(0.55,"pickup"),(0.84,"pickup"),(1.11,"pickup"),(1.30,"pickup"),(2.355,"hearth")]
STRESS = [(0.55,"pickup"),(0.565,"pickup"),(0.58,"pickup"),(0.84,"pickup"),(1.11,"pickup"),(1.30,"pickup"),(2.355,"hearth")]
assets = {k:load_asset(k) for k in ASSETS}
music = [v*min(raised(i/RATE/.065),raised((N-1-i)/RATE/.140)) for i,v in enumerate(assets["music"][:N])]
# Identical sample-aligned dry bus and silence at ambience in both versions.
def parts(schedule, depth_db, linear_boost):
    sfx = [0.]*N
    duck = [1.]*N
    drop=1-10**(depth_db/20)
    for at,k in schedule:
        loc=round(at*RATE)
        for j,x in enumerate(assets[k]):
            sfx[loc+j]+=x
        full=.115 if k=="pickup" else .45
        for i in range(round((at-.025)*RATE), min(N,round((at+full+.24)*RATE))):
            t=i/RATE-at
            shape=raised((t+.025)/.025) if t<=0 else raised((full+.24-t)/.24)
            duck[i]=min(duck[i],1-drop*shape)
    m=[i*j*linear_boost for i,j in zip(music,duck)]
    s=[i*linear_boost for i in sfx]
    return m,s,[a+b for a,b in zip(m,s)]

def report(m,s,mix):
    a,b=band(m),band(s)
    windows=[]
    for at,k in SCHEDULE:
        length=.145 if k=="pickup" else .49
        start=round(at*RATE);stop=start+round(length*RATE)
        windows.append({"position_sec":at,"cue":k,"window_sec":length,
                        "band_limited_sfx_vs_music_db":db(rms(b[start:stop])/rms(a[start:stop]))})
    return {"peak_linear":round(max(map(abs,mix)),5),"sample_peak_dbfs":db(max(map(abs,mix))),"phone_band_cue_windows":windows}

a=parts(SCHEDULE,0,1)
b=parts(SCHEDULE,-6,1)
stress={}
for key,d in (("A",0),("B",-6)):
    # +20% level on both available buses under the stacked pickup stress.
    m,s,z=parts(STRESS,d,1.2)
    peak=max(map(abs,z))
    assert peak <= .8
    stress[key]={"sample_peak_dbfs":db(peak),"peak_linear":round(peak,5),
                 "unused_full_scale_fraction":round(1-peak,5)}
combined=a[2]+[0.]*(RATE//2)+b[2]
assert max(map(abs,combined)) <= .8
with wave.open(str(HERE/'Havenline-L1-Cue-Balance-AB.wav'),'wb') as w:
    w.setparams((1,2,RATE,0,"NONE","not compressed"))
    w.writeframes(struct.pack('<'+'h'*len(combined),*(round(x*32767) for x in combined)))
data={"A_native_sketch_levels_no_duck":report(*a),"B_same_sources_6dB_music_duck":report(*b),
      "stress_1_2x_available_bus_gain_with_near_overlap":stress,
      "notes":"Ambience silent and accounted separately, no actual game, unknown subjective phone masking."}
(HERE/'measurements.json').write_text(json.dumps(data,indent=2)+'\n')
