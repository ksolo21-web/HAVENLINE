"""Read-only structural census of source archives, not a visual or motion rating."""
from pathlib import Path
import hashlib, io,json,struct,zipfile,os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sha=lambda a:hashlib.sha256(a).hexdigest()
root=Path(os.environ['HAVENLINE_SOURCE_ARCHIVE_DIR']).resolve()
archive=root/'Character1_Validated_Rig_and_LODs.zip'
assert sha(archive.read_bytes())=='820131560e89b42bfd02affba4afdf259423cc468590d38a28cddbaca4725fc9'
library=[(x.name,x.read_bytes()) for x in [root/'Character 1.glb',root/'Character 1 rigged - with fingers - no animation.glb']]
assert [sha(b) for _,b in library]==['9ffb00c49ca8cec0ab2561ab5b79c9f6fb3ea63a761f6cb3ba0010cc3dd042c9','280d493b9ddedd728835a4df2ba8c1c810ae03e3dd52c4b323c773150d03d39c']
with zipfile.ZipFile(archive) as z:
 library.extend((n,z.read(n)) for n in z.namelist() if n.lower().endswith('.glb'))
def parse(blob):
 h=struct.unpack_from('<I',blob,12)[0]
 doc=json.loads(blob[20:20+h]);bin=memoryview(blob)[28+h:]
 assert not doc.get('extensionsRequired')
 assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==1
 p=doc['meshes'][0]['primitives'][0]
 assert p.get('mode',4)==4
 def arr(id):
  c=doc['accessors'][id];v=doc['bufferViews'][c['bufferView']]
  k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[c['type']]
  typ=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[c['componentType']]); off=v.get('byteOffset',0)+c.get('byteOffset',0)
  return np.ndarray((c['count'],k),dtype=typ,buffer=bin,offset=off,strides=(v.get('byteStride',k*typ.itemsize),typ.itemsize))
 V=arr(p['attributes']['POSITION']).copy();F=arr(p['indices']).reshape(-1,3).astype('i8')
 assert np.isfinite(V).all() and F.max()<len(V)
 return doc,V,F
def graph(v,t,step):
 if step:
  W,inv=np.unique(np.round(v/step).astype('i8'),axis=0,return_inverse=True)
 else:
  W,inv=np.unique(v,axis=0,return_inverse=True)
 F=inv[t]
 E=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]])
 C=coo_matrix((np.ones(len(E),dtype='b'),(E[:,0],E[:,1])),shape=(len(W),len(W))).tocsr()
 n,L=connected_components(C,directed=False,return_labels=True)
 # Count physical surface components (faces), not unreferenced vertices.
 assert np.all(L[F]==L[F[:,0]][:,None])
 fs=L[F[:,0]]
 return fs, L[inv],n
def inventory(name,blob):
 doc,V,F=parse(blob)
 y=(V[:,1]-V[:,1].min())/np.ptp(V[:,1])
 x=V[:,0]-(V[:,0].min()+V[:,0].max())/2
 width=np.ptp(V[:,0]); out={}
 for k,step in [('exact_position',0.),('one_ppm_height',float(np.ptp(V[:,1]))*1e-6)]:
  fs,_,_=graph(V,F,step)
  comp=[]
  for c,count in sorted(zip(*np.unique(fs,return_counts=True)),key=lambda z:-z[1]):
   rows=np.unique(F[fs==c])
   if len(comp)<4 or y[rows].min()<.32:
    comp.append(dict(face_count=int(count),min_max_norm_height=[float(y[rows].min()),float(y[rows].max())]))
  sides={}
  for letter,s in [('L',1),('R',-1)]:
   selected=[]
   for c in np.unique(fs[(y[F].min(1)<.055)&((x[F]*s).max(1)>width*.04)]):
    rows=np.unique(F[fs==c])
    lorows=rows[(s*x[rows]>width*.04)&(y[rows]<.38)]
    selected.append(dict(faces=int((fs==c).sum()),rows_in_side_lower_geometry=len(lorows),continues_body_above_norm_height_44=bool(y[rows].max()>.44)))
   sides[letter]=selected
  out[k]=dict(number_face_components=int(len(np.unique(fs))),large_or_lower_components=comp,sole_to_upper_connectivity=sides)
 return dict(name=name,sha256=sha(blob),vertex_face_payload_hash=sha(V.tobytes()+F.tobytes()),
  counts=dict(verts=len(V),faces=len(F),skins=[len(s['joints']) for s in doc['skins']],
   clip_names=[m.get('name','') for m in doc.get('animations',[])],materials=len(doc['materials'])),
  source_bounds= [V.min(0).tolist(),V.max(0).tolist()],welded_topology=out)
records=[inventory(n,b) for n,b in library]
print(json.dumps(dict(new_source_archive_sha256=sha(archive.read_bytes()),candidates=records,
  zip_entries=[n for n in zipfile.ZipFile(archive).namelist()],no_remesh_rig_edit_or_engine_run=True),indent=2))
