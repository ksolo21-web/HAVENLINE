from pathlib import Path
from collections import Counter
import hashlib,math,json,sys
import numpy as np
here=Path(__file__).resolve().parent
src,tech,ref=map(Path,sys.argv[1:4])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)=='137446d82b7c679c88f85069958b0eaacb85ca38dc8d1e7f73be5bef89b7ec53'
assert sha(tech)=='8b1890810e5734e5a2552098f762e7c72f8980b05be5d369ee3952521a97774f'
assert sha(ref)=='bc95d8be5769951c7b75073952662d17d3a40e80017a14fdee2a6fe6ec8a79fc'
raw=src.read_text().splitlines()
reference=np.array([[float(a) for a in l.split()[1:4]] for l in tech.read_text().splitlines() if l.startswith('v ')])
old_v=[i for i,x in enumerate(raw) if x.startswith('v ')]
old_n=[i for i,x in enumerate(raw) if x.startswith('vn ')]
positions=[np.array([float(a) for a in raw[i].split()[1:4]]) for i in old_v]
start=raw.index('usemtl draped_snow')
end=raw.index('usemtl warm_hemp')
assert end-start-1==1920
snow_ids=[int(c.split('/')[0])-1 for l in raw[start+1:end] for c in l.split()[1:]]
assert snow_ids==list(range(snow_ids[0],snow_ids[0]+1920*3))
generated=[]
def add(*f):
    a,b,c=f
    assert np.linalg.norm(np.cross(b-a,c-a))>1e-11
    generated.append(f)
def ring(cx,y,rx,rz,zm,n,rhythm=0.,phase=0.,shape=.76):
    pts=[]
    for j in range(n):
        a=math.tau*j/n
        x,z=math.cos(a),math.sin(a)
        sx=math.copysign(abs(x)**shape,x); sz=math.copysign(abs(z)**shape,z)
        # Scallops occur across the faces in actual local X, not only
        # angular azimuth where head-on projection cancels a shallow ripple.
        wave=.055 * math.cos((sx+.12)*3.2*math.pi+phase)
        wave+=.023 * math.sin((sx-.07)*5.1*math.pi-phase*.8)
        wave+=.014 * math.sin(2*a+.35+phase) - .013
        yy=y+rhythm*wave
        pts.append([cx+rx*sx,yy,zm+rz*sz])
    return np.array(pts)
def bridge(a,b):
    A,B=len(a),len(b)
    if A==B:
        for j in range(A):
            k=(j+1)%A
            add(a[j],b[j],b[k]);add(a[j],b[k],a[k])
    else:
        assert A==2*B
        for j in range(B):
            k=(j+1)%B
            add(a[2*j],b[j],a[(2*j+1)%A])
            add(a[(2*j+1)%A],b[j],b[k])
            add(a[(2*j+1)%A],b[k],a[(2*j+2)%A])
def close(a,b):
    pa,pb=a.mean(0),b.mean(0)
    for j in range(len(a)):add(pa,a[j],a[(j+1)%len(a)])
    for j in range(len(b)):add(pb,b[(j+1)%len(b)],b[j])
proof=[]
for post in range(10):
    module=reference[192*post:192*(post+1)]
    mn,mx=module.min(0),module.max(0)
    source_snow=np.array([positions[i] for i in snow_ids[576*post:576*(post+1)]])
    xmid=(mn[0]+mx[0])*.5; zm=(mn[2]+mx[2])*.5
    rx=(mx[0]-mn[0])*.5; rz=(mx[2]-mn[2])*.5
    top=mx[1]
    front_phase=(post%3-1)*.55
    # Bigger rounded skirt, near full post width from skirt to mid-high
    # shoulder; the cap no longer reaches full width at one tiny y band.
    r=[
      ring(xmid,top-.445,rx*.959,rz*.715,zm+.002,24,1.,front_phase,.67),
      ring(xmid,top-.375,rx,rz,zm,24,.35,front_phase,.70),
      ring(xmid,top-.295,rx*.994,rz*.970,zm,12,.035,front_phase,.75),
      ring(xmid+.003*math.sin(post),top-.205,rx*.875,rz*.875,zm+.002,12),
      ring(xmid+.006*math.sin(post),top-.097,rx*.594,rz*.648,zm+.002,12),
      ring(xmid+.008*math.sin(post),top,rx*.105,rz*.130,zm+.001,12)]
    for a,b in zip(r,r[1:]):bridge(a,b)
    close(r[0],r[-1])
    out=np.array(generated[-192:]).reshape(-1,3)
    assert np.all(out.min(0)>=mn-1e-9) and np.all(out.max(0)<=mx+1e-9)
    assert np.allclose(out.max(0),mx,rtol=0,atol=1e-9) and np.allclose(out.min(0)[[0,2]],mn[[0,2]],rtol=0,atol=1e-9)
    pts=r[0][1:12]
    period=float(pts[:,1].max()-pts[:,1].min())
    proof.append({'post':post,'front_scallop_range_m':period,'prior_snow_min_y_m':float(source_snow[:,1].min()),
      'current_snow_min_y_m':float(out[:,1].min()),'nominal_rounded_front_shoulder_width_ratio_at_295_below_top':.994,
      'full_aabb_unchanged':True})
assert len(generated)==1920
vs=np.array(generated).reshape(-1,3)
normals={}
for face in generated:
    a,b,c=face; n=np.cross(b-a,c-a)
    for v in face:
        k=tuple(v)
        normals[k]=normals.get(k,np.zeros(3))+n
for row,v in zip(snow_ids,vs):
    n=normals[tuple(v)]; n/=np.linalg.norm(n)
    raw[old_v[row]]='v '+' '.join(f'{a:.9f}' for a in v)
    raw[old_n[row]]='vn '+' '.join(f'{a:.9f}' for a in n)
    normals[tuple(v)]=n
dest=here/'candidate';dest.mkdir(exist_ok=True)
path=dest/'Fence18595V3.obj'
# Strictly retain the imported contiguous material order and exact V2 names.
raw[1]='mtllib Fence18595V3.mtl'
path.write_text('\n'.join(raw)+'\n')
base_mtl=src.with_suffix('.mtl')
assert sha(base_mtl)=='c606aaf113f042e22146e199f7308d9b604e5075ba62b5b8a27ffb139ecbc3f0'
(dest/'Fence18595V3.mtl').write_bytes(base_mtl.read_bytes())
(here/'build-result.json').write_text(json.dumps({'obj_sha256':sha(path),'predecessor_contact_obj_sha':sha(src),
                'owner_actual_fence_reference_sha256':sha(ref),'modification':'snow caps positions and normals only; no V2 timber or rope changed',
                'triangle_count':8840,'posts':proof},indent=2)+'\n')
