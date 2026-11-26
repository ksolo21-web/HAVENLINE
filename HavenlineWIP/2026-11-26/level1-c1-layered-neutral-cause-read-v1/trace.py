"""Read-only diagnosis of exact failed detached boot neutral geometry."""
import hashlib,importlib.util,json,os
from pathlib import Path
from collections import Counter
import numpy as np
p=Path(os.environ['HAVENLINE_GENERATED_LAYERED_SPECIMEN']).resolve()
def h(q):return hashlib.sha256(q.read_bytes()).hexdigest()
assert h(p/'candidate/detached-assembly.LOCAL.npz')=='923379a36fef06563ed962575a110fcf532ca461a4068a39582165262e2db418'
assert h(p/'candidate/verify.json')=='493b9194d6e02b42a0aa925b0ce946458a1ba1cd1838e0a6d9cc356860396f44'
q=np.load(p/'candidate/detached-assembly.LOCAL.npz',allow_pickle=False)
X,R,F,C=(q[k] for k in ('vertices','neutral_world','faces','face_category'))
low,high=(q[k] for k in ('low_ring','upper_ring'))
verify=json.loads((p/'candidate/verify.json').read_text())
rigidsrc=Path('../level1-c1-fastener-mounts-v1/cavity-assess.py').resolve()
assert h(rigidsrc)=='cdf0184300e21eca848a1f5271f2473889fffe1b6d32a055215d99c214cabe2b'
spec=importlib.util.spec_from_file_location('strict',rigidsrc);w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
N=verify['strict_finite_full_neighborhood']['neutral']
expected=[[92674,96009],[97540,98525],[93645,98533]]
a=list(map(tuple,expected))
assert all(i in N['first_contact_pairs'].values() for i in expected)
def intersect(A,B):
 sectionA=w.section(A,B);sectionB=w.section(B,A)
 if sectionA is None or sectionB is None:return None
 u=np.cross(sectionA[0],sectionB[0]);u/=np.linalg.norm(u)
 L=[(np.array(s[1])-A[0])@u for s in [sectionA,sectionB]]
 q0,q1=max(map(min,L)),min(map(max,L))
 if q1<=q0:return None
 base=min(sectionA[1],key=lambda v:(v-A[0])@u)
 return float((q1-q0)*1000)
r=[]
for i,j in a:
 span=intersect(R[F[i]],R[F[j]])
 amt=w.proper_span(R[F[i]],R[F[j]])
 assert span is not None and abs(span-amt*1000)<1e-12
 z=dict(candidate_face_ids=[i,j],categories=[int(C[i]),int(C[j])],
  actual_face_corner_rows=F[[i,j]].tolist(),art_face_y_spans_mm=[(np.array([X[F[k],1].min(),X[F[k],1].max()])*1000).tolist() for k in [i,j]],
  exact_independent_strict_interior_common_span_world_mm=span)
 r.append(z)
# Identify the exact actual authored source rail and monotonicity violation
# at the connector; test the first witness, not an inferred radius.
assert F[98525,0]>=54902 and F[98525,0]<55076
assert all(k in set(high.tolist()) for k in F[98525][1:])
assert F[98533,0]>=54902 and F[98533,0]<55076
assert all(k in set(high.tolist()) for k in F[98533][1:])
n_lo=int((X[high,1]<.117).sum())
n_mid=int((X[high,1]<.147).sum())
# One transverse plane bisects the two interfering neutral boot strips'
# exact shared interval, never perturb authored geometry.
y=.0755
def segments(keep):
 ab=[]
 for k in keep:
  a=X[F[k]];pts=[]
  for p,q in zip(a,np.roll(a,1,axis=0)):
   if (p[1]-y)*(q[1]-y)<0:
    t=(y-p[1])/(q[1]-p[1]);pts.append((p+t*(q-p))[[0,2]])
  if pts:
   assert len(pts)==2;ab.append((int(k),*pts))
 return ab
out_ids=[i for i in np.flatnonzero(C==1) if F[i].max()<54391]
lin_ids=[i for i in np.flatnonzero(C==1) if F[i].min()>=55076 and F[i].max()<=56218]
ex=segments(out_ids);ins=segments(lin_ids)
def cross(A,B):return A[...,0]*B[...,1]-A[...,1]*B[...,0]
cx=[]
for i,a,b in ex:
 for j,c,d in ins:
  de=cross(b-a,d-c)
  if abs(de)<1e-14:continue
  s=cross(c-a,d-c)/de;t=cross(c-a,b-a)/de
  if min(s,t,1-s,1-t)>1e-7:cx.append([i,j])
# Signed inside ray test loops can be read as a soup because each closed
# transverse ring's degree-two connectivity was geometrically created.
ins_end=np.unique(np.round(np.vstack([[a,b] for _,a,b in ins]).reshape(-1,2),10),axis=0)
A=np.array([a for _,a,b in ex]);B=np.array([b for _,a,b in ex])
def inside(q):
 test=(A[:,1]>q[1])!=(B[:,1]>q[1])
 ix=(q[1]-A[test,1])/(B[test,1]-A[test,1])
 return (np.sum((A[test,0]+ix*(B[test,0]-A[test,0]))>q[0])%2)==1
def straight_dist(q):
 E=B-A;t=np.sum((q-A)*E,axis=1)/np.sum(E*E,axis=1);t=np.clip(t,0.,1.)
 return float(np.linalg.norm(A+E*t[:,None]-q,axis=1).min())
outside=np.array([z for z in ins_end if not inside(z)])
ver=dict(boot_inner_outer_active_segments=[len(ex),len(ins)],common_art_y_mm=y*1000,
 actual_strict_crosses_2d=len(cx),first_pairs=cx[:5],
 liner_section_vertices_outside_actual_shaft_outline=len(outside),
 maximum_outside_distance_art_mm=max((straight_dist(z) for z in outside),default=0.)*1000,
 y_slice_only_not_full_neutral_gate=True)
result=dict(frozen_prototype_manifest_sha256='6c6917ece9ff09d8d75382c57d910d6584588b9c5aaa99e7f5b4241a4b805e51',
 loaded_geometry_or_weight_edited=False,phase='exact original posed-independent neutral source',
 neutral_audit_context={'strict_total':N['candidate'],'boot_self':N['candidate_by_material_layer_pair']['boot/boot'],'cuff_self':N['candidate_by_material_layer_pair']['cuff/cuff'],'boot_cross_cuff':N['boot_cuff_physical_strict_overlap_pairs']},
 reproduced_three_first_exact_neutral_witnesses=r,
 sealed_boot_liner_independent_section_check=ver,
 upper_cuff_actual_immutable_ring=dict(source_vertex_count=len(high),source_art_y_span_mm=(np.array([X[high,1].min(),X[high,1].max()])*1000).tolist(),
   original_fixed_rows_below_art_117mm_lower_cuff_hem=n_lo,original_fixed_rows_below_art_147mm_connector_start=n_mid,
   rail_art_length_mm=float(np.linalg.norm(np.roll(X[high],-1,axis=0)-X[high],axis=1).sum()*1000),upper_cuff_strips_retrace_into_boot_height=True))
print(json.dumps(result,indent=2))
