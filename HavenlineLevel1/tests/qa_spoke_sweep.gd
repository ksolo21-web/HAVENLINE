extends SceneTree

const Opening = preload("res://orbit_opening.tscn")
const Enemy = preload("res://field_enemy.gd")
const Orbit = preload("res://weapon_orbit.gd")
var failures: Array = []
var checks := 0
var measurements := {}
var world
var wolf
var kit
var here := Vector3(20,0,-25)
var away := Vector3(-30,0,-30)

func check(pass_: bool, label: String) -> void:
	checks += 1
	if not pass_: failures.append(label)

func ticks(amount: int, dt := 1./30.) -> void:
	for i in amount:
		world._step_character(dt,0.)
		world.step_tree(dt)

func _initialize() -> void: run.call_deferred()

func run() -> void:
	world = Opening.instantiate()
	root.add_child(world)
	await physics_frame
	world.set_physics_process(false)
	kit = world.character_kit
	wolf = Enemy.new()
	world.add_child(wolf)
	wolf.configure(world.actor)
	world.register_hostile(wolf,wolf.contact_mesh())
	for upgraded in [false,true]:
		measure_mode(upgraded)
	test_small_cross_section()
	test_warp()
	print(JSON.stringify({"suite":"spoke_sweep","checks":checks,"failures":failures,"tip_meters":measurements}))
	world.queue_free()
	await process_frame
	quit(int(not failures.is_empty()))

func reset_scene(upgraded: bool) -> void:
	world.actor.global_position = here
	for body: Node3D in [world.resource_tree,world.resource_rock,wolf]:
		body.global_position = away
	kit.rest()
	kit.set_upgraded(upgraded)
	ticks(35)

func measure_mode(upgraded: bool) -> void:
	var mode := "upgraded" if upgraded else "normal"
	reset_scene(upgraded)
	for kind in ["tree","stone","wolf"]:
		var body: Node3D
		match kind:
			"tree":
				body = world.resource_tree
				body._regrow()
			"stone":
				body = world.resource_rock
				body.set_available(true)
			"wolf":
				body = wolf
				wolf.hp = wolf.max_hp()
		body.global_position = here + Orbit.CAMERA_NEAR * .88
		var previous: int = world.contacts.size()
		ticks(28)
		var recorded := {}
		for impact in world.contacts.slice(previous):
			if impact.target == body.name:
				check(not recorded.has(impact.turn),mode+" "+kind+" once per turn")
				recorded[impact.turn] = true
		check(not recorded.is_empty(),mode+" reaches inner "+kind+" geometry")
		if kind == "wolf":
			check(wolf.hp == wolf.max_hp() - recorded.size(),mode+" wolf loses real HP")
		else:
			check(body.strikes == recorded.size(),mode+" actual "+kind+" strike count")
		if kind != "wolf":
			ticks(85)
			check(body.strikes == 3 and body.phase not in ["seated","rooted"],mode+" "+kind+" depletes normally from the inner sweep")
		body.global_position = away

	for tool in ["axe","pickaxe"]:
		kit.begin(tool)
		var farthest := 0.0
		for frame in 180:
			kit.advance(Orbit.PERIOD/180.,here)
			farthest = maxf(farthest,Vector2(kit.current_tip.x-here.x,kit.current_tip.z-here.z).length())
			kit.finish_turn()
		measurements[mode+"_"+tool] = farthest
		check(farthest < (3.28 if upgraded else 2.72),mode+" "+tool+" shortened maximum")

	# Place the near face of the real wolf's bounds beyond every possible tip.
	wolf.hp = wolf.max_hp()
	var geom: MeshInstance3D = wolf.contact_mesh()
	wolf.global_position = here
	var box: AABB = geom.global_transform * geom.mesh.get_aabb()
	var extent := here.z-box.position.z
	wolf.global_position.z += extent + float(measurements[mode+"_axe"]) + .05
	ticks(62)
	check(wolf.hp == wolf.max_hp(),mode+" no hit outside rendered extent")
	wolf.global_position = away

func test_small_cross_section() -> void:
	reset_scene(false)
	kit.begin("axe")
	kit.advance(Orbit.PERIOD/4.,here)
	var points: PackedVector3Array = kit.slots[0].spokes
	var p := points[0].lerp(points[1],.44).lerp(points[2].lerp(points[3],.44),.41)
	# A two-millimetre geometric witness lies wholly inside the first swept
	# patch. Neither its centreline nor its edges touch the sampled rays.
	var probe := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = Vector3.ONE*.002
	probe.mesh = mesh
	world.add_child(probe)
	probe.global_position = p
	var native := mesh.generate_triangle_mesh()
	var inv := probe.global_transform.affine_inverse()
	check(native.intersect_segment(inv*points[0],inv*points[1]).is_empty(),"before spoke genuinely misses tiny witness")
	check(native.intersect_segment(inv*points[2],inv*points[3]).is_empty(),"after spoke genuinely misses tiny witness")
	check(kit.crosses_surface(probe,native),"continuous between-ray damage coverage")
	probe.free()

func test_warp() -> void:
	reset_scene(false)
	kit.begin("axe")
	kit.advance(.01,here)
	var p: Vector3 = kit.current_tip
	var travel := Vector3(5,0,0)
	wolf.hp = wolf.max_hp()
	wolf.global_position = p + travel * .50 - Vector3.UP*.89
	world.actor.global_position += travel
	kit.advance(.01,world.actor.global_position)
	check(not kit.crosses_surface(wolf.contact_mesh(),wolf.hit_surface),"teleport never joins old and new tips")
