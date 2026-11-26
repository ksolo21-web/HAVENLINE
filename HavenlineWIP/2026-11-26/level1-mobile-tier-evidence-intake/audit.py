from pathlib import Path
from hashlib import sha256
from io import BytesIO
from collections import Counter
import json, struct, base64, re
from PIL import Image
P=Path(__file__).resolve().parent
B=P.parent/'hvn-l1-e2e-stock-graphics-v1'
S=B/'staged/HavenlineLevel1'
E=B/'graphics-evidence.GMY06S5U'
def sha(p):return sha256(p.read_bytes()).hexdigest()
def pinned(path,h):assert sha(path)==h, path
pinned(B/'SHA256SUMS','bbdd2e17abe8f074f26337eb38ae601e7d5f25305e228162aabde731d2244714')
pinned(B/'staged/base.sha256','2bb931c9e15b64570e62f00ff6d4379d9b99e839c02093137063fe1ddbe13487')
pinned(E/'functional.json','cf16457673bffc6fd516eca2fd8813b6bef41aa6f9368a44b6fb399c8aab7c29')
pinned(E/'frame-evidence.json','fe05c3a148dd524f75ef7d6b031336a8d1e55254045275c48a388fa59a5a2913')
base={Path(fn.removeprefix('*')).as_posix():h for h,fn in (line.split(maxsplit=1) for line in (B/'staged/base.sha256').read_text().splitlines())}
def base_pin(path):pinned(S/path,base[path])
bounded=('project.godot','layout.json','conifers.json','previews/integrated_opening.gd','previews/integrated_opening.tscn','previews/terrain_water_preview.tscn','previews/terrain_water_preview.gd','materials/accepted_t02_river_water.gdshader','materials/neutral_shore_snow.gdshader','previews/integrated_camp_floor.gdshader')
for p in bounded:
 if p!='previews/integrated_opening.gd':base_pin(p)
pinned(P/'upstream-11c-integrated-opening.gd.txt',base['previews/integrated_opening.gd'])
pinned(B/'staged/draw-source.sha256','a70b72b7f9943b8c68931e58dd8975eed38dae6213df0b40f1ea22f27fcd12bc')
draw={Path(fn.removeprefix('*')).as_posix():h for h,fn in (line.split(maxsplit=1) for line in (B/'staged/draw-source.sha256').read_text().splitlines())}
pinned(S/'previews/integrated_opening.gd','902eaf6f24356f9a85762888e409eb753e05bd65614d6931c57c796d0bb8f3f4')
f=json.loads((E/'functional.json').read_text())
assert f['baseline']=='11c14a1c41971067c7dc97db69375f720a408f68' and f['phases']['write']['checks']==57 and f['phases']['cold']['checks']==10
log=json.loads((E/'frame-evidence.json').read_text())
assert log['image_px']==[1280,720] and log['x11_software_llvmpipe_only']
assert len(log['frames'])==6
for r,row in log['frames'].items():pinned(E/(r+'.png'),row['png_sha256'])
def png_stats(name):
 with Image.open(E/(name+'.png')) as im:
  data=list(im.convert("RGB").get_flattened_data())
  return {'png_sha256':log['frames'][name]['png_sha256'],
   'near_black_max_channel_le10_frac':sum(max(v)<=10 for v in data)/len(data),
   'near_white_min_channel_ge245_frac':sum(min(v)>=245 for v in data)/len(data),
   'channel255_any_frac':sum(max(v)==255 for v in data)/len(data)}
def tex(path):
 with Image.open(path) as im:return {'width':im.width,'height':im.height,'format':im.format,'mode':im.mode}
def glb(p):
 s=p.read_bytes();m,v,n,j,ident=struct.unpack_from('<4sIIII',s)
 assert (m,v,n,ident)==(b'glTF',2,len(s),0x4E4F534A)
 d=json.loads(s[20:20+j]);binary=s[20+j+8:]
 texes=[]
 for i,it in enumerate(d.get('images',[])):
  if 'bufferView' in it:
   bv=d['bufferViews'][it['bufferView']];start=bv.get('byteOffset',0)
   payload=binary[start:start+bv['byteLength']]
  elif it.get('uri','').startswith('data:'):
   payload=base64.b64decode(it['uri'].split(',',1)[1])
  else:
   path=(p.parent/it['uri']).resolve()
   assert path.is_relative_to(S.resolve());base_pin(str(path.relative_to(S)));payload=path.read_bytes()
  t=tex(BytesIO(payload));t.update({'name':it.get('name',str(i)),'encoded_bytes':len(payload),'sha256':sha256(payload).hexdigest()});texes.append(t)
 total=0
 for mesh in d.get('meshes',[]):
  for p in mesh['primitives']:
   assert p.get('mode',4)==4
   total+=d['accessors'][p['indices'] if 'indices' in p else p['attributes']['POSITION']]['count']//3
 return {'bytes':len(s),'texture_sources':texes,'rgba8_nominal_base_level_bytes_no_mips_not_runtime_resident':sum(r['width']*r['height']*4 for r in texes),
  'authored_mesh_triangles_not_per_frame':total,'authored_mesh_definitions':len(d.get('meshes',[])),
  'materials':len(d.get('materials',[])),'skin_joint_counts':[len(sk['joints']) for sk in d.get('skins',[])],'animation_count':len(d.get('animations',[]))}
models={}
images={}
for p in sorted((S/'assets').rglob('*')):
 if p.suffix not in ('.glb','.jpg','.png','.webp'):continue
 n=p.relative_to(S).as_posix();pinned(p,draw[n]);assert n not in base or base[n]==draw[n]
 if p.suffix=='.glb':models[n]={**glb(p),'sha256':draw[n],'pin':'stock Git asset' if n in base else 'sealed hydrated desktop asset'}
 else:images[n]={'sha256':base[n],**tex(p)}
plant=json.loads((S/'conifers.json').read_text())
count=Counter(r['variant'] for r in plant['instances'])
scene=(P/'upstream-11c-integrated-opening.gd.txt').read_text()+(S/'project.godot').read_text()
staged_scene=(S/'previews/integrated_opening.gd').read_text()+(S/'project.godot').read_text()
assert all(x in scene and x in staged_scene for x in ('Vector3(-48, -28, 0)','world_light.shadow_enabled = true','renderer/rendering_method="gl_compatibility"','camera.size = 13.0'))
assert all(x not in scene and x not in staged_scene for x in ('auto_exposure','tonemap_exposure','CameraAttributesPractical','WorldEnvironment','scaling_3d_scale'))
layout=json.loads((S/'layout.json').read_text())
print(json.dumps({'baseline_commit_for_source':'11c14a1c41971067c7dc97db69375f720a408f68',
 'scope':'Exact unchanged stock assets/source plus known detached paid-pine route witness, not shipping or real phone',
 'engine':f['engine'],'display_backend':'X11 desktop CPU llvmpipe Compatibility software','six_native_frame_sha256':{k:r['png_sha256'] for k,r in log['frames'].items()},
 'selected_descriptive_full_frame_stats':{k:png_stats(k) for k in ['fresh-spawn','paid-first-frame','east-bidirectional']},
 'stock_camp_rect_m':layout['camp_rect_xz'],'stock_exact_streamed_scene_geometry_config_files':{p:base[p] for p in bounded},
 'scene_exposure_source':'one directional light (-48,-28,0) with shadow; no explicit exposure/tonemap in checked scene+project scripts; do not claim effective device defaults',
 'stock_hero_height_m':layout['actor_height'],'stock_camera':'ortho 13 at 1280x720; no zoom equivalence assumed',
 'static_exterior_pine_counts_by_variant':count,'gltf_source_inventory':models,'loose_source_images':images,
 'evidence_device_gaps':['Android APK/build and renderer receipt','device render vs display resolution and measured refresh','presented CPU/GPU frame times and thermals','independent stock-camera material on real phone']},indent=2))
