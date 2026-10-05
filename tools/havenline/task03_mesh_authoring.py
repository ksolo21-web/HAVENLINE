"""Authored HAVENLINE reference-model candidates. No runtime primitive resources.

Explicit modeled shells, profiles, bevels, rope sweeps and snow solids. All
pieces are closed and outward-facing; component topology is independently tested.
Model-space is Godot/glTF: Y up, fronts face -Z.
"""
from __future__ import annotations
import math, json, struct, hashlib
from dataclasses import dataclass
from pathlib import Path
import numpy as np

TAU=math.tau
PALETTE={
 'snow':((.86,.94,1.),0.,.82), 'cream':((.96,.84,.63),0.,.72),
 'wood':((.44,.20,.105),0.,.78), 'wood_light':((.68,.37,.17),0.,.72),
 'metal':((.15,.23,.30),.72,.30), 'blue':((.075,.32,.60),.18,.40),
 'cyan':((.10,.68,.82),.12,.34), 'orange':((.96,.34,.08),.08,.38),
 'yellow':((1.,.68,.08),.05,.42),'green':((.12,.64,.29),.05,.48),
 'red':((.78,.12,.10),.05,.50),'dark':((.035,.07,.11),.18,.42)}

def unit(a):
 a=np.asarray(a,float);return a/max(np.linalg.norm(a),1e-15)

def basis_from_y(a,b):
 y=unit(np.asarray(b)-a);tmp=np.array([0.,0.,1.])
 if abs(y@tmp)>.95:tmp=np.array([1.,0.,0.])
 x=unit(np.cross(y,tmp));z=np.cross(x,y)
 return np.column_stack([x,y,z])

def rotation(y=0.,x=0.,z=0.):
 cy,sy,cx,sx,cz,sz=math.cos(y),math.sin(y),math.cos(x),math.sin(x),math.cos(z),math.sin(z)
 return np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])@np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])

@dataclass
class Part:
 name:str
 material:str
 vertices:np.ndarray
 faces:np.ndarray
 normals:np.ndarray
 colors:np.ndarray

class Model:
 def __init__(self,name):self.name=name;self.parts=[]
 def add(self,name,material,v,f,center=(0,0,0),matrix=None,tint=(1,1,1),smooth=True,variation=0.):
  v=np.asarray(v,float);f=np.asarray(f,np.int32)
  p=v[f];cross=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);keep=np.linalg.norm(cross,axis=1)>1e-12
  f=f[keep]
  # Orient each solid using actual topology, never the supplied normal field.
  p=v[f];vol=np.sum(np.einsum('ij,ij->i',p[:,0],np.cross(p[:,1],p[:,2])))/6
  if vol<0:f=f[:,[0,2,1]]
  if matrix is not None:v=v@np.asarray(matrix).T
  v=v+np.asarray(center)
  p=v[f];cross=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
  if smooth:
   n=np.zeros_like(v)
   for i in range(3):np.add.at(n,f[:,i],cross)
   n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-15)
  else:
   v=v[f].reshape(-1,3);n=np.repeat(cross/np.maximum(np.linalg.norm(cross,axis=1,keepdims=True),1e-15),3,axis=0);f=np.arange(len(v)).reshape(-1,3)
  col=np.ones((len(v),4));col[:,:3]*=np.asarray(tint)
  if variation:
   a=np.sin(v[:,0]*7.1+v[:,1]*2.7+v[:,2]*5.3)*.65+np.sin(v[:,0]*17.2-v[:,2]*8.1)*.35
   col[:,:3]*=(1+variation*a[:,None])
  col=np.clip(col,0,1)
  self.parts.append(Part(name,material,v,f,n,col))
  return self.parts[-1]
 def loft(self,name,mat,profile,center=(0,0,0),segments=16,radii=(1,1),matrix=None,tint=(1,1,1),phase=0.,variation=0.):
  v=[];rows=[]
  for y,r in profile:
   if abs(r)<1e-10:
    rows.append([len(v)]);v.append([0,y,0])
   else:
    row=[]
    for i in range(segments):
     a=TAU*i/segments+phase;row.append(len(v));v.append([r*math.cos(a)*radii[0],y,r*math.sin(a)*radii[1]])
    rows.append(row)
  f=[]
  for a,b in zip(rows,rows[1:]):
   if len(a)==1:
    for i in range(segments):f.append([a[0],b[(i+1)%segments],b[i]])
   elif len(b)==1:
    for i in range(segments):f.append([a[i],a[(i+1)%segments],b[0]])
   else:
    for i in range(segments):
     j=(i+1)%segments;f.extend([[a[i],a[j],b[j]],[a[i],b[j],b[i]]])
  if len(rows[0])>1:
   c=len(v);v.append([0,profile[0][0],0])
   for i in range(segments):f.append([c,rows[0][(i+1)%segments],rows[0][i]])
  if len(rows[-1])>1:
   c=len(v);v.append([0,profile[-1][0],0])
   for i in range(segments):f.append([c,rows[-1][i],rows[-1][(i+1)%segments]])
  return self.add(name,mat,v,f,center,matrix,tint,True,variation)
 def ring(self,name,mat,profile,center=(0,0,0),segments=24,matrix=None,tint=(1,1,1),radii=(1,1)):
  v=[];f=[]
  for r,y in profile:
   for i in range(segments):
    a=TAU*i/segments;v.append([r*math.cos(a)*radii[0],y,r*math.sin(a)*radii[1]])
  k=len(profile)
  for j in range(k):
   q=(j+1)%k
   for i in range(segments):
    a=j*segments+i;b=j*segments+(i+1)%segments;c=q*segments+(i+1)%segments;d=q*segments+i
    f.extend([[a,b,c],[a,c,d]])
  return self.add(name,mat,v,f,center,matrix,tint,True)
 def bevel_box(self,name,mat,size,center=(0,0,0),bevel=.03,matrix=None,tint=(1,1,1),variation=0.):
  h=np.array(size)*.5;b=min(bevel,min(h)*.48);inner=h-b
  v=[];f=[];mapping={}
  for axis in range(3):
   u,w=[i for i in range(3) if i!=axis]
   for sign in [-1,1]:
    grid=[]
    for dv in [-h[w],-inner[w],inner[w],h[w]]:
     row=[]
     for du in [-h[u],-inner[u],inner[u],h[u]]:
      p=np.zeros(3);p[axis]=sign*h[axis];p[u]=du;p[w]=dv
      q=np.clip(p,-inner,inner);p=q+unit(p-q)*b
      key=tuple(np.round(p,10))
      if key not in mapping:mapping[key]=len(v);v.append(p)
      row.append(mapping[key])
     grid.append(row)
    for r in range(3):
     for c in range(3):
      a,bb,cc,d=grid[r][c],grid[r][c+1],grid[r+1][c+1],grid[r+1][c]
      for tri in [[a,bb,cc],[a,cc,d]]:
       pp=np.array([v[i] for i in tri]);nn=np.cross(pp[1]-pp[0],pp[2]-pp[0])
       if nn[axis]*sign<0:tri=tri[::-1]
       f.append(tri)
  return self.add(name,mat,v,f,center,matrix,tint,True,variation)
 def beam(self,name,mat,a,b,width,depth=None,bevel=.025,tint=(1,1,1)):
  a=np.array(a);b=np.array(b);self.bevel_box(name,mat,(width,np.linalg.norm(b-a),depth or width),(a+b)*.5,bevel,basis_from_y(a,b),tint)
 def tube(self,name,mat,path,radius,segments=8,tint=(1,1,1)):
  p=np.array(path,float);closed=np.linalg.norm(p[0]-p[-1])<1e-8
  if closed:p=p[:-1]
  v=[];f=[];radius=np.broadcast_to(radius,len(p))
  tangent=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0) if closed else np.gradient(p,axis=0)
  for q,t,r in zip(p,tangent,radius):
   B=basis_from_y(q,q+t)
   for i in range(segments):
    a=TAU*i/segments;v.append(q+B@np.array([r*math.cos(a),0,r*math.sin(a)]))
  for j in range(len(p) if closed else len(p)-1):
   k=(j+1)%len(p)
   for i in range(segments):
    a=j*segments+i;b=j*segments+(i+1)%segments;c=k*segments+(i+1)%segments;d=k*segments+i;f.extend([[a,b,c],[a,c,d]])
  if not closed:
   for row,flip in [(0,True),(len(p)-1,False)]:
    c=len(v);v.append(p[row]);r=row*segments
    for i in range(segments):
     tri=[c,r+i,r+(i+1)%segments];f.append(tri[::-1] if flip else tri)
  return self.add(name,mat,v,f,tint=tint)
 def stone(self,name,mat,center,size,seed=1,tint=(1,1,1)):
  old=self.bevel_box(name,mat,size,bevel=min(size)*.24,tint=tint)
  self.parts.pop()
  v=old.vertices.copy();h=np.asarray(size)*.5
  x,y,z=(v/h).T
  v[:,0]+=h[0]*(.055*y+.065*z+.04*y*z)*math.sin(seed*2.17)
  v[:,1]+=h[1]*(.06*x-.045*z+.025*x*z)*math.cos(seed*1.7)
  v[:,2]+=h[2]*(.035*x+.05*y-.035*x*y)*math.sin(seed*.91)
  return self.add(name,mat,v,old.faces,center,rotation(y=seed*.817,x=.06*math.sin(seed),z=.09*math.cos(seed)),tint,True,.065)
 def snow(self,name,center,radii,seed=0,segments=18,rings=5):
  rx,ry,rz=radii;v=[[0,-ry*.3,0]];rows=[[0]]
  for r in range(1,rings):
   theta=math.pi*r/rings;row=[]
   for i in range(segments):
    a=TAU*i/segments;scallop=1+.07*math.sin(a*5+seed)+.03*math.sin(a*9-seed*.73)
    x=rx*math.sin(theta)*math.cos(a)*scallop;z=rz*math.sin(theta)*math.sin(a)*scallop
    y=-math.cos(theta)*ry
    if y<0:y*=.3
    y+=ry*.08*math.sin(3*a+seed)*math.sin(theta)**3
    row.append(len(v));v.append([x,y,z])
   rows.append(row)
  rows.append([len(v)]);v.append([0,ry,0]);f=[]
  for a,b in zip(rows,rows[1:]):
   if len(a)==1:
    for i in range(segments):f.append([a[0],b[(i+1)%segments],b[i]])
   elif len(b)==1:
    for i in range(segments):f.append([a[i],a[(i+1)%segments],b[0]])
   else:
    for i in range(segments):
     j=(i+1)%segments;f.extend([[a[i],a[j],b[j]],[a[i],b[j],b[i]]])
  return self.add(name,'snow',v,f,center,tint=(.98,.995,1.))
 def arch(self,name,mat,center,outer=(.43,.50),inner=(.30,.44),depth=.14,steps=12,tint=(1,1,1)):
  def points(w,h):
   return [(-w,-h),(w,-h)]+[(w*math.cos(t),w*math.sin(t)) for t in np.linspace(0,math.pi,steps+1)]
  outerp=points(*outer);innerp=points(*inner);n=len(outerp);v=[]
  for pts,z in [(outerp,-depth/2),(innerp,-depth/2),(outerp,depth/2),(innerp,depth/2)]:v.extend([[x,y,z] for x,y in pts])
  f=[]
  for i in range(n):
   j=(i+1)%n
   for a,b,c,d in [(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(j,i,2*n+i,2*n+j),(n+i,n+j,3*n+j,3*n+i)]:f.extend([[a,b,c],[a,c,d]])
  return self.add(name,mat,v,f,center,tint=tint,smooth=False)
 def log(self,name,a,b,radius=.11,seed=0,bindings=False):
  length=np.linalg.norm(np.array(b)-a);B=basis_from_y(a,b);C=(np.array(a)+b)*.5
  profile=[(-length/2,radius*.92),(-length/2+.025,radius),(length/2-.025,radius*.98),(length/2,radius*.88)]
  self.loft(name+'_bark','wood',profile,C,12,matrix=B,tint=(1.,.94,.90),variation=.13)
  for end in [-1,1]:
   c=C+B@np.array([0,end*length/2,0])
   self.loft(name+'_end','wood_light',[(-.007,0),(-.007,radius*.86),(.007,radius*.86),(.007,0)],c,16,matrix=B)
   for frac in [.3,.57,.76]:
    angles=np.linspace(0,TAU,25);pts=[c+B@np.array([radius*frac*math.cos(t),end*.012,radius*frac*math.sin(t)]) for t in angles]
    self.tube(name+'_growth','wood',pts,.0035,4,tint=(.8,.8,.8))
  if bindings:
   for u in [-.25,.25]:
    angles=np.linspace(0,TAU*1.9,45);pts=[C+B@np.array([(radius+.009)*math.cos(t),length*u+.015*t/TAU,(radius+.009)*math.sin(t)]) for t in angles]
    self.tube(name+'_binding','cream',pts,.013,6,tint=(.78,.70,.56))
 def metrics(self):
  v=np.concatenate([p.vertices for p in self.parts]);return dict(name=self.name,parts=len(self.parts),triangles=sum(len(p.faces) for p in self.parts),bounds_min=v.min(0).tolist(),bounds_max=v.max(0).tolist(),materials=sorted({p.material for p in self.parts}))
 def export_glb(self,path):
  data=bytearray();views=[];access=[];primitives=[];mats=[]
  def acc(arr,typ,ctype,target,bounds=False):
   while len(data)%4:data.append(0)
   off=len(data);raw=arr.tobytes();data.extend(raw);vi=len(views);views.append(dict(buffer=0,byteOffset=off,byteLength=len(raw),target=target));ai=len(access)
   item=dict(bufferView=vi,componentType=ctype,count=len(arr),type=typ)
   if bounds:item.update(min=arr.min(0).tolist(),max=arr.max(0).tolist())
   access.append(item);return ai
  for key in sorted({p.material for p in self.parts}):
   color,metal,rough=PALETTE[key]
   material=dict(name='HL_'+key,pbrMetallicRoughness=dict(baseColorFactor=[*color,1.],metallicFactor=metal,roughnessFactor=rough),doubleSided=False)
   if key in ('orange','yellow'):material['emissiveFactor']=([.70,.08,.005] if key=='orange' else [1.,.38,.012])
   mi=len(mats);mats.append(material);vs=[];ns=[];cs=[];fs=[];off=0
   for p in self.parts:
    if p.material!=key:continue
    vs.append(p.vertices);ns.append(p.normals);cs.append(p.colors);fs.append(p.faces+off);off+=len(p.vertices)
   v=np.concatenate(vs).astype('<f4');n=np.concatenate(ns).astype('<f4');c=np.concatenate(cs).astype('<f4');f=np.concatenate(fs).reshape(-1).astype('<u4')
   a=acc(v,'VEC3',5126,34962,True);b=acc(n,'VEC3',5126,34962);cc=acc(c,'VEC4',5126,34962);d=acc(f,'SCALAR',5125,34963)
   primitives.append(dict(attributes=dict(POSITION=a,NORMAL=b,COLOR_0=cc),indices=d,material=mi,mode=4))
  doc=dict(asset=dict(version='2.0',generator='HAVENLINE reference sculpt v3'),scene=0,scenes=[dict(nodes=[0])],nodes=[dict(name=self.name,mesh=0)],meshes=[dict(name=self.name,primitives=primitives)],materials=mats,accessors=access,bufferViews=views,buffers=[dict(byteLength=len(data))])
  js=json.dumps(doc,sort_keys=True,separators=(',',':')).encode();js+=b' '*((-len(js))%4);data+=b'\0'*((-len(data))%4)
  raw=struct.pack('<4sII',b'glTF',2,28+len(js)+len(data))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(data),b'BIN\0')+data
  Path(path).write_bytes(raw);return hashlib.sha256(raw).hexdigest()

def furnace():
 m=Model('hearth_vessel')
 for i in range(12):
  a=TAU*i/12;x,z=1.02*math.cos(a),.83*math.sin(a)
  m.stone('foundation_%02d'%i,'cream',(x,.115,z),(.40,.28,.35),i+20,tint=(.28,.33,.40))
  if i in (0,2,3,5,6,8,10):m.snow('base_powder_%02d'%i,(x,.24,z),(.22,.06,.17),i,12,4)
 m.loft('refractory_plinth','dark',[(.09,0),(.09,.78),(.14,.85),(.24,.85),(.27,.78),(.27,0)],segments=20,radii=(1.,.91))
 for step in range(3):m.bevel_box('front_step_%d'%step,'cream',(.84-step*.06,.13,.22),(0,.12+step*.075,-1.+step*.16),.03,tint=(.34,.38,.42))
 for j in range(10):
  a=TAU*j/10
  if j in (7,8):continue
  x,z=.55*math.cos(a),.50*math.sin(a)
  m.bevel_box('lower_shell_stave_%02d'%j,'metal',(.41,.82,.24),(x,.68,z),.065,rotation(y=-a+math.pi/2),tint=(.75,.69,.66),variation=.07)
 m.loft('upper_rounded_pressure_shell','metal',[(1.03,.52),(1.06,.65),(1.17,.69),(1.34,.64),(1.48,.49),(1.51,.44)],segments=24,radii=(1.,.92),tint=(.81,.77,.72),variation=.025)
 m.arch('firebox_outer_cast_frame','metal',(0,.70,-.60),(.43,.42),(.30,.35),.19,14,tint=(.91,.94,.95))
 m.arch('firebox_recessed_liner','wood_light',(0,.70,-.557),(.30,.35),(.257,.322),.10,14,tint=(.65,.72,.77))
 m.bevel_box('firebox_dark_back','dark',(.50,.62,.12),(0,.69,-.38),.045)
 for x in [-.20,0,.20]:m.beam('ember_grate_bar','metal',(x,.34,-.62),(x,.34,-.34),.035,.035,.008,tint=(.5,.45,.4))
 for i,x in enumerate([-.17,-.055,.06,.17]):
  h=[.32,.49,.40,.28][i]
  profiles=[(.35,0),(.385,.055),(.45,.068),(.35+h*.53,.050),(.35+h*.78,.026),(.35+h,0)]
  part=m.loft('flame_%d'%i,'orange',profiles,(x,0,-.50),12,radii=(.70,.55))
  vv=part.vertices.copy();ff=part.faces.copy();m.parts.pop();t=np.clip((vv[:,1]-.35)/h,0,1)
  vv[:,0]+=math.sin(i*2.7)*.075*t*t+.028*np.sin(t*5+i);vv[:,2]+=.025*np.sin(t*4+i)*t
  m.add('flame_%d'%i,'orange',vv,ff)
  m.loft('flame_heart_%d'%i,'yellow',[(.36,0),(.39,.038),(.48,.029),(.37+h*.58,0)],(x,0,-.55),10,radii=(.65,.55))
 for i in range(5):m.stone('glowing_coal_%d'%i,'orange',(-.20+.1*i,.345,-.50),(.09,.07,.12),40+i,tint=(.45,.24,.08))
 for y,r in [(.28,.66),(1.035,.70),(1.46,.51)]:
  m.ring('armor_hoop','metal',[(r-.018,y-.035),(r+.025,y-.035),(r+.044,y-.013),(r+.044,y+.033),(r+.014,y+.055),(r-.018,y+.055)],segments=24,radii=(1,.92),tint=(.94,.88,.78))
  for i in range(10):
   a=TAU*i/10
   if y<.5 and i in (7,8):continue
   c=((r+.05)*math.cos(a),y+.008,(r+.05)*.92*math.sin(a));end=np.array(c)+np.array([math.cos(a),0,math.sin(a)])*.020
   m.loft('hoop_rivet','cream',[(-.016,.029),(0,.039),(.016,.031)],c,8,matrix=basis_from_y(c,end),tint=(.48,.53,.59))
 for side in [-1,1]:
  for row in range(3):m.stone('firebox_jamb','cream',(side*.397,.38+row*.145,-.701),(.151,.14,.143),60+row+side,tint=(.38,.39,.41))
 for i,a in enumerate(np.linspace(.06,math.pi-.06,9)):
  center=(.40*math.cos(a),.70+.40*math.sin(a),-.698)
  m.bevel_box('arched_keystone_%02d'%i,'cream',(.15,.165,.152),center,.022,rotation(z=a-math.pi/2),tint=(.39+.015*math.sin(i),.40,.42),variation=.04)
 for i in range(8):
  a=TAU*i/8+.21;x,z=.659*math.cos(a),.607*math.sin(a)
  m.bevel_box('enamel_armor_tab','blue',(.115,.21,.065),(x,1.19,z),.021,rotation(y=-a+math.pi/2),tint=(.83,.68,.55))
  for y in [1.117,1.265]:m.loft('armor_tab_stud','cream',[(-.008,.018),(.006,.026),(.012,.02)],(x*1.027,y,z*1.027),8,matrix=basis_from_y((0,0,0),(math.cos(a),0,math.sin(a))),tint=(.48,.51,.56))
 m.loft('cap_transition','metal',[(1.49,.45),(1.53,.45),(1.61,.34),(1.64,.32)],segments=24,radii=(1,.94),tint=(.7,.71,.72))
 m.ring('chimney_wall','metal',[(.225,1.55),(.257,1.57),(.257,2.07),(.233,2.11),(.184,2.11),(.184,1.55)],(0,0,.10),24,tint=(.86,.89,.91))
 for y in [1.69,1.96,2.115]:m.ring('chimney_band','metal',[(.215,y-.025),(.269,y-.025),(.285,y),(.275,y+.037),(.215,y+.037)],(0,0,.10),24,tint=(1.,.96,.9))
 m.loft('chimney_dark_depth','dark',[(1.72,0),(1.72,.18),(1.74,.18),(1.74,0)],(0,0,.10),20)
 for j in range(6):
  a=TAU*j/6+.18;x,z=.55*math.cos(a),.48*math.sin(a)
  m.bevel_box('shoulder_clamp','wood_light',(.17,.36,.12),(x,1.27,z),.035,rotation(y=-a+math.pi/2,z=.10),tint=(.88,.73,.56))
  m.loft('clamp_stud','cream',[(-.014,.025),(.014,.035),(.027,.02)],(x,1.29,z),8,matrix=basis_from_y((0,0,0),(math.cos(a),0,math.sin(a))),tint=(.44,.47,.49))
 for side in [-1,1]:
  x=side*.70;path=[(x,.41,.15),(side*.85,.46,.15),(side*.90,.61,.15),(side*.90,1.18,.15),(side*.80,1.38,.15),(side*.51,1.41,.15)]
  m.tube('side_supply_pipe','metal',path,.067,10,tint=(.88,.79,.66))
  for y in [.62,1.13]:m.ring('pipe_coupling','wood_light',[(.069,-.035),(.087,-.035),(.087,.035),(.069,.035)],(side*.90,y,.15),12,tint=(.79,.68,.53))
 gauge=(.73,1.00,-.22);B=rotation(x=math.pi/2)
 m.loft('pressure_gauge_casing','wood_light',[(-.052,.13),(-.035,.15),(.035,.15),(.052,.13)],gauge,24,matrix=B,tint=(.85,.78,.65))
 m.loft('pressure_gauge_face','cream',[(-.006,.123),(.006,.123)],(.73,1.00,-.282),24,matrix=B)
 m.beam('gauge_hand','dark',(.73,1.0,-.294),(.78,1.075,-.294),.012,.012,.003)
 for j,(x,y,z) in enumerate([(-.89,.34,-.34),(-.89,.34,-.53),(-.89,.49,-.435)]):m.log('split_fuel_%d'%j,(x-.17,y,z),(x+.17,y,z),.077,j)
 for i,x in enumerate([-.57,.57]):
  m.bevel_box('rear_mount','wood',(.20,.45,.23),(x,.42,.63),.045,tint=(1,.98,.94))
  m.bevel_box('rear_mount_strap','metal',(.22,.075,.25),(x,.43,.63),.012)
 for i,(x,y,z,rx,rz) in enumerate([(-.45,1.41,.12,.27,.18),(.29,1.45,.36,.28,.18),(-.48,1.02,.38,.24,.16),(.84,1.35,.15,.13,.10),(-.92,.25,-.59,.20,.14)]):m.snow('shoulder_powder_%d'%i,(x,y,z),(rx,.12,rz),i+2,20,7)
 return m

def build_legacy(builder_type):
 model=furnace();builder=builder_type('hearth_vessel')
 for part in model.parts:builder.triangles(part.material,part.vertices,part.normals,part.faces.reshape(-1))
 builder.reference_model=model
 return builder

