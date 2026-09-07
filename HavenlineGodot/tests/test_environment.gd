extends SceneTree
const Main = preload("res://scripts/main.gd")
const Surface = preload("res://scripts/outpost_surface.gd")
var checks: Array=[]
var failures: Array=[]
func check(label:String, passed:bool):
	checks.append({"name":label,"passed":passed})
	if not passed:failures.append(label)
func _initialize():call_deferred("run")
func run():
	var game=Main.new()
	game.qa_mode=true;game.render_review=true;game.capture_directory="user://environment-unit-tests"
	game.size=Vector2(1280,720)
	root.add_child(game)
	game.set_process(false);game.set_physics_process(false)
	game.capture_frames=0
	game._process(.016)
	game.capture_frames=100
	var manifest=JSON.parse_string(FileAccess.get_file_as_string("res://assets/environment_v2/manifest.json"))
	check("All fourteen authored environment assets registered",manifest.assets.size()==14)
	check("Visual approval is not invented by the generator",not manifest.production_visual_approval)
	for asset in manifest.assets:
		var path:String="res://assets/environment_v2/"+asset.name+".glb"
		check("Actual imported replacement exists: "+asset.name,ResourceLoader.exists(path) and load(path) is PackedScene)
		check("Replacement has nonempty geometry and distinct material surfaces: "+asset.name,asset.triangles>0 and asset.surfaces>=2)
	var no_retired=true
	for path in game.asset_cache:
		if str(path).contains("assets/world/"):no_retired=false
	check("Active scene never loads retired blockout GLBs",no_retired)
	check("All four custom crew models are still instantiated",game.actors.size()==4)
	check("All resource locations retain their visuals",game.resource_visuals.size()==game.sim.resources.size())
	check("Native minimum resolution policy remains unchanged",game.scene_view.scaling_3d_scale==1.0)
	check("Close gameplay zoom preserved",is_equal_approx(game.camera.size,float(game.sim.contract.camera.size)*2.))
	check("Orthographic camera is not inside foreground geometry",is_equal_approx(game.camera.near,.05) and game.camera.position.distance_to(game.player_rig.position)>24.)
	var near_safe=true
	for tree in game.scenery_instances:
		var bounds:AABB=tree.mesh.get_aabb()
		for k in range(8):
			var p:Vector3=game.camera.to_local(tree.to_global(bounds.get_endpoint(k)))
			if p.z>=-game.camera.near:near_safe=false
	check("Every evergreen AABB is in front of the near plane",near_safe)
	check("Foreground cutaway is a Mobile-compatible shader",game.scenery_instances[0].mesh.surface_get_material(0) is ShaderMaterial)
	check("Tree cutaway state is tracked independently",game.scenery_cutaway.size()==game.scenery_instances.size())
	var tree:MeshInstance3D=game.resource_visuals[game.sim.resources[0].id]
	var old_position:Vector3=tree.position
	var focus:Vector3=game.xyz(game.sim.position)+Vector3(0,.95,0)
	tree.position=game.xyz(game.sim.position+Vector2(0,2.4))
	for i in range(4):game.update_foreground_visibility(focus,.1)
	check("Obscuring crown gradually cuts away",float(tree.get_instance_shader_parameter("cutaway"))>.9)
	tree.position=old_position+Vector3(20,0,0)
	for i in range(4):game.update_foreground_visibility(focus,.1)
	check("Clear sightline restores crown without respawning",is_zero_approx(float(tree.get_instance_shader_parameter("cutaway"))))
	var old_units:int=game.sim.resources[0].units
	game.sim.resources[0].units=0
	game.update_foreground_visibility(focus,.1)
	check("Camera cutaway cannot resurrect a depleted resource",not tree.visible)
	game.sim.resources[0].units=old_units;tree.position=old_position
	game._process(.016)
	check("Fog begins beyond the near gameplay plane",game.environment.fog_mode==Environment.FOG_MODE_DEPTH and game.environment.fog_depth_begin>=25.)
	check("Mobile tone mapping retains the reviewed ACES setting",game.environment.tonemap_mode==Environment.TONE_MAPPER_ACES)
	check("Mobile exposure preserves the reviewed snow highlight headroom",is_equal_approx(game.environment.tonemap_exposure,1.6) and is_equal_approx(game.environment.tonemap_white,6.0))
	check("Snowbanks use the shared actor-height sampler",Surface.height_at(Vector2(8.4,8.0))>Surface.height_at(Vector2.ZERO)+.2)
	check("Original first furnace upgrade preserved",game.sim.level==1 and is_equal_approx(game.sim.warmth(),4.5))
	check("Missing humans and animals remain honestly gated",game.population_view.nodes.is_empty() and not game.sim.threats_enabled)
	check("Actual native performance is still uncertified",not game.outpost_view.evidence(game.sim).native_4k60_certified)
	game.outpost_audio.stop_all()
	await create_timer(.35).timeout
	game.free()
	await process_frame
	await process_frame
	print(JSON.stringify({"suite":"environment_integration","passed":failures.is_empty(),"checks":checks,"failures":failures,"visual_quality_score":null,"independent_critic":false}))
	quit(0 if failures.is_empty() else 1)
