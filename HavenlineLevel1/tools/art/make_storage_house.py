"""Bake the six-zone Havenline storehouse from the four approved 30f4f037 sheets. Requires Pillow and NumPy."""
from pathlib import Path
import numpy as np,math,random,struct,io,json
from PIL import Image
from collections import defaultdict
random.seed(90);rng=np.random.default_rng(90);out=Path(__file__).resolve().parents[2]/'assets/storage_house';out.mkdir(parents=True,exist_ok=True)
W=128;Y,X=np.mgrid[0:W,0:W];u=(X+.5)/W;v=(Y+.5)/W
pal=np.array([(153,76,30),(176,90,32),(113,60,27),(207,119,38),(31,64,149),(29,57,131),(222,230,240),(114,108,109),(77,77,84),(166,159,146),(215,183,127),(160,205,219),(224,181,102),(64,50,43),(233,147,53),(151,91,48)])
atlas=np.zeros((W*4,W*4,3),dtype='B')
for i,base in enumerate(pal):
 wood=i in (0,1,2,3,4,5,10,14,15);phase=math.tau*(u*4.2+.12*np.sin(5*v+i)+.16*np.sin(11*v-6*u+i));noise=rng.normal(0,1.6,(W,W))
 if wood:grain=7*np.sin(phase)+3*np.sin(phase*2.8)+5*np.sin(phase*6.1)*(abs(np.sin(phase))**4)+7*np.cos(1.8*v+u)
 else:grain=4*np.sin(5*u+3*v+i)+3*np.cos(2*u-4*v)+4*np.cos(13*u+8*v+i)
 c=base+(grain+noise)[:,:,None]*[1,.86,.67];r,k=divmod(i,4);atlas[r*W:(r+1)*W,k*W:(k+1)*W]=c.clip(0,255)
tex=io.BytesIO();Image.fromarray(atlas).save(tex,'JPEG',quality=91,subsampling=0)
V=lambda p:np.array(p,dtype=float)
groups=defaultdict(lambda:[[],[],[],[]]);G='Frame'
def face(points,mat,uv=None):
 pts=np.array(points);cross=np.cross(pts[1]-pts[0],pts[2]-pts[0]);n=cross/max(1e-8,np.linalg.norm(cross));P,N,U,F=groups[G];base=len(P)
 if uv is None:uv=[(.08,.06),(.92,.06),(.92,.94),(.08,.94)] if len(pts)==4 else [(.5+.43*np.cos(math.tau*i/len(pts)),.5+.43*np.sin(math.tau*i/len(pts))) for i in range(len(pts))]
 r,c=divmod(mat,4)
 for pt,xy in zip(pts,uv):
  P.append(pt);N.append(n);U.append(((c+xy[0])/4,(r+xy[1])/4))
 for i in range(1,len(pts)-1):F.append([base,base+i,base+i+1])
def rings(rr,mat,caps=True):
 for a,b in zip(rr,rr[1:]):
  for i in range(len(a)):k=(i+1)%len(a);face([a[i],a[k],b[k],b[i]],mat)
 if caps:face(rr[0][::-1],mat);face(rr[-1],mat)
def timber(a,b,w,h,mat,w2=None,h2=None):
 a,b=V(a),V(b);t=b-a;t/=np.linalg.norm(t);k=V((0,1,0)) if abs(t[1])<.92 else V((0,0,-1));r=np.cross(k,t);r/=np.linalg.norm(r);up=np.cross(t,r)
 shape=[(-.40,-.5),(.40,-.5),(.5,-.39),(.5,.40),(.39,.5),(-.40,.5),(-.5,.40),(-.5,-.39)]
 rr=[]
 for o,ww,hh in [(a,w,h),(b,w if w2 is None else w2,h if h2 is None else h2)]:
  rr.append([o+r*x*ww+up*y*hh for x,y in shape])
 rings(rr,mat)
def ell(o,sz,mat,n=8):
 o,sz=V(o),V(sz);rr=[]
 for phi in [-1.40,-.60,.16,.80,1.45]:
  rr.append([o+sz*V([np.cos(phi)*np.cos(-math.tau*i/n),np.sin(phi),np.cos(phi)*np.sin(-math.tau*i/n)]) for i in range(n)])
 rings(rr,mat)
def write(name,subset):
 blob=bytearray();views=[];ac=[]
 def view(data):
  while len(blob)%4:blob.append(0)
  views.append({'buffer':0,'byteOffset':len(blob),'byteLength':len(data)});blob.extend(data);return len(views)-1
 def acc(arr,typ,ct):
  a=np.asarray(arr,dtype='<u2' if ct==5123 else '<f4');e={'type':typ,'componentType':ct,'count':len(a),'bufferView':view(a.tobytes())}
  if typ=='VEC3':e.update(min=a.min(0).tolist(),max=a.max(0).tolist())
  ac.append(e);return len(ac)-1
 nodes=[];meshes=[]
 for key in subset:
  p,n,uv,f=groups[key];prim={'attributes':{'POSITION':acc(p,'VEC3',5126),'NORMAL':acc(n,'VEC3',5126),'TEXCOORD_0':acc(uv,'VEC2',5126)},'indices':acc(np.ravel(f),'SCALAR',5123),'material':0};meshes.append({'name':key,'primitives':[prim]});nodes.append({'mesh':len(meshes)-1,'name':key})
 im=view(tex.getvalue())
 doc={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':meshes,'materials':[{'name':'Storage house painted timber, blue steel, powder and iron','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':.87}}],'images':[{'bufferView':im,'mimeType':'image/jpeg'}],'textures':[{'source':0}],'buffers':[{'byteLength':len(blob)}],'accessors':ac,'bufferViews':views}
 doc['materials'][0].update(emissiveTexture={'index':0},emissiveFactor=[.055,.055,.055])
 while len(blob)%4:blob.append(0)
 js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*(-len(js)%4);(out/(name+'.glb')).write_bytes(struct.pack('<4sIII4s',b'glTF',2,28+len(blob)+len(js),len(js),b'JSON')+js+struct.pack('<I4s',len(blob),b'BIN\0')+blob)
 print(name,sum(len(groups[g][3]) for g in subset))

def column(a,b,r,mat,sides=12,r2=None):
    a,b=V(a),V(b);t=b-a;t=t/np.linalg.norm(t)
    ref=V((0,0,1)) if abs(t[1])>.94 else V((0,1,0))
    raxis=np.cross(t,ref);raxis/=np.linalg.norm(raxis);up=np.cross(t,raxis)
    rings([[c+sz*(raxis*cos+up*sin) for cos,sin in [(math.cos(math.tau*j/sides),math.sin(math.tau*j/sides)) for j in range(sides)]] for c,sz in [(a,r),(b,r if r2 is None else r2)]],mat)

def trim(a,b,w,mat):
    timber(a,b,w,w,mat)
def box(x,y,z,w,h,d,mat):
    # Bevelled panel section around a vertical or horizontal piece.
    timber((x-w/2,y,z),(x+w/2,y,z),d,h,mat)
def fast(x,y,z,r=.033):
    ell((x,y,z),(r,r,r),9,6)
def rope(x,z,y):
    for turn in range(2):
        rr=[]
        for j in range(33):
            a=math.tau*j/32
            c=V([x+.137*math.cos(a),y+.037*turn+.037*j/32,z+.137*math.sin(a)])
            radial=V([math.cos(a),0,math.sin(a)])
            rr.append([c+(.025+.003*math.cos(3*math.tau*k/8-a*7))*(radial*math.cos(math.tau*k/8)+V([0,1,0])*math.sin(math.tau*k/8)) for k in range(8)])
        rings(rr,10)
def powder(points,width,height):
    # Long continuous ridges with rounded irregular droops and soft normals.
    start=len(groups[G][0]);points=np.asarray(points)
    rr=[]
    for i,c in enumerate(points):
        f=i/max(1,len(points)-1); tangent=points[min(i+1,len(points)-1)]-points[max(0,i-1)]
        tangent/=np.linalg.norm(tangent)
        side=np.cross(tangent,V([0,1,0]));side/=np.linalg.norm(side)
        up=np.cross(side,tangent)
        radius=(.78+.22*math.cos(12*f)**2)*(.76+.24*min(1.,f*20,(1.-f)*20))
        rr.append([c+side*(width*radius*math.cos(math.tau*j/12))+up*(height*(1+.12*math.sin(17*f))*math.sin(math.tau*j/12)) for j in range(12)])
    if np.dot(np.cross(rr[0][1]-rr[0][0],rr[0][2]-rr[0][0]),points[-1]-points[0])<0:rr=[r[::-1] for r in rr]
    rings(rr,6)
    normals=defaultdict(lambda:np.zeros(3));verts,ns,_,faces=groups[G]
    for tri in faces:
        if tri[0]<start:continue
        for idx in tri:normals[tuple(np.round(verts[idx],5))]+=ns[idx]
    for i in range(start,len(verts)):
        n=normals[tuple(np.round(verts[i],5))];ns[i]=n/max(1e-8,np.linalg.norm(n))
def crate_symbol(x,y,z,s,mat):
    lines=[((0,1),(.85,.55)),((.85,.55),(.85,-.43)),((.85,-.43),(0,-1)),((0,-1),(-.85,-.43)),((-.85,-.43),(-.85,.55)),((-.85,.55),(0,1)),((0,0),(0,-1)),((-.85,.55),(0,0)),((0,0),(.85,.55))]
    for a,b in lines:trim((x+s*a[0],y+s*a[1],z),(x+s*b[0],y+s*b[1],z),s*.12,mat)

G='Floor'
for i in range(14):
    x=-1.54+(i+.5)*3.08/14;box(x,.09,0,3.08/14-.005,.14,2.35,[0,1,15][i%3])
# Broad gray flagstones line the clear delivery aisle in the cutaway
# board. A thin reveal between stones leaves the surrounding timber intact.
for row in range(4):
    for col in range(3):
        x=(col-1)*.504
        z=-.45+row*.442
        box(x,.156,z,.497,.024+(row+col)%3*.0015,.435,7)
for x in (-1.50,1.50):
    for z in (-1.10,1.10):
        column((x,.04,z),(x,1.92,z),.14,1)
        for j in (0,1,2):
            a=j*2.0+.6;ell((x+.12*math.cos(a),.06,z+.12*math.sin(a)),(.16,.07,.13),6,8)
G='StarterRope'
for x in (-1.50,1.50):
    for z in (-1.10,1.10):
        for y in (.23,1.65):rope(x,z,y)
G='Footing'
for z in (-1.105,1.105):
    for i in range(10):
        x=(i-4.5)*.297
        if z>0 and abs(x)<.75:continue
        box(x,.14+(i%3)*.007,z,.288,.254+(i%3)*.018,.225,7)
for x in (-1.50,1.50):
    for j in range(7):box(x,.14+(j%3)*.005,(j-3)*.291,.225,.258,.287,7)
for x in (-1.50,1.50):
    for z in (-1.10,1.10):
        for y in (.32,1.7):
            column((x,y-.075,z),(x,y+.075,z),.157,8)
            for sx,sz in [(0,1),(1,0),(-1,0),(0,-1)]:fast(x+.15*sx,y,z+.15*sz)
for sign in (-1,1):
    G='RightWall' if sign==1 else 'LeftWall'
    x=1.49*sign
    for j in range(9):box(x,.99,(j-4)*.241,.12,1.68,.242,[0,1,15][j%3])
    G='RightArmor' if sign==1 else 'LeftArmor'
    for row in range(3):
        for j in range(3):
            z=(j-1)*.704;y=.535+row*.491
            box(x+sign*.064,y,z,.081,.485,.695,4 if (j+row)%2 else 5)
            for a in (-1,1):fast(x+sign*.112,y-.183,z+a*.275,.018)
    G='RightDetail' if sign==1 else 'LeftDetail'
    # Service hatch and port share their chunky amber perimeter frame.
    z=-.02;y=1.05 if sign==1 else 1.28
    w=.77 if sign==1 else 1.0;h=.64 if sign==1 else .35
    box(x+sign*.12,y,z,.10,h,w,14)
    box(x+sign*.177,y,z,.032,h-.115,w-.12,8 if sign==1 else 11)
    if sign==1:
        for j in range(5):box(x+sign*.205,y+(j-2)*.080,z,.036,.038,w-.26,13)
    else:box(x+sign*.20,y,z,.04,h-.12,.038,3)
    for a in (-1,1):
        for b in (-1,1):fast(x+sign*.17,y+a*(h*.5-.035),z+b*(w*.5-.045),.023)
G='BackWall'
for i in range(12):box((i-5.5)*.246,1.,-1.095,.244,1.72,.13,[1,0,15][i%3])
G='BackArmor'
for row in range(3):
    for i in range(4):
        x=(i-1.5)*.724;y=.53+row*.485
        box(x,y,-1.176,.715,.476,.071,4+(row+i)%2)
        for s in (-1,1):fast(x+s*.29,y+.17,-1.215,.021)
G='Facade'
for s in (-1,1):
    for i in range(3):box(s*(.93+i*.204),1.0,1.09,.197,1.72,.135,[1,0,15][i])
    timber((s*.80,.14,1.14),(s*.80,1.80,1.14),.13,.14,3)
G='FacadeArmor'
for s in (-1,1):
    for j in range(3):
        box(s*1.161,.57+j*.48,1.17,.53,.467,.064,4+(j%2))
        for k in (-1,1):fast(s*1.16+k*.20,.57+j*.48+.15,1.214,.021)
G='Track'
column((-1.37,1.80,1.225),(1.37,1.80,1.225),.055,8)
for x in (-1.28,0,1.28):fast(x,1.80,1.266)
for sign,name in [(-1,'DoorLeft'),(1,'DoorRight')]:
    G=name
    for j in range(4):
        x=sign*(.115+.197*j)
        box(x,.958,1.208,.198,1.52,.095,4 if j%2 else 5)
    for y in (.248,1.66):box(sign*.40,y,1.206,.788,.064,.13,5)
    box(sign*.12,.945,1.275,.110,.325,.065,8)
    column((sign*.12,.835,1.326),(sign*.12,1.052,1.326),.026,13)
    for y in (.835,1.052):fast(sign*.12,y,1.335,.022)
    box(sign*.60,1.75,1.245,.081,.165,.072,8);fast(sign*.60,1.79,1.29,.026)
    G=name+'Armor'
    for x in (.077,.728):box(sign*x,.96,1.265,.065,1.46,.045,4)
    for y in (.26,1.655):box(sign*.40,y,1.263,.72,.070,.048,4)
    for x in (.085,.699):
        for y in (.27,1.635):fast(sign*x,y,1.302,.025)
G='Roof'
for s in (-1,1):
    # Broad blue planks run down the pitched roof and remain recognizable between snowbanks.
    for i in range(11):
        z=(i-5)*.255
        timber((s*.008,2.76,z),(s*1.755,1.96,z),.256,.115,4 if i%3 else 5)
    timber((s*1.72,1.89,-1.42),(s*1.72,1.89,1.42),.13,.13,3)
for z in (-1.34,1.34):
    for s in (-1,1):
        timber((0,2.75,z),(s*1.74,1.93,z),.13,.14,3)
        pts=[(s*1.70*t/20,2.832-.792*t/20,z+.018*math.sin(t*.53)) for t in range(21)]
        powder(pts,.142,.099)
# A continuous wind-loaded ridge laps irregularly down both slopes.
# These sections have three deep lobes and a fourth shallower one on each
# side, rather than a tubular line along the peak.
ridge=[]
for j in range(45):
    z=-1.38+2.76*j/44
    left=.30+sum(w*math.exp(-((z-c)/r)**2) for c,r,w in [(-.93,.24,.30),(-.13,.25,.39),(.61,.22,.26),(1.15,.14,.17)])
    right=.30+sum(w*math.exp(-((z-c)/r)**2) for c,r,w in [(-1.03,.21,.29),(-.39,.18,.27),(.35,.29,.44),(.99,.21,.31)])
    ring=[]
    for k in range(24):
        a=math.tau*k/24
        x=(left if math.cos(a)<0 else right)*math.cos(a)
        y=2.83-.455*abs(x)+(.165 if math.sin(a)>0 else .044)*math.sin(a)+.012*math.cos(z*10)
        ring.append((x,y,z))
    ridge.append(ring)
start=len(groups[G][0]);rings(ridge,6)
normals=defaultdict(lambda:np.zeros(3));verts,ns,_,triangles=groups[G]
for tri in triangles:
    if tri[0]>=start:
        for idx in tri:normals[tuple(np.round(verts[idx],5))]+=ns[idx]
for i in range(start,len(verts)):
    n=normals[tuple(np.round(verts[i],5))];ns[i]=n/max(1e-8,np.linalg.norm(n))
# Sculpted winter banks scallop each eave, leaving a visible painted blue field.
for side in (-1,1):
    powder([(side*(1.706+.027*math.cos(j*.67)),2.002+.023*math.sin(j*.81),-1.36+j*2.72/30) for j in range(31)],.122,.089)
G='Gables'
for z in (-1.102,1.116):
    for i in range(13):
        x=(i-6)*.235;h=.77*(1-abs(x)/1.57)
        box(x,1.885+h/2,z,.233,h+.081,.13,1 if i%2 else 0)
G='GableArmor'
for z in (-1.191,1.195):
    for i in range(9):
        x=(i-4)*.32;h=.72*(1-abs(x)/1.57)
        box(x,1.898+h/2,z,.315,h+.047,.042,4 if i%2 else 5)
G='Signs'
# An octagonal gold-edged leather plaque carries a raised little crate.
column((0,2.173,1.237),(0,2.173,1.304),.278,2,8)
column((0,2.173,1.300),(0,2.173,1.328),.249,12,8)
column((0,2.173,1.324),(0,2.173,1.351),.223,15,8)
for xy,mat in [([(-.13,.062),(0,.127),(.13,.062),(0,-.005)],3),([(-.13,.062),(0,-.005),(0,-.137),(-.13,-.063)],1),([(0,-.005),(.13,.062),(.13,-.063),(0,-.137)],0)]:
    face([(x,2.178+y,1.360) for x,y in reversed(xy)],mat)
crate_symbol(0,2.177,1.369,.15,12)
for x in (-.177,.177):fast(x,2.173,1.351,.018)
column((0,2.18,-1.17),(0,2.18,-1.25),.195,3,16)
column((0,2.18,-1.245),(0,2.18,-1.263),.147,13,16)
for j in range(3):box(0,2.18+(j-1)*.066,-1.276,.235,.025,.025,1)
G='RoofStuds'
for s in (-1,1):
    for j in range(10):fast(s*1.515,2.119,(j-4.5)*.256,.027)
G='Shelves'
# Three side bays on either side and the back rack leave one unobstructed central aisle.
for s in [-1,1]:
    for z in (-.69,.05,.78):
        for y in (.27,.70):
            box(s*1.157,y,z,.558,.09,.681,1)
            box(s*.886,y+.045,z,.041,.114,.676,3)
        for dz in (-.334,.334):
            for x in (s*1.414,s*.902):
                box(x,.678,z+dz,.067,.899,.060,3)
    # The two active left-hand bins are open from above. The stock,
    # especially the rock pair, must remain readable from the gameplay camera.
    if s>0:
        for i in range(3):box(s*1.15,1.20,(i-1)*.733,.63,.082,.71,1)
    else:
        for z in (-.69,.05,.78):
            box(-1.44,1.19,z,.08,.075,.71,1)
for x in (-.68,0,.68):
    for y in (.259,.716,1.24):
        if x==0 and y>1.2:continue
        box(x,y,-.885,.655,.085,.42,1)
        box(x,y+.045,-.66,.654,.095,.045,3)
    for dx in (-.321,.321):box(x+dx,.81,-.711,.045,1.13,.053,3)
G='AdvancedShelves'
for x in (-.68,0,.68):
    box(x,.445,-.661,.568,.319,.040,5);box(x,.503,-.634,.134,.029,.027,9)
for side in (-1,1):
    for z in (-.66,.065,.789):
        box(side*.873,.462,z,.044,.31,.577,5);box(side*.845,.505,z,.036,.033,.13,8)
# The loading apron is level with the camp and finishes before the
# purchase/deposit location. A recessed dark mat is rimmed by pale brass.
G='Apron'
box(0,.023,1.50,1.58,.046,.56,12)
box(0,.05,1.50,1.50,.025,.50,13)
for (a,b) in [((0,-.15),(.13,-.072)),((.13,-.072),(.13,.074)),((.13,.074),(0,.15)),((0,.15),(-.13,.074)),((-.13,.074),(-.13,-.072)),((-.13,-.072),(0,-.15)),((0,0),(0,.15)),((-.13,-.072),(0,0)),((0,0),(.13,-.072))]:
    trim((a[0],.067,1.5+a[1]),(b[0],.067,1.5+b[1]),.014,12)
G='CutawayPanels'
# Preserve the architectural edge of the building in roof-off view.
for z in (-.74,0,.74):
    box(1.50,.53,z,.13,.84,.726,0)
    for y in (.32,.73):box(1.58,y,z,.045,.34,.707,5)
for x in (-1.18,1.18):
    box(x,.48,1.094,.62,.67,.11,1)
G='InteriorArmor'
for x in (-1.09,-.36,.36,1.09):
    box(x,1.42,-1.013,.715,.78,.055,5)
for z in (-.73,0,.73):box(-1.412,1.37,z,.046,.83,.71,5)
G='Headers'
for x,z,width in [(-1.40,.46,.46),(-1.39,-.55,.51),(-.68,-.82,.52),(0,-.82,.52),(.68,-.82,.52),(1.12,.46,.44)]:
    box(x,1.38,z,width,.147,.065,2)
    box(x,1.38,z+.044,width-.025,.125,.031,12)
write('camp_storehouse',list(groups))
