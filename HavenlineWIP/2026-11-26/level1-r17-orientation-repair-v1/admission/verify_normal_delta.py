import json,sys
from pathlib import Path
candidate, control = [json.loads(Path(f).read_text())['frames'] for f in sys.argv[1:]]
assert set(candidate)==set(control)
keys=['queued_tick','wood','renewals','paid','south_open','east_open']
assert all(all(candidate[k][x]==control[k][x] for x in keys) for k in candidate)
rows={}
for k in candidate:
    old=control[k]['matching_native_buffer_sha256']
    new=candidate[k]['matching_native_buffer_sha256']
    rows[k]={'before_sha256':old,'after_sha256':new,'pixel_digest_changed':old!=new}
print(json.dumps({'phase_authority_equal':True,'same_frame_digest_not_required_with_scene_motion':True,
                  'digest_difference_does_not_score_appearance':True,'frames':rows},indent=2))
