import hashlib,json,math,re,sys
from pathlib import Path
root=Path(__file__).resolve().parent
p=Path(sys.argv[1])
d=p/'previews'/'gate_pair_study'
pins={
  'GateLeaf.obj':'006c1998b400f448d86ff81612ca89624ddcc4eeeec10d33cda1b3174c7aac6b',
  'GateLeaf_Right.obj':'f39c65ee900fa27e4b53c9a588b749e5f82f5a57582f9aa0abb59b5846e69274',
  'GateLeaf.mtl':'93084c44ec4d2060898fafb46559733492eb879b3b90294e3f7949336ea43372',
  'gate_pair_mount.gd':'1aa59be56491f69ebf483c51a8dd458546d8e79aaea224a81ca3bb45c0d9cecb',
  'gate_art_review.gd':'7761974d3d5ce99e887bb64f6ea4a170ae2b8a96d42334745dab00583b6249bf',
}
for name, sha in pins.items():
    b=(d/name).read_bytes()
    assert hashlib.sha256(b).hexdigest()==sha,name
    if name.startswith('Gate'):
        assert b==(root/'donor'/name).read_bytes()
leaves={}
for name,sign in [('GateLeaf.obj',1),('GateLeaf_Right.obj',-1)]:
    raw=(d/name).read_text()
    v=[tuple(map(float,l.split()[1:4])) for l in raw.splitlines() if l.startswith('v ')]
    f=[l.split()[1:] for l in raw.splitlines() if l.startswith('f ')]
    assert len(f)==526 and sum(len(x)-2 for x in f)==1360
    assert [l for l in raw.splitlines() if l.startswith('mtllib ')]==['mtllib GateLeaf.mtl']
    assert set(re.findall(r'^usemtl (.*)$',raw,re.M))=={'board','board_warm','board_soft','beam','brace_back','snow','metal','rope','rope_dark'}
    inward=[(sign*x,y,z) for x,y,z in v]
    low=list(map(min,zip(*inward))); high=list(map(max,zip(*inward)))
    assert low==[.007,.074,-.069] and high==[1.178,1.336,.069]
    # Independent 0.1-degree projection using actual mesh vertices.
    all_angles=[a for a in range(901)]
    overlap=[]
    max_out=0.
    for tenth in all_angles:
        cos=math.cos(math.radians(tenth/10)); sin=math.sin(math.radians(tenth/10))
        # Both leaves rotate toward negative Z. Positive out is toward the post.
        vertices=[(-x*cos-z*sin,-x*sin+z*cos) for x,y,z in inward]
        max_out=max(max_out,max(x for x,z in vertices))
        if any(.008 <= x <= .38432 and -.193088 <= z <= .193088 for x,z in vertices):
            overlap.append(tenth/10)
    assert round(max_out,6)==.069 and .0 not in overlap and 90. in overlap
    leaves[name]={'obj_faces':len(f),'triangulated_faces':sum(len(x)-2 for x in f),'inward_local_AABB_m':[low,high],
        'hinge_guard_mm':7,'free_tip_guard_mm':2,'base_guard_mm':74,'ceiling_guard_mm':14,'transverse_guard_mm_each':1,
        'max_outboard_in_sampled_swing_mm':round(max_out*1000,6),
        'post_AABB_plan_projection_candidate_overlap_angles':len(overlap),
        'first_sampled_angle_with_potential_post_overlap_degrees':min(overlap)}
m=(d/'GateLeaf.mtl').read_text()
assert len(re.findall('^newmtl ',m,re.M))==9 and not re.search(r'^\s*(map_[a-zA-Z_]+|bump|disp|decal)\s',m,re.M)
net_zero=2*.008
shell=(p/'previews'/'r17_fence'/'r17_fence_view.gd').read_text()
assert 'const POST_CENTER_BACKSET := .19616' in shell and 'const POST_SCALE := Vector3(1.12, 1.14, 1.12)' in shell
for part in ('timber_gate_view.gd','timber_gate_view.tscn'):
    assert (p/'previews'/'timber_gate'/part).read_bytes()==(root/part).read_bytes()
print(json.dumps({'scope':'static geometry only; 3D terrain seating/pixel seams not measured',
 'mounted_source_pins':pins,'authority':'unchanged predecessor; 137 files checked separately',
 'mirrored_extent_pair':leaves,'max_projection_past_post_inner_plane_mm':61,
 'closed_center_gap_mm':44,'closed_hinge_to_post_plan_gap_mm_each':15,
 'clearance_and_appearance':'HOLD until exact 3D post/hinge seam and native views at closed/partial/open; sampled XZ AABB overlap not physical interference',
 'stock_collider_containment_under_all_inherited_rigid_yaws':True,'candidate_art_triangles':5440,'new_collision_shapes':0},indent=2))
