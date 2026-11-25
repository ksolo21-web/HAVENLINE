import hashlib, json, math, re, struct
from pathlib import Path
base=Path(__file__).resolve().parent
raw=(base/'service_counter.glb').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='a62f900f8587008fc0349782b4aa7da3d1a8ebcaa9847569d2b9fa67a47dd25c'
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='8654977d664202724b7089984bf7fb876ffbd331'
n=struct.unpack_from("<I",raw,12)[0]; model=json.loads(raw[20:20+n]); data=raw[28+n:]
assert model['nodes']==[{'mesh':0,'name':'service_counter'}]
def read(i):
    a=model["accessors"][i]; v=model["bufferViews"][a["bufferView"]]
    f={5126:"f",5125:"I",5123:"H",5121:"B"}[a["componentType"]]*{"SCALAR":1,"VEC3":3}[a["type"]]
    size=struct.calcsize("<"+f); off=v.get("byteOffset",0)+a.get("byteOffset",0)
    return [struct.unpack_from("<"+f,data,off+k*v.get("byteStride",size)) for k in range(a["count"])]
def vertical(x,z,tri):
    (a,y,b),(c,v,d),(e,w,f)=tri
    det=(c-a)*(f-b)-(d-b)*(e-a)
    if abs(det)<1e-10:return None
    u=((x-a)*(f-b)-(z-b)*(e-a))/det
    l=((z-b)*(c-a)-(x-a)*(d-b))/det
    return y+(v-y)*u+(w-y)*l if min(u,l,1-u-l)>=-1e-8 else None
scene=(base/'north_counter_donor.tscn').read_text()
def node(name, field):
    return scene.split('name="'+name+'"')[1].split('[node')[0].split(field+' = ')[1].splitlines()[0]
def vec(s):
    return tuple(map(float,re.search(r'Vector3\((.*)\)',s)[1].split(',')))
sizes=[vec(s) for s in re.findall(r'^size = (Vector3.*)$',scene,re.M)]
assert sizes==[(3.175,.95,.3),(3.73,.95,.3)]
pieces=[(vec(node(k,'position')),sizes[i]) for k,i in [('SurvivingFenceLeft',0),('CounterSealedBridge',1),('SurvivingFenceRight',0)]]
for (lp,ls),(rp,rs) in zip(pieces,pieces[1:]):
    overlap=tuple((a+A/2)-(b-B/2) if j==0 else min(a+A/2,b+B/2)-max(a-A/2,b-B/2)
       for j,(a,A,b,B) in enumerate(zip(lp,ls,rp,rs)))
    assert all(abs(a-b)<1e-8 for a,b in zip(overlap,(.04,.95,.30)))
    print('seam overlap m',*(round(x,6) for x in overlap))
assert pieces[0][0][0]-pieces[0][1][0]/2 == -5 and pieces[-1][0][0]+pieces[-1][1][0]/2 == 5
triangles=[]; points=[]
for pr in model["meshes"][0]["primitives"]:
    v=read(pr["attributes"]["POSITION"]); ix=[i[0] for i in read(pr["indices"])]
    points.extend(v); triangles.extend(tuple(v[a] for a in ix[i:i+3]) for i in range(0,len(ix),3))
assert len(triangles)==13624
for label in ('Stock','Payment'):
    x,y,z=vec(node(label+'RestWitness','position'))
    a,b,c=vec(node(label+'Handling','position'))
    assert (x,z)==(a,c) and b==1.3
    assert 'surface_rest_candidate' in node(label+'RestWitness','metadata/socket_kind')
    # Small local support study only; no approved prop footprint or pivot.
    heights=[]
    for ix in range(-2,3):
        for iz in range(-2,3):
            hits=[h for tri in triangles if (h:=vertical(x+ix*.0125,z+iz*.0125,tri)) is not None]
            assert hits
            heights.append(max(hits))
    assert abs(y-heights[12])<.000005 and b-heights[12]>.20
    assert (max(heights)-min(heights)>.19) if label=="Stock" else (max(heights)-min(heights)<.0003)
    print(label,'25 sampled rests, span y',round(min(heights),6),round(max(heights),6),'interaction gap',round(b-heights[12],6))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]
def unit(a):return tuple(x/math.sqrt(dot(a,a)) for x in a)
for label,view in [('inside baseline 3/4',(7,11,11)),('outside opposite 3/4',(-7,11,-11))]:
    normal=unit(view); right=unit(cross((0,1,0),normal)); up=unit(cross(normal,right))
    rows=[(dot(v,right),dot(v,up)) for v in points]
    bounds=[(min(s),max(s)) for s in zip(*rows)]
    # Exact donor-projection bounds, no renderer. 720/13 corresponds to
    # existing 1280x720 13m orthographic game camera vertical scale.
    print(label,'donor projected m',[(round(lo,6),round(hi,6)) for lo,hi in bounds],
          '720p extent px',[round((hi-lo)*720/13,2) for lo,hi in bounds])
    assert min(hi-lo for lo,hi in bounds)>2.0
    # Facing polarity is relative to the same local asset, not screen art.
    assert (view[2]>0)==(label.startswith('inside'))
    bridge=[(x,y,z) for x in (-1.865,1.865) for y in (0,.95) for z in (-.15,.15)]
    bridge_top=max(dot(v,up) for v in bridge)
    above=bounds[1][1]-bridge_top
    assert above>0
    print('  projection above opaque bridge envelope (not pixel visibility) m',round(above,6))
