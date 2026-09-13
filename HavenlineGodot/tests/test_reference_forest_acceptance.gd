extends SceneTree
const Main = preload("res://scripts/main.gd")
const Forest = preload("res://scripts/reference_forest.gd")
const Surface = preload("res://scripts/outpost_surface.gd")
var checks: Array = []
var failures: Array = []
func check(name: String, passed: bool):
	checks.append({"name":name,"passed":passed})
	if not passed: failures.append(name)
func _initialize(): call_deferred("run")
func run():
	var game = Main.new()
	game.qa_mode=true;game.render_review=true;game.capture_frames=100
	game.capture_directory="user://t01-acceptance";game.size=Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	var before: Array=[]
	for resource in game.sim.resources: before.append(resource.duplicate(true))
	var focus = game.xyz(game.sim.position)+Vector3(0,.95,0)
	check("Nine tree surfaces receive shared player-focus state",Forest.set_player_clearance(game,focus)==9)
	var batches:=0;var instance_count:=0;var material_ok:=true;var origins_finite:=true
	for child in game.world.get_children():
		if not str(child.name).begins_with("ReferenceForest_"):continue
		batches+=1
		check("Spatial forest batch stays visible: %s"%child.name,child.visible)
		instance_count+=child.multimesh.instance_count
		for i in child.multimesh.instance_count:
			var transform: Transform3D=child.multimesh.get_instance_transform(i)
			if not transform.origin.is_finite():origins_finite=false
		for s in child.multimesh.mesh.get_surface_count():
			var mat=child.multimesh.mesh.surface_get_material(s)
			if not mat is ShaderMaterial:material_ok=false;continue
			if mat.get_shader_parameter("player_focus_world")!=focus or mat.get_shader_parameter("player_clearance_enabled")!=true:material_ok=false
	check("Every instanced forest surface supports the actual cutaway shader",material_ok)
	check("All instance origins are finite",origins_finite)
	check("Batch counts match the scene record",batches==game.reference_forest_evidence.spatial_batches)
	check("No tree instances lost through batch grouping",instance_count==game.reference_forest_evidence.instances)
	check("Forest remains dense after visibility integration",instance_count>=350)
	check("Sightline update does not change source quantities",before==game.sim.resources)
	for variant in range(1,4):
		var mesh: ArrayMesh=game.merged_cache["world/pine_%d"%variant]
		check("Variant %d retains three material surfaces"%variant,mesh.get_surface_count()==3)
		check("Variant %d has a seated continuous trunk"%variant,mesh.get_aabb().position.y<=-.17)
		for s in mesh.get_surface_count():
			var mat: ShaderMaterial=mesh.surface_get_material(s)
			check("Variant %d surface %d has an authored albedo map"%[variant,s],mat.get_shader_parameter("albedo_texture")!=null)
			check("Variant %d surface %d has no alpha-blending fallback"%[variant,s],not mat.shader.code.contains("ALPHA =") and mat.shader.code.contains("discard"))
	var seated:=true
	var bounds=Vector2(game.sim.contract.world.boundX,game.sim.contract.world.boundZ)
	for place in Forest.placements(bounds):
		var p: Vector2=place.point
		for offset in [Vector2(.23,0),Vector2(-.23,0),Vector2(0,.23),Vector2(0,-.23)]:
			if Surface.height_at(p)-.17*place.scale > Surface.height_at(p+offset*place.scale):seated=false
	check("Decorative trunk bases seat below all four local ground samples",seated)
	for index in game.sim.resources.size():
		var resource=game.sim.resources[index]
		if resource.kind!="wood":continue
		var tree: MeshInstance3D=game.resource_visuals[resource.id]
		var old_position: Vector3=tree.position
		tree.position=game.xyz(game.sim.position+Vector2(0,2.4))
		for step in range(6):game.update_foreground_visibility(focus,.1)
		check("Wood resource %s can clear the camera without disappearing from simulation"%resource.id,float(tree.get_instance_shader_parameter("cutaway"))>.9 and tree.visible and resource.units==before[index].units)
		resource.units=0;game.update_foreground_visibility(focus,.1)
		check("Wood resource %s remains depleted through clearance update"%resource.id,not tree.visible)
		resource.units=before[index].units;tree.position=old_position
	Forest.set_player_clearance(game,Vector3.ZERO,false)
	var disabled:=true
	for variant in range(1,4):
		var mesh: ArrayMesh=game.merged_cache["world/pine_%d"%variant]
		for s in mesh.get_surface_count():
			if mesh.surface_get_material(s).get_shader_parameter("player_clearance_enabled")!=false:disabled=false
	check("Isolated asset diagnostics explicitly disable player clearance",disabled)
	check("All resource quantities/locations restored after tests",before==game.sim.resources)
	check("Native render scale remains exactly one",game.scene_view.scaling_3d_scale==1.0)
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame
	print(JSON.stringify({"suite":"reference_forest_acceptance","checks":checks,"failures":failures,"passed":failures.is_empty(),"independent_critic":false,"visual_score":null,"physical_4k60_verified":false}))
	quit(0 if failures.is_empty() else 1)
