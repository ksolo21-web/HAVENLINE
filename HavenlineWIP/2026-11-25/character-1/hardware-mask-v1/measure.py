import os
import numpy as np,json,struct,hashlib,io
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
gpath=Path(os.environ['C1_EXACT_GLB'])
b=gpath.read_bytes();assert sha(gpath)=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
assert sha(Path(os.environ['C1_EXACT_BLEND']))=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
n,t=struct.unpack_from('<II',b,12);g=json.loads(b[20:20+n]);bin0=28+n
def acc(i):
 a=g['accessors'][i];d=g['bufferViews'][a['bufferView']]
 tp={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
 co={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
 return np.ndarray((a['count'],co),dtype=tp,buffer=b,offset=bin0+a.get('byteOffset',0)+d.get('byteOffset',0),strides=(d.get('byteStride',co*np.dtype(tp).itemsize),np.dtype(tp).itemsize))
me=g['meshes'][0]['primitives'][0]
geo=acc(me['attributes']['POSITION']).astype(float); xy=geo[:,[0,2,1]]*np.array([1,-1,1])
T=acc(me['indices']).reshape(-1,3).astype(int); UV=acc(me['attributes']['TEXCOORD_0'])
a_path=(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
assert sha(a_path)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
a=np.load(a_path);norm=(xy-a['source_origin'])*float(a['scale'])
assert np.max(abs(norm-a['rest']))<2e-7 and np.array_equal(T,a['tri'])
_,rep,weld=np.unique(np.rint(norm/1e-6).astype('int64'),axis=0,return_index=True,return_inverse=True)
m=g['materials'][0]
roles={'baseColor':m['pbrMetallicRoughness']['baseColorTexture']['index'],'metallicRoughness':m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],'normal':m['normalTexture']['index']}
png={}; pbr={}
for key,i in roles.items():
 d=g['bufferViews'][g['images'][g['textures'][i]['source']]['bufferView']];z=bin0+d.get('byteOffset',0);raw=b[z:z+d['byteLength']]
 png[key]=np.asarray(Image.open(io.BytesIO(raw)).convert('RGB'))
 pbr[key]={'sha':hashlib.sha256(raw).hexdigest(),'size':list(png[key].shape[:2])}
# Eyelet anchors chosen independently from saved textured render pixels. A side source
# sees exterior; the +45 camera candidate only sees the opposite medial fasteners on R.
# Centers given in original crop view (210,610)-(570,759) at 3x, not newly rendered.
cards={
 'L':[(2,'lateral',[(468,119),(491,182),(480,223),(455,258),(426,287)])],
 'R':[(5,'lateral',[(607,119),(588,183),(601,223),(617,260),(653,289)]),(1,'medial',[(370,126),(368,184),(354,224),(341,252),(317,291)])]}
def camera(i):
 ang=np.deg2rad([0,45,90,135,180,270][i]); C=np.array([np.sin(ang),-np.cos(ang),0.])
 X=np.array([np.cos(ang),np.sin(ang),0.])
 xy0=np.column_stack((390+(780/2.04)*(xy@X),390-(780/2.04)*xy[:,2],xy@C))
 return xy0,X,C
closest_cache={}
def locate(K,boot_side,px):
 xy0,X,C,cent=closest_cache[K]
 cand=np.max(np.abs(cent-px),axis=1)<5
 cand &= ((1 if boot_side=='L' else -1)*norm[T,0]>.027).all(1)&(norm[T,2]<.30).all(1)
 ix=np.flatnonzero(cand)
 u=xy0[T[ix],:2]
 aa=u[:,1]-u[:,0]; bb=u[:,2]-u[:,0];cp=px-u[:,0]
 det=aa[:,0]*bb[:,1]-aa[:,1]*bb[:,0]
 wi=np.zeros((len(u),3)); nz=abs(det)>1e-12
 wi[nz,1]=(cp[nz,0]*bb[nz,1]-cp[nz,1]*bb[nz,0])/det[nz]
 wi[nz,2]=(aa[nz,0]*cp[nz,1]-aa[nz,1]*cp[nz,0])/det[nz];wi[:,0]=1-wi[:,1]-wi[:,2]
 hit=(wi.min(1)>-1e-8)&nz
 if not hit.any():return None
 dep=(xy0[T[ix],2]*wi).sum(1)
 ii=np.argmax(np.where(hit,dep,-1e9)); fi=int(ix[ii]); ww=wi[ii]
 position=ww@xy[T[fi]];uv=ww@UV[T[fi]]
 return dict(face=fi,raw=T[fi].tolist(),bary=ww.tolist(),xyz_raw=position.tolist(),xyz_175_m=((position-a['source_origin'])*float(a['scale'])).tolist(),uv=uv.tolist())
all_sites=[]; views=set(i for z in cards.values() for i,_,_ in z)
for k in (0,1,2,5):closest_cache[k]=(*camera(k),camera(k)[0][T,:2].mean(1))
for s,ls in cards.items():
 for k,name,points in ls:
  data=closest_cache[k]
  path=Path(os.environ['C1_EXISTING_VIEW_DIR'])/('ortho%d.png'%k);im=Image.open(path).convert('RGB');draw=ImageDraw.Draw(im)
  for j,mark in enumerate(points):
   c=np.array([210+mark[0]/3,610+mark[1]/3]);hit=locate(k,s,c)
   if hit is None:
    all_sites.append(dict(side=s,side_view=name,view=k,label='rim stud' if not j else 'lace port %d'%j,state='occluded or geometric no match',px=c.tolist()));continue
   uid=np.array(hit['xyz_raw']); ref=[]
   for ang in np.arange(12)*np.pi/6:
    pr=c+np.array([np.cos(ang),np.sin(ang)])*3.8
    out=locate(k,s,pr)
    if out is not None:ref.append(np.array(out['xyz_raw'])@data[2])
   relief=None if len(ref)<8 else (uid@data[2]-np.median(ref))*float(a['scale'])*1000
   # Restrict to measured front portion of the relief and nearby visible normals.
   data_p=data[0]; dist=np.linalg.norm(data_p[:,:2]-c,axis=1)
   rr=(dist<1.80)&(np.abs(data_p[:,2]-uid@data[2])<.010)&(np.linalg.norm(xy-uid,axis=1)<.013)
   rr&= (1 if s=='L' else -1)*norm[:,0]>.027
   ids=np.flatnonzero(rr)
   if not set(hit['raw']).issubset(set(ids.tolist())):ids=np.unique(np.r_[ids,hit['raw']])
   wp=np.unique(weld[ids]); ali=np.flatnonzero(np.isin(weld,wp)); ff=np.flatnonzero(np.isin(T,ali).all(1))
   vals={}
   for role,arr in png.items():
    u,v=np.clip(hit['uv'],0,.999999);vals[role]=arr[int(v*arr.shape[0]),int(u*arr.shape[1])].tolist()
   # Texture not treated as proof of mechanical stiffness. CAD-normal is a local rest anchor only.
   q=xy[T[hit['face']]];nu=np.cross(q[1]-q[0],q[2]-q[0]);nu/=np.linalg.norm(nu)
   pred={}
   for oi in (0,1,2,5):
    V,X,O=camera(oi)
    pt=np.array([390+780/2.04*(uid@X),390-780/2.04*uid[2]])
    ray=locate(oi,s,pt)
    dz=None if ray is None else (np.asarray(ray['xyz_raw'])-uid)@O*float(a['scale'])*1000
    pred[oi]=dict(px=pt.tolist(),front_depth_difference_mm=dz,visible=bool(dz is not None and abs(dz)<1.25))
   hit.update(side=s,side_view=name,view=k,px=c.tolist(),label='rim stud' if not j else 'lace port %d'%j, relieffront_mm=relief,relief_samples=len(ref),normal=nu.tolist(),pbr_texel=vals, candidate='relief-backed visible core' if relief is not None and relief>1.5 else 'uncertain color or elongated surface',core_raw=ids.tolist(),welded_ids=wp.tolist(),raw_seam_aliases=ali.tolist(),island_inner_faces=ff.tolist(),projected_witness=pred)
   all_sites.append(hit)
   cc=tuple(c);color='#46ffd3' if hit['candidate'].startswith('relief') else '#ffd03e'
   draw.ellipse((cc[0]-2,cc[1]-2,cc[0]+2,cc[1]+2),outline=color,width=1);draw.text((cc[0]+3,cc[1]-5),s+str(j),fill=color)
  im.crop((210,610,570,759)).resize((1080,447),Image.Resampling.NEAREST).save(P/('existing-view-%d-%s-analytic-overlay.png'%(k,s)))
(P/'islands.json').write_text(json.dumps({'source':sha(gpath),'pbr':pbr,'observations':all_sites},indent=2))
print(len(all_sites),[(x.get('side'),x.get('side_view'),x['label'],x.get('relieffront_mm'),len(x.get('raw_seam_aliases',[]))) for x in all_sites])
