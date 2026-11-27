extends SceneTree

const Session = preload("res://tests/lifecycle_test_profile.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var game = load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	for tick in 6: await physics_frame
	game.set_physics_process(false)
	var checks := {}
	for variant in range(3,6):
		var bank_scene: PackedScene = game.field_env.pine_scenes[variant]
		var rows: Array = game.forest.records.filter(func(row):
			return row.variant == variant and row.index >= 0 and row.proxy_visible and not row.get("occupied",false))
		checks["bank %d loaded and has visible source"%variant] = bank_scene != null and not rows.is_empty()
		if rows.is_empty():continue
		var row: Dictionary = rows[0]
		var proxy: MultiMeshInstance3D = row.source
		# Headless RenderingServer cannot read back instance transforms. The
		# same authored CPU transform is what install_woods sends to the batch.
		var template := bank_scene.instantiate() as Node3D
		var parts: Array[MeshInstance3D] = []
		game.meshes(template,parts)
		var before: Transform3D = row.transform * parts[0].transform
		template.free()
		game.forest._open_pine(row)
		var part: MeshInstance3D = game.surfaces[row.live][0]
		var original: Mesh = proxy.multimesh.mesh
		var same := original.get_surface_count() == part.mesh.get_surface_count()
		for surface in original.get_surface_count():
			var baked: Array = original.surface_get_arrays(surface)
			var active: Array = part.mesh.surface_get_arrays(surface)
			same = same and baked[Mesh.ARRAY_VERTEX] == active[Mesh.ARRAY_VERTEX] and baked[Mesh.ARRAY_INDEX] == active[Mesh.ARRAY_INDEX]

		var same_transform := before.is_equal_approx(part.global_transform)
		if not same_transform or not same:
			print("BANK_MISMATCH ", JSON.stringify({"variant":variant,"surface_arrays":same,"expected":str(before),"actual":str(part.global_transform)}))
		checks["bank %d drawn and contact positions agree"%variant] = same_transform and same
		checks["bank %d retains shared harvest source ID"%variant] = row.live.get_meta("field_source_id") == row.id and game.lifecycle.loaded[row.id] == row.live
		checks["bank %d images embedded"%variant] = ResourceLoader.get_dependencies(bank_scene.resource_path).is_empty()
	print("BANK_PROMOTION ",JSON.stringify(checks))
	await Session.drain_field_audio(self,game)
	game.queue_free()
	for tick in 7: await process_frame
	quit(int(checks.values().has(false)))
