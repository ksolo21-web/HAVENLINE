"""Rebuild the fitted Meshy axe and backpack extension from the two existing authored GLBs."""
import json, struct, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix, csgraph

root = Path(sys.argv[1])
def read(path):
    raw = path.read_bytes()
    size = int.from_bytes(raw[12:16], 'little')
    return json.loads(raw[20:20+size]), bytearray(raw[28+size:])
def array(doc, buf, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    dtype = {5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]
    width = {'VEC3':3,'VEC4':4,'SCALAR':1}[a['type']]
    return np.frombuffer(buf, dtype=dtype, count=width*a['count'], offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)
def write(path, doc, buf):
    doc['buffers']=[{'byteLength':len(buf)}]
    header=json.dumps(doc,separators=(',',':')).encode()
    header+=b' '*(-len(header)%4)
    buf+=b'\x00'*(-len(buf)%4)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(header)+len(buf))+struct.pack('<I4s',len(header),b'JSON')+header+struct.pack('<I4s',len(buf),b'BIN\0')+buf)
tools=root/'assets/tools'
d,b=read(tools/'axe-meshy.glb')
primitive=d['meshes'][0]['primitives'][0]
v=array(d,b,primitive['attributes']['POSITION']); normals=array(d,b,primitive['attributes']['NORMAL'])
y=v[:,1].copy()
# The free grip follows this donor's curved wooden centerline. The metal head and
# wood immediately below its eye (y >= -.08) keep their authored vertices/normals.
t=np.clip((y+.34)/.26,0,1)
factor=.75+.25*t*t*(3-2*t)
slope=.25*6*t*(1-t)/.26
center=.44-.40*np.maximum(0.,y+.56)
dcenter=np.where(y>-.56,-.40,0.)
dxdy=dcenter*(1-factor)+(v[:,0]-center)*slope
dzdy=v[:,2]*slope
mask=y<-.08
nx=normals[:,0]/factor
nz=normals[:,2]/factor
n=np.stack([nx,normals[:,1]-dxdy*nx-dzdy*nz,nz],axis=1)
normals[mask]=n[mask]/np.linalg.norm(n[mask],axis=1,keepdims=True)
v[mask,0]=center[mask]+factor[mask]*(v[mask,0]-center[mask]);v[mask,2]*=factor[mask]
a=d['accessors'][primitive['attributes']['POSITION']]
a['min']=v.min(axis=0).tolist();a['max']=v.max(axis=0).tolist()
start=len(b)
for im in d['images']:
    view=d['bufferViews'][im.pop('bufferView')]
    start=min(start,view['byteOffset'])
    uri='axe-meshy_'+im['name']+('.jpg' if 'jpeg' in im['mimeType'] else '.png')
    assert (tools/uri).read_bytes()==b[view['byteOffset']:view['byteOffset']+view['byteLength']]
    im.clear();im['uri']=uri
d['bufferViews']=d['bufferViews'][:4];write(tools/'axe-field-grip.glb',d,b[:start])

pack=root/'assets/field_pack'
d,b=read(pack/'carry_frame.glb');src=d['meshes'][0]['primitives'][0]
v=array(d,b,src['attributes']['POSITION']); normal=array(d,b,src['attributes']['NORMAL'])
color=array(d,b,src['attributes']['COLOR_0']);f=array(d,b,src['indices']).reshape(-1,3)
w,inv=np.unique(v.round(5),axis=0,return_inverse=True);vf=inv[f]
edges=coo_matrix((np.ones(vf.size),(vf.ravel(),np.roll(vf,1,axis=1).ravel())),shape=(len(w),len(w)))
_,labels=csgraph.connected_components(edges,directed=False)
# Copy the original lowest rounded transverse rail, including bevels, normals
# and vertex colors from the author's original rack.
component=next(k for k in set(labels) if w[labels==k,0].min()<-.42 and w[labels==k,1].max()<.19)
select=f[labels[inv[f[:,0]]]==component];keep,newidx=np.unique(select,return_inverse=True)
rail=v[keep].copy();rail-=(rail.min(0)+rail.max(0))*.5
idx=newidx.reshape(-1,3)
mat=d['materials'];d={'asset':{'version':'2.0'},'materials':mat,'accessors':[],'bufferViews':[],'meshes':[],'nodes':[],'scenes':[{'nodes':[0,1]}],'scene':0}
buf=bytearray()
def attr(a,typ,gltf,position=False):
    buf.extend(b'\x00'*(-len(buf)%4))
    offset=len(buf);buf.extend(a.tobytes());i=len(d['accessors'])
    d['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':a.nbytes})
    desc={'bufferView':i,'componentType':typ,'count':len(a),'type':gltf}
    if position:desc.update(min=a.min(0).tolist(),max=a.max(0).tolist())
    d['accessors'].append(desc);return i
for bay,(start,end,cross) in enumerate([(-.14,-.62,-.40),(-.62,-.94,-.82)]):
    positions=[];normals=[];colors=[];indices=[]
    pieces=[(np.eye(3),np.array([0,.172,cross]))]
    for x in (-.28,.28):
        oriented=np.array([[0,0,1],[0,1,0],[-(start-end)/.86,0,0]])
        pieces.append((oriented,np.array([x,.137,(start+end)*.5])))
    for transform,at in pieces:
        indices.append(idx+sum(map(len,positions)));positions.append(rail@transform.T+at)
        n=normal[keep]@np.linalg.inv(transform);normals.append(n/np.linalg.norm(n,axis=1,keepdims=True));colors.append(color[keep])
    c=np.concatenate(colors);assert c.dtype==np.float32
    attrs={'POSITION':attr(np.concatenate(positions).astype('<f4'),5126,'VEC3',True),'NORMAL':attr(np.concatenate(normals).astype('<f4'),5126,'VEC3'),'COLOR_0':attr(c,5126,'VEC4')}
    name=['MiddleSupport','RearSupport'][bay];d['meshes'].append({'name':name,'primitives':[{'attributes':attrs,'indices':attr(np.concatenate(indices).astype('<u2').ravel(),5123,'SCALAR'),'material':0}]});d['nodes'].append({'name':name,'mesh':bay})
write(pack/'expedition_shelf.glb',d,buf)
