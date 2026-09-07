#!/usr/bin/env python3
"""Deterministically author Havenline's winter environment replacement meshes.

Original GLBs are never modified. No cone/cube blockout is used as a visual fallback.
Geometry is authored as curved boughs, rounded joinery, layered roofs, masonry and
machined metal. Outputs remain CANDIDATES until actual in-engine visual review.
Requires numpy, scipy and Pillow. Coordinates: Y up, front +Z, metres.
"""
from __future__ import annotations
import hashlib, io, json, math, struct
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter, distance_transform_edt
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'HavenlineGodot/assets/environment_v2'
OUT.mkdir(parents=True,exist_ok=True)
TAU=math.tau

def norm(a):
    a=np.asarray(a,dtype=float)
    return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-10)
def color(c):return np.array([int(c[i:i+2],16)/255 for i in (0,2,4)])

# Original, tileable material maps; no downloaded art or generated-image mockups.
def texture(kind,base,size=256):
    yy,xx=np.mgrid[:size,:size]/size
    rng=np.random.default_rng(sum(map(ord,kind))+9031)
    fine=rng.random((size,size))-.5
    if kind=='wood':
        warp=xx+.025*np.sin(yy*TAU*2)+.009*np.sin(yy*TAU*7)
        h=.52+.11*np.sin(warp*TAU*22)+.07*np.sin(warp*TAU*71)+fine*.09
        for cx,cy in [(0.23,.34),(.72,.76)]:
            d=np.sqrt((xx-cx)**2+((yy-cy)*.21)**2)
            h+=.12*np.cos(d*250)*np.exp(-d*20)
    elif kind=='bark':
        h=.52+.12*np.sin((xx+.015*np.sin(yy*TAU*2))*TAU*17)+fine*.14
    elif kind=='stone':
        h=.50+.08*np.sin(xx*TAU*7+np.sin(yy*TAU*3))+.055*np.sin(yy*TAU*19)+fine*.10
    elif kind=='snow':
        h=.57+.025*np.sin(xx*TAU*3)*np.cos(yy*TAU*5)+fine*.04
    elif kind=='needles':
        h=.49+.10*np.sin((xx+yy*.3)*TAU*35)+fine*.12
    elif kind=='canvas':
        h=.54+.035*np.cos(xx*TAU*64)+.035*np.cos(yy*TAU*64)+fine*.03
    else:h=.53+fine*.08
    rgb=np.clip(color(base)[None,None,:]*(.78+h[...,None]*.42),0,1)
    image=Image.fromarray((rgb*255).astype(np.uint8),'RGB')
    buf=io.BytesIO();image.save(buf,format='PNG',optimize=True)
    gy,gx=np.gradient(h)
    strength=1.5 if kind in ['wood','bark','stone'] else .5
    n=norm(np.stack([-gx*strength,-gy*strength,np.ones_like(h)],axis=-1))
    nb=io.BytesIO();Image.fromarray(((n*.5+.5)*255).astype(np.uint8)).save(nb,format='PNG')
    return buf.getvalue(),nb.getvalue()

MATS={
 'timber':('wood','a66b3b',.92,0.,None),
 'timber_dark':('wood','624833',.94,0.,None),
 'endgrain':('wood','bf935b',.94,0.,None),
 'bark':('bark','6f513b',.98,0.,None),
 'snow':('snow','c7d9e3',.83,0.,None),
 'needles':('needles','173e39',.95,0.,None),
 'needles_light':('needles','2d6253',.95,0.,None),
 'blue':('metal','315c7a',.43,.52,None),
 'orange':('metal','c07937',.5,.20,None),
 'iron':('metal','394c57',.42,.72,None),
 'brass':('metal','b18b52',.40,.62,None),
 'stone':('stone','667a81',.97,0.,None),
 'stone_dark':('stone','3f525b',.98,0.,None),
 'ore':('stone','74a5b5',.3,.55,None),
 'coal':('stone','2f3943',.56,.1,None),
 'canvas':('canvas','315f7e',.96,0.,None),
 'glass':('metal','f6aa51',.38,.0,[1.0,.42,.075]),
 'ember':('stone','fd933d',.90,0.,[1.,.20,.012]),
 'black':('metal','121e26',.98,0.,None),
}
TEX={k:texture(v[0],v[1]) for k,v in MATS.items()}

class Model:
 def __init__(self,name):self.name=name;self.parts={};self.features=[]
 def add(self,v,f,mat,n=None,uv=None):
    v=np.asarray(v,dtype=np.float32);f=np.asarray(f,dtype=np.uint32).reshape(-1,3)
    if n is None:
        n=np.zeros_like(v);fn=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
        for k in range(3):np.add.at(n,f[:,k],fn)
        n=norm(n)
    if uv is None:uv=v[:,[0,1]]*.6
    self.parts.setdefault(mat,[]).append((v,f,np.asarray(n,dtype=np.float32),np.asarray(uv,dtype=np.float32)))
 def patch(self,fn,nu,nv,mat):
    v=[];uv=[];f=[]
    for j in range(nv+1):
      for i in range(nu+1):
        u=i/nu;t=j/nv;v.append(fn(u,t));uv.append((u,t))
    for j in range(nv):
      for i in range(nu):
        a=j*(nu+1)+i;b=a+1;c=a+nu+1;d=c+1
        f.extend([(a,c,b),(b,c,d)])
    self.add(v,f,mat,uv=uv)
 def tube(self,points,radii,mat,sides=10):
    p=np.asarray(points,float);r=np.broadcast_to(radii,(len(p),));v=[];ns=[];uv=[];f=[]
    for j,pt in enumerate(p):
      tangent=norm(p[min(j+1,len(p)-1)]-p[max(0,j-1)])
      ref=np.array([0,1,0]) if abs(tangent[1])<.91 else np.array([1,0,0])
      u=norm(np.cross(tangent,ref));w=np.cross(tangent,u)
      for i in range(sides):
        a=i/sides*TAU;nn=u*math.cos(a)+w*math.sin(a)
        v.append(pt+nn*r[j]);ns.append(nn);uv.append((i/sides,j/(len(p)-1)))
    for j in range(len(p)-1):
      for i in range(sides):
        a=j*sides+i;b=j*sides+(i+1)%sides;c=a+sides;d=b+sides
        f.extend([(a,b,c),(b,d,c)])
    v.extend([p[0],p[-1]]);ns.extend([-norm(p[1]-p[0]),norm(p[-1]-p[-2])]);uv.extend([(0.5,0.5)]*2)
    for i in range(sides):
      f.extend([(len(v)-2,(i+1)%sides,i),(len(v)-1,(len(p)-1)*sides+i,(len(p)-1)*sides+(i+1)%sides)])
    self.add(v,f,mat,ns,uv)
 def lathe(self,profile,mat,center=(0,0,0),sides=32):
    v=[];uv=[];f=[];center=np.asarray(center)
    for j,(r,h) in enumerate(profile):
      for i in range(sides+1):
        a=i/sides*TAU;v.append(center+np.array([r*math.sin(a),h,r*math.cos(a)]));uv.append((i/sides,j/max(1,len(profile)-1)))
    for j in range(len(profile)-1):
      for i in range(sides):
        a=j*(sides+1)+i;b=a+1;c=a+sides+1;d=c+1
        f.extend([(a,b,c),(b,d,c)])
    self.add(v,f,mat,uv=uv)
 def box(self,center,size,mat,bevel=.035,rotation=0):
    # Analytic rounded joinery: six bevelled patches, not a CubeMesh fallback.
    h=np.asarray(size,dtype=float)/2;r=min(bevel,min(h)*.45);c=np.asarray(center)
    co,si=math.cos(rotation),math.sin(rotation)
    rot=np.array([[co,0,si],[0,1,0],[-si,0,co]])
    for axis in range(3):
      others=[i for i in range(3) if i!=axis]
      for side in [-1,1]:
        grids=[]
        for a in others:
          grids.append(np.unique([-h[a],-h[a]+r*.293,-h[a]+r,h[a]-r,h[a]-r*.293,h[a]]))
        v=[];ns=[];uv=[];f=[]
        for y in grids[1]:
          for x in grids[0]:
            p=np.zeros(3);p[axis]=side*h[axis];p[others[0]]=x;p[others[1]]=y
            q=np.clip(p,-h+r,h-r);n=norm(p-q);p=q+n*r
            v.append(rot@p+c);ns.append(rot@n);uv.append((x/max(.02,size[others[0]]),y/max(.02,size[others[1]])))
        nx=len(grids[0]);ny=len(grids[1])
        for j in range(ny-1):
          for i in range(nx-1):
            a=j*nx+i;b=a+1;cc=a+nx;d=cc+1
            tri=[(a,b,cc),(b,d,cc)]
            for t in tri:
              vv=np.array([v[k] for k in t]);nn=np.mean(np.array([ns[k] for k in t]),axis=0)
              if np.dot(np.cross(vv[1]-vv[0],vv[2]-vv[0]),nn)<0:t=t[::-1]
              f.append(t)
        self.add(v,f,mat,ns,uv)
 def blob(self,center,scale,mat,seed=0,nu=16,nv=10,rough=.06):
    rng=np.random.default_rng(seed);phase=rng.random(4)*TAU;c=np.array(center);s=np.array(scale)
    def fn(u,v):
      a=u*TAU;b=v*math.pi
      k=1+rough*(math.sin(a*3+phase[0])*math.sin(b*2+phase[1])+.5*math.cos(a*5-b*3+phase[2]))
      return c+s*np.array([math.sin(b)*math.sin(a),math.cos(b),math.sin(b)*math.cos(a)])*k
    self.patch(fn,nu,nv,mat)
 def export(self):
    binary=bytearray();views=[];access=[];images=[];materials=[];textures=[];primitives=[]
    def buf(data):
      while len(binary)%4:binary.extend(b'\0')
      offset=len(binary);binary.extend(data);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(data)});return len(views)-1
    def acc(a,ctype,typ):
      a=np.ascontiguousarray(a);q={'bufferView':buf(a.tobytes()),'componentType':ctype,'count':len(a),'type':typ}
      if typ=='VEC3':q.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
      access.append(q);return len(access)-1
    # Geometry-derived contact occlusion, baked into vertex colors. This is not
    # a claim of runtime global illumination; it gives joinery and foliage depth.
    all_vertices=np.concatenate([part[0] for parts in self.parts.values() for part in parts])
    tree=cKDTree(all_vertices)
    def ambient_occlusion(v,n):
      distance,neighbor=tree.query(v,k=32,distance_upper_bound=.17,workers=2)
      valid=(neighbor<len(all_vertices)) & (distance>1e-4)
      direction=all_vertices[np.minimum(neighbor,len(all_vertices)-1)]-v[:,None,:]
      direction=np.divide(direction,distance[...,None],out=np.zeros_like(direction),where=valid[...,None])
      projected=np.maximum(0,np.sum(direction*n[:,None,:],axis=2))
      weight=np.exp(-np.where(valid,distance,100)/.095)*valid
      ao=np.clip(np.exp(-np.sum(projected*weight,axis=1)*.24),.48,1.)
      ao*=.86+.14*np.clip(v[:,1]/.20,0,1)
      return np.c_[np.repeat(ao[:,None],3,axis=1),np.ones(len(v))].astype('<f4')
    bounds=[];triangles=0
    for mat,parts in self.parts.items():
      vv=[];ff=[];nn=[];uu=[];offset=0
      for v,f,n,uv in parts:vv.append(v);ff.append(f+offset);nn.append(n);uu.append(uv);offset+=len(v)
      v=np.concatenate(vv);f=np.concatenate(ff).astype('<u4');n=np.concatenate(nn);uv=np.concatenate(uu)
      good=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)>1e-10;f=f[good]
      assert np.isfinite(v).all() and np.isfinite(n).all()
      # Finite tangent frames, including pole and cap vertices.
      lengths=np.linalg.norm(n,axis=1);n[lengths<1e-6]=[0,1,0];n=norm(n)
      tan=np.zeros_like(v);bit=np.zeros_like(v)
      e1=v[f[:,1]]-v[f[:,0]];e2=v[f[:,2]]-v[f[:,0]]
      d1=uv[f[:,1]]-uv[f[:,0]];d2=uv[f[:,2]]-uv[f[:,0]]
      det=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0]
      inv=np.divide(1.,det,out=np.zeros_like(det),where=np.abs(det)>1e-8)
      ft=(e1*d2[:,1,None]-e2*d1[:,1,None])*inv[:,None]
      fb=(e2*d1[:,0,None]-e1*d2[:,0,None])*inv[:,None]
      for k in range(3):np.add.at(tan,f[:,k],ft);np.add.at(bit,f[:,k],fb)
      tan-=n*np.sum(tan*n,axis=1)[:,None]
      missing=np.linalg.norm(tan,axis=1)<1e-5
      ref=np.tile([1.,0.,0.],(len(v),1));ref[np.abs(n[:,0])>.9]=[0.,0.,1.]
      tan[missing]=np.cross(ref[missing],n[missing]);tan=norm(tan)
      handed=np.where(np.sum(np.cross(n,tan)*bit,axis=1)<0,-1.,1.)
      tangent=np.c_[tan,handed].astype('<f4')
      bounds.append(v);triangles+=len(f)
      indices=[]
      for data in TEX[mat]:
        images.append({'bufferView':buf(data),'mimeType':'image/png'});textures.append({'source':len(images)-1,'sampler':0});indices.append(len(textures)-1)
      p=MATS[mat];m={'name':mat,'pbrMetallicRoughness':{'baseColorTexture':{'index':indices[0]},'metallicFactor':p[3],'roughnessFactor':p[2]},'normalTexture':{'index':indices[1],'scale':.65},'doubleSided':False}
      if p[4]:m['emissiveFactor']=p[4]
      materials.append(m)
      primitives.append({'attributes':{'POSITION':acc(v.astype('<f4'),5126,'VEC3'),'NORMAL':acc(n.astype('<f4'),5126,'VEC3'),'TANGENT':acc(tangent,5126,'VEC4'),'TEXCOORD_0':acc(uv.astype('<f4'),5126,'VEC2'),'COLOR_0':acc(np.ones((len(v),4),dtype='<f4') if mat=='snow' else ambient_occlusion(v,n),5126,'VEC4')},'indices':acc(f.reshape(-1),5125,'SCALAR'),'material':len(materials)-1})
    meta={'asset':{'version':'2.0','generator':'Havenline authored winter kit 0.4.4'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':self.name,'mesh':0}],'meshes':[{'name':self.name,'primitives':primitives}],'materials':materials,'textures':textures,'images':images,'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}],'accessors':access,'bufferViews':views,'buffers':[{'byteLength':len(binary)}]}
    js=json.dumps(meta,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary.extend(b'\0'*((-len(binary))%4))
    data=struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(binary))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(binary),b'BIN\0')+binary
    path=OUT/(self.name+'.glb');path.write_bytes(data);v=np.concatenate(bounds)
    return {'name':self.name,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'triangles':triangles,'surfaces':len(materials),'bounds':[v.min(axis=0).tolist(),v.max(axis=0).tolist()],'features':self.features}


def tree(variant):
 m=Model('pine_'+str(variant));rng=np.random.default_rng(1144+variant);height=[4.35,4.0,4.65][variant-1]
 p=[(math.sin(t*2)*.04,t*height,math.sin(t*3)*.04) for t in np.linspace(0,1,14)]
 m.tube(p,np.linspace(.16,.012,len(p)),'bark',12)
 for i in range(5):
   a=i*TAU/5+.2;m.tube([(math.sin(a)*d,.1*(1-d/.48),math.cos(a)*d) for d in np.linspace(.03,.48,5)],np.linspace(.105,.02,5),'bark',8)
 def tuft(start,end,width,thick,mat,phase):
   axis=np.asarray(end)-start;direction=norm(axis);side=norm(np.cross(direction,[0,1,0]));up=np.cross(side,direction)
   # Solid, tapering needle-cluster with separate lobed ridges; no flat foliage card.
   def fn(u,v):
     angle=u*TAU;shape=math.sin(math.pi*v)**.64
     ridge=1+.09*math.cos(angle*4+phase)+.06*math.sin(v*13+phase)
     return start+axis*v+side*math.sin(angle)*width*shape*ridge+up*(math.cos(angle)*thick*shape+.045*math.sin(v*math.pi))
   m.patch(lambda u,v:fn(1-u,v),8,5,mat)
 for j in range(55):
   t=j/55;h=.51+t*(height-.65)+rng.uniform(-.12,.12);angle=j*2.39996+rng.uniform(-.42,.42)
   length=(1.39*(1-t)**.70+.09)*rng.uniform(.76,1.12);width=length*rng.uniform(.24,.35)
   a=np.array([math.sin(angle),0,math.cos(angle)]);b=np.array([-math.cos(angle),0,math.sin(angle)])
   bend=rng.uniform(.05,.19);phase=rng.uniform(0,TAU)
   def spine(u):return a*(.025+length*u)+np.array([0,h-.23*length*u+.18*length*u*u,0])+b*math.sin(u*2.6)*bend
   m.tube([spine(u) for u in np.linspace(0,1,5)],np.linspace(.041,.006,5),'bark',7)
   for k in range(5):
    u=.12+k*.155
    for side in [-1,1]:
     spread=width*(math.sin(math.pi*u)**.6)*rng.uniform(.85,1.18)
     start=spine(u);end=spine(min(.99,u+.23))+b*side*spread+np.array([0,rng.uniform(-.03,.055),0])
     tuft(start,end,spread*.36+.018,length*.048,'needles_light' if (j+k)%7==0 else 'needles',phase+k)
   tuft(spine(.60),spine(1.015),length*.09,length*.051,'needles',phase)
   # Irregular, fully rounded snow saddle nested in the foliage instead of a white tier.
   if j%9!=3:
    cover=rng.uniform(.80,.96);snow_width=width*rng.uniform(.80,.98)
    def saddle(u,v):
      along=.04+v*cover;angle=(1-u)*TAU;shape=math.sin(math.pi*v)**.63
      width_variation=1+.16*math.sin(v*17+phase)
      return spine(along)+b*math.sin(angle)*snow_width*shape*width_variation+np.array([0,.073+math.cos(angle)*length*.082*shape+.075*shape,0])
    m.patch(saddle,12,9,'snow')
 m.features=['55 asymmetric branching boughs','605 solid tapered needle clusters','rounded irregular snow saddles','three distinct silhouettes','bark and needle normal maps','root flares']
 return m

def window(m,c,w=.66,h=.72):
 x,y,z=c
 m.box((x,y,z),(w+.15,h+.15,.13),'timber_dark',.035)
 m.box((x,y,z+.075),(w,h,.025),'glass',.01)
 for dx in [-w/2,w/2]:m.box((x+dx,y,z+.105),(.055,h+.10,.065),'orange',.018)
 for dy in [-h/2,h/2,0]:m.box((x,y+dy,z+.115),(w+.07,.045,.06),'timber',.012)
 m.box((x,y,z+.12),(.045,h,.06),'timber',.012)
 m.box((x,y-h/2-.06,z+.17),(w+.28,.08,.25),'timber_dark',.02)
 m.blob((x,y-h/2-.005,z+.17),(w*.53,.045,.14),'snow',7,16,6,.025)

def lantern(m,c,scale=1.):
 x,y,z=c;s=scale
 m.lathe([(.11*s,-.19*s),(.16*s,-.16*s),(.15*s,-.12*s)],'iron',c,16)
 m.lathe([(.13*s,.12*s),(.18*s,.15*s),(.05*s,.23*s)],'iron',c,16)
 m.lathe([(.11*s,-.11*s),(.11*s,.10*s)],'glass',c,16)
 for a in np.arange(4)*math.pi/2:
   p=np.array([math.sin(a)*.12*s,0,math.cos(a)*.12*s])+np.array(c)
   m.tube([p+[0,-.12*s,0],p+[0,.13*s,0]],[.015*s,.015*s],'brass',6)
 m.tube([(x+math.sin(t)*.09*s,y+.24*s+math.cos(t)*.09*s,z) for t in np.linspace(-math.pi/2,math.pi/2,8)],.018*s,'iron',6)

def shelter():
 m=Model('shelter')
 def roof_y(x):return 3.03-1.00*(abs(x)/1.52)**1.12+.06*math.cos(x*1.8)
 # Staggered foundation stones, individual timber boards and dressed corners.
 for x in [-.96,-.32,.32,.96]:
  for z in [-1.05,1.05]:m.blob((x,.12,z),(.36,.17,.25),'stone',int((x+2)*50+(z+2)*5),12,7,.08)
 for row in range(10):
  y=.31+row*.175
  for x in [-1.10,1.10]:m.tube([(x,y,-1.14),(x,y,1.12)],[.104,.099],'timber' if row%3 else 'timber_dark',10)
  m.tube([(-1.13,y,-1.03),(1.13,y,-1.03)],[.099,.10],'timber',10)
  for a,b in [(-1.12,-.44),(.44,1.12)]:m.tube([(a,y,1.03),(b,y,1.03)],[.102,.1],'timber',10)
 for x in [-1.12,1.12]:
  for z in [-1.05,1.05]:m.box((x,1.13,z),(.17,1.95,.17),'timber_dark',.04)
 # Five blue door panels with forged hinges and pull ring.
 for i in range(5):m.box((-.34+i*.17,.94,1.035),(.164,1.42,.12),'blue',.012)
 for y in [.52,1.36]:
  m.box((0,y,1.112),(.74,.066,.03),'iron',.012)
  for x in [-.29,.29]:m.blob((x,y,1.14),(.026,.026,.02),'brass',1,8,5,0)
 m.tube([(.23+math.cos(t)*.055,.94+math.sin(t)*.065,1.14) for t in np.linspace(0,TAU,13)],.012,'brass',6)
 m.box((0,.20,1.28),(1.15,.14,.54),'timber_dark',.04)
 for i in range(4):m.box((-.43+i*.285,.29,1.26),(.278,.065,.50),'timber',.01)
 window(m,(-.78,1.16,1.05),.38,.50);window(m,(.78,1.16,1.05),.38,.50)
 # Gabled ends with individual tapered boards, rear opening and structural rafters.
 for z in [-1.035,1.035]:
  # Continuous fitted gable backing closes hairline gaps behind separate boards.
  sign=1 if z>0 else -1
  def backing(u,v,sg=sign,zz=z):
   x=(u-.5)*2.40*sg
   return (x,1.91+v*(roof_y(x)-.035-1.91),zz)
  m.patch(backing,28,3,'timber_dark')
  for i in range(13):
   x=-1.05+i*.175;top=2.94-abs(x)*.78
   m.box((x,(1.91+top)/2,z),(.17,top-1.91,.14),'timber',.015)
  for sign in [-1,1]:m.tube([(0,2.99,z+.04),(sign*1.40,1.91,z+.04)],[.075,.075],'timber_dark',10)
 window(m,(0,2.35,1.10),.44,.40)
 # Curved blue roof; thick continuous scalloped snow sheet, curled eaves.
 def roof(u,v,raised=0):
  x=(u-.5)*3.18;z=(v-.5)*2.95
  return (x,roof_y(x)+raised,z)
 m.patch(lambda u,v:roof(u,v),32,16,'blue')
 m.patch(lambda u,v:roof(u,1-v,-.08),32,16,'timber_dark')
 for z in [-1.475,1.475]:
  m.tube([(x,roof_y(x)-.03,z) for x in np.linspace(-1.59,1.59,28)],.07,'orange',8)
 for x in [-1.56,1.56]:m.tube([(x,roof_y(x),-1.48),(x,roof_y(x),1.48)],.045,'brass',8)
 for z in np.linspace(-1.4,1.4,12):m.tube([(x,roof_y(x)+.03,z) for x in np.linspace(-1.5,1.5,22)],.012,'iron',5)
 def snowroof(u,v):
  x=(u-.5)*3.27;z=(v-.5)*3.02
  edge=max(abs(x)/1.635,abs(z)/1.51)
  thick=.15+.045*math.sin(x*3.1+z*2)+.025*math.cos(z*5+x)
  return (x,roof_y(x)+thick+.04*(1-edge),z)
 m.patch(snowroof,36,26,'snow')
 for sign in [-1,1]:
  m.patch(lambda u,v,sg=sign:np.array(snowroof(u if sg==1 else 1-u,1 if sg==1 else 0))+np.array([0,-v*(.15+.025*math.sin(u*46)),sg*v*.025]),36,4,'snow')
  m.patch(lambda u,v,sg=sign:np.array(snowroof(1 if sg==1 else 0,1-u if sg==1 else u))+np.array([sg*v*.025,-v*(.15+.025*math.sin(u*35)),0]),28,4,'snow')
 # Chimney, cap, lantern, hardware, snow caught on sill and porch.
 for j in range(5):
  for i in range(2):m.box((.66+(i-.5)*.20,2.84+j*.13,-.63),(.197,.128,.36),'stone_dark' if (i+j)%3 else 'stone',.018)
 m.box((.66,3.46,-.63),(.53,.10,.49),'iron',.045)
 m.blob((.67,3.54,-.63),(.29,.09,.27),'snow',6,16,8,.035)
 lantern(m,(1.03,1.73,1.31),.85)
 m.tube([(1.03,1.97,1.30),(1.03,2.04,1.09)],.025,'iron',8)
 m.features=['rounded interlocking timber walls','five-panel blue door','glazed mullioned windows','continuous curved snowy roof','staggered masonry chimney','forged hinges and lantern','front and rear geometry']
 return m

def furnace():
 m=Model('furnace')
 # Ring of shaped masonry with grout spaces, carved iron shell and copper bands.
 for j in range(2):
  for i in range(13):
   a=i/13*TAU+j*.22;r=.78
   m.blob((math.sin(a)*r,.12+j*.16,math.cos(a)*r),(.24,.115,.21),'stone' if i%3 else 'stone_dark',i+j*31,12,7,.045)
 m.lathe([(.60,.22),(.67,.30),(.64,.36),(.63,1.15),(.59,1.28),(.53,1.38),(.24,1.68),(.21,1.72)],'blue',sides=40)
 for y,r in [(.35,.66),(1.15,.64),(1.37,.535)]:
  m.lathe([(r,y-.025),(r+.025,y),(r,y+.025)],'brass',sides=40)
 for i in range(12):
  a=i*TAU/12;m.tube([(math.sin(a)*.638,.43,math.cos(a)*.638),(math.sin(a)*.638,1.12,math.cos(a)*.638)],[.032,.028],'iron',7)
  for y in [.42,1.09]:m.blob((math.sin(a)*.665,y,math.cos(a)*.665),(.028,.028,.028),'brass',1,8,5,0)
 m.box((0,.76,.637),(.77,.72,.085),'iron',.075)
 m.box((0,.75,.69),(.60,.55,.025),'black',.055)
 m.box((0,.73,.707),(.52,.44,.025),'ember',.065)
 for x in [-.22,-.11,0,.11,.22]:m.tube([(x,.49,.739),(x,1.,.739)],[.026,.026],'iron',8)
 m.box((0,.46,.77),(.68,.075,.20),'brass',.025)
 m.lathe([(.20,1.64),(.205,1.72),(.17,1.76),(.17,2.38),(.21,2.40),(.22,2.45),(.21,2.49)],'iron',sides=32)
 # Continuous rim plus dark inner wall: never see the ground through a culled pipe.
 m.lathe([(.21,2.49),(.175,2.49)],'iron',sides=32)
 m.lathe([(.175,2.49),(.155,2.42),(.155,2.18),(0.0,2.18)],'black',sides=32)
 for y in [1.82,2.25]:m.lathe([(.18,y-.025),(.194,y),(.18,y+.025)],'brass',sides=24)
 m.box((.64,.89,0),(.15,.25,.35),'iron',.04)
 m.tube([(.76,.82,.12),(.82,.93,.12),(.76,1.03,.12)],[.028,.03,.028],'brass',8)
 m.features=['rounded cast-metal boiler','ribbed shell','glowing barred firebox','layered masonry base','rivets and bronze seams','collared chimney']
 return m

def storage():
 m=Model('storage')
 for x in [-.79,.79]:
  m.box((x,.62,0),(.13,1.15,1.23),'blue',.04)
  m.box((x,.16,0),(.17,.13,1.43),'iron',.03)
 for z in [-.49,.49]:m.box((0,.18,z),(1.78,.15,.16),'timber_dark',.025)
 for row in range(4):
  for col in range(5-row):
   x=(col-(4-row)/2)*.31;y=.36+row*.25
   m.tube([(x,y,-.51),(x+.014,y+.008,.51)],[.145,.14],'bark',12)
   m.tube([(x,y,.514),(x,y,.523)],[.126,.126],'endgrain',12)
 for x in [-.83,.83]:m.box((x,1.21,0),(.17,.10,1.32),'orange',.025)
 # Curved supporting roof and a closed, irregular snow blanket with rounded eaves.
 m.patch(lambda u,v:((u-.5)*1.91,1.25+.10*math.sin(u*math.pi),(v-.5)*1.39),16,10,'blue')
 def snowblanket(u,v):
  a=u*TAU;b=v*math.pi;d=math.sin(b)**.37
  x=.98*math.sin(a)*d;z=.74*math.cos(a)*d
  return (x,1.35+math.cos(b)*.105+.026*math.sin(x*7+z*3),z)
 m.patch(snowblanket,40,14,'snow')
 m.features=['forged blue rack','bark and cut-end logs','separate snow cap','rounded frame']
 return m

def rocks(kind):
 m=Model(kind);rng=np.random.default_rng(817 if kind=='snow_rock' else 661);rocks=[]
 layout=[(-.37,.16,-.08),(.23,.20,.13),(.05,.32,-.20)] if kind=='snow_rock' else [(-.35,.21,-.18),(.30,.23,-.12),(-.08,.30,-.40),(.08,.18,.35)]
 for i,(x,y,z) in enumerate(layout):
  c=np.array((x,y,z));s=np.array((rng.uniform(.34,.46),rng.uniform(.30,.39),rng.uniform(.33,.44)))
  phase=np.random.default_rng(i+57).random(4)*TAU
  rocks.append((c,s,phase));m.blob(c,s,'coal' if kind=='fuel' else 'stone_dark',i+57,24,16,.14)
  if kind=='metal':
   for j in range(2):m.blob(c+[j*.12-.05,.13,.28],(.13,.065,.10),'ore',i+j*5,12,8,.17)
 def top(x,z,rock):
  c,s,phase=rock;xx=(x-c[0])/s[0];zz=(z-c[2])/s[2];q=math.hypot(xx,zz);a=math.atan2(xx,zz)
  def k(b):return 1+.14*(math.sin(a*3+phase[0])*math.sin(b*2+phase[1])+.5*math.cos(a*5-b*3+phase[2]))
  if q>k(math.pi/2):return -100.
  lo=0.;hi=math.pi/2
  for _ in range(13):
   b=(lo+hi)/2
   if math.sin(b)*k(b)<q:lo=b
   else:hi=b
  b=(lo+hi)/2;return c[1]+s[1]*math.cos(b)*k(b)
 # A single smoothed height-field blanket over the union of the boulders.
 # Avoid radial pole fans and overlapping caps that looked like crumpled petals.
 grid=np.linspace(-.86,.86,65);raw=np.array([[max(top(x,z,rock) for rock in rocks) for x in grid] for z in grid])
 valid=raw>-50
 nearest=distance_transform_edt(~valid,return_distances=False,return_indices=True)
 filled=raw[tuple(nearest)]
 smoothed=gaussian_filter(filled,1.3)
 heights=np.maximum(raw+.016,smoothed+.041)
 mask=valid & (distance_transform_edt(valid)>.095/(grid[1]-grid[0])) & (smoothed>.31)
 vertices=[];uv=[];lookup={};faces=[]
 for iz,z in enumerate(grid):
  for ix,x in enumerate(grid):
   if mask[iz,ix]:lookup[(ix,iz)]=len(vertices);vertices.append((x,heights[iz,ix],z));uv.append((x,z))
 for iz in range(64):
  for ix in range(64):
   for tri in [((ix,iz),(ix,iz+1),(ix+1,iz)),((ix+1,iz),(ix,iz+1),(ix+1,iz+1))]:
    if all(k in lookup for k in tri):faces.append(tuple(lookup[k] for k in tri))
 m.add(vertices,faces,'snow',uv=uv)
 m.features=[('three asymmetrically grouped stones' if kind=='snow_rock' else 'four lobed sculpted stones'),'normal-mapped mineral surfaces','snow conforms to exposed union of rocks','no buried cap intersections']
 return m

def barricade():
 m=Model('barricade')
 for i in range(9):
  x=-1.34+i*.335;h=1.20+.15*math.sin(i*4.13)
  m.tube([(x,.03,0),(x+.025,h-.13,0),(x+.009,h,.01)],[.105,.10,.013],'timber',9)
  m.blob((x,h-.11,.005),(.10,.07,.115),'snow',i,10,6,.045)
 for y in [.42,.86]:m.box((0,y,-.10),(2.95,.13,.13),'timber_dark',.025)
 for x in [-1.03,0,1.03]:
  m.box((x,.65,.13),(.058,.68,.038),'iron',.01)
  for y in [.41,.88]:m.blob((x,y,.166),(.027,.027,.015),'brass',0,8,5,0)
 m.features=['split irregular timber tops','cross braces','forged straps','snow crowns']
 return m

def log():
 m=Model('log');m.tube([(0,-.30,0),(.014,0,0),(0,.30,0)],[.12,.126,.115],'bark',12)
 m.tube([(0,.301,0),(0,.306,0)],[.108,.108],'endgrain',12)
 m.tube([(0,-.301,0),(0,-.306,0)],[.109,.109],'endgrain',12)
 return m

def dressing():
 result=[]
 m=rocks('snow_rock');m.features.append('asymmetric three-boulder scenery cluster');result.append(m)
 m=Model('winter_shrub')
 for i in range(9):
  a=i*2.4;h=.28+.19*(math.sin(i*1.31)*.5+.5);end=np.array([math.sin(a)*.36,h,math.cos(a)*.36])
  m.tube([np.zeros(3),end*.65,end],[.019,.012,.004],'timber_dark',5)
  for sign in [-1,1]:
   q=end*.6+np.array([sign*.16,.07,0]);m.tube([end*.48,q],[.01,.004],'timber_dark',5)
   m.blob(q,(.022,.025,.022),'orange',i,6,4,0)
 result.append(m)
 m=Model('lantern_post');m.tube([(0,0,0),(0,1.65,0),(.32,1.74,0)],[.066,.055,.04],'timber_dark',10)
 m.lathe([(.07,.07),(.10,.10),(.07,.16)],'iron',sides=12)
 lantern(m,(.33,1.47,0),.8);m.blob((0,1.70,0),(.13,.05,.12),'snow',1,12,6,.02);result.append(m)
 return result

if __name__=='__main__':
 models=[tree(i) for i in (1,2,3)]+[shelter(),furnace(),storage(),barricade(),log()]+[rocks(k) for k in ['stone','metal','fuel']]+dressing()
 manifest={'schema':1,'kit':'Havenline winter environment 0.4.4','source':'tools/havenline/bake_environment.py','deterministic':True,'original_glbs_modified':False,'production_visual_approval':False,'assets':[m.export() for m in models]}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'assets':len(models),'triangles':sum(a['triangles'] for a in manifest['assets']),'bytes':sum(a['bytes'] for a in manifest['assets']),'output':str(OUT)},indent=2))
