#!/usr/bin/env python3
"""Replace original last paint buffer only, preserving all other glTF source bytes."""
import hashlib,io,json,struct,sys
from pathlib import Path
from PIL import Image
def h(a):return hashlib.sha256(a).hexdigest()
def parse(b):
 m,v,k,n,t=struct.unpack_from('<4sIIII',b)
 assert (m,v,k,t)==(b'glTF',2,len(b),0x4e4f534a)
 d=json.loads(b[20:20+n]);z,q=struct.unpack_from('<II',b,20+n)
 assert q==0x004e4942 and z==len(b)-28-n
 return d,b[28+n:]
def write(d,raw):
 j=json.dumps(d,separators=(',',':'),sort_keys=True).encode()
 j+=b' '*((-len(j))%4); raw+=b'\x00'*((-len(raw))%4)
 return struct.pack('<4sIIII',b'glTF',2,28+len(j)+len(raw),len(j),0x4e4f534a)+j+struct.pack('<II',len(raw),0x004e4942)+raw
def view(d,data,i):
 v=d['bufferViews'][i]
 return data[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
src=Path(sys.argv[1]).read_bytes()
assert h(src)=='0f961e1dbf66c954eb557ecbae54d34c34cf15121011c0866203d05cb73d419b'
old,raw=parse(src);d=json.loads(json.dumps(old))
pic=Path('paint.png').read_bytes(); img=Image.open(io.BytesIO(pic)).convert('RGBA')
assert img.size==(1320,1040) and img.getextrema()[-1]==(255,255)
assert len(d['images'])==1 and d['images'][0]['mimeType']=='image/png'
i=d['images'][0]['bufferView']; assert i==len(d['bufferViews'])-1
offset=d['bufferViews'][i]['byteOffset']; old_png=view(d,raw,i)
assert h(old_png)=='b345b9472e5061ce7201ee18f70a3f0f72d0d2125d978b67ac97658a7dd73063'
assert 0<=len(raw)-offset-len(old_png)<4
d['bufferViews'][i]['byteLength']=len(pic); d['buffers'][0]['byteLength']=offset+len(pic)
new=write(d,raw[:offset]+pic)
D,B=parse(new); assert B[:offset]==raw[:offset] and view(D,B,i)==pic
D['bufferViews'][i]['byteLength']=old['bufferViews'][i]['byteLength']
D['buffers'][0]['byteLength']=old['buffers'][0]['byteLength']
assert D==old
for j in range(len(old['bufferViews'])-1):assert view(D,B,j)==view(old,raw,j)
assert d['materials']==old['materials'] and not any('emissive' in str(x).lower() for x in d['materials'])
assert [m['pbrMetallicRoughness']['roughnessFactor'] for m in d['materials']]==[.88,.94]
Path('wood_storage_empty.glb').write_bytes(new)
report={'base_glb_sha256':h(src),'patched_glb_sha256':h(new),'paint_png_sha256':h(pic),'unchanged_geometry_binary_prefix_sha256':h(raw[:offset]),
        'unchanged_positions_normals_triangles_uvs_accessors_materials_roughness_and_transform':True,
        'changed_json_fields_only':['bufferViews[image].byteLength','buffers[0].byteLength'],'embedded_srgb_paint_dimensions':[1320,1040],
        'new_visual_score':None,'source_game_scene_edited':False,'world_align_or_support_stability_proven':False}
print(json.dumps(report,indent=2,sort_keys=True))
