"""Render original Havenline field foley and two arrangements of Alfred's 96 BPM motif.

No recordings, soundfonts, web assets, or generative services are required.
Inputs are the five previously checksum-verified Havenline sounds in the QA archive.
"""
from pathlib import Path
import argparse
import math
import shutil
import json
import hashlib
import numpy as np
from scipy import signal
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'assets/audio'
SOURCES = BANK
SR = 32000
TAU = 2*np.pi
rng = np.random.default_rng(11262026)


def time(seconds):
    return np.arange(round(seconds*SR))/SR


def noise(t, lo, hi):
    sos = signal.butter(2, [lo,hi], fs=SR, btype='bandpass', output='sos')
    y = signal.sosfilt(sos, rng.standard_normal(len(t)))
    return y / max(.05, float(np.std(y)))


def edges(t, attack, release):
    return np.minimum(1,t/attack)**2 * np.minimum(1,np.maximum(0,(t[-1]-t)/release))**2


def impact(t, modes, decay, grain, band):
    phases = rng.uniform(-.65,.65,len(modes))
    body = sum(amp*np.exp(-t/(decay/(1+i*.65))) * np.sin(TAU*f*t+p)
               for i,((f,amp),p) in enumerate(zip(modes,phases)))
    transient = grain * noise(t,*band)*np.exp(-t/.013)
    return (body+transient)*edges(t,.0015,.012)


def wood(pitch=1, length=.27):
    t = time(length)
    return impact(t, [(pitch*f,a) for f,a in [(176,.69),(362,.52),(703,.29),(1405,.12)]],.068,.35,(420,5200))


def stone(pitch=1, length=.34):
    t = time(length)
    return impact(t,[(pitch*f,a) for f,a in [(523,.30),(886,.51),(1771,.22),(2940,.14),(4180,.08)]],.107,.48,(1100,6900))


def thump(seconds=.26, freq=63):
    t=time(seconds)
    return np.sin(TAU*(freq*t+.68*(1-np.exp(-t/.025)))) * np.exp(-t/.068)*edges(t,.003,.015)


def rub(seconds,lo,hi,attack,concentration):
    t=time(seconds)
    env=edges(t,attack,.025)*np.exp(-np.maximum(t-attack,0)/concentration)
    return noise(t,lo,hi)*env


def grit(seconds,number,low=900,high=5800):
    """Tiny pressure fractures interleaved with a grain bed, rather than a white-noise burst."""
    y=np.zeros(len(time(seconds)))
    for pos in sorted(rng.uniform(.002,seconds-.024,number)):
        t=time(rng.uniform(.006,.022))
        grain=noise(t,low,high)*np.exp(-t/.0045)*edges(t,.001,.003)
        add(y,pos,grain,rng.uniform(.10,.38)*(1-pos/seconds))
    return y


def add(out,at,sample,amp=1):
    i=round(at*SR)
    k=min(len(sample),len(out)-i)
    if k>0:
        out[i:i+k] += sample[:k]*amp


def scene(seconds,parts):
    y=np.zeros(len(time(seconds)))
    for at,sound,vol in parts: add(y,at,sound,vol)
    return y


def swish(seconds=.28,lo=200,hi=4900):
    t=time(seconds); sweep=(.23+2.6*t/seconds)
    env=np.sin(np.pi*t/seconds)**1.4 * np.exp(-((t/seconds-.56)/.37)**2)
    return (.64*noise(t,lo,1000)+.24*noise(t,1400,hi)*sweep)*env


def vocal(seconds, start, end, shape, breath=.16):
    """Original inharmonic creature/effort source through moving resonant formants."""
    t=time(seconds); phase=TAU*np.cumsum(np.linspace(start,end,len(t))*(1+.045*np.sin(TAU*29*t)))/SR
    src=np.tanh(2.2*(np.sin(phase)+.38*np.sin(2*phase)+.16*np.sin(3*phase)))
    src*=.83+.17*np.sin(TAU*(start*.42)*t)
    voice=np.zeros_like(t)
    for f,bw,weight in shape:
        filt=signal.iirpeak(f,f/bw,fs=SR); voice+=weight*signal.lfilter(*filt,src)
    return (voice+breath*noise(t,180,1450))*edges(t,.025,.09)*np.exp(-t/(seconds*.57))


def write(name,sound,peak=.67):
    x=signal.sosfilt(signal.butter(2,32,btype='highpass',fs=SR,output='sos'),sound,axis=0)
    x[-min(len(x),240):]*=np.linspace(1,0,min(len(x),240)).reshape((-1,)+(1,)*(x.ndim-1))
    x*=peak/max(.0001,np.abs(x).max())
    wavfile.write(BANK/(name+'.wav'),SR,np.int16(np.rint(x*32767)))


def add_recovered():
    records=json.loads((ROOT/'tools/audio/alfred-cues.json').read_text())
    for item in records:
        p=SOURCES / item['output']
        if not p.exists():
            p=next(SOURCES.rglob(item['source']))
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Source SHA mismatch: '+p.name)
        if p.resolve() != (BANK/item['output']).resolve():
            shutil.copyfile(p,BANK/item['output'])


def steps():
    for i in range(3):
        snow=scene(.30,[(0,thump(.22,79+i*6),.57),(.006,rub(.22,210,1060,.022,.072),.37),
                       (.013,grit(.19,55),.84),(.067,rub(.19,1300,4400,.026,.048),.24)])
        write('step_snow_'+str(i+1),snow)
        floor=scene(.25,[(.003,wood(.72+i*.04),.75),(0,thump(.23,92+i*3),.59),(.047,rub(.12,270,1650,.012,.038),.22)])
        write('step_camp_'+str(i+1),floor)
    for i in range(2):
        write('swing_'+str(i+1),swish(.23+i*.035,165,4800))
        write('impact_wood_'+str(i+1),scene(.32,[(0,wood(.90+i*.14),1),(.003,thump(.22,89),.75),(.021,grit(.16,23,1100,5400),.55)]))
        write('impact_stone_'+str(i+1),scene(.39,[(0,stone(.93+i*.09),.91),(.011,thump(.21,134),.64),(.067,stone(1.66,.13),.19)]))
    write('drop_wood',scene(.48,[(0,wood(.78),1),(.028,thump(.26,83),.50),(.13,wood(.91,.2),.37),(.25,grit(.16,13),.3)]))
    write('drop_stone',scene(.52,[(0,stone(.64),.81),(.013,thump(.24,78),.61),(.12,stone(.83),.48),(.20,stone(1.5,.22),.25)]))
    write('deplete_wood',scene(.91,[(0,rub(.39,90,1800,.12,.25),.53),(.165,wood(1.32),.73),(.215,wood(.72),.87),(.24,grit(.50,95,350,5900),.79),(.46,thump(.35,47),.96),(.52,rub(.35,230,1900,.09,.11),.59)]))
    write('deplete_stone',scene(.78,[(0,stone(.58),.92),(.035,thump(.31,54),.87),(.07,grit(.57,95,350,5000),.85),
                (.11,stone(.80),.60),(.19,stone(1.11),.38),(.28,stone(1.44),.24),(.43,stone(.98),.18)]))
    strap=rub(.21,350,2800,.028,.056)
    write('carry',scene(.28,[(0,strap,.73),(.055,wood(.69,.12),.3),(.10,wood(.96,.14),.20)]))
    write('pickup_full',scene(.42,[(0,strap,.54),(.032,wood(.92),.58),(.087,wood(1.30),.47),(.12,rub(.24,450,2500,.023,.079),.55)]))
    for k,base in [('wood',wood),('stone',stone)]:
        write('deposit_'+k,scene(.38,[(0,swish(.103,270,2650),.24),(.085,base(.90),.91),(.103,thump(.19,112),.52),(.16,base(1.33,.15),.19)]))
        write('spend_'+k,scene(.25,[(0,base(1.32,.18),.47),(.052,base(.66,.17),.64),(.07,rub(.15,450,2200,.013,.05),.45)]))
    def soft_land(scale):
        return scene(.37,[(0,thump(.25,71*scale),1),(.008,rub(.19,150,1300,.013,.048),.54),(.05,rub(.18,550,2400,.023,.055),.28)])
    write('drop_meat',soft_land(.88))
    write('deposit_meat',scene(.43,[(0,swish(.095,190,2800),.31),(.079,soft_land(1.19),.85)]))
    write('spend_meat',scene(.27,[(0,rub(.2,330,1900,.021,.064),.4),(.043,thump(.2,116),.78),(.085,wood(.67,.14),.18)]))
    write('meat',scene(.34,[(0,rub(.17,370,2650,.023,.066),.47),(.047,thump(.25,103),.68),(.083,wood(1.48,.13),.21)]))
    write('build',scene(.90,[(0,wood(.65),.91),(.13,wood(1.03),.73),(.21,grit(.41,50,400,3450),.72),(.35,stone(.72),.82),(.42,thump(.37,49),.88)]))
    write('rise',scene(.74,[(0,swish(.51,85,2600),.59),(.17,rub(.48,220,1680,.09,.2),.33),(.48,thump(.24,74),.47)]))
    t=time(.38); creak=np.sin(TAU*(155*t+11*t*t)+.96*np.sin(TAU*380*t))*(.6+.4*np.sin(TAU*13*t))*edges(t,.024,.08)
    write('gate',scene(.56,[(0,wood(.62,.16),.46),(.055,creak,.46),(.1,rub(.34,195,1500,.05,.11),.29)]))
    write('gate_latch',scene(.25,[(0,wood(.69),.93),(.039,stone(1.36,.14),.22),(.054,wood(.91,.15),.33)]))
    dog=[(470,150,1),(980,230,.8),(1930,360,.49)]
    write('approach',scene(.70,[(0,vocal(.55,89,69,dog),.99),(.12,rub(.31,240,1040,.07,.11),.27),(.35,thump(.21,71),.32)]))
    write('enemy_attack',scene(.45,[(0,vocal(.35,143,78,dog,.23),1),(.043,swish(.27,205,3250),.72),(.22,grit(.17,27),.33)]))
    write('player_attack',scene(.34,[(0,rub(.17,280,1450,.029,.056),.37),(.045,swish(.26,310,6300),.93),(.09,vocal(.17,130,98,[(620,90,.8),(1270,170,.55)],.10),.31)]))
    write('hit',scene(.34,[(0,thump(.25,75),.85),(.002,wood(.67,.19),.40),(.012,rub(.20,210,1520,.014,.052),.52)]))
    write('player_hurt',scene(.42,[(0,thump(.25,72),.67),(.014,vocal(.35,148,92,[(620,160,1.2),(1520,240,.69),(2370,350,.4)],.13),1)]))
    write('defeat',scene(.85,[(0,vocal(.51,115,55,dog,.12),.85),(.25,rub(.35,160,970,.10,.15),.60),(.36,thump(.35,43),.95),(.4,grit(.30,40),.32)]))
    write('reset',scene(.59,[(0,rub(.31,250,1080,.05,.11),.45),(.24,rub(.31,210,1450,.04,.17),.34),(.30,thump(.21,92),.33)]))


def music():
    # Interlocking live arrangements follow Snow Between Embers' 16-beat changes.
    beat=60/96
    chords=[[50,57,64],[46,53,60],[48,55,62],[45,52,62]]
    def pluck(midi,span):
        t=time(span);f=440*2**((midi-69)/12)
        body=sum(np.sin(TAU*f*h*(1+.00013*h*h)*t)*np.exp(-t*(2.6+h*.94))*np.sin(.59*h)/(h**.76)
                 for h in range(1,10))
        return (body+.08*noise(t,1200,4800)*np.exp(-t/.009))*edges(t,.006,.06)
    def bow(midi,span):
        t=time(span);f=440*2**((midi-69)/12)
        vibrato=.0008*np.sin(TAU*4.8*t)*(1-np.exp(-t*3.3))
        phase=TAU*f*t+TAU*f*vibrato
        vals=sum(np.sin(h*phase)*np.exp(-h*.15)/(h**.72) for h in range(1,11))
        return (vals+.017*noise(t,800,2700))*edges(t,.18,.22)*(.85+.15*np.sin(t*4))
    n=round(16*beat*SR)
    camp=np.zeros((n,2));danger=np.zeros_like(camp)
    def phrase(layer,beatpos,notes,level,pan):
        start=round(beatpos*beat*SR)
        ids=(start+np.arange(len(notes)))%n
        layer[ids,0]+=notes*level*math.sqrt((1-pan)/2);layer[ids,1]+=notes*level*math.sqrt((1+pan)/2)
    for bar,chord in enumerate(chords):
        for pos,idx,octave,vol,pan in [(0,0,0,.28,-.35),(1.5,1,12,.18,.31),(2.5,2,0,.13,-.15),(3.3,1,12,.14,.26)]:
            phrase(camp,4*bar+pos,pluck(chord[idx]+octave,1.24),vol,pan)
        phrase(camp,4*bar+.22,bow(chord[1],2.31),.082,.25)
        phrase(danger,4*bar,bow(chord[0]-12,2.4),.31,-.21)
        for p,g in [(0,.76),(1.52,.40),(2.5,.54),(3.75,.31)]:
            phrase(danger,4*bar+p,scene(.32,[(0,thump(.29,77),.78),(.005,rub(.15,260,1450,.003,.042),.35)]),g,.1)
        phrase(danger,4*bar+.75,pluck(chord[1]-12,.82),.47,.3)
    # Tap a little early room reflection. Wrap both the physical tail and transport loop.
    for layer,name in [(camp,'camp_score'),(danger,'threat_score')]:
        layer+=np.roll(layer,round(.091*SR),axis=0)[:,::-1]*.09
        layer-=np.mean(layer,axis=0)
        layer*=.26/np.max(np.abs(layer))
        wavfile.write(BANK/(name+'.wav'),SR,np.int16(np.rint(layer*32767)))
    for name,notes in [('reveal',[(0,62,.64),(.13,69,.48),(.23,74,.37)]),
                       ('victory',[(0,62,.54),(.18,65,.48),(.31,69,.44)])]:
        y=np.zeros(len(time(1.10)))
        for at,midi,g in notes:add(y,at,pluck(midi,.78),g)
        write(name,y,.48)


def transitions():
    write('equip_axe',scene(.23,[(0,rub(.12,210,950,.009,.06),.33),(.045,wood(1.46,.16),.58)]))
    write('equip_pickaxe',scene(.24,[(0,rub(.12,250,1080,.009,.06),.30),(.051,stone(1.41,.15),.51)]))
    write('regrow_wood',scene(.40,[(0,rub(.35,860,4300,.06,.11),.7),(.07,grit(.22,16,820,3800),.45)]))
    write('regrow_stone',scene(.35,[(0,grit(.24,23,360,2150),.55),(.10,stone(.53,.21),.23)]))
    write('wolf_brace',scene(.29,[(0,vocal(.25,77,70,[(380,120,.9),(900,145,.5)],.12),.52),(.06,rub(.18,220,920,.026,.06),.22)]))
    write('wolf_return',scene(.32,[(.01,rub(.15,320,1300,.014,.065),.38),(.13,grit(.13,20,560,2500),.46)]))
    write('player_fall',scene(.53,[(.04,rub(.29,150,950,.04,.13),.35),(.22,thump(.3,58),.85),(.25,grit(.24,38,490,3200),.51)]))


def world_one_events():
    # Keep the two wolf accents distinct from the ordinary bark and body fall.
    # Midrange resonances let the larger animal read on small speakers.
    chest = [(330, 110, 1.0), (805, 165, .82), (1620, 280, .5)]
    write('boss_arrival', scene(1.10, [
        (0, vocal(.43, 98, 61, chest, .12), .9),
        (.31, vocal(.72, 78, 49, chest, .17), 1.0),
        (.38, rub(.38, 220, 1100, .055, .19), .24)
    ]), .64)
    # This snow collapse and short score resolution sit beneath the normal defeat event.
    t = time(.72)
    resolution = (np.sin(TAU*146.83*t) + .44*np.sin(TAU*220*t)) * edges(t, .025, .20) * np.exp(-t/.30)
    write('boss_defeat', scene(.96, [
        (0, thump(.32, 59), .80), (.075, grit(.31, 32, 360, 2650), .47),
        (.15, resolution, .34), (.28, rub(.44, 125, 1020, .035, .21), .30)
    ]), .58)
    t = time(.29)
    string = sum((np.sin(TAU*f*t) / (i+1)) * np.exp(-t*(16+i*12))
                 for i, f in enumerate([197.0, 389.0, 581.0, 986.0]))
    write('tower_fire', scene(.46, [
        (0, wood(1.22, .19), .53), (.012, string * edges(t, .001, .05), .75),
        (.044, swish(.28, 240, 4800), .45)
    ]), .65)
    write('tower_hit', scene(.39, [
        (0, thump(.23, 93), .83), (.002, wood(1.7, .14), .54),
        (.025, grit(.18, 25, 640, 3900), .39), (.08, rub(.22, 200, 1220, .024, .08), .25)
    ]), .61)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Rebuild Havenline’s original field score and effects.')
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--originals',type=Path,default=SOURCES)
    args=parser.parse_args()
    BANK, SOURCES = args.output, args.originals
    BANK.mkdir(parents=True,exist_ok=True)
    add_recovered()
    steps()
    music()
    transitions()
    world_one_events()
