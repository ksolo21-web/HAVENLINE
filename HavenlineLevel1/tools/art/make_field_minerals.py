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
def fit_turnaround(v, normals, kind, views):
 # Camera-registered volumetric reconstruction gives a useful starting point.
 # Keep the calibrated x/z width while fitting the outer supports of all eight
 # silhouettes. The smooth cage also carries the existing chips, veins and UVs.
 from scipy.spatial import ConvexHull
 from scipy.optimize import least_squares
 def cage(p):
  x,y,z=p.T
  return np.stack([x,y,z,x*x,x*y,x*z,y*y,y*z,z*z,x**3,z**3,x*x*z,x*z*z],axis=1)
 def deform(p, coeff):
  return p+cage(p)@coeff
 hull=v[ConvexHull(v).vertices].astype(float)
 basis=cage(hull)
 angles=np.arange(32)*math.tau/32
 directions=np.stack([np.cos(angles),np.sin(angles)])
 def outline(p):
  low=p.min(0);high=p.max(0)
  centered=p-np.array([(low[0]+high[0])*.5,low[1]])
  return (centered@directions/(high[0]-low[0])).max(0)
 cams=[];targets=[]
 elevation=math.radians(29 if kind=='slate' else 14)
 for i,(_,mask,_,_) in enumerate(views):
  y,x=np.where(mask)
  contour=np.stack([x,-y],axis=1)
  targets.append(outline(contour[ConvexHull(contour).vertices]))
  az=i*math.pi/4
  cams.append(np.array([[math.cos(az),0,-math.sin(az)],[-math.sin(elevation)*math.sin(az),math.cos(elevation),-math.sin(elevation)*math.cos(az)]]).T)
 def residual(c):
  mesh=hull+basis@c.reshape(-1,3)
  error=[(outline(mesh@cam)-reference)*(1.7 if i==0 else 1.) for i,(cam,reference) in enumerate(zip(cams,targets))]
  return np.concatenate(error+[.09*c])
 result=least_squares(residual,np.zeros(basis.shape[1]*3),bounds=(-.9,.9),max_nfev=100)
 coeff=result.x.reshape(-1,3)
 new=deform(v,coeff)
 eps=1e-4
 jacobian=np.stack([(deform(v+axis*eps,coeff)-deform(v-axis*eps,coeff))/(2*eps) for axis in np.eye(3)],axis=2)
 assert np.linalg.det(jacobian).min()>.25
 rotated=np.linalg.solve(jacobian.transpose(0,2,1),normals[:,:,None])[:,:,0]
 rotated/=np.maximum(np.linalg.norm(rotated,axis=1,keepdims=True),1e-9)
 new[:,1]-=new[:,1].min()
 for axis in [0,2]:new[:,axis]-=(new[:,axis].min()+new[:,axis].max())*.5
 new/=max(np.ptp(new[:,0]),np.ptp(new[:,2]))
 return new,rotated

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
   if k in (1,2):
    # The 45° plate shows each small silver outcrop on the forward shoulder;
    # bring its bevel forward while retaining the contact root within the host.
    center+=eye*.045-right*.018
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
 fitted=v.copy();fitted_norm=norm.copy()
 if kind in ('metal','slate'):
  fitted[:,1]-=fitted[:,1].min()
  for axis in [0,2]: fitted[:,axis]-=(fitted[:,axis].min()+fitted[:,axis].max())*.5
  fitted/=max(np.ptp(fitted[:,0]),np.ptp(fitted[:,2]))
  fitted,fitted_norm=fit_turnaround(fitted,norm,kind,views)
 res=512
 paint_pos=np.zeros((res,res,3),dtype='f')
 posmap=np.zeros((res,res,3),dtype='f');normmap=posmap.copy();nodule=np.zeros((res,res),bool);m=np.zeros((res,res),bool)
 for tri in f:
  p=uv[tri]*res-.5;a,b,c=p;u=b-a;w=c-a;det=u[0]*w[1]-u[1]*w[0]
  if abs(det)<1e-7:continue
  lo=np.maximum(np.floor(p.min(axis=0)).astype(int),0);hi=np.minimum(np.ceil(p.max(axis=0)).astype(int)+1,res)
  if np.any(lo>=hi):continue
  yy,xx=np.mgrid[lo[1]:hi[1],lo[0]:hi[0]];dx=xx-a[0];dy=yy-a[1]
  t=(dx*w[1]-dy*w[0])/det;q=(u[0]*dy-u[1]*dx)/det;inside=(t>=0)&(q>=0)&(t+q<=1)
  yy,xx=yy[inside],xx[inside];t=t[inside,None];q=q[inside,None]
  for field,arr in [(posmap,v),(normmap,norm),(paint_pos,fitted)]:
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
  # Calibrate each paint camera to the reconstructed silhouette. The rear
  # three-quarter illustration exposes the complete bent pale quartz vein.
  # A single registered paint projection keeps it continuous over the top.
  pts=paint_pos[m]
  # Keep separate side layers and scarps readable with their nearest reference azimuth.
  def paint(view,pts):
   c,_,_,(x0,y0,x1,y1)=views[view];right,up=proj[view][:2]
   xx=fitted@right;yy=fitted@up
   tx=x0+(pts@right-xx.min())/np.ptp(xx)*(x1-x0)
   ty=y1-(pts@up-yy.min())/np.ptp(yy)*(y1-y0)
   return np.stack([nd.map_coordinates(c[:,:,ch],(ty,tx),order=1,mode='nearest') for ch in range(3)],axis=1)
  painted=np.stack([paint(i,pts) for i in range(8)],axis=1)
  side_w=np.stack([np.maximum(nn@proj[i][2],.01)**28 for i in range(8)],1)
  side=(painted*side_w[:,:,None]).sum(1)/side_w.sum(1,keepdims=True)
  # Smooth transition from the seam running over the upper plate into the
  # individual dark lateral cleavage beds.
  top=np.clip((nn[:,1]-.27)/.30,0.,1.)
  # Sample the front and back presentations on their respective surfaces.
  # A narrow feather, limited to the middle of the long bed, keeps the pale
  # seam connected without stretching an occluded edge over the whole top.
  front=np.clip((pts[:,2]+.06)/.15,0.,1.)
  front=front*front*(3.-2.*front)
  # On the opposite rear flank the 135-degree camera can see the broken
  # continuation of the vein behind the raised right corner.
  rear_edge=np.clip((-.075-pts[:,2])/.075,0.,1.)
  rear_edge=rear_edge*rear_edge*(3.-2.*rear_edge)
  rear=painted[:,5]*(1-rear_edge[:,None])+painted[:,3]*rear_edge[:,None]
  upper=painted[:,0]*front[:,None]+rear*(1-front[:,None])

  rgb=(1.-top[:,None])*(.75*side+.25*rgb)+top[:,None]*upper

 below=nn[:,1]<-.42
 base={'coal':[32,31,35],'metal':[69,58,62],'slate':[50,62,80]}[kind]
 rgb[below]=np.asarray(base)*.55+rgb[below]*.45
 tex=np.zeros((res,res,3),np.uint8);tex[m]=np.clip(rgb,0,255)
 _,ii=nd.distance_transform_edt(~m,return_indices=True);tex=tex[ii[0],ii[1]]
 v[:,1]-=v[:,1].min()
 for axis in [0,2]:v[:,axis]-=(v[:,axis].min()+v[:,axis].max())*.5
 v/=max(np.ptp(v[:,0]),np.ptp(v[:,2]))
 if kind in ('metal','slate'):
  v,norm=fitted,fitted_norm
  # Retain short-range contrast in the existing projected mineral inclusions and strata.
  rgb=tex.astype(float)
  tex=np.clip(rgb+.30*(rgb-nd.gaussian_filter(rgb,(1.4,1.4,0))),0,255).astype('B')
 write_glb(out/(kind+'.glb'),v,f,norm,uv,tex);print('built',kind,'vertices',len(v),'triangles',len(f),np.ptp(v,axis=0))

for kind in args.kinds or files:
 build(kind)
