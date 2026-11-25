"""Read-only exact source scope for left shoulder influence, no reweight or pose."""
from pathlib import Path
import hashlib
seal_path=Path('../hvn-c1-shoulder-torso-jacobian-v1.ulS8v6')
seal_id='d17972b3aeb10b21aa2c59da04320347100f9bee7f58567798e3ade641384eeb'
assert hashlib.sha256((seal_path/'SHA256SUMS').read_bytes()).hexdigest()==seal_id
for ln in (seal_path/'SHA256SUMS').read_text().splitlines():
 sh,name=ln.split();assert hashlib.sha256((seal_path/name).read_bytes()).hexdigest()==sh
text=(seal_path/'audit.py').read_text()
prefix=text[:text.index('p_pair=support_for_pair()')]
prefix=prefix.replace('def derive(side,kind,rows):','JM={};\ndef derive(side,kind,rows):')
assert prefix.count('M=jac[1]')==1
prefix=prefix.replace('M=jac[1]','M=jac[1]; JM[(side,kind)]=(rows,M)')
exec(compile(prefix,str(seal_path/'audit.py'),'exec'))
left=mix0['L']
_ = derive('L','whole_arm_open_hypothetical',left)
row,Der=JM['L','whole_arm_open_hypothetical']
assert np.array_equal(row,left)
mat=Der.reshape(len(left),3,4)[:,:,:3]
# Differ exact source coordinates vs quantized owner weight controls. Alias
# clustering is read only, NOT permission to weld or share stored texture rows.
native_representative, inv_exact=np.unique(P,axis=0,return_inverse=True)
left_phys=np.unique(inv_exact[left])
assert len(left_phys)>500
weights=Rsource[left,ix['upper_arm.L']]
assert (weights>0).all()
assert Rsource[left][:,rids['L'][1:]].sum()==0
actual_set=np.unique(inv_exact[bis],axis=0)
actual_set=actual_set[actual_set[:,0]!=actual_set[:,1]]
sleeveFace,coatFace=674738,556546
assert not np.intersect1d(F[coatFace],left).size
assert not Rsource[F[coatFace]][:,rids['L']].any()
assert np.all(Rsource[F[sleeveFace],ix['upper_arm.L']]==1)
assert not np.isin(inv_exact[F[coatFace]],left_phys).any()
assert not np.isin(inv_exact[F[sleeveFace]],left_phys).any()
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.sparse import csr_matrix
def comp(nodes,e):
 nodes=np.asarray(nodes)
 ed=e[np.isin(e,nodes).all(1)]
 uu,vv=np.searchsorted(nodes,ed).T
 G=coo_matrix((np.ones(2*len(ed),int),(np.r_[uu,vv],np.r_[vv,uu])),shape=(len(nodes),len(nodes))).tocsr()
 n,classes=connected_components(G,directed=False)
 co=[]
 for cls in range(n):
  p=nodes[classes==cls];co.append(p)
 return sorted(co,key=lambda c:(-len(c),int(c.min())))
parts=comp(left_phys,actual_set)
indexed=comp(left,bis)
induce=np.isin(actual_set,left_phys)
rim_nodes=np.unique(actual_set[induce.sum(1)==1])
rim_in=rim_nodes[np.isin(rim_nodes,left_phys)]
rim_out=rim_nodes[~np.isin(rim_nodes,left_phys)]
# One graph on actual full left outer half, no chart or semantically
# guessed color links. Duplicate mesh-atlas positions enter only as an
# explicit exact coincident physical incidence, untouched chart indices.
Ex=actual_set[(native_representative[actual_set,0]>.12).all(1)]
ux,vx=Ex.T; D=np.linalg.norm(native_representative[ux]-native_representative[vx],axis=1); assert D.min()>0
GN=len(native_representative)
G=coo_matrix((np.r_[D,D],(np.r_[ux,vx],np.r_[vx,ux])),shape=(GN,GN)).tocsr()
def near(source, target):
 ds,pr,first=dijkstra(G,directed=False,indices=np.unique(source),min_only=True,return_predecessors=True)
 hit=target[np.argmin(ds[target])]
 value=float(ds[hit])
 if not np.isfinite(value):return {'distance_geodesic_mm':None}
 out=[int(hit)];k=int(hit)
 while pr[k]>=0:
  k=int(pr[k]);out.append(k)
 byG={}
 pinmask=np.isin(inv_exact,out)
 for j in np.flatnonzero(pinmask):byG.setdefault(int(inv_exact[j]),[]).append(int(j))
 rec=[{'representative_physical_row':k,'indexed_aliases':byG[k][:7],'bind_xyz_m':native_representative[k].tolist(),'in_sensitive_set':bool(np.isin(k,left_phys))} for k in out]
 return {'distance_geodesic_mm':value*1000,'physical_edge_count':len(out)-1,'nearest_physical_target_id':int(hit),
   'path_includes_unclassified_or_fixed_rows':sum(not a['in_sensitive_set'] for a in rec),
   'source_start_and_target':[rec[-1],rec[0]],'first_and_last_two_physical_records':rec[:2]+rec[-2:]}
def ss(x):return np.linalg.svd(x.reshape(-1,3),compute_uv=False)
parts_rank=[]
for c in parts:
 k=np.isin(inv_exact[left],c)
 normal=np.flatnonzero(k)
 if not len(normal):continue
 u=ss(mat[~k]) if not k.all() else np.array([0.,0.,0.])
 indexed_rows=left[k]
 parts_rank.append({'physical_vertices':int(len(c)),'indexed_rows':int(k.sum()),'this_component_alone_left_shoulder_SVD_m_per_rad':ss(mat[k]).tolist(),'remaining_frozen_left_shoulder_SVD_m_per_rad':u.tolist(),
   'remaining_frozen_shoulder_rank':int((u>1e-6).sum()),'bind_AABB_m':[P[indexed_rows].min(0).tolist(),P[indexed_rows].max(0).tolist()]})
assert len(parts_rank)>0
largest_and_aux=np.isin(inv_exact[left],np.concatenate(parts[:2]))
rest_mat=mat[~largest_and_aux]
resid_sigma=ss(rest_mat)
from itertools import combinations
sing_pairs=[(tuple(map(int,left[~largest_and_aux][list(c)])),float(ss(rest_mat[list(c)])[2])) for c in combinations(range(len(rest_mat)),2)]
both_big_unpinned={'indexed_remaining':int((~largest_and_aux).sum()),'SVD_m_per_rad':resid_sigma.tolist(),
  'rank':int((resid_sigma>1e-6).sum()),
  'singleton_two_pin_controls':[{'indexed_row_pair':k,'min_stacked_sv_m_per_rad':mn} for k,mn in sing_pairs],
  'singleton_two_pin_full_rank_controls_n':sum(mn>1e-6 for _,mn in sing_pairs),
  'no_rows_unpinned_in_model':True}
assert body_delta.max()>0.002
assert len(doc['materials'])==len(doc['meshes'][0]['primitives'])==1
c0=np.flatnonzero(np.isin(inv_exact[left],parts[0]))
assert len(c0)>0
oneRing=actual_set[np.isin(actual_set,parts[0]).sum(1)==1]
outs=np.unique(oneRing[~np.isin(oneRing,parts[0])])
outr=np.flatnonzero(np.isin(inv_exact,outs))
body_checkout={'outer_one_ring_from_largest_component_physical_count':len(outs),
  'outer_one_ring_from_largest_component_existing_negative_weight_rows':int((Rsource[outr,ix['upper_arm.L']]==0).sum()),
  'outer_one_ring_from_largest_component_original_indexed_count':len(outr),
  'one_ring_is_read_only_not_a_relaxation_proposal':True}
report={'status':'HOLD_NO_AUTHORED_NARROW_ARMHOLE_TREATMENT','producer_Jacobian_seal':seal_id,
 'left_source_chart_sensitive_indexed':len(left),'exact_coincident_physical_count':len(left_phys),
 'left_chart_weight_min_max':[float(weights.min()),float(weights.max())],
 'indexed_blend_component_sizes':list(map(len,indexed)),
 'exact_physical_blend_component_sizes':list(map(len,parts)),
 'pinned_boundary_in_sensitive_set_n':len(rim_in),'pinned_boundary_immediately_outside_sensitive_set_n':len(rim_out),
 'component_leave_one_unpinned_test':parts_rank,'two_largest_counterfactual_leave_five_original_pins':both_big_unpinned,
 'path_to_named_left_pure_sleeve':near(inv_exact[F[sleeveFace]],left_phys),
 'path_to_named_left_fixed_chest':near(inv_exact[F[coatFace]],left_phys),
 'candidate_torso_or_coat_panel_source_faces_kept_unchanged':[coatFace,557749],
 'old_source_armhole_material_separately_authored':False,'known_chart_contributor_not_rendered_material_mask':True,
 'one_ring_bound_largest_component':body_checkout,
 'guard':'This labels numerical positive arm-blend support under original pins only. A graph estimate locates adjacency, not a valid reweight domain. No authorized widening of torso, coat, clavicle, chart or bind changes.'}
print(json.dumps(report,indent=2,sort_keys=True))
