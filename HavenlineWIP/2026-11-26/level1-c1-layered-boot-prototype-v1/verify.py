"""Read-only material/topology/contact and full exact-load inspection, no render."""
import contextlib,io,json,sys,os
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from scipy.spatial import cKDTree,ConvexHull
with contextlib.redirect_stdout(io.StringIO()):
 from domain import *
from inspect_source import load
doc,Vs,Ns,UVs,Js,Ws,Fs=load(f.STOCK/'assets/characters/Character1.glb')
rec=json.loads(Path('candidate/build.json').read_text())
assert all(h(Path('candidate')/n)==v for n,v in rec['private_payload_hashes'].items())
q=np.load('candidate/detached-assembly.LOCAL.npz',allow_pickle=False)
X,F1,Y,R1,WB,U,C=(q[k] for k in ('vertices','faces','pose','neutral_world','weights_dense','uv','face_category'))
keep=q['keep_original_source_face_ids'];trim=q['retained_trim_source_ids']; n=len(V)
assert np.array_equal(X[:n],V) and np.array_equal(U[:n],UVs) and np.array_equal(F1[C==0],F[keep]) and np.array_equal(F1[C==3],F[trim])
OrigW=np.zeros_like(WB[:n]);np.add.at(OrigW,(np.arange(n)[:,None],f.J),f.W)
assert np.array_equal(WB[:n],OrigW) and np.max(np.abs(Y[:n]-P))<1e-13
assert np.all(np.isin(q['original_lower_face_ids'],keep))
right_support=q['sole_support_original_rows']
assert np.all(np.isin(right_support,np.unique(F[q['original_lower_face_ids']])))
assert not ((V[F[q['original_replaced_face_ids']],0]>=-.04).any(1)).any()
material=doc['materials'][doc['meshes'][0]['primitives'][0]['material']]
def supports(P):
 pack={}
 for side,b in f.bounds.items():
  y=P[:,[0,2,1]].copy();y[:n][b['leg'],2]=f.distance(P[:n],b['leg'])
  k=f.connected(y,b['faces'],f.tags)
  marker=b['anchor'];S=P[marker];k.update(sole_min_mm=float(y[:n][b['leg'],2].min()*1000),declared_row=int(marker),
   declared_gap_mm=float((S[1]-f.ground(*S[[0,2]]))*1000))
  pack[side]=k
 return pack
p0=supports(P);p1=supports(Y)
assert np.max(np.abs(Y[right_support]-P[right_support]))<1e-13
near=np.unique(np.r_[F1[C!=0].ravel(),right_support])
new=F1[C!=0]
neutral_tags=np.unique(np.round(X,6),axis=0,return_inverse=True)[1]; aliases=neutral_tags[F1]
main=C<=2
edges={}
for k in range(4):
 subset=F1[C==k]
 rays=Counter(tuple(sorted((int(neutral_tags[i]),int(neutral_tags[j])))) for face in subset for i,j in zip(face,np.roll(face,-1)))
 direct=Counter((int(neutral_tags[i]),int(neutral_tags[j])) for face in subset for i,j in zip(face,np.roll(face,-1)))
 edges[k]=(rays,direct)
l,u=q['low_ring'],q['upper_ring']
def join(r,component):
 ring=[(int(neutral_tags[i]),int(neutral_tags[j])) for i,j in zip(r,np.roll(r,-1))]
 def both(e,k):a,b=e;return edges[k][1][a,b],edges[k][1][b,a]
 def sane(e,k):
  a,b=both(e,0);c,d=both(e,k)
  return (a+c,b+d)==(1,1)
 assert all(sane(e,component) for e in ring)
 return len(ring)
jn=[join(l,1),join(u,2)]
parts={}
for k in [1,2,3]:
 rays,dr=edges[k]
 parts[k]=dict(open_edges=int(sum(v==1 for v in rays.values())),nonmanifold_edges=int(sum(v>2 for v in rays.values())),
               interior_edges_not_oppositely_wound=int(sum(v==2 and (dr[a,b]!=1 or dr[b,a]!=1) for (a,b),v in rays.items())))
closure=dict(boot_preserved_join_edges=jn[0],cuff_preserved_join_edges=jn[1],
 actual_welded_layer_parts_before_source_attachment=parts,
 boot_extra_open_edges_after_sole_mate=parts[1]['open_edges']-jn[0],
 cuff_real_internal_liner_mouth_edges_after_trouser_mate=parts[2]['open_edges']-jn[1],
 original_trim_fit_witness_open_edges=parts[3]['open_edges'],
 source_texture_material_slot=doc['meshes'][0]['primitives'][0]['material'],source_texture_sha256_untouched=True,
 uv_range=[U.min(0).tolist(),U.max(0).tolist()],
 all_source_corner_uv_exact=True,
 new_uv_nearest_constrained_source_donor_dist_world_mm=np.quantile(q['source_texel_donor_distance_m']*f.S*1000,[0,.5,.95,1]).tolist(),
 rgb_shading_native_or_raster_verified=False)
# Strict plane/triangle faces against all original/candidate neighbors.
# Pin independent baseline finite helper; actively record distinct class pairs.
src=Path(os.environ['HAVENLINE_ARCHIVED_GROUND_EVALUATOR']).resolve();assert h(src)=='0b33c50478530a6266535d7c4b7e286703454e04f260b12d12249c52818e8c82'
text=src.read_text();a=text.index('def mesh_overlap(P):');b=text.index('\nnb=mesh_overlap',a);code=text[a:b]
def scan(positions,face,tags,active):
 u={'np':np,'cKDTree':cKDTree,'TR':face,'Weld':tags,'active':active}
 exec(code,u);return u['mesh_overlap'](positions)
K=np.flatnonzero(C!=0)
# Include vulnerable lower shell in candidate comparisons, not just new
# visible upper. Remaining source body outside authored seam also included.
kept_lows=np.flatnonzero(np.isin(keep,q['original_lower_face_ids']))
Nidx=np.r_[K,kept_lows]
Aidx=np.r_[q['original_replaced_face_ids'],q['original_lower_face_ids']]
scores={};details={}
labels=['unchanged','boot','cuff','preserved_trim_fit']
for at,srcworld,newworld in [('neutral',R,R1),('loaded',P,Y)]:
 main1=scan(newworld,F1,neutral_tags,Nidx)
 main0=scan(srcworld,F,f.tags,Aidx)
 pairs=Counter('/'.join(sorted((labels[C[i]],labels[C[j]]))) for i,j in main1)
 score=dict(original=len(main0),candidate=len(main1),candidate_by_material_layer_pair=dict(pairs),
   exact_held_source_pair_removed_from_candidate=(8677 in set(q['original_replaced_face_ids']) and 8892 in set(q['original_replaced_face_ids'])),
   boot_cuff_physical_strict_overlap_pairs=int(sum(C[i]+C[j]==3 and C[i]!=3 and C[j]!=3 for i,j in main1)),
   first_contact_pairs={s:list(min((i,j) for i,j in main1 if '/'.join(sorted((labels[C[i]],labels[C[j]])))==s)) for s in pairs})
 scores[at]=score
# Trajectory orientation projected against candidate's actual own transported
# neutral normals under fresh rigid outputs (not simply old face aliases).
df=np.einsum('nk,kij->nij',WB,M[:,:3,:3])
rn=np.cross(R1[F1[K,1]]-R1[F1[K,0]],R1[F1[K,2]]-R1[F1[K,0]])
yn=np.cross(Y[F1[K,1]]-Y[F1[K,0]],Y[F1[K,2]]-Y[F1[K,0]])
frame=df[F1[K]].mean(1);pred=np.einsum('nij,nj->ni',frame,rn)
bad=np.flatnonzero((pred*yn).sum(1)<=0)
ori=Counter(labels[C[K[i]]] for i in bad)
# Guard same full surface group and preserve true normal game projection.
def boxes(A,t):
 z=(A[np.asarray(t)]-f.cam)@f.basis[:2].T*720/13
 return ([float(v) for v in np.r_[z.min(0),z.max(0)]],ConvexHull(z).volume)
oo=np.unique(F[q['original_replaced_face_ids']]); nn=np.unique(F1[K])
def projects(o,n):
 p0,a0=boxes(o,oo); p1,a1=boxes(n,nn)
 return dict(original_projected_bounds_px=p0,candidate_projected_bounds_px=p1,
    max_bounds_change_px=float(np.max(np.abs(np.asarray(p0)-p1))),original_hull_area_px2=float(a0),
    candidate_hull_area_px2=float(a1),is_hull_bbox_not_rendered_silhouette=True)
ss=dict(status='HOLD_NO_INSTALL_OR_GAIT_PASS',faces_changed_left_or_other_parts=False,source_support_vertices_and_soles_exact=True,
     contact_baseline=p0,contact_candidate=p1,source_xyz_uv_and_weight_rows_unchanged=n,closure=closure,
     exact_loaded_transport_orientation_alarms=dict(ori),neutral_degenerate_new_excluding_trim=int((np.linalg.norm(rn,axis=1)<1e-15).sum()),
     strict_finite_full_neighborhood=scores,normal_camera_math=dict(rest=projects(R,R1),held=projects(P,Y)),
     actual_original_material_state_retained_but_not_raster_tested=True,renderer_native_spend_or_install=False)
print(json.dumps(ss,indent=2))
