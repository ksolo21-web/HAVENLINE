"""Outside-engine source manifest and OBJ geometry/material identity."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,sys
def h(path): return hashlib.sha256(path.read_bytes()).hexdigest()
base=Path(sys.argv[1])
candidate=Path(sys.argv[2])
roll=Path(sys.argv[3])
pins=json.loads(roll.read_text())
rel=('previews/r17_fence/assets/fence_panel.obj','previews/r17_fence/assets/gate_post.obj')
def check_paths(root):
    fs=list(root.rglob('*'))
    assert not any(x.is_symlink() for x in fs)
    return {str(x.relative_to(root)) for x in fs if x.is_file()}
allpaths=check_paths(base)
assert len(allpaths)==137 and allpaths==check_paths(candidate)
assert set(pins['output_sha256'])=={Path(x).name for x in rel}
assert set(x for x in allpaths if h(base/x)!=h(candidate/x))==set(rel)
def fingerprint(path):
    stable=[]
    faces=Counter()
    normals=[]
    exact_face_indices=[]
    group=[]
    for line in path.read_text().splitlines():
        words=line.split()
        if not words:
            continue
        tok=words[0]
        if tok=='vn':
            values=tuple(map(float,words[1:]))
            assert len(values)==3 and all(math.isfinite(x) for x in values)
            normals.append(values)
            continue
        if tok=='f':
            assert len(words)==4
            corners=[tuple(x.split('/')) for x in words[1:]]
            assert all(len(c)==3 and len(c[2])>0 for c in corners)
            faces[(tuple(group),tuple(sorted(c[:2] for c in corners)))]+=1
            exact_face_indices.append(corners)
            continue
        if tok in ('o','g','usemtl','s'):
            group.append(line)
        if not tok.startswith('#'):
            stable.append(line)
    assert normals 
    return stable,faces,normals,exact_face_indices
rows={}
for path,count in zip(rel,(640,176)):
    old,new=base/path,candidate/path
    assert h(new)==pins['output_sha256'][new.name]
    a,b=fingerprint(old),fingerprint(new)
    assert a[:2]==b[:2] and sum(b[1].values())==count
    assert b[3]==[[r[0],r[2],r[1]] for r in a[3]]
    assert len(a[2])==len(b[2])
    changed=[(u,v) for u,v in zip(a[2],b[2]) if u!=v]
    assert len(changed)=={640:1200,176:312}[count] and all(
        all(abs(x+y)<1e-9 for x,y in zip(u,v)) for u,v in changed)
    rows[new.name]={'old_sha256':h(old),'new_sha256':h(new),'vertices_uv_and_material_labels_unchanged':True,
                    'triangles':count,'normal_count_before':len(a[2]),'normal_count_after':len(b[2]),
                    'exact_face_winding_reversals':count,'exact_explicit_normal_negations':len(changed)}
print(json.dumps({'project_files_verified':137,'allowed_donor_differences':rows,
                  'gds_scene_gate_physics_save_and_native_observers_unchanged':True,
                  'runtime_import_capture_and_appearance':'not executed in stage'},indent=2))
