extends SceneTree
## Measure footplants on vertices of the exported sole throughout an actual gameplay route.
var world: Node3D
var skel: Skeleton3D
var skin: Skin
var points: Array = []
var failures: Array[String] = []
var report := {}
const DT := 1.0 / 60.0
const ORIGIN := Vector2(80,620)

func _initialize() -> void:
	Engine.physics_ticks_per_second = 60
	call_deferred("run")

func load_sole(part: MeshInstance3D) -> void:
	skel = part.get_node(part.skeleton)
	skin = part.skin
	var arrays := part.mesh.surface_get_arrays(0)
	var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
	var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
	var influences := bones.size() / vertices.size()
	var unique := {}
	for i in vertices.size():
		var p := vertices[i]
		if p.y > 0.027 or unique.has(p): continue
		unique[p] = true
		var bindings := {}
		for k in influences:
			var j := i * influences + k
			if weights[j] > 0.0: bindings[bones[j]] = weights[j]
		points.append([p, bindings])

func soles_world() -> PackedVector3Array:
	var transforms: Array[Transform3D] = []
	for i in skin.get_bind_count():
		var bone := skel.find_bone(skin.get_bind_name(i))
		transforms.append(skel.global_transform * skel.get_bone_global_pose(bone) * skin.get_bind_pose(i))
	var surface := PackedVector3Array()
	for point: Array in points:
		var v := Vector3.ZERO
		for binding: int in point[1]:
			v += (transforms[binding] * Vector3(point[0])) * float(point[1][binding])
		surface.append(v)
	return surface

func drag(strength: float) -> void:
	var event := InputEventScreenDrag.new()
	event.index = 5
	event.position = ORIGIN + Vector2(strength * 82.0, 0)
	world._input(event)

func measure(label: String, strength: float) -> void:
	drag(strength)
	var peak_turn := 0.0
	var gait_mismatch := 0
	var min_height := INF
	var footfall_period := 0.0
	var slips: Array[float] = []
	var transition_slips: Array[float] = []
	var last_yaw: float = world.actor.rotation.y
	var previous := soles_world()
	var gait = world.character_kit.locomotion
	for i in 165:
		await physics_frame
		var yaw: float = world.actor.rotation.y
		peak_turn = maxf(peak_turn, absf(angle_difference(last_yaw, yaw)))
		last_yaw = yaw
		var surface := soles_world()
		if i >= 35:
			if gait.current != ("run" if label == "reverse" else label): gait_mismatch += 1
			footfall_period += gait.stride_hz
			for j in surface.size():
				min_height = minf(min_height, surface[j].y)
				if surface[j].y < .005 and previous[j].y < .005:
					slips.append((surface[j] - previous[j]).slide(Vector3.UP).length() / DT)
		if i < 35:
			for j in surface.size():
				if surface[j].y < .005 and previous[j].y < .005:
					transition_slips.append((surface[j] - previous[j]).slide(Vector3.UP).length() / DT)
		previous = surface
	slips.sort()
	var measured: float = world.actor.velocity.length()
	report[label] = {"settled_world_speed_m_s": measured, "settled_steps_per_minute": 120.0 * footfall_period / 130.0, "max_yaw_delta_per_tick_deg": rad_to_deg(peak_turn), "gait_mismatches": gait_mismatch, "lowest_sole_m": min_height, "near_ground_vertex_pairs":slips.size()}
	transition_slips.sort()
	if not transition_slips.is_empty():
		report[label]["transition_p95_near_ground_point_speed_m_s"] = transition_slips[int(.95*(transition_slips.size()-1))]
	if not slips.is_empty():
		report[label]["median_near_ground_point_speed_m_s"] = slips[slips.size()/2]
		report[label]["p95_near_ground_point_speed_m_s"] = slips[int(.95 * (slips.size()-1))]
	var wanted_speed := 0.0 if label=="idle" else (1.1171 if label=="walk" else 2.80)
	var within_contact_budget := min_height > -.002 and min_height < .005 and not slips.is_empty()
	if within_contact_budget:
		within_contact_budget = slips[slips.size()/2] < .12
	if gait_mismatch != 0 or rad_to_deg(peak_turn) > 10.5 or absf(measured - wanted_speed) > .04 or not within_contact_budget:
		failures.append(label)

func run() -> void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	await physics_frame
	world.actor.position = Vector3(-7,0,-5)
	for node: MeshInstance3D in world.actor.find_children("*","MeshInstance3D",true,false):
		if node.skin: load_sole(node); break
	if points.is_empty():
		printerr("No weighted sole vertices"); quit(1); return
	var touch := InputEventScreenTouch.new()
	touch.index = 5
	touch.position = ORIGIN
	touch.pressed = true
	world._input(touch)
	await measure("walk",.42)
	await measure("run",1)
	await measure("reverse",-1)
	await measure("idle",0)
	report["tested_sole_vertices"] = points.size()
	report["failures"] = failures
	print(JSON.stringify(report))
	await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,world)
	world.queue_free()
	for i in 5: await process_frame
	quit(0 if failures.is_empty() else 1)
