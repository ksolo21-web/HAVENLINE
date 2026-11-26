"""Render the two original non-looping Level 1 service sounds. No sampled recordings."""
from pathlib import Path
import hashlib
import json
import wave

import numpy as np
from scipy.signal import butter, sosfilt

rate=32000
rng=np.random.default_rng(20261126)
root=Path(__file__).parent

def time_axis(duration):
    return np.arange(round(duration*rate))/rate

def band_noise(count,low,high):
    filtering=butter(2,[low,high],fs=rate,btype='bandpass',output='sos')
    result=sosfilt(filtering,rng.normal(0,1,count))
    return result/np.sqrt(np.mean(result**2)+1e-14)

def place(track,onset,event):
    start=round(onset*rate)
    count=min(len(track)-start,len(event))
    if count>0:
        track[start:start+count] += event[:count]

def rise_decay(t,attack,release):
    return (-np.expm1(-t/attack))*np.exp(-t/release)

def sweep_tone(t,high,low,drop):
    return np.sin(2*np.pi*(low*t+(high-low)*drop*(-np.expm1(-t/drop))))

def paper_and_counter():
    # Leading bill flex, dry edge flutter against grain, a dull fingertip settling the stack.
    result=np.zeros(len(time_axis(.49)))
    for onset,duration,low,high,amp in [
        (.023,.14,900,5400,.072),(.074,.116,1550,6150,.086),(.156,.142,720,4750,.058)]:
        t=time_axis(duration)
        env=np.sin(np.pi*t/duration)**1.8
        rolling=.62+.38*np.sin(2*np.pi*(45*t+43*t*t)+rng.uniform(0,2*np.pi))**2
        place(result,onset,amp*env*rolling*band_noise(len(t),low,high))
    for onset,amp,pitch in [(.058,.070,920),(.101,.078,1220),(.152,.062,1070),(.183,.047,965)]:
        t=time_axis(.038)
        edge=band_noise(len(t),1900,8200)*rise_decay(t,.0005,.0038)
        flutter=sweep_tone(t,pitch,pitch*.51,.004)*rise_decay(t,.0006,.006)
        place(result,onset,amp*(.63*edge+.21*flutter))
    t=time_axis(.15)
    tap=(.43*sweep_tone(t,175,111,.012)+.26*sweep_tone(t,348,287,.009)
         +.16*band_noise(len(t),350,2010))*rise_decay(t,.0017,.021)
    place(result,.221,.25*tap)
    t=time_axis(.084)
    place(result,.242,.026*band_noise(len(t),560,3400)*rise_decay(t,.0035,.016))
    return result

def hot_griddle():
    # Damp first contact, bright irregular steam beads, low sizzle as moisture drains.
    t=time_axis(1.25)
    env=rise_decay(t,.049,.44)
    slow=np.interp(t,np.arange(0,1.33,.035),rng.uniform(.68,1.13,38))
    result=(.046*band_noise(len(t),1350,8100)+.018*band_noise(len(t),370,2200))*env*slow
    for _ in range(136):
        onset=.016+min(rng.exponential(.28),1.11)+rng.uniform(0,.01)
        d=rng.uniform(.009,.037);st=time_axis(d)
        center=rng.uniform(800,4200); micro=rise_decay(st,.00042,rng.uniform(.0013,.006))
        drop=sweep_tone(st,center*1.45,center,.0013)
        bubble=(.78*band_noise(len(st),1100,9200)+.32*drop)*micro
        place(result,onset,rng.uniform(.011,.063)*bubble*(1.1-.49*onset))
    ct=time_axis(.13)
    damp=(sweep_tone(ct,182,81,.011)*.44+band_noise(len(ct),210,1780)*.6)*rise_decay(ct,.004,.020)
    place(result,.014,.085*damp)
    return result

def store(name,signal,peak_db):
    fade=round(.018*rate)
    signal[-fade:]*=np.linspace(1,0,fade)
    signal=signal-np.mean(signal)
    signal[:round(.004*rate)]*=np.linspace(0,1,round(.004*rate))
    signal[-fade:]*=np.linspace(1,0,fade)
    signal*=10**(peak_db/20)/np.max(np.abs(signal))
    quantized=np.rint(signal*32767).astype('<i2')
    filename=root/(name+'.wav')
    with wave.open(str(filename),'wb') as file:
        file.setparams((1,2,rate,len(quantized),'NONE','not compressed'))
        file.writeframes(quantized.tobytes())
    with wave.open(str(filename),'rb') as file:
        assert file.getframerate()==rate and file.getnchannels()==1
        check=np.frombuffer(file.readframes(file.getnframes()),dtype='<i2')
        assert np.array_equal(check,quantized) and int(check[0])==int(check[-1])==0
    rms=float(np.sqrt(np.mean((quantized.astype(float)/32768.)**2)))
    return dict(file=filename.name,sha256=hashlib.sha256(filename.read_bytes()).hexdigest(),
                rate_hz=rate,channels=1,sample_format='signed 16-bit little endian PCM',
                seconds=len(quantized)/rate,peak_dbfs=round(float(peak_db),2),
                rms_dbfs=round(20*np.log10(rms),2))

if __name__=='__main__':
    files=[store('service_cash_paper',paper_and_counter(),-6.4),
           store('cook_griddle',hot_griddle(),-6.4)]
    (root/'Cue-verification.json').write_text(json.dumps({'origin':'Original deterministic synthesis. No outside sample or reference music used.','cues':files},indent=2)+'\n')
