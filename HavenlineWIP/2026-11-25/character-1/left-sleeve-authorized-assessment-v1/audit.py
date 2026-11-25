"""Approved LEFT-only sleeve scope; reject infeasible weight correction before writing."""
from pathlib import Path
import hashlib
def packet(path, pins):
 assert hashlib.sha256((path/'SHA256SUMS').read_bytes()).hexdigest()==pins,path
 for line in (path/'SHA256SUMS').read_text().splitlines():
  d,k=line.split();assert hashlib.sha256((path/k).read_bytes()).hexdigest()==d,(path,k)
coupled=Path('../hvn-c1-coupled-shoulder-open-v1.Ik28DQ')
co_manifest='0c711d29f9589f4625097e580ed60d8356503c27e4df3431d9e6838b17360c1e'
indep=Path('../hvn-c1-coupled-shoulder-independent-v1.V6hQUK')
in_manifest='be483b3856160a37232032c60260e9c62d21f1b52d019d9c755501cd8979d2d5'
armhole=Path('../hvn-c1-left-armhole-authority-v2.9HGlb0')
ar_manifest='42a922cb2bcdfea5577199a74966fc468b3a9bf11e0f616b1fe9940e2e4d5082'
for p,sh in zip((coupled,indep,armhole),(co_manifest,in_manifest,ar_manifest)):packet(p,sh)
coupled_file=(coupled/'audit.py').read_text()
prefix=coupled_file[:coupled_file.index('# Full posed character')]
exec(compile(prefix,str(coupled/'audit.py'),'exec'))
co_out=json.loads((coupled/'result.json').read_text())
left_done=source_positions.copy()
assert hashlib.sha256(left_done.tobytes()).hexdigest()==co_out['original_52j_candidate_positions_sha256']
assert len(frozen_body_tri)==600396
locked=mix0['L']; assert len(locked)==1160
true_left_error=left_done[locked]-V[locked]
ix_max=np.argmax(np.linalg.norm(true_left_error,axis=1))
# The strongest admitted sleeves are actual named source face triplets, or
# their own coincident split-index aliases. Because the one-material source
# lacks a separately authored armhole cut, permit no expansion by name/box.
panels=np.array([674738,675186,675258])
pn=np.unique(F[panels])
upper=ix['upper_arm.L']
assert np.all(Rsource[pn,upper]==1)
Puniq,apparent=np.unique(P,axis=0,return_inverse=True)
permit=np.flatnonzero(np.isin(apparent,apparent[pn]))
assert np.all(Rsource[permit,upper]==1)
assert P[permit,0].min()>.28 and P[permit,0].max()<.4
full_coat_guard=np.unique(F[frozen_body_tri])
cuffs=np.unique(np.r_[s['R_loop_source_vertex_edges'],s['L_loop_source_vertex_edges']])
for still in (full_coat_guard,cuffs,se,F[[556546,557749]].reshape(-1)):
 assert not np.intersect1d(permit,still).size
 assert not np.intersect1d(apparent[permit],apparent[still]).size
# Because armature DQS is per-indexed vertex with rig pose fixed, ANY weight
# edit confined to the allowed sleeve is independent of all the protected
# source rows (N×G weight vector blocks): exact zero feasibility matrix.
# This is stronger than a linearized numerical solve; same nonzero residual
# for every sleeve-only proposal at the same fixed coupled posture.
assert np.count_nonzero(np.linalg.norm(true_left_error,axis=1)>0)==len(locked)
uv_multi=sum(len(np.unique(uv[permit[apparent[permit]==k]],axis=0))>1 for k in np.unique(apparent[permit]))
ordinal={'admitted_only_named_left_sleeve_faces':panels.tolist(),
  'identified_positive_source_rows_and_exact_coincident_aliases':permit.tolist(),
  'observed_pure_existing_upper_arm_weight':True,'exact_locally_approved_safe_test_island_not_found':True,
  'indexed_aliases_with_distinct_original_UV':uv_multi,'source_candidate_subset_bind_xyz_AABB_m':[P[permit].min(0).tolist(),P[permit].max(0).tolist()],
  'held_and_open_source_weights_geometry_untouched':True,
  'owned_left_sleeve_to_pinned_original_torso_derivative_rank':0,
  'fixed_target_torso_position_rows_n':len(locked),
  'coupled_open_torso_max_unfixable_by_sleeve_weights_mm':float(np.linalg.norm(true_left_error[ix_max])*1000),
  'coupled_open_torso_locked_row_with_max_error':int(locked[ix_max]),
  'coupled_open_torso_RMS_unfixable_by_sleeve_weights_mm':float(np.linalg.norm(true_left_error)/np.sqrt(len(locked))*1000),
  'all_permitted_changes_preserve_locked_constraint_error_at_exact_coupled_pose':True,
  'no_corrective_weight_candidate_or_diff_written':True}
# Left-only readback of exact earlier elbow-plane arm result, from unchanged
# original, no new angles/weights. The right side stays exact original; this
# is a control, not an adopted repair or new asset pose.
elbow=Path('../hvn-c1-coordinated-open-v1.jbZ4Tz')
el_manifest='0b6e88b44adb4b6539ca87f087f997586bbe64f3e7b132a1143536772d30f6ab'
packet(elbow,el_manifest)
ef=(elbow/'audit.py').read_text()
ec=ef[:ef.index('# Full posed character')]
exec(compile(ec,str(elbow/'audit.py'),'exec'))
eout=json.loads((elbow/'result.json').read_text())
assert hashlib.sha256(source_positions.tobytes()).hexdigest()==eout['original_52j_candidate_positions_sha256']
assert hashlib.sha256(right_positions.tobytes()).hexdigest()==eout['right_patch_candidate_positions_sha256']
left_open=V.copy()
left_ids=movable['L']; left_open[left_ids]=source_positions[left_ids]
assert np.array_equal(V[movable['R']],left_open[movable['R']])
assert np.array_equal(V[P[:,2]<-.2],left_open[P[:,2]<-.2])
# Coupled-source chart remains in effect, including all known affected torso
# and true outside rows, even though this same-layer readback only bends elbow.
assert np.array_equal(V[full_coat_guard],left_open[full_coat_guard])
for old_case in ([556546,674738],[557749,675186],[557749,675258]):
 i,j=old_case
 assert np.array_equal(V[F[old_case]],left_open[F[old_case]])
 assert not (crosses(left_open[F[i]],left_open[F[j]]) or crosses(left_open[F[j]],left_open[F[i]]))
movable['R']=np.zeros(0,np.int64)
right_positions=local['vertices']
# Import ONLY unchanged face predicate helpers, no pose driver/candidate write.
geom=ef[ef.index('def aabb_scan'):ef.index('keep_face=np.setdiff1d')]
exec(compile(geom,str(elbow/'tool-test-helpers'),'exec'))
keep_face=np.setdiff1d(np.arange(len(F)),local['removed'])
remain=F[keep_face];pface=local['faces']; source_ids_used=np.unique(remain)
ta_old,bc1=aabb_scan(V[remain],tool);ta_open,bc2=aabb_scan(left_open[remain],tool)
assert len(ta_old)==298
own_tri=np.isin(remain,left_ids).any(1)
aL=[(i,j) for i,j in ta_old if own_tri[i]]; bL=[(i,j) for i,j in ta_open if own_tri[i]]
aR=[(i,j) for i,j in ta_old if not own_tri[i]]; bR=[(i,j) for i,j in ta_open if not own_tri[i]]
assert aR==bR # unchanged source arm still known clipping
start_cont,_=tool_inside(V[left_ids]); after_cont,_=tool_inside(left_open[left_ids])
# Local retest face-relative garment intersections, scope only contracting
# original left elbow chain. No fresh geometry; side independence includes
# testing actual held right rows against moved left rows as retained body.
body=ef[ef.index('from scipy.spatial import cKDTree\nfull_faces'):ef.index('old_body,obn=body_pairs')]
body=body.replace("labels[nm:]=1","labels[nm:]=0") # right owned pressure remains exactly original
body=body.replace('source_positions,right_positions','left_open,right_positions')
exec(compile(body,str(elbow/'aggregate-body-test-helpers'),'exec'))
old_body,obn=body_pairs(old_full);new_body,nbn=body_pairs(new_full)
new_body=sorted(new_body-old_body)
def orig_id(k):return int(keep_face[k]) if k<len(keep_face) else ['existing_right_append_face',int(k-len(keep_face))]
readonly={'scope':'actual previous 5.880769deg left-elbow source result only; same original held right, no new joints or offsets',
  'source_elbow_manifest':el_manifest,
  'frozen_torso_chart_unchanged':True,'frozen_right_rows_unchanged':True,
  'named_left_current_control_faces_unchanged_and_clear':True,
  'strict_left_source_tool_before':len(aL),'strict_left_source_tool_after':len(bL),
  'inside_original_tool_left_before':start_cont,'inside_original_tool_left_after':after_cont,
  'retained_existing_other_hand_exact_tool_pairs_unchanged':len(aR),
  'new_left_actor_relative_strict_nonincident_body_pairs':len(new_body),
  'first_20_named_body_crossings_actual_source_faces':[[orig_id(a),orig_id(b)] for a,b in new_body[:20]],
  'tool_or_static_model_acceptance':False}
result={'status':'HOLD_NO_FORBIDDEN_TORSO_WEIGHT_CORRECTION_ADMITTED','exact_approved_scope':'LEFT sleeve following shoulder only; no right/cuff/coat design/mesh/tool/bind edits',
 'input_seals':[co_manifest,in_manifest,ar_manifest,el_manifest],
 'same_pose_weight_frozen_guard':ordinal,'previous_left_elbow_only_readback':readonly}
print(json.dumps(result,indent=2,sort_keys=True))
