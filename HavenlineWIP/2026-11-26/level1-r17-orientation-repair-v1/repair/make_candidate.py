"""Optional detached R17 repair: reverse proven inside-out source faces and correct only inward normals."""
import contextlib,io,hashlib,json
from collections import Counter
from pathlib import Path
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
 from diagnose import D,parse,face_audit,comps,jnorm,H
P=Path('candidate/assets');P.mkdir(parents=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def raw_obj(path):
 v=[];n=[];f=[];m=[];mat=None
 for line in path.read_text().splitlines():
  a=line.split()
  if not a:continue
  if a[0]=='usemtl':mat=a[1]
  if a[0]=='v':v.append([float(x) for x in a[1:]])
  if a[0]=='vn':n.append([float(x) for x in a[1:]])
  if a[0]=='f': f.append([[int(x)-1 for x in p.split('//')] for p in a[1:]]);m.append(mat)
 return [np.array(x) for x in [v,n,f,m]]
summarize={}
for file in ['fence_panel.obj','gate_post.obj']:
 donor=D/'assets'/file; out=P/file
 V,N,F,T,M=parse(file);X,normal,stored,raw=face_audit(V,N,F,T,M)
 weld,tw,com=comps(V,F)
 assert len(np.unique(T))==T.size==len(N) # no outward/inward shared-normal conflict
 should=np.zeros(len(F),bool)
 cc={}
 for k in np.unique(com):
  I=np.flatnonzero(com==k);A=X[I]
  center=(A.max((0,1))+A.min((0,1)))*.5
  radial=np.einsum('ni,ni->n',normal[I],A.mean(1)-center)
  assert (radial<-1e-7).all()
  faces=tw[I]
  dc=Counter(tuple(map(int,e)) for r in faces for e in zip(r,np.roll(r,-1)))
  u={tuple(sorted(e)) for e in dc}
  assert all(dc[a,b] in (0,1) and dc[b,a] in (0,1) for a,b in u)
  oo=sum((dc[a,b]+dc[b,a])==1 for a,b in u)
  if len(I)==28:
   assert oo==0
   vol=float(np.einsum('ni,ni->n',A[:,0]-center,np.cross(A[:,1]-center,A[:,2]-center)).sum()/6.)
   assert vol<0
   cc['closed']=cc.get('closed',0)+1
  else:
   assert len(I)==8 and oo==8 and (M[I]=='snow').all()
   assert (normal[I,1] < -1e-7).all() # all open roof sides point down
   cc['open_peak']=cc.get('open_peak',0)+1
  should[I]=True
 assert should.all()
 corner=np.einsum('ni,nji->nj',-normal,N[T])
 assert np.min(np.abs(corner))>.99999
 bad=np.unique(T[corner<0])
 nbad=set(bad.tolist())
 source=donor.read_text().splitlines()
 lines=[];fr=nr=0
 for l in source:
  a=l.split()
  if a and a[0]=='f':
   a[2],a[3]=a[3],a[2]
   l=' '.join(a);fr+=1
  elif a and a[0]=='vn':
   if nr in nbad:
    a=['vn',*[format(-float(x),'.9g') if float(x)!=0. else '0' for x in a[1:]]]
    l=' '.join(a)
   nr+=1
  lines.append(l)
 out.write_text('\n'.join(lines)+'\n')
 A,B,S,TAG=raw_obj(out);A0,B0,S0,TAG0=raw_obj(donor)
 assert np.array_equal(A,A0) and np.array_equal(TAG,TAG0) and np.array_equal(S,S0[:,[0,2,1]])
 # Normal difference occurs exactly for the selected objectively inward rows.
 assert np.array_equal(np.flatnonzero(np.any(B!=B0,axis=1)),bad)
 G=A[S[:,:,0]];C=np.cross(G[:,1]-G[:,0],G[:,2]-G[:,0]);C/=np.linalg.norm(C,axis=1)[:,None]
 Dots=np.einsum('ni,nji->nj',C,B[S[:,:,1]])
 assert Dots.min()>.99999
 for k in np.unique(com):
  I=np.flatnonzero(com==k);A=G[I]
  center=(A.max((0,1))+A.min((0,1)))*.5
  assert (np.einsum('ni,ni->n',C[I],A.mean(1)-center)>1e-7).all()
  if len(I)==28:
   vol=float(np.einsum('ni,ni->n',A[:,0]-center,np.cross(A[:,1]-center,A[:,2]-center)).sum()/6.)
   assert vol>0
  else:assert (C[I,1]>0).all()
 def non_mesh_lines(raw):
  return [s for s in raw.splitlines() if s.split() and s.split()[0] not in {'f','vn'}]
 assert non_mesh_lines(donor.read_text())==non_mesh_lines(out.read_text())
 mcount=dict(Counter(M.tolist()))
 assert mcount==dict(Counter(TAG.tolist()))
 # Face orientation and positions are independently checked; actual Godot
 # import/visual/main route acceptance specifically not asserted here.
 summarize[file]=dict(original_sha256=sha(donor),detached_repaired_sha256=sha(out),retained_surface_triangle_counts=mcount,
   vertex_xyz_lines_byte_exact=len(V),faces_winding_only=len(F),flipped_stored_inward_normal_rows=len(bad),
   untouched_already_correct_corner_normals=len(N)-len(bad),min_explicit_outward_normal_dot_after=float(Dots.min()),
   verified_source_shells=cc)
print(json.dumps(dict(status='DETACHED_STATIC_WINDING_REPAIR_NOT_NATIVE',asset_only=summarize,
 existing_geometry_locations_materials_uv_or_triangle_multiplicity_changed=False,
 runtime_lights_camera_input_colliders_tracks_or_gate_changed=False,native_renderer_or_reference_acceptance=False),
 indent=2))
