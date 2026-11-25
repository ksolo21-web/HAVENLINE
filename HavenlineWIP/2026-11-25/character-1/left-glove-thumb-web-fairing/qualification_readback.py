"""Keep the frozen source-admission gate separate from actual candidate first hits."""
import gzip,json
from pathlib import Path
p=Path(__file__).resolve().parent
D=json.loads(gzip.decompress((p/'native_rays.json.gz').read_bytes()))
R={}
for pose,r in D.items():
    blocked=[];valid=0; positive_hits=0; mn=1.
    for f in (141,142,143,144):
        for i,s in enumerate(r['new_exact_test'][str(f)]):
            actual=s['actual_outer_first_hit']
            assert actual and actual['part']=='local' and actual['id']==f and s['new_face_dot_outward']>.3
            positive_hits+=1
            mn=min(mn,s['new_face_dot_outward'])
            if s['owner_first_valid']:
                assert s['positive_and_target_first'];valid+=1
                continue
            h=s['original_native_outward_first_hit']
            assert h and h['face_row']!=s['original_native_nearest_face_row'] and h['distance_from_original_native_nearest_mm']>18
            blocked.append({'candidate_row':f,'sample_slot':i,**s})
    assert positive_hits==140
    assert not any(x['old_inward_skin_still_first'] for w in r['repeat_prior_probe'].values() for x in w)
    exact_old=[x for slot,x in enumerate(r['repeat_prior_probe']['111']) if slot in (30,32,34)]
    assert all(x['new_outer_occludes_with_positive_normal'] for x in exact_old)
    R[pose]={'attempted_candidate_first_positive_hits':positive_hits,'admitted_source_and_actual_candidate_hits':valid,
             'minimum_raw_candidate_first_dot':mn,'source_direction_failed_by_farther_original_skin':blocked,
             'all_three_old_escape_slots_exact':exact_old}
assert [len(R[k]['source_direction_failed_by_farther_original_skin']) for k in ('neutral','open')]==[11,6]
out={'status':'HOLD_ORIGINAL_NATIVE_SOURCE_NEIGHBORHOOD_ADMISSION',
 'physical_candidate_first_pass_not_a_source_approval':R,
 'exact_controllable_degrees_keep_private_geometry':{'allowed_shape_study_vertex_ids':[116,117,118,119],
  'used_degrees':'two cross-edge anatomical plane angles with paired 1.15mm and 2.35mm arc travel; existing geometry/UV/winding retained',
  'not_enough_for_frozen_source_admission':'old native hand far exterior occludes selected 17 closest branch rays while candidate physically faces them; a local fairing of these colors/normals is not evidence for alternative owner-side mapping',
  'next_nonduplicated_action':'Freeze this authored geometry. For 142/144, require an independent actual owner thumb-web source branch or direction witness tied to the real outside of the old native hand, preserving source seam/side and the cited blocked rays. No arbitrary scope/gate relax or additional offset study.'}}
(p/'qualification_readback.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{i:v for i,v in q.items() if i not in ['source_direction_failed_by_farther_original_skin','all_three_old_escape_slots_exact']} for k,q in R.items()},indent=2))
