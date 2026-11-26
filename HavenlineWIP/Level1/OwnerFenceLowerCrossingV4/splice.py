"""Copy only actual lower front v/vn from recipe into exact private grain mesh."""
import hashlib,re,json,sys,shutil
from pathlib import Path
root=Path('.')
assert len(sys.argv)==2, 'Pass the exact textured V3 directory'
args=Path(sys.argv[1])
prefix='FenceOwner33036BoldMeshyGrainV1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files={
prefix+'.obj':'d181219092789be172347a4472fea771c8d35f72de07543bbb20e562b410fd59',
prefix+'.mtl':'56e5d3d16292a495a2ed344d6ffd850fb64526a1b197c4ad0881410ff640b2f1',
'MeshyBold_AmberWoodFront.png':'c8cb9fc0221d74d6b36d75839590d374e7b2a05642d2777cb0d4473f1574a076'}
for n,h in files.items():assert sha(args/n)==h
before=args/(prefix+'.obj')
after=root/'candidate/generated.obj'
def parse(p):
 lines=p.read_text().splitlines()
 v=[]; vn=[]; group={}
 for i,l in enumerate(lines):
    if l.startswith('v '):v.append(i)
    if l.startswith('vn '):vn.append(i)
    if l.startswith('usemtl '):seq=group[l.split()[1]]=[]
    if l.startswith('f '):seq.append(l)
 return lines,v,vn,group
old,v0,n0,g0=parse(before);new,v1,n1,g1=parse(after)
orig=list(old); patched=set()
for label in ('ivory_hemp_warm','ivory_hemp_cream'):
 assert len(g0[label])==len(g1[label])==4320
 assert g0[label]==g1[label]
 for face in g1[label][:960]:
    for tok in face.split()[1:]:
        vid,tid,nid=tok.split('/'); assert not tid
        for x,y,k in ((v0,v1,int(vid)-1),(n0,n1,int(nid)-1)):
            if old[x[k]]!=new[y[k]]:
                patched.add(x[k]);old[x[k]]=new[y[k]]
assert patched
assert all(old[i]==orig[i] for i in range(len(orig)) if i not in patched)
for label,faces in g0.items():
 ids=[int(k.split('/')[0])-1 for face in faces for k in face.split()[1:]]
 assert label.startswith('ivory') or all(v0[k] not in patched for k in ids)
def restore_rows(v,n,ls,face):
 for tok in face.split()[1:]:
    a,b,c=tok.split('/')
    yield ls[v[int(a)-1]]
    yield ls[n[int(c)-1]]
# Ensure upper rail and rear/free turns remain literally the original vertices/normals,
# and no hidden cracks occur at authored patch edge despite split seams in OBJ.
for label in ('ivory_hemp_warm','ivory_hemp_cream'):
 for face in g0[label][960:]:
    assert list(restore_rows(v0,n0,old,face))==list(restore_rows(v0,n0,orig,face))
 for face in g0[label][:960]:
    assert list(restore_rows(v0,n0,old,face))==list(restore_rows(v1,n1,new,face))
dest=root/'candidate'/('FenceOwner33036LowerCrossingV4.obj')
# Original MTL basename, metadata, per-face vertex/UV/normal indices stay exact.
dest.write_text('\n'.join(old)+'\n')
for f in files:
 if not f.endswith('.obj'): shutil.copyfile(args/f,dest.parent/f)
reports=dict(source_exact_sha256=files,candidate_obj_sha=sha(dest),only_changed_lower_front_position_and_normal_records=len(patched),all_face_and_uv_indices_exact=True, upper_ropes_and_rear_normals_exact=True, mtl_and_atlas_exact=True)
print(json.dumps(reports,indent=2))
