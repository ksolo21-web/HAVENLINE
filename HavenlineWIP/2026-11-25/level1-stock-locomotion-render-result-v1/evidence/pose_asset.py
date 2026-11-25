"""Bake exact original indices/texcoords/PBR with verified native skin matrices.
The manifest normalizes the exact exporter rows; no pose interpolation.
"""
from pathlib import Path
import copy,struct,json,hashlib
import numpy as np
SHA='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
def affine(row):
 o,*c=np.array(row,dtype=float); A=np.eye(4); A[:3,:3]=np.asarray(c).T; A[:3,3]=o
 assert np.isfinite(A).all()
 return A
def bake_factory(path,manifest,manifest_path):
 b=Path(path).read_bytes(); assert hashlib.sha256(b).hexdigest()==SHA and manifest['actor_source_glb_sha256']==SHA
 n,k=struct.unpack_from('<II',b,12); assert k==0x4e4f534a
 d=json.loads(b[20:20+n]); size,k=struct.unpack_from('<II',b,20+n)
 assert k==0x004e4942
 raw=b[28+n:28+n+size]
 def view(i):return d['bufferViews'][i]
 def buf(i):
  a=view(i); off=a.get('byteOffset',0); return raw[off:off+a['byteLength']]
 def acc(i):
  a=d['accessors'][i]; w=view(a['bufferView']); assert not a.get('sparse') and not w.get('byteStride') and not a.get('normalized')
  dt={5126:'<f4',5121:'<u1',5123:'<u2',5125:'<u4'}[a['componentType']]
  k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
  return np.frombuffer(buf(a['bufferView']),dt,count=a['count']*k,offset=a.get('byteOffset',0)).reshape(-1,k)
 p,=d['meshes'][0]['primitives']; at=p['attributes']; skin,=d['skins']
 v,nn,uv,j,w=(acc(at[k]) for k in ('POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0'))
 orig_b=acc(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
 order=np.asarray(manifest['verified_glb_joint_to_native_slot'],int); assert sorted(order.tolist())==list(range(66))
 binds=np.array([affine(b) for b in manifest['bind_inverse_by_slot']])
 assert np.max(abs(orig_b-binds[order]))<=2e-5
 weights_path=Path(manifest_path).parent/manifest['native_weights_relative']
 private=weights_path.read_bytes()
 assert hashlib.sha256(private).hexdigest()==manifest['native_weights_sha256']
 weights=np.frombuffer(private,'<u2').reshape(len(v),4).astype(float)/65535.
 assert np.max(abs(weights.sum(1)-1))<=2e-4
 # Verification records from actual native CPU skin, not manufactured by renderer.
 samples=manifest.get('original_native_source_spot_checks',[]); assert manifest.get('fresh_world_vertex_controls') is False
 normals=np.asarray(nn,dtype=float)
 vh=np.column_stack([v,np.ones(len(v))])
 tri=acc(p['indices']); assert len(v)==52898 and len(tri)==288003 and len(d['images'])==3
 source_atts={k:at[k] for k in ('POSITION','NORMAL','TEXCOORD_0')}
 out_doc={k:copy.deepcopy(d[k]) for k in ('asset','materials','textures','images','samplers')}
 out_doc.update(scenes=[{'nodes':[0]}],scene=0,nodes=[{'mesh':0}],meshes=[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3,'material':p['material']}]}])
 def frame(row,out):
  F=np.asarray([affine(t) for t in row['poses_by_skin_binding_slot']]); assert F.shape==(66,4,4)
  skinm=(F@binds)[order]; M=affine(row['mesh_world'])
  P=np.zeros((len(v),3)); N=np.zeros(P.shape)
  for k in range(4):
   L=skinm[j[:,k]]
   P+=(L@vh[:,:,None])[:,:3,0]*weights[:,k,None]
   N+=(L[:,:3,:3]@normals[:,:,None])[:,:,0]*weights[:,k,None]
  P=P@M[:3,:3].T+M[:3,3]
  N=N@M[:3,:3].T
  length=np.linalg.norm(N,axis=1)
  assert np.isfinite(P).all() and np.isfinite(N).all() and np.min(length)>1e-6
  N/=length[:,None]
  for sm in samples:
   if sm['age']!=row['age_tick']:continue
   ii=sm['original_vertex_i']
   assert np.max(abs(v[ii]-sm['native_bind_position']))<2e-5
   assert np.max(abs(uv[ii]-sm['native_uv']))<2e-5
   assert set(order[j[ii][weights[ii]>0]])==set(sm['nonzero_native_joint_slots'])
   assert np.linalg.norm(P[ii]-sm['native_world_skinned'])<4e-5
  z=copy.deepcopy(out_doc); z['accessors']=[];z['bufferViews']=[]; payload=bytearray()
  def add(t):
   index=len(z['bufferViews']);z['bufferViews'].append({'buffer':0,'byteOffset':len(payload),'byteLength':len(t)})
   payload.extend(t)
   while len(payload)%4:payload.append(0)
   return index
  for ii,data in [(at['POSITION'],P.astype('<f4')),(at['NORMAL'],N.astype('<f4')),(at['TEXCOORD_0'],uv),(p['indices'],tri)]:
   a=copy.deepcopy(d['accessors'][ii]);a.pop('byteOffset',None);a['bufferView']=add(data.tobytes())
   if ii==at['POSITION']:a['min']=data.min(0).tolist();a['max']=data.max(0).tolist()
   z['accessors'].append(a)
  for original,im in zip(d['images'],z['images']):im['bufferView']=add(buf(original['bufferView']))
  z['buffers']=[{'byteLength':len(payload)}]
  text=json.dumps(z,separators=(',',':')).encode(); text+=b' '*((-len(text))%4)
  Path(out).write_bytes(struct.pack('<4sII',b'glTF',2,12+8+len(text)+8+len(payload))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(payload),0x004e4942)+payload)
 return frame
