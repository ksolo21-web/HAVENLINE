"""Read back exact known escape locations and new nonpassing grazing witnesses."""
import gzip,json
from pathlib import Path
p=Path(__file__).resolve().parent
det=json.loads(gzip.decompress((p/'native_rays.json.gz').read_bytes()))
d={}
for name,r in det.items():
    old=[r['repeat_prior_probe']['111'][i] for i in (30,32,34)]
    assert all(x['new_outer_occludes_with_positive_normal'] and not x['old_inward_skin_still_first'] for x in old)
    a={}
    for i in ('141','142','143','144'):
        h=r['new_exact_test'][i]
        indexed=[(k,x) for k,x in enumerate(h) if x['owner_first_valid'] and x['actual_outer_first_hit'] is not None and x['actual_outer_first_hit']['id']==int(i)]
        g,w=min(indexed,key=lambda z:z[1]['new_face_dot_outward'])
        assert w['new_face_dot_outward']>0
        a[i]={'minimum_exposed_owner_direction_dot':w['new_face_dot_outward'],'exact_minimum_record':w,'probe_row':g,
              'all_valid_actual_same_face_count':len(indexed),'same_face_positive_count':sum(x['new_face_dot_outward']>0 for k,x in indexed),
              'strict_point_and_outward_gate':sum(x['positive_and_target_first'] for x in h)}
    assert all(a[i]['minimum_exposed_owner_direction_dot']<.3 for i in ('141','142'))
    d[name]={'earlier_escape_indices_now_covered':[30,32,34],'exact_new_earlier_escape_positive_hit':old,'minimum_actual_exposed_positive_direction':a}
out={'status':'ORIGINAL_ESCAPE_CLEARS_NEW_SOURCE_GRAZING_HOLD','two_pose_corner_evidence':d,
     'next_concrete_shape_gate':'One owner-source normal-field transition along the actual sheltered thumb-web/outer arc. Source-facing first surface must clear angular margin at the checked corner, not just occlude old liner. Preserve the previous protected attachments; do not change thickness globally, texture-shade it away, or extend the closing perimeter.'}
(p/'qualification_readback.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{i:v['minimum_exposed_owner_direction_dot'] for i,v in r['minimum_actual_exposed_positive_direction'].items()} for k,r in d.items()},indent=2))
