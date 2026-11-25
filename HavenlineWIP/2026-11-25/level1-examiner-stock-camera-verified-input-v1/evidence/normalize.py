from pathlib import Path
import hashlib,json,sys,struct,zstandard
from collections import Counter
import numpy as np
from PIL import Image
from io import BytesIO
from pose_asset import affine
capture,glb,scn,out=map(Path,sys.argv[1:]); assert not out.exists()
def digest(b): return hashlib.sha256(b).hexdigest()
c=capture.read_bytes(); lines=c.decode().splitlines()
records=[l for l in lines if l.startswith('CAP_PRIVATE_')]
assert digest("\n".join(l.split(" ",1)[1] for l in records if l.startswith(("CAP_PRIVATE_START ","CAP_PRIVATE_FRAME "))).encode())=='05a26f8ae50f6397cef1efe3b37334f3c918b646d51c4467d70047347eaba894'
def get(tag):return [json.loads(l[len(tag)+1:]) for l in lines if l.startswith(tag+' ')]
st,=get('CAP_PRIVATE_START'); fs=get('CAP_PRIVATE_FRAME'); assert [f['age'] for f in fs]==list(range(0,267,2))
b=glb.read_bytes(); assert digest(b)=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
n=struct.unpack_from('<I',b,12)[0]; d=json.loads(b[20:20+n]); bin0=b[n+28:]
def vbytes(i):
 o=d['bufferViews'][i]; st=o.get('byteOffset',0);return bin0[st:st+o['byteLength']]
def acc(i,k,dt):
 v=d['accessors'][i];return np.frombuffer(vbytes(v['bufferView']),dtype=dt,count=v['count']*k,offset=v.get('byteOffset',0)).reshape(-1,k)
pr,=d['meshes'][0]['primitives']; a=pr['attributes']
P=acc(a['POSITION'],3,'<f4'); U=acc(a['TEXCOORD_0'],2,'<f4'); J=acc(a['JOINTS_0'],4,'u1').astype('<i4'); W0=acc(a['WEIGHTS_0'],4,'<f4')
I=acc(pr['indices'],1,'<u2').ravel().reshape(-1,3)
binds=[z['bind_inverse'] for z in st['bindings']]
Bind=np.array([affine(x) for x in binds]); old=acc(d['skins'][0]['inverseBindMatrices'],16,'<f4').reshape(66,4,4).transpose(0,2,1)
assert np.array_equal(Bind,old) and [z['slot'] for z in st['bindings']]==list(range(66))
assert [z['bone'] for z in st['bindings']]==[d['nodes'][j]['name'] for j in d['skins'][0]['joints']]
w0=np.floor(W0.astype(float)*65535).astype('<u2')
# Actual imported compressed resource: require exact native hash after extraction.
packed=scn.read_bytes(); mg,mode,block,total=struct.unpack_from('<4sIII',packed)
assert (mg,mode,block)==(b'RSCC',2,4096)
q=total//block+1; sizes=struct.unpack_from(f'<{q}I',packed,16); at=16+4*q
Z=zstandard.ZstdDecompressor(); stream=bytearray()
for sz in sizes:
 stream+=Z.decompress(packed[at:at+sz]); at+=sz
assert len(stream)==total and packed[at:]==b'RSCC'
def segment(k,size):
 key=k.encode()+b'\0'; start=stream.index(key)+len(key)
 assert struct.unpack_from('<II',stream,start)==(31,size)
 return memoryview(stream)[start+8:start+8+size]
L=len(P); Nv=np.frombuffer(segment('vertex_data',L*20),'<f4',count=L*3).reshape(L,3)
Nu=np.frombuffer(segment('attribute_data',L*8),'<f4').reshape(L,2)
S=np.frombuffer(segment('skin_data',L*16),'<u2').reshape(L,8);Nj=S[:,:4].astype('<i4');Nw=S[:,4:]
Ni=np.frombuffer(segment('index_data',I.size*2),'<u2').astype('<i4'); assert len(Ni)==I.size
# VARIANT encoding recomputed below; independently spot-check real live rows.
for s in st['sparse_native_uv_weight_basis_checks']:
 i=s['row']; assert np.array_equal(Nv[i],s['p']) and np.array_equal(Nu[i],s['uv'])
 assert np.array_equal(Nj[i],s['slot']) and np.array_equal(Nw[i],np.rint(np.array(s['wgt'])*65535))
# Canonical key is position+UV and all nonzero (bone, uint16 weight) tuples.
def key(P,U,J,W):
 V=np.column_stack((P,U)).astype('<f4');V[V==0]=0 # normalize signed zero only
 Q=np.sort(np.where(W!=0, J*65536+W.astype(np.int64),0),axis=1).astype('<i4')
 return [a.tobytes()+b.tobytes() for a,b in zip(V,Q)]
K,NK=[x[:20] for x in key(P,U,J,w0)],[x[:20] for x in key(Nv,Nu,Nj,Nw)]
assert Counter(K)==Counter(NK)
codes={k:i for i,k in enumerate(sorted(set(K)))}
to0=np.array([codes[k] for k in K]);to1=np.array([codes[k] for k in NK]); assert len(to0)==len(to1)==52898
matches0=np.argsort(to0,kind='stable'); matches1=np.argsort(to1,kind='stable')
assert np.array_equal(to0[matches0],to1[matches1])
the_duplicate=np.flatnonzero(np.diff(to0[matches0])==0); assert len(the_duplicate)==1
for pair in (matches0,matches1):
 i,j=pair[the_duplicate[0]:the_duplicate[0]+2]
 if pair is matches0:assert np.array_equal(w0[i],w0[j]) and np.array_equal(J[i],J[j])
 else:assert np.array_equal(Nw[i],Nw[j]) and np.array_equal(Nj[i],Nj[j])
j_of_native=np.empty(L,int);j_of_native[matches1]=matches0
skin_exact=np.empty_like(Nw); native_order=np.empty_like(Nj)
skin_exact[j_of_native]=Nw; native_order[j_of_native]=Nj
assert np.all((skin_exact==0)|(native_order==J))
assert np.max(abs(skin_exact.astype(int)-w0))<=1
def canon(ix, flip=False):
 q=ix[:,[0,2,1]] if flip else ix
 # Canonical cyclic orientation, with fully degenerate equal-key triangles handled.
 return Counter(min((a,b,c),(b,c,a),(c,a,b)) for a,b,c in q.tolist())
assert canon(to0[I],True)==canon(to1[Ni.reshape(-1,3)])
counts=st['surface_roles'][0]; assert counts['vertices']==L and counts['indices']==I.size
# Validate native fixed-point weights and live deformed marker samples.
sample=[]; parsed=[]
for f in fs:
 assert f['projection']==1 and f['camera_size']==13 and f['tick']==1333+f['age']
 assert all(z['visible'] and z['identity_continues'] and z['one_fixture_owner'] and z['slot']==i for i,z in enumerate(f['subject']))
 cc=f['character']; assert cc['visibility'] and len(cc['poses_by_skin_binding_slot'])==66
 if f['age']%4==0 or f['age']==266: parsed.append(dict(age_tick=f['age'],camera=f['camera'],crowns=[z['matrix'] for z in f['subject']],viewport=[1280,720],camera_size=13,camera_projection='orthographic',mesh_world=cc['mesh_world'],poses_by_skin_binding_slot=cc['poses_by_skin_binding_slot'],actor_triangles=len(I)))
 evaluated=f['evaluated_sparse_native_markers']; assert len(evaluated)==(5 if f['age'] in [0,40,100,266] else 0)
 for live in evaluated:
  i=live['row']; ids=np.flatnonzero(to0==to1[i]); assert len(ids)>=1
  j=int(j_of_native[i]); sm,n=affine(cc['mesh_world']),np.array([affine(k) for k in cc['poses_by_skin_binding_slot']])
  blend=(n@Bind)[Nj[i]]@np.r_[Nv[i],1.]; q=((blend[:,:3]).T@(Nw[i]/65535))
  err=np.linalg.norm((sm@np.r_[q,1.])[:3]-live['world']);assert err<1e-5
  sample.append(dict(age=f['age'],original_vertex_i=j,native_bind_position=Nv[i].tolist(),native_uv=Nu[i].tolist(),nonzero_native_joint_slots=Nj[i][Nw[i]>0].tolist(),native_world_skinned=live['world'],error_m=err))
assert len(parsed)==68 and len(sample)==20 and all(z['state']=='parked' for z in fs[-1]['subject'])
# Re-create Godot's exact Array/packed canonical serialization from independently decoded arrays.
def gdval(tag,a,n):return struct.pack('<II',tag,n)+a.tobytes()
h=digest(struct.pack('<II',28,5)+gdval(36,Nv,len(Nv))+gdval(30,Ni,len(Ni))+gdval(35,Nu,len(Nu))+gdval(30,Nj,Nj.size)+gdval(32,(Nw.astype(np.float32)/np.float32(65535)),Nw.size))
assert h==counts['native_import_packed_godot_variant_sha256'],(h,counts['native_import_packed_godot_variant_sha256'])
assert len(d['images'])==3
tex=[Image.open(BytesIO(vbytes(i['bufferView']))).size for i in d['images']]
assert tex==[(4096,4096)]*3
weights_path=out.parent/'skin-weights.LOCAL.bin'; assert not weights_path.exists()
weights_path.write_bytes(skin_exact.tobytes()); weights_path.chmod(0o600)
m=dict(native_weights_relative=weights_path.name,native_weights_sha256=digest(weights_path.read_bytes()),version=1,native_role='EXAMINER_SHADOW_ONLY',fps=15,actor_source_glb_sha256=digest(b),actor_evidence='exact native evaluated skinned surfaces with imported original character materials and UV',
 verified_glb_joint_to_native_slot=list(range(66)),bind_inverse_by_slot=binds, original_native_source_spot_checks=sample,frames=parsed)
with out.open('x') as f:json.dump(m,f,separators=(',',':'))
out.chmod(0o600)
print(json.dumps(dict(native_surface_array_digest_exact=h,mesh_positions_uv_nonzero_joint_weight_rows=L,exact_oriented_triangles_reversed_for_godot_clockwise=len(I),material_texture_count=len(tex),actual_markers=len(sample),max_native_world_marker_error_m=max(x['error_m'] for x in sample),authentic_capture_frames=len(fs),planned_render_frames=len(parsed),manifest_sha256=digest(out.read_bytes()),graphics=False),indent=2))
