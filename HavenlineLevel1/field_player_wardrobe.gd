extends RefCounted
## Preserve the active player and inventory while changing its visible compact skin.
# Register each compact player's verified runtime skin here after comparison
# with the owner's current model sheet. Character 1 is the built-in controller.
const CHARACTERS := {
	2: "res://assets/characters/Character2Compact.glb",
	3: "res://assets/characters/Character3Compact.glb",
	4: "res://assets/characters/Character4Compact.glb",
}
var world
var source: Skeleton3D
var originals: Array[Node] = []
var visual: Node3D
var target: Skeleton3D
var number := 1
var settings_path := ""
var mapping: Array = []
var feet: Array = []
var arms: Array = []
var tread = preload("res://field_tread_samples.gd").new()
var last_actor := Vector3.INF
var previous_tread := PackedVector3Array()
var bind_offset:=Vector3.ZERO
var hip_settle:=0.
var hip_shift:=Vector3.ZERO
var pack_rest:=Vector3.ZERO
var grounded_ids: Array[int] = [-1,-1]
var grounded_points: Array[Vector3] = [Vector3.ZERO,Vector3.ZERO]

func setup(host: Node3D) -> void:
	world = host
	pack_rest=world.carry.rack.position
	source = world.hero_model.find_children("*","Skeleton3D",true,false)[0]
	originals = world.hero_model.find_children("*","MeshInstance3D",true,false)
	settings_path = "user://field-player.cfg" if world.field_save.native_profile else world.field_save.directory.path_join("field-player.cfg")
	var prefs := ConfigFile.new()
	if prefs.load(settings_path) == OK:
		choose(int(prefs.get_value("player","character",1)),false)

func choose(id: int, persist := true) -> bool:
	if id == number: return true
	if id!=1 and not CHARACTERS.has(id):return false
	var next: Node3D
	var rig: Skeleton3D
	var next_mapping: Array = []
	var next_feet: Array = []
	var next_tread = preload("res://field_tread_samples.gd").new()
	if id != 1:
		var body := load(CHARACTERS[id]) as PackedScene
		if not body: return false
		next = world.model(body,world.hero_model,float(world.layout.actor_height)/world.hero_model.global_basis.get_scale().y)
		var skeletons := next.find_children("*","Skeleton3D",true,false)
		if skeletons.size() != 1:
			next.queue_free()
			return false
		rig = skeletons[0]
		# The runtime body uses the same anatomical names and bind axes as the
		# compact input rig. Every deform bone must have a real controller source.
		for joint in rig.get_bone_count():
			var original := source.find_bone(rig.get_bone_name(joint))
			if original < 0:
				next.queue_free()
				return false
			next_mapping.append([original,joint,source.get_bone_rest(original),rig.get_bone_rest(joint)])
		for side: String in [".L",".R"]:
			var leg := [rig.find_bone("Thigh"+side),rig.find_bone("Shin"+side),rig.find_bone("Foot"+side)]
			if -1 in leg:
				next.queue_free()
				return false
			next_feet.append(leg)
		var pieces := next.find_children("*","MeshInstance3D",true,false)
		var floor_y := INF
		for mesh: MeshInstance3D in pieces:
			if mesh.skin and mesh.mesh:
				floor_y=minf(floor_y,mesh.get_aabb().position.y)
		for mesh: MeshInstance3D in pieces:
			if mesh.skin and mesh.mesh and mesh.get_aabb().position.y<=floor_y+.01:
				next_tread.bind(mesh,rig)
		if next_tread.soles.is_empty():
			next.queue_free()
			return false
	if persist:
		var prefs := ConfigFile.new()
		prefs.set_value("player","character",id)
		if prefs.save(settings_path) != OK:
			if next: next.queue_free()
			return false
	if visual:
		visual.hide()
		visual.queue_free()
	for piece in originals: piece.visible = id == 1
	number = id
	visual = next
	target = rig
	mapping = next_mapping
	feet = next_feet
	arms.clear()
	if rig:
		for side: String in [".L",".R"]:
			arms.append([rig.find_bone("UpperArm"+side),rig.find_bone("Forearm"+side),rig.find_bone("Hand"+side)])
	tread = next_tread
	grounded_ids.assign([-1,-1])
	last_actor = Vector3.INF
	previous_tread.clear()
	world.carry.rack.position=pack_rest
	if not visual: return true
	bind_offset=visual.position
	hip_settle=0.
	hip_shift=Vector3.ZERO
	visual.name = "PlayerCharacter"+str(id)
	world._disable_worn_shadow(visual)
	update_pose(0.)
	return true

func _place_ankle(side: int, shift: Vector3) -> void:
	var ids: Array = feet[side]
	var hip := target.get_bone_global_pose(ids[0])
	var knee := target.get_bone_global_pose(ids[1])
	var boot := target.get_bone_global_pose(ids[2])
	var to := boot.origin + target.global_basis.inverse()*shift
	var direction := hip.origin.direction_to(to)
	var upper := hip.origin.distance_to(knee.origin)
	var lower := knee.origin.distance_to(boot.origin)
	var shortest := sqrt(upper*upper+lower*lower+2.*upper*lower*cos(deg_to_rad(120.)))
	var longest := sqrt(upper*upper+lower*lower+2.*upper*lower*cos(deg_to_rad(7.)))
	var length := clampf(hip.origin.distance_to(to),shortest,longest)
	var along := (upper*upper-lower*lower+length*length)/(2.*length)
	var pole := (knee.origin-hip.origin).slide(direction)
	# A nearly straight leg must retain the same forward bend branch.
	var front: Vector3 = (target.global_basis.inverse()*world.actor.global_basis.z).slide(direction).normalized()
	pole=front if pole.dot(front)<.006 else pole.normalized().lerp(front,.90).normalized()
	var hinge := hip.origin + direction*along + pole.normalized()*sqrt(maxf(0.,upper*upper-along*along))
	var end := hip.origin+direction*length
	hip.basis = Basis(Quaternion(hip.origin.direction_to(knee.origin),hip.origin.direction_to(hinge)))*hip.basis
	knee.basis = Basis(Quaternion(knee.origin.direction_to(boot.origin),hinge.direction_to(end)))*knee.basis
	knee.origin=hinge
	boot.origin=end
	target.set_bone_global_pose(ids[0],hip)
	target.set_bone_global_pose(ids[1],knee)
	target.set_bone_global_pose(ids[2],boot)

func update_pose(dt: float) -> void:
	if not target: return
	for pair: Array in mapping:
		var original: int = pair[0]
		var joint: int = pair[1]
		var from: Transform3D = pair[2]
		var to: Transform3D = pair[3]
		# The actor-specific rest locations remain fitted to the knees, gloves,
		# head and boot fasteners on the selected source mesh.
		var motion := from.basis.get_rotation_quaternion().inverse()*source.get_bone_pose_rotation(original)
		target.set_bone_pose_rotation(joint,(to.basis.get_rotation_quaternion()*motion).normalized())
		target.set_bone_pose_position(joint,to.origin+source.get_bone_pose_position(original)-from.origin)
		target.set_bone_pose_scale(joint,source.get_bone_pose_scale(original))
	if not world.gait_motor.skeleton or tread.soles.is_empty(): return
	for chain: Array in arms:
		if -1 not in chain:
			var forward_wrist := .414 if number==3 else (.405 if number==2 and chain==arms[1] else 0.)
			preload("res://field_glove_clearance.gd").solve(target,world.actor,chain,.79,forward_wrist)
	visual.position=bind_offset
	var boots: Vector2 = world.gait_motor._heights()
	var points: PackedVector3Array = tread.points()
	var low: Array[int] = tread.lowest(points)
	if low[0]<0 or low[1]<0:return
	var actor_at: Vector3 = world.actor.global_position
	if actor_at.distance_squared_to(last_actor)>1.:
		grounded_ids.assign([-1,-1])
		previous_tread.clear()
		hip_settle=0.
		hip_shift=Vector3.ZERO
	last_actor=actor_at
	# Preserve this fitted body's authored hip-to-ankle arc through flight.
	# Settling its lowest tread to the same flight height as the driver keeps
	# the true soles on the snow without folding the free knee to match C1.
	var offset := minf(boots.x,boots.y)-minf(points[low[0]].y,points[low[1]].y)
	visual.global_position.y+=offset
	var goals:=PackedVector3Array([Vector3.ZERO,Vector3.ZERO])
	var settle:=0.
	# The fourth character's longer boot starts rolling onto its own
	# forefoot sooner. Keep the planted patch at the ball during push-off.
	var roll_margin:=.0026 if number==4 else .009
	for side in 2:
		var threshold:=.012 if grounded_ids[side]>=0 else .006
		if boots[side]-actor_at.y>threshold:
			grounded_ids[side]=-1
			continue
		var marker := grounded_ids[side]
		if marker<0 or points[marker].y-points[low[side]].y>roll_margin:
			var continuing := marker>=0 and previous_tread.size()==points.size()
			marker=low[side]
			grounded_ids[side]=marker
			# When pressure rolls heel to ball, pick up the new material patch
			# at its last rendered world position, including its previous IK.
			grounded_points[side]=previous_tread[marker] if continuing else points[marker]+Vector3.UP*offset
		var shift := (grounded_points[side]-points[marker]).slide(Vector3.UP)
		shift.y=boots[side]-points[low[side]].y-offset
		var leg:Array=feet[side]
		var hip:=target.to_global(target.get_bone_global_pose(leg[0]).origin)
		var knee:=target.to_global(target.get_bone_global_pose(leg[1]).origin)
		var ankle:=target.to_global(target.get_bone_global_pose(leg[2]).origin)
		goals[side]=ankle+shift
		var reach:=(hip.distance_to(knee)+knee.distance_to(ankle))*.995
		var lane:=(goals[side]-hip).slide(Vector3.UP).length_squared()
		# Reach the planted toe by settling the hips during late stance. A
		# straight, maxed-out leg otherwise lifts its leather off the snow.
		settle=minf(settle,goals[side].y+sqrt(maxf(.001,reach*reach-lane))-hip.y)
	# Weight shifts toward the planted boot. Ease the pelvis through start
	# and release instead of dropping the free toe or snapping the body up.
	hip_settle=move_toward(hip_settle,maxf(settle,-.050),dt*1.35)
	visual.global_position.y+=hip_settle
	hip_shift=hip_shift.move_toward(Vector3.ZERO,dt*1.55)
	for side in 2:
		if grounded_ids[side]<0:continue
		var leg:Array=feet[side]
		var hip:=target.to_global(target.get_bone_global_pose(leg[0]).origin)
		var knee:=target.to_global(target.get_bone_global_pose(leg[1]).origin)
		var ankle:=target.to_global(target.get_bone_global_pose(leg[2]).origin)
		var reach:=(hip.distance_to(knee)+knee.distance_to(ankle))*.995
		var span:=goals[side]-hip-hip_shift
		var horizontal:=span.slide(Vector3.UP)
		var excess:=horizontal.length()-sqrt(maxf(.001,reach*reach-span.y*span.y))
		if excess>0.:
			hip_shift+=horizontal.normalized()*excess
	hip_shift=hip_shift.limit_length(.23)
	visual.global_position+=hip_shift
	world.carry.rack.position=pack_rest+world.actor.global_basis.inverse()*(hip_shift+Vector3.UP*hip_settle)
	for side in 2:
		if grounded_ids[side]<0:continue
		var ankle:=target.to_global(target.get_bone_global_pose(feet[side][2]).origin)
		_place_ankle(side,goals[side]-ankle)
	# Changing legs rotates a few blended tread vertices. Correct their last
	# millimetres on support without touching the freely swinging boot.
	points=tread.points()
	low=tread.lowest(points)
	for side in 2:
		var marker:=grounded_ids[side]
		if marker<0:
			var under:=actor_at.y+.0009-points[low[side]].y
			if under>.0002:_place_ankle(side,Vector3.UP*under)
			continue
		var correction:=(grounded_points[side]-points[marker]).slide(Vector3.UP)
		correction.y=boots[side]-points[low[side]].y
		if correction.length_squared()>.0000001:
			_place_ankle(side,correction)
	previous_tread=tread.points()

func boot_contacts() -> PackedVector3Array:
	return tread.contacts() if target else world.gait_motor.snow_contact_points()
