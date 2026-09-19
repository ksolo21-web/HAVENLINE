extends "res://tests/capture_task02.gd"
# Read-only diagnostic: separately inspect scene light sources and resolved settings.
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
	var water: MeshInstance3D=game.outpost_view.lake
	var original: Material=water.material_override
	var lights: Array=[];var light_records: Array=[]
	for light in game.world.find_children("*","Light3D",true,false):
		lights.append(light)
		light_records.append({"path":str(light.get_path()),"type":light.get_class(),"position":str(light.global_position),"energy":light.light_energy,"visible":light.visible})
	await stable_snap("original-all-lights")
	for light in lights:
		if light is OmniLight3D:light.visible=false
	await stable_snap("original-directional-only")
	for light in lights:light.visible=false
	await stable_snap("original-no-direct-lights")
	var mat:=StandardMaterial3D.new();mat.albedo_color=Color(.002,.44,.77);mat.roughness=1.0;mat.metallic_specular=0.0
	water.material_override=mat
	await stable_snap("constant-ambient-only")
	game.outpost_view.environment.ambient_light_energy=0.0
	await stable_snap("constant-no-light")
	game.sun.visible=true
	await stable_snap("constant-directional-only")
	game.sun.shadow_enabled=false
	await stable_snap("constant-directional-no-shadow")
	game.sun.visible=false
	for light in lights:
		if light is OmniLight3D:light.visible=true
	await stable_snap("constant-omni-only")
	for light in lights:light.visible=false
	var shader:=ShaderMaterial.new();shader.shader=Shader.new()
	shader.shader.code="shader_type spatial;render_mode specular_disabled,ambient_light_disabled;void fragment(){ALBEDO=vec3(.001,.16,.55);}void light(){DIFFUSE_LIGHT+=ALBEDO*LIGHT_COLOR*ATTENUATION*max(dot(NORMAL,LIGHT),0.0)/3.14159265;}"
	water.material_override=shader;game.sun.visible=true
	await stable_snap("custom-directional-no-shadow")
	var settings={}
	for p in ProjectSettings.get_property_list():
		var n:String=p.name
		if n.begins_with("rendering/") and ("vertex" in n or "light" in n or "normal" in n):settings[n]=ProjectSettings.get_setting(n)
	var report={"task":"T02-light-source-diagnosis","captures":records,"lights":light_records,"resolved_settings":settings,"shader_custom_light_tested":true,"diagnostic_only":true,"renderer":RenderingServer.get_current_rendering_method()}
	var file=FileAccess.open(output.path_join("diagnostic.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t"));file.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
