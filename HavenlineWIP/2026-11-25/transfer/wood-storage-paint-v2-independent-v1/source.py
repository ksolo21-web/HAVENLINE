import json,struct,hashlib,sys
from pathlib import Path
a,b=map(Path,sys.argv[1:])
def load(p):
 d=p.read_bytes(); m,v,total,n,kind=struct.unpack_from('<4sIIII',d)
 assert m==b'glTF' and v==2 and total==len(d) and kind==0x4e4f534a
 j=json.loads(d[20:20+n]); sz,kind=struct.unpack_from('<II',d,20+n)
 assert kind==0x004e4942 and sz==len(d)-28-n
 return j,d[28+n:],hashlib.sha256(d).hexdigest()
z,u,h0=load(a);w,v,h1=load(b)
assert h0=='0f961e1dbf66c954eb557ecbae54d34c34cf15121011c0866203d05cb73d419b' and h1=='3db8ed722b3a41b31003a7a43b85c1b1344fc3e98dcd3c9c94a9f96d34838045'
vf=z['images'][0]['bufferView']; assert vf==w['images'][0]['bufferView']==len(z['bufferViews'])-1
off=z['bufferViews'][vf]['byteOffset']; assert off==w['bufferViews'][vf]['byteOffset']
assert u[:off]==v[:off]
i0=z['bufferViews'][vf]['byteLength']; i1=w['bufferViews'][vf]['byteLength']
assert v[off:off+i1]==(b.parent/'paint.png').read_bytes() and u[off:off+i0]!=(b.parent/'paint.png').read_bytes()
w['bufferViews'][vf]['byteLength']=i0;w['buffers'][0]['byteLength']=z['buffers'][0]['byteLength']
assert w==z
print(json.dumps({'sha_base':h0,'sha_candidate':h1,'unchanged_non_image_binary_bytes':off,'scene_and_material_json_preserved':True,
 'roughness':[m['pbrMetallicRoughness']['roughnessFactor'] for m in w['materials']],
 'only_final_image_payload_changed':True},indent=2))
