"""Rebuild the shore sawmill and cable-drill from Alfred's eight-view plates.

Usage: python build_shore_processors.py reference_directory output_directory
Raw sheets are Docs/Design/RenderArchive/2026-11-23/selected/equipment at
26bb649e0a8090c9c9af7e91e62f384fc86372d8. Axle tooth geometry is read from
the recovered cooker_workshop GLB produced by build_lakeshore_cooker.py.
"""
import argparse, hashlib, io, json, math, struct
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("references",type=Path)
p.add_argument("out",type=Path)
args=p.parse_args()
out=args.out
out.mkdir(exist_ok=True,parents=True)
rng=np.random.default_rng(51)
tau=math.tau

# Timber, trunk, cut end, iron, steel, orange enamel, quarried stone,
# twisted binding and pine snow. All surfaces use one UV atlas per station.
samples=[(168,105,53),(133,80,39),(210,161,96),(67,75,80),(147,157,163),
         (216,118,41),(116,125,132),(174,146,99),(224,233,238),(52,104,143)]
tile=192
atlas=Image.new('RGB',(tile*len(samples),tile))
yy,xx=np.mgrid[0:tile,0:tile]
for i,color in enumerate(samples):
    grain=rng.normal(0,1,(tile,tile))
    if i in (0,1):
        wav=xx+2.9*np.sin(yy/24+xx/19)+1.3*np.sin(yy/44)
        lines=np.cos(wav*(.34 if i==0 else .24))
        noise=11*lines+11*gaussian_filter(grain,(7,.9))+2.6*grain
        noise-=np.where(np.sin(.59*wav+np.sin(yy/29))>.91,12 if i==0 else 21,0)
        for cx,cy in ((54,68),(147,141)):
            radius=np.sqrt((xx-cx)**2+((yy-cy)*.33)**2)
            noise+=7*np.cos(radius*.8)*np.exp(-radius/9)
    elif i==2:
        radius=np.hypot(xx-95+2*np.sin(yy/21),yy-92)
        noise=12*np.cos(radius*.31)+7*np.cos(radius*.71)+3*grain
    elif i==7:
        noise=11*np.sin((xx+yy*.43)/3)+3*grain
    else:
        noise=3*grain+23*gaussian_filter(grain,2)+18*gaussian_filter(grain,6)
    pix=np.asarray(color)+noise[:,:,None]
    atlas.paste(Image.fromarray(np.clip(pix,0,255).astype('B')),(tile*i,0))
source_hash={n:hashlib.sha256((args.references/(n+'.png')).read_bytes()).hexdigest()
             for n in ('saw_station','quarry_drill_station')}
# Each element is a complete UV-mapped triangle, grouped by moving assembly.
parts={}; group='Frame'
def tri(points,mat,uv):
    bucket=parts.setdefault(group,[])
    a,b,c=map(np.asarray,points)
    n=np.cross(b-a,c-a); norm=np.linalg.norm(n)
    if norm<1e-9:return
    for q,(u,v) in zip(points,uv):
        bucket.append([*q,*(n/norm),(mat+.02+.96*u)/len(samples),.02+.96*v])
def quad(a,b,c,d,mat):
    tri([a,b,c],mat,[(0,0),(1,0),(1,1)])
    tri([a,c,d],mat,[(0,0),(1,1),(0,1)])
def section(a,b,rw,rd,mat,sides=8,roundwood=False,endmat=None):
    a=np.array(a,dtype=float);b=np.array(b,dtype=float)
    axis=b-a;axis/=np.linalg.norm(axis)
    ref=np.array([0.,1.,0.]) if abs(axis[1])<.91 else np.array([0.,0.,1.])
    u=np.cross(ref,axis);u/=np.linalg.norm(u);v=np.cross(axis,u)
    if roundwood:
        outline=[(math.cos(tau*i/sides)*rw,math.sin(tau*i/sides)*rd) for i in range(sides)]
    else:
        cut=.20*min(rw,rd)
        outline=[(rw,rd-cut),(rw-cut,rd),(-rw+cut,rd),(-rw,rd-cut),(-rw,-rd+cut),(-rw+cut,-rd),(rw-cut,-rd),(rw,-rd+cut)]
    lo=[a+u*x+v*y for x,y in outline];hi=[b+u*x+v*y for x,y in outline]
    endmat=mat if endmat is None else endmat
    for i in range(len(lo)):
        j=(i+1)%len(lo)
        quad(lo[i],lo[j],hi[j],hi[i],mat)
        coords=[(.5+x/(2*rw),.5+y/(2*rd)) for x,y in (outline[i],outline[j])]
        tri([a,lo[j],lo[i]],endmat,[(.5,.5),coords[1],coords[0]])
        tri([b,hi[i],hi[j]],endmat,[(.5,.5),*coords])
def beam(a,b,w,d,mat=0):section(a,b,w/2,d/2,mat,endmat=2 if mat in (0,1) else mat)
def rod(a,b,r,mat,n=14):section(a,b,r,r,mat,n,True,2 if mat in (0,1) else mat)
def box(c,size,mat):
    x,y,z=c;w,h,d=size
    beam((x,y-h/2,z),(x,y+h/2,z),w,d,mat)
def deck(x0,x1,y,z0,z1,boards,mat=0):
    width=(z1-z0)/boards
    for i in range(boards):
        beam((x0,y,z0+(i+.5)*width),(x1,y,z0+(i+.5)*width),width*.95,.09,mat)
def collar(a,b,r,mat):rod(a,b,r,mat,14)
def rock(x,y,z,w,h,d,mat=6):
    phases=np.linspace(0,tau,11)[:-1];phase=rng.uniform(0,.28)
    rows=[]
    for fraction,r in [(0,.75),(.32,1.),(.77,.90),(1.,.62)]:
        points=[]
        for angle in phases:
            jitter=rng.uniform(.88,1.07)
            points.append(np.array([x+w*.5*jitter*r*math.cos(angle+phase),y+h*fraction+rng.uniform(-.018,.018)*h,z+d*.5*jitter*r*math.sin(angle+phase)]))
        rows.append(points)
    for i in range(10):
        j=(i+1)%10
        for k in range(3):quad(rows[k][j],rows[k][i],rows[k+1][i],rows[k+1][j],mat)
        tri([[x,y+h,z],rows[-1][j],rows[-1][i]],mat,[(.5,.5),(1,0),(0,0)])
def write(name):
    global parts,group
    blob=bytearray(); views=[];acc=[];nodes=[];meshes=[]
    def view(data,target=None):
        blob.extend(b'\0'*(-len(blob)%4));i=len(views)
        views.append(dict(buffer=0,byteOffset=len(blob),byteLength=len(data)))
        if target:views[-1]['target']=target
        blob.extend(data);return i
    def attribute(arr,t):
        i=len(acc);acc.append(dict(bufferView=view(np.ascontiguousarray(arr,dtype='<f4').tobytes(),34962),componentType=5126,count=len(arr),type=t,min=arr.min(0).tolist(),max=arr.max(0).tolist()));return i
    for label,vertices in parts.items():
        data=np.array(vertices,dtype='<f4')
        mesh=dict(attributes={'POSITION':attribute(data[:,:3],'VEC3'),'NORMAL':attribute(data[:,3:6],'VEC3'),'TEXCOORD_0':attribute(data[:,6:],'VEC2')},material=0)
        nodes.append(dict(name=label,mesh=len(meshes)));meshes.append(dict(name=label,primitives=[mesh]))
    texture=io.BytesIO();atlas.save(texture,format='JPEG',quality=89)
    im=view(texture.getvalue())
    doc=dict(asset=dict(version='2.0',generator='Havenline turnaround reconstruction',extras=source_hash),scene=0,scenes=[dict(nodes=list(range(len(nodes))))],nodes=nodes,meshes=meshes,materials=[dict(name='WeatheredWorkshop',pbrMetallicRoughness=dict(baseColorTexture=dict(index=0),roughnessFactor=.81,metallicFactor=.05))],images=[dict(bufferView=im,mimeType='image/jpeg')],textures=[dict(source=0)],buffers=[dict(byteLength=len(blob))],bufferViews=views,accessors=acc)
    # The fixed sun underexposes camera-facing end grain and steel; the atlas
    # supplies low diffuse bounce on just these two freestanding outdoor rigs.
    if name.startswith('shore_'):
        doc['materials'][0].update(emissiveTexture={'index':0},emissiveFactor=[.32,.30,.28])
    hdr=json.dumps(doc,separators=(',',':')).encode();hdr+=b' '*(-len(hdr)%4);blob.extend(b'\0'*(-len(blob)%4))
    (out/(name+'.glb')).write_bytes(struct.pack('<4sIII4s',b'glTF',2,28+len(hdr)+len(blob),len(hdr),b'JSON')+hdr+struct.pack('<I4s',len(blob),b'BIN\0')+blob)
    parts={};group='Frame'

def donor_blade():
    raw=(out.parent/'lakeshore/cooker_workshop.glb').read_bytes()
    length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);data=raw[28+length:]
    def accessor(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        return np.frombuffer(data,{'5123':'<u2','5126':'<f4','5125':'<u4'}[str(a['componentType'])],count=a['count']*(3 if a['type']=='VEC3' else 1),offset=v.get('byteOffset',0)+a.get('byteOffset',0))
    for pr in doc['meshes'][1]['primitives']:
        xyz=(accessor(pr['attributes']['POSITION']).reshape(-1,3)-[.03,1.27,-.669])*2.05
        for ids in accessor(pr['indices']).reshape(-1,3):tri(xyz[ids],4,[(0,0),(1,0),(1,1)])

# Saw bench: four plated splayed feet, strapped log feed, board deck, toothed
# original wheel on the front axle, upper depth stop and separate outfeed tray.
for x in [-.86,.86]:
    for z in [-.43,.43]:
        foot=(x*1.22,.05,z*1.34)
        beam(foot,(x,.96,z),.30,.26)
        rock(foot[0],.012,foot[2],.36,.13,.31,8)
for x in [-.88,.88]:
    beam((x,.81,-.69),(x,.81,.70),.34,.23)
for z in [-.47,.46]:
    beam((-1.13,.33,z),(1.13,.33,z),.19,.18)
for z,height in [(-.59,1.05),(-.28,1.09),(.04,1.02),(.36,.98),(.66,.925)]:
    beam((-1.34,height,z),(1.34,height,z),.21,.22)
for x in [-1.15,1.15]:
    for z in [-.60,.66]:
        box((x,1.042,z),(.33,.245,.275),3)
        rod((x,1.088,z+.132),(x,1.088,z+.164),.06,4,10)
        rod((x,1.158,z),(x,1.18,z),.049,4,10)
for x in [-.65,.65]:
    beam((x,1.11,-.32),(x,1.83,-.32),.155,.15,0)
    collar((x,1.66,-.32),(x,1.735,-.32),.103,3)
beam((-.63,1.80,-.32),(.64,1.80,-.32),.095,.09,0)
beam((-.34,1.48,-.31),(-.04,1.81,-.31),.079,.075,3)
rod((-.98,1.415,-.14),(1.02,1.415,-.14),.27,0,18)
for x in [-.84,.82]:
    rod((x-.053,1.415,-.14),(x+.053,1.415,-.14),.280,3,20)
# Projecting split bark ridges frame the sawn end. Actual concentric age rings
# have slight eccentricity, so they remain visible as the end foreshortens.
for i in range(14):
    a=tau*i/14
    y=1.415+.257*math.cos(a);z=-.14+.257*math.sin(a)
    rod((-.94,y,z),(.96,y+.002*math.sin(i),z+.002),.015,1,6)
for end in [-1.002,1.033]:
    direction=1. if end>0 else -1.
    for ring,r in enumerate([.261,.210,.164,.107,.052]):
        for i in range(28):
            a=tau*i/28;b=tau*(i+1)/28
            def point(t):
                radius=r*(1+.028*math.sin(3*t+.4*ring))
                return (end,1.419+radius*math.cos(t),-.141+radius*math.sin(t))
            rod(point(a),point(b),.007 if ring else .011,1,5)
    rod((end-direction*.015,1.415,-.14),(end+direction*.001,1.415,-.14),.260,2,40)
rod((.06,1.13,.36),(.06,1.13,.62),.124,3)
deck(-1.32,-.50,.52,.60,1.05,4)
for x in [-1.22,-.60]:beam((x,.02,.96),(x,.50,.96),.12,.12)
group='SawRotor';donor_blade()
# Shaped cutting tips on both faces of the donor drive disc. Unequal rake
# gives its working edge a readable silhouette even on an edge-on crest.
for i in range(19):
    a=tau*i/19
    profile=[(.398,a),(.457,a+.09),(.392,a+.23)]
    front=[(r*math.cos(t),r*math.sin(t),.016) for r,t in profile]
    back=[(x,y,-.028) for x,y,z in front]
    tri(front,4,[(0,0),(.5,1),(1,0)])
    tri(back[::-1],4,[(0,0),(.5,1),(1,0)])
    for j in range(3):quad(back[j],back[(j+1)%3],front[(j+1)%3],front[j],3)
rod((0,0,-.068),(0,0,.060),.105,3,16)
rod((0,0,.059),(0,0,.073),.040,4,6)
rod((0,0,.070),(0,0,.153),.119,3,20)
rod((0,0,.143),(0,0,.189),.078,4,14)
beam((0,0,.177),(.225,-.083,.225),.07,.075,3)
rod((.225,-.083,.190),(.225,-.083,.342),.061,1,14)
write('shore_saw_bench')

# Drill rig: the turnaround's pyramidal braced timber tower, oversize sheave,
# head cable, fluted moving steel bit, orange plant, belt drum and stone crib.
for x in [-.57,.57]:
    for z in [-.60,.60]:
        rock(x,.02,z,.46,.26,.42)
        beam((x,.18,z),(x*.48,2.78,z*.48),.15,.15)
        box((x*.98,.32,z*.98),(.19,.15,.19),3)
for y in [.51,1.16,1.84,2.53]:
    f=1.-(y-.18)*.2
    for side in [-1,1]:
        beam((-.57*f,y,side*.60*f),(.57*f,y,side*.60*f),.095,.115)
        beam((side*.57*f,y,-.60*f),(side*.57*f,y,.60*f),.095,.115)
        if y<2.5:
            beam((-.57*f,y,side*.60*f),(.57*(f-.12),y+.65,side*.60*(f-.12)),.070,.085)
            beam((side*.57*f,y,-.60*f),(side*.57*(f-.12),y+.65,.60*(f-.12)),.070,.085)
beam((-.39,2.79,-.31),(.39,2.79,-.31),.17,.17)
beam((-.39,2.79,.31),(.39,2.79,.31),.17,.17)
rod((-.16,2.65,0),(.16,2.65,0),.21,3,24)
for x in [-.17,.17]:rod((x-.018,2.65,0),(x+.018,2.65,0),.23,4,24)
rod((0,2.68,.19),(0,.74,.19),.024,3)
rod((0,2.68,-.19),(.96,.97,-.40),.026,3)
# The side-on tracked generator occupies the near side of the tower. Closed
# track loops, tread shoes and sprockets present a clear three-quarter profile.
for x in [.625,1.26]:
    box((x,.249,-.035),(.215,.255,1.17),3)
    for z in [-.595,-.34,-.035,.27,.525]:
        rod((x-.115,.258,z),(x+.115,.258,z),.162,3,20)
        rod((x-.124,.258,z),(x+.124,.258,z),.112,4,16)
        rod((x-.137,.258,z),(x+.137,.258,z),.051,3,8)
        rod((x-.143,.258,z),(x+.143,.258,z),.025,4,8)
    for z in np.linspace(-.64,.58,10):
        box((x,.098,z),(.245,.059,.070),4)
        box((x,.418,z),(.245,.054,.070),4)
    for z in [-.677,.603]:
        box((x,.25,z),(.24,.196,.065),4)
box((.94,.51,-.045),(.81,.193,1.30),9)
box((.94,.745,-.363),(.74,.44,.61),5)
box((.94,.975,-.36),(.65,.075,.58),5)
for t in range(6):
    box((1.327,.765,-.601+.077*t),(.030,.206,.036),3)
# Cobalt cabin, dark glazing around the visible faces, isolated brass door and
# a broad blue hood like the plate. Nose points toward the camera.
box((.94,.820,.180),(.68,.57,.55),9)
box((.94,1.142,.131),(.66,.33,.48),3)
box((.94,1.153,.380),(.53,.20,.032),4)
box((1.282,1.156,.128),(.034,.194,.344),4)
for z in [-.085,.353]:box((1.280,1.164,z),(.045,.285,.045),5)
box((.94,1.331,.131),(.74,.102,.54),9)
box((1.296,1.153,.084),(.020,.21,.026),3)
beam((.710,1.084,.402),(.870,1.217,.402),.023,.019,3)
beam((1.305,1.084,.239),(1.305,1.227,.096),.019,.022,3)
box((.96,.797,.551),(.61,.28,.248),9)
for x in [.71,1.19]:
    rod((x,.866,.674),(x,.866,.695),.051,5,14)
box((1.307,.851,.147),(.035,.298,.287),5)
box((1.331,.936,.227),(.034,.042,.086),3)
rod((.906,1.01,-.351),(.906,1.104,-.351),.095,4,20)
rod((.73,.669,.65),(1.14,.669,.65),.129,3,20)
for x in np.linspace(.765,1.105,11):rod((x,.669,.65),(x+.022,.669,.65),.137,7,16)
for i in range(18):
    ang=tau*i/18
    px=.71*math.cos(ang)+rng.uniform(-.08,.08)
    pz=.87*math.sin(ang)+rng.uniform(-.07,.07)
    height=.15+rng.uniform(0,.10)
    rock(px,.01,pz,.32,height,.27)
    if i%3!=1:rock(px,.012+.89*height,pz,.238,.047,.191,8)
deck(-1.33,-.65,.33,-.61,.54,6)
for z in [-.49,.39]:beam((-1.22,.05,z),(-1.22,.30,z),.13,.14)
group='DrillHead'
rod((0,-.40,0),(0,.29,0),.070,4,14)
for i in range(6):
    a=tau*i/6
    tip=[0,-.63,0];b=[.11*math.cos(a),-.36,.11*math.sin(a)]
    c=[.11*math.cos(a+1.04),-.36,.11*math.sin(a+1.04)]
    tri([tip,b,c],4,[(.5,0),(0,1),(1,1)])
rod((0,.24,0),(0,.40,0),.12,3,14)
write('shore_quarry_drill')

# Finished stock: separated milled board edges, bundled straps; an evenly
# dressed stone billet with offset chipped arrises unlike raw round ore.
for i in range(3):
    box((0,.046+.079*i,0),(.68,.079,.225),0)
for x in [-.21,.21]:
    box((x,.125,0),(.048,.251,.232),7)
write('finished_planks')
section((0,.012,0),(0,.23,0),.218,.15,6)
write('dressed_block')
