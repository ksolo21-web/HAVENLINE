"""Frozen source decisions only; no rig, pose, meshes, motion or native use."""
from pathlib import Path
import re,json,hashlib
P=Path(__file__).resolve().parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seals={
'hvn-l1-c1-source-choice-v1':'ba72b2f610bc1b5954a6875ba0ce5a2308969deca1575c5cd295b612f0c6c5f2',
'hvn-l1-c1-owner24-contact-v1':'6b1dbdc01d1a5dbeb6c9b50a17b62ff97ed501828e007a22db08124f42edc16a',
'hvn-l1-c1-owner24-support-screen-v1':'91d3dfffd6433f999dd8584bab5a8f700db5841d98fdae54cf58f3d1355cc976',
'hvn-l1-c1-owner24-roll-handoff-v1':'a32616279c5056f4884a8ce47328ab0995ae78f3ba65a12fa29f7a6c6df9cb3d',
'hvn-l1-c1-heel-entry-v1':'f40e72ff8f365844f9460f3430da7c83259cf0c2c85f7f4201a9ff4465fdbf28'}
for n,h in seals.items():
 d=P/n; assert sha(d/'SHA256SUMS')==h,(n,sha(d/'SHA256SUMS'))
 for line in (d/'SHA256SUMS').read_text().splitlines():
  s,p=line.split(maxsplit=1);assert sha(d/p)==s
owner=P/'hvn-c1-distinct-art-source-read/Character 1.glb'
fingers=P/'hvn-c1-distinct-art-source-read/Character 1 rigged - with fingers - no animation.glb'
native=P/'hvn-l1-carry-passive-rehearsal-parser-v2'
stock=native/'staged/project/assets/characters/Character1.glb'
measured=native/'graphics-evidence.3ekSzqv3/passive.log'
assert sha(owner)=='9ffb00c49ca8cec0ab2561ab5b79c9f6fb3ea63a761f6cb3ba0010cc3dd042c9'
assert sha(fingers)=='280d493b9ddedd728835a4df2ba8c1c810ae03e3dd52c4b323c773150d03d39c'
assert sha(stock)=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
assert sha(measured)=='82eb19085fe189d07806f95b7557d64d49f219952de228f5fd948510c9285162'
rec,=[json.loads(l) for l in re.findall(r'^CARRY_PASSIVE_REHEARSAL (.+)$',measured.read_text(),re.M)]
location=rec['rows'][47]['common']
assert location['tick']==48 and location['floor']
supp=json.loads((P/'hvn-l1-c1-owner24-support-screen-v1/result.json').read_text())
roll=json.loads((P/'hvn-l1-c1-owner24-roll-handoff-v1/result.json').read_text())
def one(k,r):return next(v for v in roll if v['k']==k and v['role']==r)
tri_test=P/'hvn-l1-c1-owner24-contact-v1/triangle_witness.py'
v=1.50; hz=120; nominal_window=14/hz
print(json.dumps(dict(
 scope='design/source admission only; no authored gait',
 asset_sha256={'owner24_primary_hypothesis':sha(owner),'fingered73_rejected_import_parity_as_now':sha(fingers),'stock66_baseline_only':sha(stock)},
 tests_sealed=seals, stock_camera_and_terrain_origin_only_m=location['position'], source_location_tick=48,
 no_equivalence_claim_to_native_walk=True, owner24_fit_m=1.75,
 old_owner24_witness_mm={'L_known_static_flat':max(q['max_connect_width_mm'] for q in supp[0]['matched_static_support']),
 'R_broad_existing_key_k43':one(43,'right')['max_connect_width_mm'],
 'R_at_outgoing_L_roll_k39':one(39,'right')['max_connect_width_mm'],
 'L_broad_existing_key_k7':one(7,'left')['max_connect_width_mm'],
 'L_at_outgoing_R_roll_k72':one(72,'left')['max_connect_width_mm']},
 distinct_bounded_test={'window':'one separately pose-authored walk double-support window: first bilateral broad before start cap; loaded narrow roll after transfer never counts as qualifying','samples':15,'intervals':14,'hz':hz,'duration_s':nominal_window,
  'speed_mps':v,'root_travel_m':nominal_window*v,'loaded_connected_width_floor_m':.100,'no_load_claim_from_joint_points':True,
  'target':'solve two indexed patch feasibility simultaneously with pinned world feet and allowed pelvis trajectories; share joint motion only after feasible patch/center path',
  'compare_support_measurement_sha256':sha(tri_test)},
 exact_dependency='two connected broad actual support components simultaneously feasible and center transfer through their interior without interference/skate; existing certificates validate either foot on separate times only, no common solution proved',
 gameplay_or_pose_changed=False),indent=2))
