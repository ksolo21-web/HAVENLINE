"""Reduce local raw native pose evidence without disclosing any skin vertices."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
stage=Path(sys.argv[1])
raw=stage/'capture.log'; log=raw.read_text()
data=[json.loads(s[11:]) for s in log.splitlines() if s.startswith('PAID_CARRY ')]
assert len(data)==1 and 'failures 0' in log
d=data[0];assert d['wood_stock']==d['pine_occurrences']==d['native_presented_units']==2
assert d['paid_receipt']['typed_debit']=={'wood':3} and d['original_bundle_visible'] and d['original_bundle_parent_is_stock_view']
assert d['no_persistence'] and d['actors_native_grounded'] and not d['has_receiver']
assert len(d['gates'])==2 and d['gates'][0]['target_open'] and d['gates'][0]['in_player_reach']
assert d['gates'][0]['outside_freeze_box'] and abs(d['gates'][0]['angle']-np.pi/2)<.001
assert all(len(g['leaf_boxes'])==2 for g in d['gates'])
assert len(d['actual_bundle_mesh_parts'])==6 and all(m['visible'] for m in d['actual_bundle_mesh_parts'])
assert len(d['carry_node_child_names'])==2 and 'TechnicalWoodBundleRepresentative' in d['carry_node_child_names']
hero_file=stage/'hero_world.json'
mesh=json.loads(hero_file.read_bytes())
vs=np.concatenate([np.array(m['positions']) for m in mesh]); ix=sum(len(m['triangles'])//3 for m in mesh)
assert ix==96001 and np.isfinite(vs).all()
actor=d['actor_world']; worldactor=np.array(actor['basis_cols']).T
local=(vs-actor['origin'])@np.linalg.inv(worldactor).T
def bbox(q):return np.stack([q.min(0),q.max(0)]).tolist()
fit=d['original_fit']; stock_fringe_z=fit['position'][2]+fit['size'][2]
report={'native':d,'triangle_count':ix,'world_cpu_skin_bounds':bbox(vs),'actor_relative_cpu_skin_bounds':bbox(local),
 'stock_fit_nearest_back_projection_gap_m':float(local.min(0)[2]-stock_fringe_z),
 'candidate_unscaled_crown_role_exists_as_individual_in_this_source':False,
 'actual_bundle_mesh_internal_parts_not_detachable_stock_ids':True,
 'mesh_partial_intersections_not_tested':True,'local_raw_cpu_pose_sha256':hashlib.sha256(hero_file.read_bytes()).hexdigest()}
print(json.dumps(report,indent=2,sort_keys=True))
