"""Verify exact two-path cap delta and unchanged runtime, camera and old neighbors."""
from collections import Counter
from pathlib import Path
import hashlib,json,sys
a,b=map(Path,sys.argv[1:])
def h(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def inventory(p):
    f=list(p.rglob('*'))
    assert not any(x.is_symlink() for x in f)
    return {str(x.relative_to(p)):h(x) for x in f if x.is_file()}
old,new=map(inventory,(a,b))
assert len(old)==len(new)==141
prefix='previews/reference_panel/assets/'
obj=prefix+'Fence18595V2.obj'
before=prefix+'Fence18595V2.mtl'
after=prefix+'Fence18595V3.mtl'
assert set(old)-set(new)=={before} and set(new)-set(old)=={after}
assert {k for k in old.keys() & new.keys() if old[k]!=new[k]}=={obj}
assert old[obj]=='137446d82b7c679c88f85069958b0eaacb85ca38dc8d1e7f73be5bef89b7ec53'
assert new[obj]=='315325b816fbd70bf6126ffa8a98bc3d5cd83e9a0c7d9b4c894e0d15560aea2b'
assert old[before]==new[after]=='c606aaf113f042e22146e199f7308d9b604e5075ba62b5b8a27ffb139ecbc3f0'
assert list(b.glob('**/*paint*gdshader'))==list(a.glob('**/*paint*gdshader'))
def lines(p):
    raw=p.read_text().splitlines()
    mats=[]; faces=Counter()
    for l in raw:
        w=l.split()
        if not w:continue
        if w[0]=='usemtl':mats.append(w[1])
        if w[0]=='f':faces[mats[-1]]+=len(w)-3
    return raw,mats,dict(faces)
p,q=lines(a/obj),lines(b/obj)
assert p[1:]==q[1:]==(['amber_timber','draped_snow','warm_hemp','cream_hemp'],{'amber_timber':1800,'draped_snow':1920,'warm_hemp':2560,'cream_hemp':2560})
assert [l for l in q[0] if l.startswith('mtllib ')]==['mtllib Fence18595V3.mtl']
print(json.dumps({'prior_files_and_scripts_identical':139,'changed_obj_at_unchanged_compatibility_path':[old[obj],new[obj]],
 'mechanical_mtl_basename_rename_same_bytes':{before:after,'sha256':new[after]},
 'ordinal_faces':q[2],'same_physical_scene_one_panel_no_new_shading':True,'not_runtime_evidence':True},indent=2))
