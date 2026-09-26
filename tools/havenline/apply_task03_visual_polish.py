#!/usr/bin/env python3
"""Apply the source-bound T03 visual repair discovered during critic closure.

Repairs actual presentation defects without changing fence collision, gate widths,
river geometry, economy, saves or Task 1/2 assets:
- hide zero-progress defense barricades instead of rendering 15%-height debris;
- root authored fence panels slightly into the sampled terrain;
- shorten/open gate leaves farther so entrances read clearly from oblique views.
Fails closed if expected source snippets have drifted.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace_once(text,old,new,label):
    assert text.count(old)==1,(label,text.count(old))
    return text.replace(old,new,1)

changed=[]
# Boundary geometry: collision/gate endpoints unchanged; only visible open leaves.
p=ROOT/'HavenlineGodot/scripts/camp_boundary.gd';s=p.read_text()
s=replace_once(s,'const PANEL_SOURCE_LENGTH := 2.95\n','const PANEL_SOURCE_LENGTH := 2.95\nconst GATE_LEAF_LENGTH := 0.92\nconst GATE_OPEN_ANGLE := 1.28\n','boundary constants')
s=replace_once(s,'\tvar result:Array[Dictionary]=[];var leaf_length:=1.16\n','\tvar result:Array[Dictionary]=[];var leaf_length:=GATE_LEAF_LENGTH\n','leaf length')
s=replace_once(s,'\t\tvar left_dir:=tangent.rotated(1.10)\n\t\tif left_dir.dot(inward)<0:left_dir=tangent.rotated(-1.10)\n\t\tvar right_dir:=(-tangent).rotated(1.10)\n\t\tif right_dir.dot(inward)<0:right_dir=(-tangent).rotated(-1.10)\n','\t\tvar left_dir:=tangent.rotated(GATE_OPEN_ANGLE)\n\t\tif left_dir.dot(inward)<0:left_dir=tangent.rotated(-GATE_OPEN_ANGLE)\n\t\tvar right_dir:=(-tangent).rotated(GATE_OPEN_ANGLE)\n\t\tif right_dir.dot(inward)<0:right_dir=(-tangent).rotated(-GATE_OPEN_ANGLE)\n','leaf angle')
s=replace_once(s,'\t\t"south_fence_required_margin":SOUTH_FENCE_MARGIN,"collision_radius":COLLISION_RADIUS,"lane_half_width":LANE_HALF,\n','\t\t"south_fence_required_margin":SOUTH_FENCE_MARGIN,"collision_radius":COLLISION_RADIUS,"lane_half_width":LANE_HALF,\n\t\t"gate_leaf_length":GATE_LEAF_LENGTH,"gate_open_angle":GATE_OPEN_ANGLE,\n','evidence')
p.write_text(s);changed.append(str(p.relative_to(ROOT)))

# Visual grounding: barricade AABB begins slightly above local origin, so sink
# the visible authored fence a few cm. Collision remains the exact 2D panels.
p=ROOT/'HavenlineGodot/scripts/camp_boundary_view.gd';s=p.read_text()
s=replace_once(s,'const Scenery=preload("res://scripts/scenery_batch.gd")\n','const Scenery=preload("res://scripts/scenery_batch.gd")\nconst FENCE_ROOT_SINK := 0.04\n','root sink const')
s=replace_once(s,'\tvar pa:=Vector3(a.x,Surface.height_at(a),a.y);var pb:=Vector3(b.x,Surface.height_at(b),b.y)\n','\tvar pa:=Vector3(a.x,Surface.height_at(a)-FENCE_ROOT_SINK,a.y);var pb:=Vector3(b.x,Surface.height_at(b)-FENCE_ROOT_SINK,b.y)\n','segment grounding')
s=replace_once(s,'\tdescriptor["authored_gate_post_asset"]="environment_v2/lantern_post.glb"\n','\tdescriptor["authored_gate_post_asset"]="environment_v2/lantern_post.glb"\n\tdescriptor["fence_root_sink"]=FENCE_ROOT_SINK\n','view evidence')
p.write_text(s);changed.append(str(p.relative_to(ROOT)))

# Runtime: retain defense state/model but do not present zero-progress 15% debris.
p=ROOT/'HavenlineGodot/scripts/main.gd';s=p.read_text()
s=replace_once(s,'const ENVIRONMENT_REVISION := "0.5.0-task03-boundary"','const ENVIRONMENT_REVISION := "0.5.1-task03-visual-polish"','revision')
s=replace_once(s,'\tfor side in sim.defenses:\n\t\tdefense_visuals[side] = model("world/barricade", world, xyz(sim.defenses[side].position))\n\t\tdefense_visuals[side].scale.y = 0.15\n','\tfor side in sim.defenses:\n\t\tvar defense:Dictionary=sim.defenses[side]\n\t\tvar progress:=int(defense.delivered.wood)+int(defense.delivered.stone)\n\t\tdefense_visuals[side] = model("world/barricade", world, xyz(defense.position))\n\t\tdefense_visuals[side].visible = bool(defense.built) or progress > 0\n\t\tdefense_visuals[side].scale.y = .35 + .65 * clampf(float(progress)/11.0,0.0,1.0) if defense_visuals[side].visible else 1.0\n','initial defense presentation')
s=replace_once(s,'\tfor side in sim.defenses:\n\t\tvar d: Dictionary = sim.defenses[side]\n\t\tdefense_visuals[side].scale.y = .15 + .85 * (float(d.delivered.wood + d.delivered.stone) / 11)\n','\tfor side in sim.defenses:\n\t\tvar d: Dictionary = sim.defenses[side]\n\t\tvar progress:=int(d.delivered.wood)+int(d.delivered.stone)\n\t\tdefense_visuals[side].visible = bool(d.built) or progress > 0\n\t\tif defense_visuals[side].visible:\n\t\t\tdefense_visuals[side].scale.y = .35 + .65 * clampf(float(progress)/11.0,0.0,1.0)\n','runtime defense presentation')
p.write_text(s);changed.append(str(p.relative_to(ROOT)))

# Strengthen T03 acceptance around the defects that triggered this repair.
p=ROOT/'HavenlineGodot/tests/test_task03_boundary.gd';s=p.read_text()
s=replace_once(s,'\tcheck("Six gates have twelve lantern posts and twelve open timber leaves",desc.gate_count==6 and desc.gate_post_instances==12 and desc.open_gate_leaf_instances==12)\n','\tcheck("Six gates have twelve lantern posts and twelve open timber leaves",desc.gate_count==6 and desc.gate_post_instances==12 and desc.open_gate_leaf_instances==12)\n\tcheck("Gate leaves use the polished readable opening geometry",Boundary.GATE_LEAF_LENGTH==.92 and Boundary.GATE_OPEN_ANGLE==1.28)\n\tcheck("Authored fence roots are deliberately sunk into terrain",is_equal_approx(float(desc.fence_root_sink),.04))\n\tvar zero_progress_hidden:=true\n\tfor side in game.sim.defenses:\n\t\tzero_progress_hidden=zero_progress_hidden and not game.defense_visuals[side].visible\n\tcheck("Zero-progress defense barricades do not appear as collapsed fence debris",zero_progress_hidden)\n','T03 visual checks')
p.write_text(s);changed.append(str(p.relative_to(ROOT)))

print(json.dumps({'repair':'T03-visual-polish-1','changed':changed,'hashes':{name:sha(ROOT/name) for name in changed},'collision_gate_endpoints_changed':False,'river_geometry_changed':False,'economy_changed':False,'save_schema_changed':False,'task_approved':False},indent=2))
