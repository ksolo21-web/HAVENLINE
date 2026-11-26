from pathlib import Path
import hashlib,json,math,re,subprocess,sys
out, stage=map(Path,sys.argv[1:])
r=json.loads((stage/'cap-control.json').read_text())
control=r['cap_paid_control']
rct=r['native_cap_rectangle_control']['rectangle_px']
log=(out/'write.log').read_text()
def paid(prefix):
    x=[json.loads(l[len(prefix):]) for l in log.splitlines() if l.startswith(prefix)]
    found=[i for i in x if i['phase']=='paid-first-frame']
    assert len(found)==1
    return found[0]
native=paid('L1_POST_DRAW ')
npct=paid('REFERENCE_PANEL_BOUNDS ')['rectangle_px']
assert max(abs(x-y) for x,y in zip(npct,rct))<1e-5,'projected bounding mask differs'
for k in ('draw','queued'):
    assert native[k]==control[k],f'exact {k} camera/actor/authority stamp mismatch; no pixel causality claim'
assert native['viewport_px']==control['viewport_px']==[1280,720]
assert native['pixel_sha256']!=control['pixel_sha256']
for phase in ('write','cold'):
    x=(out/(phase+'.log')).read_text()
    assert x.count('V3_LOCAL_PAINT_MOUNT exact 4 per-instance overrides; no source or world material changes')==1
    assert 'REFERENCE_PANEL_FALLBACK' not in x
def decode(f,pix):
    return subprocess.check_output(['ffmpeg','-nostdin','-v','error','-protocol_whitelist','file,pipe','-i',str(f),'-f','rawvideo','-pix_fmt',pix,'-'])
def rgb(f,expected):
    x=decode(f,'rgb24')
    assert len(x)==1280*720*3
    if hashlib.sha256(x).hexdigest()!=expected:
        assert hashlib.sha256(decode(f,'rgba')).hexdigest()==expected
    return x
old=stage/'cap-only-paid-control.png'
new=out/'paid-first-frame.png'
assert hashlib.sha256(old.read_bytes()).hexdigest()==r['cap_paid_png_sha256']
a=rgb(old,control['pixel_sha256']);b=rgb(new,native['pixel_sha256'])
X,Y,U,V=(math.floor(npct[0])-2,math.floor(npct[1])-2,math.ceil(npct[2])+2,math.ceil(npct[3])+2)
changed=[]
outside=0
for p in range(1280*720):
    k=p*3
    if a[k:k+3] != b[k:k+3]:
        y,x=divmod(p,1280)
        if X<=x<U and Y<=y<V:
            changed.append((x,y))
        else:
            outside+=1
assert outside==0,'unexpected paint-frame delta outside projected module and two-pixel AA border'
assert len(changed)>0
print(json.dumps({'scope':'same exact untreated cap geometry vs local paint material including combined pigment/roughness/low emission; no renderer signature or art approval',
 'local_module_rectangle_px':npct,'exact_geometry_masks_and_origin_pose':True,'paid_frame_changed_px':len(changed),'outside_panel_plus_two_px_changed_px':outside,
 'cap_png_sha256':r['cap_paid_png_sha256'],'painted_png_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),
 'not_an_emission_only_or_dark_side_causal_trial':True},indent=2))
