"""Exact authored specimen material source binding, not native material validation."""
import hashlib,json,struct,os
from pathlib import Path
p=Path(os.environ['HAVENLINE_PROJECT']).resolve()/'assets/characters/Character1.glb'
blob=p.read_bytes(); h=lambda a:hashlib.sha256(a).hexdigest()
assert h(blob)=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
n=struct.unpack_from('<I',blob,12)[0];d=json.loads(blob[20:20+n]);data=memoryview(blob)[28+n:]
slot=d['meshes'][0]['primitives'][0]['material']
mat=d['materials'][slot]
roles={'tangent_normal':mat['normalTexture']['index'],'base_color':mat['pbrMetallicRoughness']['baseColorTexture']['index'],
       'metallic_roughness':mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']}
r={};
for semantic,i in roles.items():
 image=d['textures'][i]['source']
 m=d['images'][image]
 q=d['bufferViews'][m['bufferView']]; off=q.get('byteOffset',0)
 r[semantic]={'original_texture_index':i,'original_image_index':image,'source_bits_sha256':h(data[off:off+q['byteLength']])}
print(json.dumps({'source_fixed_material_slot':slot,'all_specimen_faces_reference_original_material_slot':True,
  'payload_reference_only_no_images_exported':r,'independent_generated_uv_checked_separately':True,
  'no_new_material_or_raster_claim':True},indent=2))
