extends SceneTree
## Verifies that movement collision and strike detection meet the same stone surface
## before and after hits, depletion, renewal, and handoff from a streamed proxy.
var world
var failures: Array[String] = []
var checks := 0

func _initialize() -> void:
	call_deferred("run")

func check(observed: bool, label: String) -> void:
	checks += 1
	if not observed: failures.append(label)

func compare_surface(rock, label: String) -> void:
	var part: MeshInstance3D = rock._mesh
	var surface: TriangleMesh = world.surfaces[rock][1]
	var matched := 0
	var sampled := 0
	for x in [-.35,0.,.35]:
		for z in [-.35,0.,.35]:
			var top := part.to_global(Vector3(x,3,z))
			var bottom := part.to_global(Vector3(x,-2,z))
			var hit = surface.intersect_segment(part.to_local(top),part.to_local(bottom))
			if not hit is Dictionary or hit.is_empty(): continue
			sampled += 1
			var q := PhysicsRayQueryParameters3D.create(top,bottom,1)
			var ray: Dictionary = world.get_world_3d().direct_space_state.intersect_ray(q)
			if ray.get("collider") == rock.bank_body and ray.position.distance_to(part.to_global(hit.position)) < .012:
				matched += 1
	check(sampled >= 3 and matched == sampled, label+" walking / swept surface (%s/%s)" % [matched,sampled])

func run() -> void:
	world = load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	for i in 4: await physics_frame
	world.set_physics_process(false)
	var starter = world.resource_rock
	compare_surface(starter,"starter full")
	world.lifecycle._restore_strikes(starter,1)
	await physics_frame
	compare_surface(starter,"starter after a strike")
	world.lifecycle.deplete(starter)
	check(not starter._mesh.visible and starter.bank_body.collision_layer == 0,"depleted bank clears movement and draw")
	world.lifecycle.advance(world.lifecycle.stone_seconds+.1)
	await physics_frame
	check(starter._mesh.visible and starter.bank_body.collision_layer == 1,"regrown bank restores movement and draw")
	compare_surface(starter,"regrown bank")
	var landscape = world.world_landscape
	for chunk: Dictionary in landscape.chunks.values():
		for row: Dictionary in chunk.sources:
			if row.kind != "stone" or is_instance_valid(row.live): continue
			var proxy_part: Dictionary = chunk.batches[row.variant][0]
			var expected := Transform3D(Basis(Vector3.UP,row.yaw).scaled(Vector3.ONE*float(row.scale)),row.position) * (proxy_part.local as Transform3D)
			if DisplayServer.get_name() != "headless":
				var actual: Transform3D = chunk.node.global_transform * proxy_part.mesh.get_instance_transform(row.index)
				check(actual.is_equal_approx(expected),"drawn far-bank transform matches template")
			world.actor.position = row.position + Vector3(2,0,1)
			landscape._update_neighborhood()
			var live: MeshInstance3D = row.live._mesh
			check(live.global_transform.is_equal_approx(expected),"streamed proxy and nearby mesh geometry agree")
			await physics_frame
			compare_surface(row.live,"streamed bank")
			world.lifecycle._restore_strikes(row.live,2)
			world.lifecycle.record_strike(row.live)
			var damaged := live.global_transform
			world.actor.position = row.position + Vector3(9,0,0)
			landscape._update_neighborhood()
			check(row.proxy_visible and not is_instance_valid(row.live),"damaged source returns to a visible proxy")
			if DisplayServer.get_name() != "headless":
				var far: Transform3D = chunk.node.global_transform * proxy_part.mesh.get_instance_transform(row.index)
				check(far.is_equal_approx(damaged),"two-strike far bank preserves its reduced silhouette")
			world.actor.position = row.position + Vector3(2,0,1)
			landscape._update_neighborhood()
			check(row.live.strikes == 2 and row.live._mesh.global_transform.is_equal_approx(damaged),"near source restores both strikes and geometry")
			await finish()
			return
	check(false,"streamed stone required")
	await finish()

func finish() -> void:
	world.queue_free()
	for i in 8: await process_frame
	print(JSON.stringify({"checks":checks,"failures":failures}))
	quit(int(not failures.is_empty()))
