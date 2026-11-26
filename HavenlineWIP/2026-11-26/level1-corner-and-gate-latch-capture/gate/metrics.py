from pathlib import Path
from hashlib import sha256
import json, re, sys, statistics
from PIL import Image, ImageDraw

def digest(p):return sha256(p.read_bytes()).hexdigest()
def paid(out):
    log=(out/'write.log').read_text()
    line=re.findall(r'^R17_NATIVE_DRAW_EVIDENCE (.+)$',log,re.M)
    assert line
    data=[json.loads(x) for x in line if 'paid-first-frame' in x and 'projected_hinge_verticals_px' in x]
    assert len(data)==1
    return data[0]
def discover(r):
    if isinstance(r,dict):
        if {'gate-south','gate-east'}<=r.keys() and all(isinstance(r[g],dict) and 'projected_hinge_verticals_px' in r[g] for g in ('gate-south','gate-east')):
            return r
        for x in r.values():
            v=discover(x)
            if v:return v
def masks(out):
    r=discover(paid(out));assert r
    return {g:r[g]['projected_hinge_verticals_px'] for g in ('gate-south','gate-east')}
def calc(out,vertices):
    path=out/'paid-first-frame.png'
    with Image.open(path) as im: rgb=list(im.convert('RGB').getdata());assert im.size==(1280,720)
    rows={}
    for gate,(a,b) in vertices.items():
        x0,b0,x0b,t0=a;x1,b1,x1b,t1=b
        assert x0==x0b and x1==x1b and t0<b0 and t1<b1
        def v(u,q):
            return ((1-u)*x0+u*x1,(1-q)*((1-u)*t0+u*t1)+q*((1-u)*b0+u*b1))
        m=Image.new('1',(1280,720))
        ImageDraw.Draw(m).polygon([v(.12,.17),v(.88,.17),v(.88,.86),v(.12,.86)],fill=1)
        selected=[p for p,k in zip(rgb,m.getdata()) if k]
        y=[.2126*r+.7152*g+.0722*b for r,g,b in selected]
        assert len(y)>=1000
        rows[gate]={'red_at_255':sum(r==255 for r,g,b in selected),'median_encoded_Y':statistics.median(y),'near_black_Y_lt30':sum(i<30 for i in y),'n':len(y)}
    return {'png_sha256':digest(path),'metrics':rows}
if __name__=='__main__':
    c,b=map(Path,sys.argv[1:3])
    cm,bm=masks(c),masks(b)
    assert cm==bm, 'paid hinge projections differ; not a same-camera comparison'
    print(json.dumps({'control':calc(b,bm),'candidate':calc(c,cm),'same_masks':cm,'scope':'Encoded pixels in original gate-interior polygons, not segmentation, scene-linear values, visual score or acceptance'},indent=2))
