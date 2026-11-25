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
# Representative material landmarks, not masks: width/physical rigidity unknown.
cands=[
 ('L',2,'lace-span observational only',(447,164)),('L',2,'lace-span observational only',(458,210)),
 ('R',5,'lace-span observational only',(630,166)),('R',5,'lace-span observational only',(639,202)),
 ('L',2,'upper/collar soft leather next to lace path',(546,156)),('R',5,'upper/collar soft leather next to lace path',(534,156)),
 ('L',2,'collar band apparent trim, mechanical stiffness unknown',(570,119)),('R',5,'collar band apparent trim, mechanical stiffness unknown',(500,119)),
 ('L',2,'sole rim visible, use existing exact contact lock',(536,381)),('R',5,'sole rim visible, use existing exact contact lock',(534,380)),
 ('L',0,'medial/inner aperture unresolved by outer view',(722,187)),('L',0,'medial/inner aperture unresolved by outer view',(736,255))
]
for ki in (0,2,5):closest_cache[ki]=(*camera(ki),camera(ki)[0][T,:2].mean(1))
for_all=[]
for side,k,role,xy0 in cands:
 p=np.array([210+xy0[0]/3,610+xy0[1]/3])
 h=locate(k,side,p)
 if not h:
  for_all.append(dict(side=side,view=k,role=role,visible_triangle=None));continue
 w=np.unique(weld[h['raw']]);q=xy[T[h['face']]]
 surface=np.cross(q[1]-q[0],q[2]-q[0]);surface/=np.linalg.norm(surface)
 upward=np.array([0.,0.,1.]);upward-=surface*(surface@upward);ll=np.linalg.norm(upward)
 frame=None
 if ll>1e-5:
  upward/=ll; trans=np.cross(upward,surface)
  frame=np.stack([trans,upward,surface],axis=1)
  assert np.linalg.det(frame)>.999999
 h.update(side=side,view=k,role=role,raw_seam_aliases=np.flatnonzero(np.isin(weld,w)).tolist(),welded_ids=w.tolist(),anchor_frame_columns_unit=None if frame is None else frame.tolist())
 for_all.append(h)
(P/'material-observations.json').write_text(json.dumps(for_all,indent=2))
print([(x['side'],x['role'],x.get('face')) for x in for_all])
