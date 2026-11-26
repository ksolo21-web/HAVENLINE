from pathlib import Path
import hashlib,json,struct,sys,math
import numpy as np
from scipy.spatial.transform import Rotation
import author as A,stock as S
h=Path(__file__).resolve().parent
file=h/'Character1-Stock66ContactWalk.LOCAL.glb';data=file.read_bytes()
l=struct.unpack_from('<I',data,12)[0]
m=json.loads(data[20:20+l]);b=data[l+28:]
assert b[:len(S.raw)]==S.raw
D=S.d
keys=['nodes','skins','meshes','materials','images','textures','scenes']
assert all(D.get(k)==m.get(k) for k in keys)
assert all(m[k][:len(D[k])]==D[k] for k in ['accessors','bufferViews','animations'])
a=m['animations'][-1]
assert a['name']=='Havenline_stock66_contact_walk_take_v1'
assert len(a['channels'])==85 and all(x['target']['node']!=40 for x in a['channels'])
raw_get=lambda i: np.frombuffer(b,dtype='<f4',count=m['accessors'][i]['count']*int(m['accessors'][i]['type'][3:] if m['accessors'][i]['type']!='SCALAR' else '1'),offset=m['bufferViews'][m['accessors'][i]['bufferView']]['byteOffset']).reshape((m['accessors'][i]['count'],-1))
t0=raw_get(a['samplers'][0]['input'])[:,0]
results=[]
for k,role in [(39,'left'),(72,'right')]:
 t,q,s=S.T.copy(),S.Q.copy(),S.S.copy()
 for track in a['channels']:
  target=track['target']; ch=a['samplers'][track['sampler']]
  [t if target['path']=='translation' else q if target['path']=='rotation' else s][0][target['node']]=raw_get(ch['output'])[k]
 _,_,_,req,actor=A.motion(k/72)
 world=(S.skin(t,q,s)+A.offset)*A.scale+actor
 rows=A.feet[role]['rows']; scores=world[rows,1]-A.ground_batch(world[rows])
 raw=int(rows[np.argmin(scores)]); mark=int(req[role]['row'])
 assert req[role]['plant'] and scores.min()<-.007
 results.append(dict(foot=role,key=k,stamp=float(t0[k]),actual_row=raw,bad_mm=float(scores.min()*1000), actual_vertex_world_m=world[raw].tolist(), minimum_original_boot_vertex=bool(S.v[raw,1]<.008),marker_row=mark,marker_delta_mm=float(np.linalg.norm(world[mark]-req[role]['target'])*1000),vertex_bind_asset_xyz=S.v[raw].tolist(),weights=[(S.N[S.jp[int(j)]]['name'],float(w)) for j,w in zip(S.J[raw],S.W[raw]) if w>1e-6]))
print(json.dumps({'candidate_sha256':hashlib.sha256(data).hexdigest(),'all_original_asset_data_retained':True,'source_original_sections':keys,'emitted_failure_reproduction':results},indent=2))
