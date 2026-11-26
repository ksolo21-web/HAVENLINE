"""Bake three mineable banks, portable units and HUD icons from their eight-view art.

Input: reviewed-concepts/{13-coal,05-metal-ore,03-slate}.png at
ksolo21-web/HAVENLINE commit 25b4ec6dd407c1c2530a3781527df64eabb63b99,
Docs/Design/ResourceTurnarounds/2026-11-23. Pass the containing directory.
Requires Pillow, NumPy, SciPy, scikit-image, fast-simplification and xatlas.
"""
import argparse, io, json, math, struct
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage.measure import marching_cubes
import fast_simplification, xatlas

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('reference_dir',type=Path)
parser.add_argument('kinds',nargs='*')
args=parser.parse_args()
bas=args.reference_dir
out=Path(__file__).resolve().parents[2]/'assets/field'
icons=out.parent/'field_ui'
files={'coal':'13-coal','metal':'05-metal-ore','slate':'03-slate'}
def segment(kind):
 source=np.asarray(Image.open(bas/(files[kind]+'.png')).convert('RGB'));views=[]
 for i in range(8):
  row,col=divmod(i,4)
  y0,y1=([102,434] if row==0 else [525,837]);x0=col*384+12
  rgb=source[y0:y1,x0:(col+1)*384-11].copy()
  r,g,b=rgb.astype('f').transpose(2,0,1)
  mask=(r > b*({'coal':.53,'metal':.47,'slate':.39}[kind])+1.0) & (r>9) & (r>g*(.62 if kind=='slate' else .70))
  lab,num=nd.label(mask)
  bins=np.bincount(lab.ravel());bins[0]=0;mask=(lab==bins.argmax())
  mask=nd.binary_fill_holes(nd.binary_closing(mask,iterations=1))
  yy,xx=np.where(mask);box=(xx.min(),yy.min(),xx.max(),yy.max())
  distance=nd.distance_transform_edt(mask)-nd.distance_transform_edt(~mask)
  _,ix=nd.distance_transform_edt(~mask,return_indices=True)
  views.append((rgb[ix[0],ix[1]],mask,distance,box))
 return views
def write_glb(file,v,f,n,uv,atlas):
 blob=bytearray();views=[];acc=[]
 def add(data,target=None):
  blob.extend(b'\0'*(-len(blob)%4));rec={'buffer':0,'byteOffset':len(blob),'byteLength':len(data)}
  if target:rec['target']=target
  views.append(rec);blob.extend(data);return len(views)-1
 def a(data,typ,ct,target):
  data=np.ascontiguousarray(data);entry={'bufferView':add(data.tobytes(),target),'componentType':ct,'type':typ,'count':len(data)}
  if len(acc)==0:entry.update({'min':v.min(0).tolist(),'max':v.max(0).tolist()})
  acc.append(entry);return len(acc)-1
 vi=a(v.astype('<f4'),'VEC3',5126,34962);ni=a(n.astype('<f4'),'VEC3',5126,34962);ti=a(uv.astype('<f4'),'VEC2',5126,34962);fi=a(f.astype('<u2').ravel(),'SCALAR',5123,34963)
 tex=io.BytesIO();Image.fromarray(atlas).save(tex,format='JPEG',quality=90,subsampling=0,optimize=True);iv=add(tex.getvalue())
 j={'asset':{'version':'2.0','generator':'Havenline multi-view reconstruction'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':file.stem}],'meshes':[{'primitives':[{'attributes':{'POSITION':vi,'NORMAL':ni,'TEXCOORD_0':ti},'indices':fi,'material':0}]}],'materials':[{'name':file.stem,'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':{'coal':.13,'metal':.21,'slate':0.}[file.stem],'roughnessFactor':{'coal':.64,'metal':.71,'slate':.88}[file.stem]}}],'images':[{'bufferView':iv,'mimeType':'image/jpeg'}],'textures':[{'source':0}],'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':acc}
 head=json.dumps(j,separators=(',',':')).encode();head+=b' '*(-len(head)%4);blob.extend(b'\0'*(-len(blob)%4))
 file.write_bytes(struct.pack('<4sIII4s',b'glTF',2,28+len(head)+len(blob),len(head),b'JSON')+head+struct.pack('<I4s',len(blob),b'BIN\0')+blob)
def build(kind):
 views=segment(kind);scale=np.mean([views[i][3][2]-views[i][3][0] for i in [0,4]])
 # Width is finally normalized to 1.0 after geometry extraction.
 rz={'coal':.48,'metal':.365,'slate':.265}[kind]
 elev=math.radians({'coal':13,'metal':14,'slate':29}[kind])
 c0,m0,_,(x0,y0,x1,y1)=views[0]
 alpha=Image.fromarray((m0*255).astype('B'));icon=Image.fromarray(c0).convert('RGBA');icon.putalpha(alpha)
 icon=icon.crop((x0,y0,x1+1,y1+1));icon.thumbnail((114,110),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(128,128));canvas.paste(icon,((128-icon.width)//2,(128-icon.height)//2));canvas.save(icons/(kind+'.png'))
 proj=[]
 for i,(_,m,d,bb) in enumerate(views):
  az=i*math.pi/4
  right=np.array([math.cos(az),0,-math.sin(az)]);rad=np.array([math.sin(az),0,math.cos(az)])
  up=np.array([0,math.cos(elev),0])-rad*math.sin(elev);eye=rad*math.cos(elev)+np.array([0,math.sin(elev),0])
  cu=(bb[0]+bb[2])/2
  depth_box=views[(i+2)%8][3];depth=(depth_box[2]-depth_box[0])/scale
  sy=(bb[3]-bb[1])/(.166*math.cos(elev)+depth*.93*math.sin(elev)) if kind=='slate' else scale
  cv=bb[3]-(.91 if kind=='slate' else .70)*.5*depth*math.sin(elev)*sy
  proj.append((right,up,eye,cu,cv,sy))
 def projection(i,P):
  r,u,eye,cu,cv,sy=proj[i];return np.stack((cv-sy*(P@u),cu+scale*(P@r)))
 step=.009 if kind=='slate' else .012
 x=np.arange(-.63,.63+step,step);y=np.arange(-.12,.36 if kind=='slate' else 1.05,step);z=np.arange(-rz*1.30,rz*1.30+step,step)
 grid=np.stack(np.meshgrid(x,y,z,indexing='ij'),-1);P=grid.reshape(-1,3)
 def sample(arr,i,points):
  return nd.map_coordinates(arr,projection(i,points),order=1,mode='nearest',prefilter=False)
 distances=np.stack([sample(v[2].astype('f'),i,P) for i,v in enumerate(views)])
 dist=np.sort(distances,axis=0)
 field=(dist[0]*.3+dist[1]*.55+dist[2]*.15).reshape(grid.shape[:-1])
 field=nd.gaussian_filter(field,0.85)
 field=np.minimum(field, (grid[:,:,:,1]+.008)*scale) # grounded underside
 v,f,_,_=marching_cubes(field,0,spacing=(step,)*3,gradient_direction='ascent');v+=np.array([x[0],y[0],z[0]])
 v,f=fast_simplification.simplify(v,f,target_count=5000)
 # Move the actual stone surface into cracks, and lift local crystalline
 # inclusions where their source-view contrast is supported by its normal.
 edges=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
 if np.sum(edges*v[f[:,0]])<0:f=f[:,[0,2,1]];edges=-edges
 nn=np.zeros_like(v)
 for j in range(3):np.add.at(nn,f[:,j],edges)
 nn/=np.maximum(1e-8,np.linalg.norm(nn,axis=1,keepdims=True))
 relief=np.zeros(len(v));weight=np.zeros(len(v))
 for i,(c,_,dist,_) in enumerate(views):
  lum=c.astype('f').mean(axis=2)/255
  detail=nd.gaussian_filter(lum,2.0)-nd.gaussian_filter(lum,13.)
  local=np.clip(sample(detail,i,v)*3.,-.85,.85)
  if kind=='metal':
   local+=np.clip((sample(lum,i,v)-.43)*1.9,0,.7)
  w=np.maximum(nn@proj[i][2],0.0)**9
  relief+=w*local;weight+=w
 offset=({'metal':.021,'coal':.058,'slate':.018}[kind])*relief/np.maximum(weight,.001)
 v+=nn*offset[:,None]*np.clip(v[:,1:2]*30,0,1)
 if kind=='slate':
  # The exposed cleavage planes terminate around the perimeter of the slab.
  yfrac=np.clip(v[:,1]/.18,0,1)
  notch=np.maximum(0,1-abs(yfrac-.30)*22)+np.maximum(0,1-abs(yfrac-.57)*22)
  v[:,0]-=nn[:,0]*.014*notch
  v[:,2]-=nn[:,2]*.014*notch
 v,f=fast_simplification.simplify(v,f,target_count={'coal':1150,'metal':1340,'slate':880}[kind])
 if kind=='slate':
  # Slate cleaves into a compact slab. Its near-rectangular corners and two
  # recessed fracture planes are physical geometry even on its narrow edge.
  outline=np.array([[-.50,-.165],[-.466,-.248],[-.333,-.255],[-.172,-.248],[-.095,-.26],[.085,-.247],[.288,-.255],[.425,-.246],[.486,-.193],[.489,-.052],[.500,.002],[.485,.143],[.451,.231],[.330,.241],[.164,.250],[.084,.230],[-.016,.251],[-.174,.243],[-.26,.26],[-.419,.248],[-.486,.201],[-.482,.109],[-.50,.035],[-.487,-.058]])
  verts=[];tris=[];n=len(outline)
  for layer,(y0,sx,sz) in enumerate([(0,.936,.92),(.014,.976,.944),(.042,.988,.98),(.047,.947,.917),(.059,.988,.993),(.092,.99,1),(.099,.949,.928),(.112,.996,.994),(.155,1,1),(.169,.973,.958),(.178,.86,.82),(.184,.52,.54)]):
   for j,(x,z) in enumerate(outline):
    wave=(.007*np.sin(6.7*x+9.0*z)+.003*np.sin(14*x-7*z)+.0025*np.sin(j*3.3+layer*.2))*(min(y0/.028,1.))
    verts.append([x*sx,y0+wave,z*sz])
   if layer:
    for j in range(n):
     a=(layer-1)*n+j;b=(layer-1)*n+(j+1)%n;c=b+n;d=a+n
     tris.extend([[a,d,c],[a,c,b]])
  for j in range(1,n-1):tris.extend([[0,j,j+1],[(layer*n),layer*n+j+1,layer*n+j]])
  v=np.array(verts);f=np.array(tris)
 nodule_start=len(v)
 if kind=='metal':
  # Each silver inclusion has its own buried root, bevel and exposed facets.
  # Fit the bright components visible at 0 degrees to their depth on the host.
  from scipy.spatial import ConvexHull
  right,up,eye,cu,cv,sy=proj[0]
  screen=projection(0,v);vlist=[v];flist=[f];count=len(v)
  for k,(px,py,rx,ry,rd) in enumerate([(135,133,.213,.181,.128),(282,171,.105,.086,.111),(293,240,.097,.078,.102)]):
   radius=((screen[1]-px)/(rx*scale))**2+((screen[0]-py)/(ry*sy))**2
   face_depth=np.quantile((v@eye)[radius<.43],.90)
   center=right*((px-cu)/scale)+up*((cv-py)/sy)+eye*(face_depth-rd*.48)
   points=[]
   for l,(height,r) in enumerate([(-1,.52),(-.43,.95),(.31,1.00),(.79,.71),(.94,.40)]):
    for j in range(8):
     a=j*math.tau/8+.16*l+k*.33
     rr=r*(.98+.052*math.cos(3*a+k))
     x=rx*rr*math.cos(a);y=ry*rr*math.sin(a)
     points.append(center+right*x+up*(y+x*.15)+eye*(height*rd+.023*math.sin(a)*r))
   pts=np.array(points);polys=ConvexHull(pts).simplices.copy()
   cross=np.cross(pts[polys[:,1]]-pts[polys[:,0]],pts[polys[:,2]]-pts[polys[:,0]])
   inward=np.sum(cross*(pts[polys[:,0]]-pts.mean(0)),axis=1)<0
   polys[inward]=polys[inward][:,[0,2,1]]
   vlist.append(pts);flist.append(polys+count);count+=len(pts)
  v=np.vstack(vlist);f=np.vstack(flist)
 # Ensure exterior winding by enclosed volume.
 face_norm=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
 if np.sum(face_norm*v[f[:,0]])<0:f=f[:,[0,2,1]];face_norm=-face_norm
 norm=np.zeros_like(v)
 for i in range(3):np.add.at(norm,f[:,i],face_norm)
 norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-8)
 vm,indices,uv=xatlas.parametrize(v.astype('f'),f.astype(np.uint32));is_nodule=vm>=nodule_start;v=v[vm];norm=norm[vm];f=indices.astype(int)
 res=512
 posmap=np.zeros((res,res,3),dtype='f');normmap=posmap.copy();nodule=np.zeros((res,res),bool);m=np.zeros((res,res),bool)
 for tri in f:
  p=uv[tri]*res-.5;a,b,c=p;u=b-a;w=c-a;det=u[0]*w[1]-u[1]*w[0]
  if abs(det)<1e-7:continue
  lo=np.maximum(np.floor(p.min(axis=0)).astype(int),0);hi=np.minimum(np.ceil(p.max(axis=0)).astype(int)+1,res)
  if np.any(lo>=hi):continue
  yy,xx=np.mgrid[lo[1]:hi[1],lo[0]:hi[0]];dx=xx-a[0];dy=yy-a[1]
  t=(dx*w[1]-dy*w[0])/det;q=(u[0]*dy-u[1]*dx)/det;inside=(t>=0)&(q>=0)&(t+q<=1)
  yy,xx=yy[inside],xx[inside];t=t[inside,None];q=q[inside,None]
  for field,arr in [(posmap,v),(normmap,norm)]:
   c0,c1,c2=arr[tri];field[yy,xx]=c0+t*(c1-c0)+q*(c2-c0)
  m[yy,xx]=True;nodule[yy,xx]=is_nodule[tri[0]]
 pp=posmap[m];nn=normmap[m];nn/=np.maximum(1e-8,np.linalg.norm(nn,axis=1,keepdims=True))
 colors=[];weights=[]
 for i,(c,mask,dist,box) in enumerate(views):
  rgb=np.stack([sample(c[:,:,k],i,pp) for k in range(3)],axis=1).astype(float)
  facing=np.maximum(nn@proj[i][2],.015)**24
  if kind=='slate':
   # Front and rear overhead views have different painted marbling; use one
   # strongest top source to keep the fat seams distinct.
   facing*=np.where(nn[:,1]>.34,100 if i==0 else (.2 if i in [2,6] else .03),1.)
  facing*=np.clip((sample(dist.astype('f'),i,pp)+7)/18,.06,1)
  weights.append(facing);colors.append(rgb)
 w=np.stack(weights,-1);den=w.sum(1,keepdims=True);rgb=(np.stack(colors,1)*w[:,:,None]).sum(1)/np.maximum(den,1e-20)
 if kind=='metal':
  q=nodule[m]
  rgb[q]=np.maximum([99.,93.,102.],.85*colors[0][q]+.15*rgb[q])
 if kind=='slate':
  # Register the unbroken top sheet to the full front-view quartz vein.
  # Side seams use the azimuth bake above, preserving its stratified edge.
  x0,y0,x1,y1=views[0][3];c=views[0][0];top=nn[:,1]>.46
  tx=x0+7+(pp[top,0]+.5)*(x1-x0-14)
  ty=y0+11+(pp[top,2]+.26)/.52*(y1-y0-49)
  rgb[top]=np.stack([nd.map_coordinates(c[:,:,ch],(ty,tx),order=1,mode='nearest') for ch in range(3)],axis=1)
 below=nn[:,1]<-.42
 base={'coal':[32,31,35],'metal':[69,58,62],'slate':[50,62,80]}[kind]
 rgb[below]=np.asarray(base)*.55+rgb[below]*.45
 tex=np.zeros((res,res,3),np.uint8);tex[m]=np.clip(rgb,0,255)
 _,ii=nd.distance_transform_edt(~m,return_indices=True);tex=tex[ii[0],ii[1]]
 v[:,1]-=v[:,1].min()
 for axis in [0,2]:v[:,axis]-=(v[:,axis].min()+v[:,axis].max())*.5
 v/=max(np.ptp(v[:,0]),np.ptp(v[:,2]))
 write_glb(out/(kind+'.glb'),v,f,norm,uv,tex);print('built',kind,'vertices',len(v),'triangles',len(f),np.ptp(v,axis=0))

for kind in args.kinds or files:
 build(kind)
