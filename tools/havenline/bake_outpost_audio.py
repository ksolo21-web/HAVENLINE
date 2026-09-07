#!/usr/bin/env python3
"""Bake original deterministic game sound. No downloads, voices, or licensed samples.
WAVs are generated build outputs; this script is the reproducible source.
"""
import array, hashlib, json, math, random, wave
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2] / 'HavenlineGodot' / 'assets' / 'audio'
RATE = 22050

def bake(name, seconds):
    rng = random.Random(9171 + sum(map(ord, name)))
    samples=[]; low=0.; lower=0.; crackle=0.
    for i in range(int(RATE*seconds)):
        t=i/RATE; noise=rng.uniform(-1.,1.)
        low=low*.976+noise*.024; lower=lower*.996+noise*.004
        if name=='wind':
            value=(low*.82+lower*2.1)*(.72+.2*math.sin(t*.74)+.08*math.sin(t*1.47))
        elif name=='fire':
            if rng.random()<.0014: crackle=rng.uniform(.2,.8)
            crackle*=.86
            value=low*.6+noise*crackle
        elif name=='wood':
            value=(noise*.45+math.sin(2*math.pi*(166-70*t)*t)*.48)*math.exp(-t*24.)
        elif name=='stone':
            value=(noise*.45+math.sin(2*math.pi*1623*t)*.16+math.sin(2*math.pi*2471*t)*.10)*math.exp(-t*20.)
        elif name=='transfer':
            value=math.sin(2*math.pi*(690*t-320*t*t))*math.exp(-t*23.)*.30+noise*math.exp(-t*65.)*.16
        else:
            value=0.
            for j,freq in enumerate([523.25,659.25,783.99,1046.5]):
                age=t-j*.095
                if age>=0: value+=math.sin(2*math.pi*freq*age)*math.exp(-age*3.4)*min(1.,age/.01)*.115
        edge=min(1.,t/.015,(seconds-t)/.04)
        samples.append(value*edge)
    peak=max(abs(x) for x in samples); gain=min(2.4,.72/max(peak,1e-9))
    pcm=array.array('h',(int(max(-.98,min(.98,x*gain))*32767) for x in samples))
    target=ROOT/(name+'.wav')
    with wave.open(str(target),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(RATE);out.writeframes(pcm.tobytes())
    return {'file':target.name,'seconds':seconds,'sample_rate':RATE,'peak':peak*gain,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}

if __name__=='__main__':
    ROOT.mkdir(parents=True,exist_ok=True)
    records=[bake(name,duration) for name,duration in [('wind',12.),('fire',12.),('wood',.28),('stone',.32),('transfer',.22),('upgrade',1.65)]]
    (ROOT/'bake-manifest.json').write_text(json.dumps({'origin':'original deterministic synthesis','listening_review':'not certified','files':records},indent=2)+'\n')
    print(json.dumps(records))
