extends SceneTree
var checks: Array = []
var failures: Array = []
func check(label: String, passed: bool):
	checks.append({"name":label,"passed":passed})
	if not passed: failures.append(label)
func _initialize(): call_deferred("run")
func run():
	var scene = load("res://scenes/main.tscn").instantiate()
	scene.qa_mode = true
	scene.render_review = true
	scene.capture_directory = "user://native-ui-test-captures"
	root.add_child(scene)
	await process_frame
	check("active scene uses native completion runtime",scene.get_script().resource_path == "res://scripts/main_native.gd")
	check("all four original identities are instantiated",scene.actors.keys().size() == 4 and scene.actors.has(1) and scene.actors.has(2) and scene.actors.has(3) and scene.actors.has(4))
	check("static forest uses fewer mesh groups without changing geometry",scene.world_batch_report.static_tree_roots == 38 and scene.world_batch_report.instanced_mesh_groups < scene.world_batch_report.mesh_submissions_before and not scene.world_batch_report.source_geometry_modified)
	check("harvested trees retain independent visuals",scene.resource_visuals.size() == scene.sim.resources.size())
	check("review scene rejects unrendered threat damage",not scene.sim.threat_presentation_ready)
	check("camp has assignments for the three actual companions",scene.job_controls.size() == 3 and not scene.job_controls.has(scene.sim.lead))
	scene.recorder.warmup = 0
	for i in range(125): scene.recorder.sample(1000000+i*16667,Vector2i(3840,2160))
	var samples: int = scene.recorder.count
	scene.toggle_menu()
	check("opening Camp preserves the completed measurement segment",scene.paused and scene.recorder.count == samples)
	scene.write_diagnostics()
	var diagnostics = JSON.parse_string(FileAccess.get_file_as_string("user://diagnostics/native-performance.json"))
	check("Camp exports measurements without certifying device performance",diagnostics.sample_count == samples and diagnostics.performance_certified == false)
	scene.switch_lead(2)
	check("lead swap remaps job controls to the unselected lead",scene.sim.lead == 2 and scene.job_controls.has(1) and not scene.job_controls.has(2) and scene.actors.size() == 4)
	scene.job_controls[1].selection.item_selected.emit(3)
	check("remapped assignment changes the real companion's job",scene.sim.companions.filter(func(c):return c.id==1)[0].job == "stone")
	check("resuming starts a new uninterrupted measurement segment",scene.recorder.count == 0 and not scene.paused)
	check("Camp is vertically scrollable for constrained landscape windows",scene.menu.get_child(0) is ScrollContainer)
	scene.free()
	print(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures}))
	quit(0 if failures.is_empty() else 1)
