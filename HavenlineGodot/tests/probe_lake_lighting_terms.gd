extends "res://tests/capture_task02.gd"
# Disclosed test-only material variations; never an approved runtime fallback.
func stable_snap(label: String):
	for i in range(4):
		await process_frame
		await RenderingServer.frame_post_draw
	await snap(label)
func run():
	DirAccess.make_dir_recursive_absolute(output)
	game=Main.new();game.qa_mode=true;game.render_review=false;game.capture_frames=100
	game.capture_directory=output;game.size=Vector2(3840,2160)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	normal_at(Vector2(0,-9))
	focus_at(Vector2(0,-10.8),Vector3(0,25,24),22.0)
	for animation in game.world.find_children("*","AnimationPlayer",true,false): animation.pause()
	var original: ShaderMaterial=game.outpost_view.lake_material
	var code: String=original.shader.code
	await stable_snap("original-lit")
	var modes={
		"no-specular":code.replace("render_mode diffuse_burley, specular_schlick_ggx;","render_mode diffuse_burley, specular_disabled;"),
		"no-ambient":code.replace("render_mode diffuse_burley, specular_schlick_ggx;","render_mode diffuse_burley, specular_disabled, ambient_light_disabled;"),
		"lambert":code.replace("render_mode diffuse_burley, specular_schlick_ggx;","render_mode diffuse_lambert, specular_disabled;"),
		"custom-diffuse":code+"\nvoid light(){DIFFUSE_LIGHT += ALBEDO * LIGHT_COLOR * ATTENUATION * max(dot(NORMAL,LIGHT),0.0)/3.14159265;}\n",
		"no-shadow-receive":code.replace("render_mode diffuse_burley, specular_schlick_ggx;","render_mode diffuse_burley, specular_schlick_ggx, shadows_disabled;"),
		"no-specular-no-normal":code.replace("render_mode diffuse_burley, specular_schlick_ggx;","render_mode diffuse_lambert, specular_disabled;")
	}
	var normal_start: int=modes["no-specular-no-normal"].find(" NORMAL_MAP=")
	var normal_end: int=modes["no-specular-no-normal"].find(" NORMAL_MAP_DEPTH=.4;",normal_start)+" NORMAL_MAP_DEPTH=.4;".length()
	modes["no-specular-no-normal"]=modes["no-specular-no-normal"].substr(0,normal_start)+modes["no-specular-no-normal"].substr(normal_end)
	for label in modes:
		var material: ShaderMaterial=original.duplicate();material.shader=Shader.new();material.shader.code=modes[label]
		game.outpost_view.lake.material_override=material
		await stable_snap(label)
	game.outpost_view.lake.material_override=original
	await stable_snap("original-restored")
	var file=FileAccess.open(output.path_join("diagnostic.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"task":"T02-water-lighting-diagnosis","source_runtime":"0b75bd8366f680df31b708ed181a007de201eef1","renderer":RenderingServer.get_current_rendering_method(),"captures":records,"diagnostic_only":true,"runtime_shader_unchanged":true,"four_settle_frames_per_change":true},"\t"));file.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
