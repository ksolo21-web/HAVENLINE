"""Fit the generated House D03 visual to the live shell and the typed conveyor mouths."""
import io,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
src,out=map(Path,sys.argv[1:3])
def load(path,name=None):
 raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
 meta=json.loads(raw[20:20+size]);blob=raw[28+size:]
 def buf(ind):
  v=meta['bufferViews'][ind];p=v.get('byteOffset',0)
  return blob[p:p+v['byteLength']]
 def attr(idx):
  v=meta['accessors'][idx];typ={5125:'<u4',5123:'<u2',5126:'<f4'}[v['componentType']]
  return np.frombuffer(buf(v['bufferView']),typ).reshape(v['count'],-1)
 node=next((n for n in meta['nodes'] if n.get('name')==name),None)
 mesh=meta['meshes'][node['mesh'] if node else 0]['primitives'][0];a=mesh['attributes']
 return np.column_stack((attr(a['POSITION']),attr(a['NORMAL']),attr(a['TEXCOORD_0']))).astype(float),attr(mesh['indices']).reshape(-1,3),Image.open(io.BytesIO(buf(meta['images'][0]['bufferView']))).convert('RGB')
data={k:load(src/(k+'.glb')) for k in ('utility','food')}
nodes=[]
def clip(poly,ax,lim,direction):
 if not poly:return []
 outp=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  aa=(a[ax]-lim)*direction>=0;bb=(b[ax]-lim)*direction>=0
  if aa:outp.append(a)
  if aa!=bb:outp.append(a+(b-a)*((lim-a[ax])/(b[ax]-a[ax])))
 return outp
def emit(name,key,verts,faces,boxes,matrix,offset):
 result=[];ix=[]
 for limits in boxes:
  valid=np.ones(len(faces),dtype=bool)
  for ax,(lo,hi) in enumerate(limits):
   valid&=(verts[faces,ax].max(1)>=lo)&(verts[faces,ax].min(1)<=hi)
  for f in faces[valid]:
   poly=list(verts[f])
   for ax,(lo,hi) in enumerate(limits):
    poly=clip(clip(poly,ax,lo,1),ax,hi,-1)
   if len(poly)<3:continue
   idx=len(result);result.extend(poly)
   ix.extend((idx,idx+k,idx+k+1) for k in range(1,len(poly)-1))
 a=np.array(result);idx=np.array(ix);xyz=a[:,:3]@matrix.T+offset
 n=a[:,3:6]@np.linalg.inv(matrix);n/=np.maximum(1.e-12,np.linalg.norm(n,axis=1,keepdims=True))
 vv=np.concatenate((xyz,n,a[:,6:]),1).round(6)
 dedup,lookup=np.unique(vv,axis=0,return_inverse=True);idx=lookup[idx]
 ok=(idx[:,0]!=idx[:,1])&(idx[:,1]!=idx[:,2])&(idx[:,0]!=idx[:,2]);idx=idx[ok]
 if np.linalg.det(matrix)<0:idx=idx[:,::-1]
 nodes.append((name,key,dedup,idx))
 print(name,len(dedup),len(idx),dedup[:,:3].min(0),dedup[:,:3].max(0))
L=(-1.,1.)
v,f,im=data['utility']
# Keep snow, ridge, edge timbers and real crate crest. Replace only the blanket
# blue rear triangle and its incorrect second crate with the generated rear vent.
face=v[f,:3].mean(1);n=v[f,3:6].mean(1)
drop=(face[:,2]<-.354)&(abs(face[:,0]-.115)<.29)&(face[:,1]>.013)&(n[:,2]<-.56)
emit('ConnectedRoof','utility',v,f[~drop],[[L,(-.004,1.),L]],np.diag([4.8,3.55,3.89]),[-.552,1.834,.3404])
# Retain the first generated gable, crest, fascia and outer timber. Its
# repeated snow pillows are replaced with the source house's continuous banks.
keyn,mat,body,faces=nodes.pop()
tex=np.array(data['utility'][2]);coords=(body[faces,6:].mean(1)*tex.shape[1::-1]).astype(int)%tex.shape[1::-1]
color=tex[coords[:,1],coords[:,0]].astype(float)
c=body[faces,:3].mean(1);no=body[faces,3:6].mean(1)
orange=(color[:,0]>color[:,1]*1.24)&(color[:,0]>color[:,2]*1.42)
blue=(color[:,2]>color[:,0]*1.55)&(color[:,0]<100)
front_back=(np.abs(c[:,2])>1.01)&(np.abs(no[:,2])>.43)
hardware=(c[:,1]<2.03)&front_back
keep=(front_back&(orange|blue|hardware))|(orange&(c[:,1]<2.02))
nodes.append((keyn,mat,body,faces[keep]))
# D03 retains a wide joined ridge with an uneven scalloped edge, a slim snow
# return at the eaves, and an exposed band of blue timber shingles. Reuse
# the original complete layered substrate and its seven sculpted snow banks.
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
source_shell=Path(sys.argv[3]) if len(sys.argv)>3 else out.parent/'camp_storehouse.glb'
data['shell']=load(source_shell,'Roof')
old,raw,_=data['shell'];old=old.copy()
pts,look=np.unique(old[:,:3].round(4),axis=0,return_inverse=True);tr=look[raw]
graph=coo_matrix((np.ones(tr.size),(tr.flatten(),np.roll(tr,1,axis=1).flatten())),shape=(len(pts),len(pts)))
_,groups=connected_components(graph,directed=False);fg=groups[tr[:,0]];vg=groups[look]
ridge=max(set(fg),key=lambda k:sum(k==fg))
sel=(vg==ridge);xx=old[sel,0].copy();zz=old[sel,2];newx=xx.copy()
for sign in (-1.,1.):
 side=sign*xx>0
 series=np.round(zz[side],3);unique=np.unique(series)
 outer=[np.max(np.abs(xx[side][series==k])) for k in unique]
 # Grid ends include a cap with a reduced span. Keep its rounded closure.
 extent=np.interp(zz[side],unique,outer)
 target=.65+.12*np.sin(zz[side]*2.0+sign*.7)+.08*np.sin(zz[side]*4.5+sign*1.8)+.035*np.cos(zz[side]*7.5)
 newx[side]*=1.+np.clip((target-extent)/np.maximum(.48,extent),-.26,.35)*np.minimum(1.,(1.39-np.abs(zz[side]))/.17).clip(0,1)
old[sel,0]=newx
old[sel,1]+=.50*(np.abs(xx)-np.abs(newx))+.036*np.maximum(0.,1.-(newx/.82)**2)
# Align the original tile/overhang under the new gable fascia.
old[:,1]=1.823+(old[:,1]-1.823)*1.06+.018
# The connected generation supplies the outer orange timber, so discard only
# the duplicate original trim. Its blue roof and every continuous snow bank stay.
tex=np.array(data['shell'][2]);tuv=(old[raw,6:].mean(1)*tex.shape[1::-1]).astype(int)%tex.shape[1::-1]
cc=tex[tuv[:,1],tuv[:,0]].astype(float);keep=~((cc[:,0]>1.30*cc[:,1])&(cc[:,0]>1.60*cc[:,2]))
nodes.append(('SnowAndRoof','shell',old,raw[keep]))
v,f,im=data['food'];face=v[f,:3].mean(1);n=v[f,3:6].mean(1)
select=(n[:,2]>.18)&(abs(face[:,0])<.30)&(face[:,1]<.292)
emit('RearVent','food',v,f[select],[[(-.30,.30),(.013,.291),(.194,.277)]],np.diag([-4.76,3.55,-3.89]),[0.,1.84,-.40])
for key,name,to_axes,cen,below,above,mouth,frontal,scale in [
 ('utility','UtilityDockFrame',[[0,0,1],[0,1,0],[-1,0,0]],.047,-.272,-.166,-.212,.199,3.02),
 ('food','FoodDockFrame',np.eye(3),-.117,-.170,-.044,-.119,.21,3.13)]:
 v,f,_=data[key];v=v.copy();basis=np.array(to_axes);v[:,:3]=v[:,:3]@basis.T;v[:,3:6]=v[:,3:6]@basis.T
 depth=(frontal,frontal+.115);span=.096;opening=.066
 # Four non-overlapping cut volumes. No triangle remains inside the cargo tunnel.
 # Keep the native bezel cheeks and upper lip, using real moving belts for the deck.
 boxes=[[(cen-span,cen-opening),(below,above),depth],[(cen+opening,cen+span),(below,above),depth],[(cen-opening,cen+opening),(above-.013,above),depth]]
 emit(name,key,v,f,boxes,np.diag([scale,scale*1.30,2.7]),[-cen*scale,-mouth*scale*1.30,-frontal*2.7-.075])
 frame=nodes.pop();body=frame[2].copy()
 # Scale the upper frame around the deck. The bound log stack and the plated dish
 # retain their actual gameplay dimensions at the bend to the indoor shuttle.
 grow=2.78 if key=='utility' else 1.48
 upper=body[:,1]>0
 body[upper,1]*=grow;body[upper,4]/=grow;body[upper,3:6]/=np.maximum(1e-12,np.linalg.norm(body[upper,3:6],axis=1,keepdims=True))
 # The generated cream placard for this mouth has approximated lettering. Sample
 # its own clear painted area and leave the IN / OUT lettering to the routed sign.
 sy=-.136 if key=='utility' else -.006
 front=.210 if key=='utility' else .239
 plate=[[(cen-.076,cen+.076),(sy-.015,sy+.017),(front,front+.040)]]
 emit(name,key,v,f,plate,np.diag([2.43,3.29,1.02]),[-cen*2.43,.584-sy*3.29,.019-front*1.02])
 _,_,sign,signfx=nodes.pop();im=data[key][2];ts=np.array(im)
 uvs=(sign[:,6:]*[im.width,im.height]).astype(int)%[im.width,im.height]
 rgb=ts[uvs[:,1],uvs[:,0]].astype(float)
 goal=np.array([252,224,177.]);clean_uv=sign[np.argmin(np.linalg.norm(rgb-goal,axis=1)),6:].copy()
 sign[:,6:]=clean_uv
 nodes.append((name,key,np.concatenate((body,sign)),np.vstack((frame[3],signfx+len(body)))))

# Roof boards are the upper boundary of the replacement fascia. Crop every
# triangle (including the cooked-food generation's inherited edge frost) with
# both pitches so no pigment or sliver may protrude through the visible snow.
for ni,(id,key,vertices,faces) in enumerate(nodes):
 if id not in ['ConnectedRoof','RearVent']:continue
 index=[];verts=[]
 for face in faces:
  poly=list(vertices[face])
  for side in [-1.,1.]:
   nextp=[]
   for a,b in zip(poly,poly[1:]+poly[:1]):
    da=2.845-a[1]-side*.515*a[0];db=2.845-b[1]-side*.515*b[0]
    if da>=0:nextp.append(a)
    if (da>=0)!=(db>=0):nextp.append(a+(b-a)*(da/(da-db)))
   poly=nextp
  if len(poly)<3:continue
  start=len(verts);verts.extend(poly);index.extend([start,start+k,start+k+1] for k in range(1,len(poly)-1))
 values,lookup=np.unique(np.array(verts).round(6),axis=0,return_inverse=True)
 nodes[ni]=(id,key,values,lookup[np.array(index)])
buf=bytearray();views=[];access=[];meshes=[];hier=[];images=[];materials=[]
def buffer(b):
 pos=len(buf);buf.extend(b);views.append(dict(buffer=0,byteOffset=pos,byteLength=len(b)));buf.extend(bytes((-len(buf))%4));return len(views)-1
def accessor(v,t,fmt,dim):
 arr=np.ascontiguousarray(v,dtype=fmt);a=dict(bufferView=buffer(arr.tobytes()),componentType=t,count=len(v),type=dim)
 if dim=='VEC3':a.update(min=arr.min(0).tolist(),max=arr.max(0).tolist())
 access.append(a);return len(access)-1
for key,(_,_,im) in data.items():
 im.thumbnail((2048,2048),Image.Resampling.LANCZOS);enc=io.BytesIO();im.save(enc,format='JPEG',quality=87,subsampling=0,optimize=True)
 images.append(dict(bufferView=buffer(enc.getvalue()),mimeType='image/jpeg',name='Storehouse'+key))
 mi=len(materials)
 fill=.16 if key=='shell' else .21
 materials.append(dict(name=key+' paint and timber',pbrMetallicRoughness=dict(baseColorTexture=dict(index=mi),roughnessFactor=.78,metallicFactor=.08),emissiveTexture=dict(index=mi),emissiveFactor=[fill,fill,fill],doubleSided=True))
for name,key,v,i in nodes:
 assert np.isfinite(v).all(),name
 degenerate=np.linalg.norm(v[:,3:6],axis=1)<.001
 v[degenerate,3:6]=[0.,1.,0.]
 p=dict(attributes=dict(POSITION=accessor(v[:,:3],5126,'<f4','VEC3'),NORMAL=accessor(v[:,3:6],5126,'<f4','VEC3'),TEXCOORD_0=accessor(v[:,6:],5126,'<f4','VEC2')),indices=accessor(i.flatten(),5123,'<u2','SCALAR'),material=list(data).index(key))
 hier.append(dict(name=name,mesh=len(meshes)));meshes.append(dict(name=name,primitives=[p]))
j=dict(asset=dict(version='2.0',generator='Havenline D03 connected storehouse fitting'),scene=0,scenes=[dict(nodes=list(range(len(nodes))))],nodes=hier,meshes=meshes,materials=materials,images=images,textures=[dict(source=i) for i in range(len(images))],buffers=[dict(byteLength=len(buf))],bufferViews=views,accessors=access)
b=json.dumps(j,separators=(',',':'),allow_nan=False).encode();b+=b' '*(-len(b)%4)
tmp=out.with_suffix('.building');tmp.write_bytes(struct.pack('<4sIII4s',b'glTF',2,28+len(b)+len(buf),len(b),b'JSON')+b+struct.pack('<I4s',len(buf),b'BIN\0')+buf);tmp.replace(out)
