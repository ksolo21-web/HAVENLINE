from pathlib import Path
import hashlib,json,re,sys
old,new=map(Path,sys.argv[1:])
def make(p):
    assert not any(x.is_symlink() for x in p.rglob('*'))
    return {str(x.relative_to(p)):hashlib.sha256(x.read_bytes()).hexdigest() for x in p.rglob('*') if x.is_file()}
a,b=map(make,(old,new))
assert len(a)==141 and len(b)==143 and set(a)<=set(b)
changes={k for k in a if a[k]!=b[k]}
assert changes=={'previews/reference_panel/reference_panel.gd','tests/hvn_l1_combined_draw.gd'}
adding=set(b)-set(a)
assert adding=={'previews/reference_panel/assets/material_reference_paint.gdshader','previews/reference_panel/assets/material-map.json'}
assert a['previews/reference_panel/assets/Fence18595V2.obj']=='315325b816fbd70bf6126ffa8a98bc3d5cd83e9a0c7d9b4c894e0d15560aea2b'
assert a['previews/reference_panel/assets/Fence18595V3.mtl']=='c606aaf113f042e22146e199f7308d9b604e5075ba62b5b8a27ffb139ecbc3f0'
shader=new/'previews/reference_panel/assets/material_reference_paint.gdshader'
assert b[str(shader.relative_to(new))]=='f52ae2a71745ec2220a07ac5a0f20b5aa7f3a8b1ed3e3977289f83ddf928fc3f'
assert re.search(r'void vertex\(\)\s*\{\s*local_v = VERTEX;\s*local_n = NORMAL;\s*\}',shader.read_text())
assert not re.search(r'\b(?:ALPHA|discard|POSITION|DEPTH|sampler2D|GI)\b',shader.read_text())
map=json.loads((new/'previews/reference_panel/assets/material-map.json').read_text())
assert map['bindings']=={'amber_timber':0,'draped_snow':1,'warm_hemp':2,'cream_hemp':3}
print(json.dumps({'unchanged_v3_project_files':139,'dedicated_adapter_and_observer_only':{k:[a[k],b[k]] for k in sorted(changes)},
 'added_exact_local_art':{k:b[k] for k in sorted(adding)},'stock_silhouette_and_exact_original_geometry_unchanged':True,
 'claimed_renderer_or_import_proof':False},indent=2))
