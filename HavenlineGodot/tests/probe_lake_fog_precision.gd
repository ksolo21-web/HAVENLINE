extends "res://tests/capture_task02.gd"
func stable_snap(label: String):
	for i in range(3):
		await process_frame
		await RenderingServer.frame_post_draw
	await snap(label)
func run():
	DirAccess.make_dir_recursive_absolute(output)
	game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_frames=100
	game.capture_directory=output;game.size=Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	normal_at(Vector2(0,-9));focus_at(Vector2(0,-10.8),Vector3(0,25,24),22.0)
	for animation in game.world.find_children("*","AnimationPlayer",true,false): animation.pause()
	var original:ShaderMaterial=game.outpost_view.lake.material_override
	var code:String=original.shader.code
	await stable_snap("original")
	var variants={
		"fog-disabled":code.replace("ambient_light_disabled;","ambient_light_disabled, fog_disabled;"),
		"forced-world-normal":code.replace("void fragment(){","void fragment(){\nNORMAL=normalize((VIEW_MATRIX*vec4(0.,1.,0.,0.)).xyz);"),
		"manual-fragment-light":"shader_type spatial;render_mode unshaded;uniform float sim_time=0.;varying vec2 world_xz;void vertex(){world_xz=(MODEL_MATRIX*vec4(VERTEX,1.)).xz;}void fragment(){ALBEDO=vec3(.001,.16,.55);}",
		"standard-fog-disabled":"shader_type spatial;render_mode diffuse_lambert, specular_disabled, fog_disabled;void fragment(){ALBEDO=vec3(.001,.16,.55);ROUGHNESS=1.;SPECULAR=0.;NORMAL=normalize((VIEW_MATRIX*vec4(0.,1.,0.,0.)).xyz);}"
	}
	for label in variants:
		var mat:ShaderMaterial=original.duplicate();mat.shader=Shader.new();mat.shader.code=variants[label]
		game.outpost_view.lake.material_override=mat;await stable_snap(label)
	var file=FileAccess.open(output.path_join("diagnostic.json"),FileAccess.WRITE);file.store_string(JSON.stringify({"captures":records,"diagnostic_only":true,"renderer":RenderingServer.get_current_rendering_method()},"\t"));file.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
