"""Regenerate the eastern tower, pivot launcher and bolt with Python, NumPy and Pillow."""
from pathlib import Path
import numpy as np,math,random,struct,io,json
from PIL import Image
from collections import defaultdict
random.seed(90);rng=np.random.default_rng(90);out=Path(__file__).resolve().parents[2]/'assets/field_world';out.mkdir(parents=True,exist_ok=True)
W=128;Y,X=np.mgrid[0:W,0:W];u=(X+.5)/W;v=(Y+.5)/W
pal=np.array([(147,88,46),(179,114,62),(101,60,39),(208,146,78),(73,106,148),(53,83,121),(227,235,242),(121,118,114),(91,95,102),(154,147,132),(112,84,54),(103,123,147),(184,178,164),(74,63,55),(180,148,99),(131,76,44)])
atlas=np.zeros((W*4,W*4,3),dtype='B')
for i,base in enumerate(pal):
 wood=i in (0,1,2,3,10,14,15);phase=math.tau*(u*4.2+.12*np.sin(5*v+i)+.16*np.sin(11*v-6*u+i));noise=rng.normal(0,1.6,(W,W))
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
def post(x,z):
 G='';rr=[]
 for y,s in [(0,.20),(.035,.235),(.22,.19),(.25,.15)]:
  ps=[]
  for i in range(8):
   a=-math.tau*i/8+math.pi/8;ps.append(V([x+math.cos(a)*s,y,z+math.sin(a)*s]))
  rr.append(ps)
 rings(rr,7)
 for a in [0,2.4,4.4]:
  ell([x+.16*math.cos(a),.026,z+.16*math.sin(a)],[.115,.036,.084],6,7)
G='Footings'
for x in [-.63,.63]:
 for z in [-.63,.63]:post(x,z)
G='Trestle'
for sx in [-1,1]:
 for sz in [-1,1]:
  timber([sx*.63,.17,sz*.63],[sx*.535,1.52,sz*.535],.225,.225,0,.204,.204)
  for y in [.34,1.38]:
   ell([sx*.648,y,sz*.72],[.048,.046,.025],8)
for side in range(4):
 def xyz(s,y,out=0):
  a=[(s,y,.59+out),(.59+out,y,-s),(-s,y,-.59-out),(-.59-out,y,s)][side];return V(a)
 for d in [-1,1]:
  off=.026*d
  timber(xyz(d*.53,.36,off),xyz(-d*.50,1.41,off),.128,.097,1 if d==1 else 0)
 timber(xyz(-.64,1.42,.025),xyz(.64,1.42,.025),.15,.17,1)
 for d in [-1,1]:ell(xyz(d*.53,1.43,.108),[.043,.04,.043],9,7)
G='Gallery'
for i in range(9):
 x=-.65+i*.163;timber([x,1.54,-.71],[x,1.54,.72],.158,.09,random.choice([0,1,3]))
for x in [-.58,.58]:
 for z in [-.58,.58]:timber([x,1.50,z],[x,2.60,z],.145,.14,1)
for side in range(4):
 spans=[(-.66,-.37),(.37,.66)] if side==0 else [(-.68,.68)]
 for lo,hi in spans:
  timber(xyz(lo,1.89,.035),xyz(hi,1.89,.035),.13,.12,3)
  timber(xyz(lo,1.61,.033),xyz(hi,1.61,.033),.10,.12,1)
  width=hi-lo
  for i in range(max(2,round(width/.16))):
   x=lo+(i+.5)*width/max(2,round(width/.16));timber(xyz(x,1.62,.02),xyz(x,1.85,.02),width/max(2,round(width/.16))-.009,.068,random.choice([0,1,2]))
# Timber trestle and pintle anchor the working launcher to the watch deck.
for ax,az in [(-.21,-.18),(.21,-.18),(0,.24)]:
 timber([ax,1.57,az],[0,1.96,0],.075,.085,0)
timber([0,1.88,0],[0,2.10,0],.115,.115,8)
# Sloping access ladder with separately socketed rungs.
for x in [-.21,.21]:timber([x,.024,1.01],[x,1.70,.71],.065,.079,1)
for i in range(7):
 y=.17+i*.213;z=1.01-.30*y/1.676;timber([-.22,y,z],[.22,y,z],.061,.057,3)
G='Eaves'
for side in range(4):timber(xyz(-.79,2.60,.16),xyz(.79,2.60,.16),.11,.11,0)
G='SlateRoof'
def roofpoint(side,u,t):
 half=.85*(1-t)+.03*t;s=(2*u-1)*half
 return V([(s,2.60+.55*t,half),(half,2.60+.55*t,-s),(-s,2.60+.55*t,-half),(-half,2.60+.55*t,s)][side])
for side in range(4):
 for tier in range(4):
  lo=tier/4;hi=(tier+1)/4;cols=7-tier
  for col in range(cols):
   u0=(col+.024)/cols;u1=(col+.977)/cols
   t0=lo+.007;t1=hi-.005
   a,b,c,d=[roofpoint(side,u,t) for u,t in [(u0,t0),(u1,t0),(u1,t1),(u0,t1)]]
   face([d,c,b,a][::-1],4 if (col+side+tier)%3 else 5)
   # reverse cross direction case (slopes are outward); include underside and fascia.
   face([a,b,c,d][::-1],4 if (col+side+tier)%3 else 5)
   face([a,a-V((0,.045,0)),b-V((0,.045,0)),b],5)
for x in [-1,1]:
 for z in [-1,1]:
  a=V([x*.84,2.60,z*.84]);b=V([0,3.18,0]);timber(a,b,.097,.105,1)
  ridge=b-a;across=V([z,0,-x])/np.sqrt(2)
  for lo,hi,w in [(-.015,.28,.090),(.33,.77,.083),(.81,.97,.070)]:
   rr=[]
   for i in range(10):
    t=i/9;v=lo+(hi-lo)*t;center=a+ridge*v+V([0,.056,0]);wx=w*(.25+.75*math.sin(math.pi*t)**.30)*(1+.19*math.sin(9*t+x-z))
    crown=.049*(.35+.65*math.sin(math.pi*t)**.44);ring=[]
    for k in range(8):
     angle=math.tau*k/8;ring.append(center+across*np.cos(angle)*wx+V([0,crown*np.sin(angle),0]))
    rr.append(ring)
   # Reverse cross-sections when the diagonal points the other way.
   if np.dot(np.cross(rr[0][1]-rr[0][0],rr[0][2]-rr[0][0]),ridge)<0:rr=[r[::-1] for r in rr]
   rings(rr,6)
ell([0,3.18,0],[.118,.087,.114],6,9)
G='Launcher'
timber([0,-.10,-.31],[0,.02,.63],.10,.115,2);timber([0,.02,.0],[0,.04,.61],.047,.07,9)
for sx in [-1,1]:
 timber([0,0,.22],[.24*sx,.01,.19],.064,.077,0)
 timber([.24*sx,.01,.19],[.39*sx,.01,.04],.047,.05,1)
 timber([.39*sx,.01,.04],[0,.025,-.19],.014,.014,10)
G='Bolt'
timber([0,0,-.23],[0,0,.23],.032,.032,1)
for i in range(3):
 a=math.tau*i/3;r=V([np.cos(a),np.sin(a),0]);p0=V([0,0,-.22]);p1=V([0,0,-.07]);p2=p0+r*.048
 face([p0,p1,p2],12);face([p2,p1,p0],12)
for i in range(4):
 a=math.tau*i/4;bb=math.tau*(i+1)/4
 face([[.068*np.cos(a),.068*np.sin(a),.15],[.068*np.cos(bb),.068*np.sin(bb),.15],[0,0,.32]],8)
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
 doc={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':meshes,'materials':[{'name':'Painted timber, slate, snow and iron','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':.87}}],'images':[{'bufferView':im,'mimeType':'image/jpeg'}],'textures':[{'source':0}],'buffers':[{'byteLength':len(blob)}],'accessors':ac,'bufferViews':views}
 if name=='eastern_watchtower':doc['materials'][0].update(emissiveTexture={'index':0},emissiveFactor=[.10,.10,.10])
 while len(blob)%4:blob.append(0)
 js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*(-len(js)%4);(out/(name+'.glb')).write_bytes(struct.pack('<4sIII4s',b'glTF',2,28+len(blob)+len(js),len(js),b'JSON')+js+struct.pack('<I4s',len(blob),b'BIN\0')+blob)
 print(name,sum(len(groups[g][3]) for g in subset))
write('eastern_watchtower',['Footings','Trestle','Gallery','Eaves','SlateRoof'])
write('tower_launcher',['Launcher']);write('tower_bolt',['Bolt'])
