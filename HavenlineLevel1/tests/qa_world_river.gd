extends SceneTree

const Session = preload("res://tests/lifecycle_test_profile.gd")
const World = preload("res://field_opening.tscn")
var checks := {}
var field

func _initialize() -> void:
	call_deferred("run")

func check(label: String, passed: bool) -> void:
	checks[label] = passed
	if not passed: push_error(label)

func support_height(at: Vector2) -> float:
	var state: PhysicsDirectSpaceState3D = field.get_world_3d().direct_space_state
	var ray := PhysicsRayQueryParameters3D.create(Vector3(at.x,3.,at.y),Vector3(at.x,-2.,at.y),1,[field.actor.get_rid()])
	var hit := state.intersect_ray(ray)
	return hit.position.y if not hit.is_empty() else INF

func cross_with_controls(start: Vector2, end: Vector2) -> bool:
	field.actor.global_position = Vector3(start.x,0.,start.y)
	field.camera.global_position = field.actor.global_position + field.camera_follow_offset
	field.previous_dry_position = field.actor.global_position
	var press := InputEventScreenTouch.new()
	press.index = 0
	press.position = Vector2(360,535)
	press.pressed = true
	root.push_input(press,true)
	await physics_frame
	var drag := InputEventScreenDrag.new()
	drag.index = 0
	var right: Vector3 = field.camera.global_basis.x
	var near: Vector3 = right.cross(Vector3.UP)
	var forward := Vector3.FORWARD
	drag.position = press.position + Vector2(forward.dot(right),forward.dot(near)) * 85.
	root.push_input(drag,true)
	var passed := true
	for tick in 180:
		await physics_frame
		var at := Vector2(field.actor.global_position.x,field.actor.global_position.z)
		passed = passed and field.river.is_dry(at,float(field.layout.actor_radius))
		if at.y <= end.y: break
	press.pressed = false
	root.push_input(press,true)
	await physics_frame
	return passed and field.actor.position.z <= end.y and field.touch_id < 0

func run() -> void:
	if Session.isolated(self,"res://tests/qa_world_river.gd"): return
	field = World.instantiate()
	root.add_child(field)
	for i in 6: await physics_frame
	field.player_invulnerability = 60.
	var river = field.river
	var water: MeshInstance3D = river.get_node("FlowingRiver")
	var positions: PackedVector3Array = water.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var indices: PackedInt32Array = water.mesh.surface_get_arrays(0)[Mesh.ARRAY_INDEX]
	var box := water.get_aabb()
	check("continuous water traverses both playable world edges",box.position.x < -river.half_map and box.end.x > river.half_map and indices.size() == (river.sections.size()-1)*6)
	var valid := true
	for i in range(0,indices.size(),3):
		var a := positions[indices[i]]
		var b := positions[indices[i+1]]
		var c := positions[indices[i+2]]
		valid = valid and (c-a).cross(b-a).y > .0001
	check("all water triangles are finite and face up",valid and positions.size() > 50)
	var min_width := INF
	var max_width := 0.0
	var dry_lanes := true
	for x in range(-512,513):
		var banks: Vector2 = river.banks_at(x)
		min_width = minf(min_width,banks.y-banks.x)
		max_width = maxf(max_width,banks.y-banks.x)
		dry_lanes = dry_lanes and river.is_dry(Vector2(x,banks.x-2.4),.31) and river.is_dry(Vector2(x,banks.y+2.4),.31)
	check("width stays in the approved range and both banks are continuous",min_width >= 3.2 and max_width <= 4.6 and dry_lanes)
	var remote := -18.0
	var banks: Vector2 = river.banks_at(remote)
	var near := Vector2(remote,banks.y + 3.2)
	var shore_end := Vector2(remote,banks.x - 3.2)
	check("real collision supports the dry shore",absf(support_height(near)) < .025)
	check("open river has no phantom flat walking surface",support_height(Vector2(remote,(banks.x+banks.y)*.5)) == INF)
	var approaches: PackedVector2Array = river.crossing_approaches(.31)
	check("real ground supports the ice crossing",absf(support_height(approaches[0].lerp(approaches[1],.5))) < .025)
	check("long sweep cannot tunnel through the channel",not river.travel_clear(near,shore_end,.31))
	var stop: Vector3 = river.constrain_motion(Vector3(near.x,0,near.y),Vector3(shore_end.x,0,shore_end.y),.31)
	check("blocked movement stays on the original dry bank",stop.z > banks.y and river.is_dry(Vector2(stop.x,stop.z),.31))
	check("crossing preserves the wide truck envelope",river.travel_clear(approaches[0],approaches[1],field.snow_truck.HALF_WIDTH))
	check("ordinary touch movement crosses from dry bank to dry bank",await cross_with_controls(approaches[1],approaches[0]))
	var after_crossing := Vector2(field.actor.position.x,field.actor.position.z)
	check("the crossing never lifts the player off its support",absf(field.actor.position.y - support_height(after_crossing)) < .025)
	var route = preload("res://field_home_route.gd").new()
	check("camp guide finds the crossing from the opposite bank",route.update(field,shore_end) and route.distance > shore_end.distance_to(Vector2.ZERO))
	var pack = preload("res://field_pack_route.gd").new()
	pack.configure(field,.50)
	var legs: PackedVector2Array = pack.route(shore_end,near)
	var all_clear := legs.size() >= 2
	var last := shore_end
	for point in legs:
		all_clear = all_clear and river.travel_clear(last,point,.50)
		last = point
	check("pack routes use the same crossing envelope",all_clear)
	var distant_routes := true
	for x in [-504.0,-60.0,-27.0,-9.0,8.0,25.0,120.0,502.0]:
		var edges: Vector2 = river.banks_at(x)
		var far_bank := Vector2(x,edges.x-2.06)
		var camp_bank := Vector2(x,edges.y+2.06)
		distant_routes = distant_routes and route.update(field,far_bank) and river.travel_clear(far_bank,route.direction_target,.31)
		var journey: PackedVector2Array = pack.route(far_bank,camp_bank)
		distant_routes = distant_routes and journey.size() >= 2 and journey[-1].is_equal_approx(camp_bank)
		var previous := far_bank
		for step in journey:
			distant_routes = distant_routes and river.travel_clear(previous,step,.50)
			previous = step
	check("near-bank actors can route home across local bends and the outer districts",distant_routes)
	var inventory_before: Dictionary = field.inventory.snapshot()
	var wet_z := lerpf(banks.x,banks.y,.24)
	field.lifecycle._restore_actor({"x":remote,"z":wet_z})
	check("legacy wet save restores on the same side with its inventory",field.actor.position.z < banks.x and field.inventory.snapshot() == inventory_before)
	field.set_physics_process(false)
	var stamp: float = river.flow_time
	for i in 12: await physics_frame
	check("water clock pauses with the field simulation",is_equal_approx(river.flow_time,stamp))
	river.tick(.75)
	check("water shader reads the simulation time",is_equal_approx(river.water_material.get_shader_parameter("sim_time"),fmod(stamp+.75,400.)))
	for x in river.Profile.CROSSING_X:
		var width: Vector2 = river.banks_at(x)
		check("crossing reserve is protected at %s" % x,river.reserves(Vector2(x,(width.x+width.y)*.50)))
	print("WORLD_RIVER ",JSON.stringify({"checks":checks,"sections":river.sections.size(),"water_triangles":indices.size()/3,"width_range":[min_width,max_width],"span":[box.position.x,box.end.x]}))
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 6: await process_frame
	quit(1 if false in checks.values() else 0)
