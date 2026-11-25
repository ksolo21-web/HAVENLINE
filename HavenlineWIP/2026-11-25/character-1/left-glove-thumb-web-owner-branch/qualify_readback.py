"""Read back always-same-rule supplemental evidence, preserving old failed angles."""
import gzip,hashlib,json
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parent
spec=json.loads((p/'result.json').read_text())
buf=gzip.decompress((p/'full_unmasked_samples.json.gz').read_bytes())
assert hashlib.sha256(buf).hexdigest()==spec['decompressed_full_ray_evidence_sha256']
res=json.loads(buf)
Q={}
for phase,tests in res.items():
  index={r:[] for r in ('branch_facet_fan_mean','branch_to_bone_side_0.25','branch_to_bone_side_0.50','branch_to_bone_side_0.75','true_bone_plane_side')}
  for key,test in tests.items():
    assert test['exact_original_failed_and_unchanged']
    assert test['source_face_in_immutable_anatomical_branch']
    arc=test['separate_supplement_attempts']
    assert list(index)==[a['direction_named_rule'] for a in arc]
    for a in arc:
      data=a.copy()
      vis=a['full_owner_reference_origin_first']; cand_vis=a['full_owner_candidate_origin_first']; u=np.array(a['direction'])
      if a['source_ref_and_candidate_admitted']:
        dist=1000*np.linalg.norm(np.array(cand_vis['point'])-np.array(vis['point']))
        data.update(first_mapped_source_distance_mm=float(dist),both_owner_alignment_min=float(min(np.dot(u,vis['normal']),np.dot(u,cand_vis['normal']))))
      index[a['direction_named_rule']].append((key,data))
  q={}
  for rule,notes in index.items():
    a=[(k,d) for k,d in notes if d['source_ref_and_candidate_admitted']]
    q[rule]={'admitted_count':len(a),'target_count':len(notes),'failed_targets':[k for k,d in notes if not d['source_ref_and_candidate_admitted']],
     'candidate_first_hit_min_dot':min((d['candidate_outward_dot'] for k,d in a),default=None),
     'owner_minimum_true_outward_hit_dot':min((d['both_owner_alignment_min'] for k,d in a),default=None),
     'owner_max_gap_between_both_first_hits_mm':max((d['first_mapped_source_distance_mm'] for k,d in a),default=None)}
  assert all(q[k]['admitted_count']==len(tests) for k in ('branch_facet_fan_mean','branch_to_bone_side_0.25'))
  Q[phase]={'original_historical_unchanged_failed_count':len(tests),'unmasked_source_and_target_by_fixed_rule':q}
(p/'supplement_readback.json').write_text(json.dumps(Q,indent=2)+'\n')
print(json.dumps(Q,indent=2))
