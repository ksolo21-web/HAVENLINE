"""Detached geometry only: owner reference image custody, exact occupied envelope."""
from collections import defaultdict
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
here=Path(__file__).resolve().parent
source,reference=map(Path,sys.argv[1:3])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(reference)=='bc95d8be5769951c7b75073952662d17d3a40e80017a14fdee2a6fe6ec8a79fc'
assert sha(source)=='8b1890810e5734e5a2552098f762e7c72f8980b05be5d369ee3952521a97774f'
v=np.array([[float(q) for q in l.split()[1:4]] for l in source.read_text().splitlines() if l.startswith('v ')])
assert len(v)==1920
raw=defaultdict(list)
def ring(radial,tau,exp=.85):
    c,s=math.cos(tau),math.sin(tau)
    return (radial[0]*math.copysign(abs(c)**exp,c),radial[1]*math.copysign(abs(s)**exp,s))
def patch(mat,a,b,c):
    assert np.linalg.norm(np.cross(b-a,c-a))>1e-11
    raw[mat].append((a,b,c))
def strip(mat,rings,axial=False,cap=True):
    n=len(rings[0])
    for a,b in zip(rings,rings[1:]):
        for j in range(n):
            k=(j+1)%n
            if axial:
                patch(mat,a[j],a[k],b[k]);patch(mat,a[j],b[k],b[j])
            else:
                patch(mat,a[j],b[j],b[k]);patch(mat,a[j],b[k],a[k])
    if cap:
        a,b=rings[0],rings[-1]
        ca,cb=np.mean(a,axis=0),np.mean(b,axis=0)
        for j in range(n):
            k=(j+1)%n
            patch(mat,ca,a[j],a[k]);patch(mat,cb,b[k],b[j])
def loft(c,cy,rx,rz,phases,drip=None):
    out=[]
    for j,a in enumerate(phases):
        x,z=ring((rx,rz),a)
        out.append([c[0]+x,cy+(drip[j] if drip is not None else 0.),c[1]+z])
    return np.array(out)
controls=[]
for post in range(10):
    sv=v[post*192:(post+1)*192]
    lo,hi=sv.min(0),sv.max(0)
    ys=np.unique(sv[:,1])
    xmid=(hi[0]+lo[0])*.5
    zm=(hi[2]+lo[2])*.5
    height=hi[1]
    lip=ys[1]-.083
    r=.1325
    tiny=.003*math.sin(post*1.7)
    wood_phases=[j*math.tau/10 for j in range(10)]
    # Rounded log section; remove only a shallow broad curve beneath the ties,
    # not high-contrast polygon notches framing each post.
    wood_levels=[(0.,.124,.047),(.08,r,.050),(.245,.128,.042),(.375,.128,.042),
        (.49,r,.051),(.686,.128,.041),(.816,.128,.041),(.94,r,.052),(ys[2],.111,.050)]
    wood_rings=[loft((xmid+tiny*math.sin(2*y),0),y,rx,rz,wood_phases) for y,rx,rz in wood_levels]
    strip('amber_timber',wood_rings)
    rad_x=(hi[0]-lo[0])*.5;rad_z=(hi[2]-lo[2])*.5
    phases=[j*math.tau/12 for j in range(12)]
    scallops=[.014*math.sin(3*t+.40*post)+.012*math.sin(5*t-.74*post)+.010*math.cos(2*t) for t in phases]
    snow=[
      loft((xmid,zm),lip,rad_x*.88,rad_z*.92,phases,scallops),
      loft((xmid,zm),lip+.034,rad_x*.969,rad_z*.983,phases,[x*.55 for x in scallops]),
      loft((xmid,zm),lip+.103,rad_x,rad_z,phases,[0. for x in scallops]),
      loft((xmid+.006*math.sin(post),zm+.002),lip+.228,rad_x*.88,rad_z*.89,phases),
      loft((xmid+.009*math.sin(post),zm+.004),lip+.338,rad_x*.62,rad_z*.67,phases),
      loft((xmid+.009*math.sin(post),zm+.003),height-.057,rad_x*.35,rad_z*.42,phases),
      loft((xmid+.010*math.sin(post),zm+.003),height-.015,rad_x*.164,rad_z*.22,phases),
      loft((xmid+.010*math.sin(post),zm+.003),height,rad_x*.060,rad_z*.09,phases)]
    strip('draped_snow',snow)
    # Actual carrier paths wrap around both faces. Radial clearance is
    # concentrated at the crossing, not spread along dead-black air gaps.
    # The cross section is taller in the screen-friendly up dimension.
    for y in (.311,.751):
        for sign in (-1,1):
            centers=[]
            sections=[]
            for i in range(16):
                angle=math.tau*i/16
                x,z=ring((.131,.0528),angle,.62)
                depth=abs(z/.0528)
                z+=sign*.0093*depth**7
                centers.append(np.array([xmid+x,y+sign*.055*(x/.131)-.006*(1-(x/.131)**2),z]))
            for i,c in enumerate(centers):
                tangent=centers[(i+1)%16]-centers[(i-1)%16]
                tangent/=np.linalg.norm(tangent)
                radial=np.cross(tangent,[0.,1.,0.]);radial/=np.linalg.norm(radial)
                down_up=np.cross(tangent,radial)
                # Four silhouette-support points with smooth exported normals.
                section=[c+.0075*radial,c+.0165*down_up,c-.0075*radial,c-.0165*down_up]
                sections.append(np.array(section))
            limb='cream_hemp' if sign>0 else 'warm_hemp'
            strip(limb,sections+[sections[0]],axial=True,cap=False)
    controls.append({'post':post,'lo':lo.tolist(),'hi':hi.tolist(),'belt_depth_interior_m':.042,'pitch_m':.440,
                     'crossed_lashing_face_center_separation_m':.0186,
                     'snow_skirt_y_range_m':snow[0][:,1].min().item(),'snow_rollover_full_width_y_m':lip+.103})
out=here/'candidate';out.mkdir(exist_ok=True)
p=out/'Fence18595V2.obj'
lines=['# Detached art draft, studied geometry and panel-only palette',
       'mtllib Fence18595V2.mtl','o Fence18595V2','s 1']
positions=[];normals=[];meta=[]
for material,faces in raw.items():
    # Area-weighted proper vertex normals where rounded side/top/skirt meet.
    accum={}
    meta.append((material,len(positions)+1,len(faces)))
    for a,b,c in faces:
        n=np.cross(b-a,c-a)
        for q in (a,b,c):
            k=tuple(q)
            accum[k]=accum.get(k,np.zeros(3))+n
    for f in faces:
        for q in f:
            vn=accum[tuple(q)]
            positions.append(q)
            normals.append(vn/np.linalg.norm(vn))
positions=np.array(positions);normals=np.array(normals)
assert np.isfinite(normals).all()
assert np.allclose(positions.min(0),v.min(0),atol=1e-8,rtol=0) and np.allclose(positions.max(0),v.max(0),atol=1e-8,rtol=0), (positions.min(0),positions.max(0))
lines += [f'v {x:.9f} {y:.9f} {z:.9f}' for x,y,z in positions]
lines += [f'vn {x:.9f} {y:.9f} {z:.9f}' for x,y,z in normals]
for mat,first,count in meta:
    lines.append('usemtl '+mat)
    for i in range(first,first+3*count,3):
        lines.append('f '+' '.join(f'{j}//{j}' for j in range(i,i+3)))
p.write_text('\n'.join(lines)+'\n')
(out/'Fence18595V2.mtl').write_text('newmtl amber_timber\nKd .79 .43 .225\nPr .90\nnewmtl draped_snow\nKd .88 .935 .995\nPr .79\nnewmtl cream_hemp\nKd .91 .72 .45\nPr .79\nnewmtl warm_hemp\nKd .77 .55 .32\nPr .82\n')
res={'source_reference_sha256':sha(reference),'source_technical_volume_sha256':sha(source),'asset_sha256':sha(p),
     'panel_aabb_m':[positions.min(0).tolist(),positions.max(0).tolist()],
     'triangle_counts':{k:len(x) for k,x in raw.items()},'panel_total':sum(map(len,raw.values())),
     'modules':controls,'drawn_render_or_native_integration':False}
(here/'build-result.json').write_text(json.dumps(res,indent=2)+'\n')
