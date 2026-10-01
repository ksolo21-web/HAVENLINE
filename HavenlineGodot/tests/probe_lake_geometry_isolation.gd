extends "res://tests/capture_task02.gd"
# Explicit diagnostic overrides; never production artwork or critic approval.
func stable_snap(label: String):
	for i in range(2):
		await process_frame
		await RenderingServer.frame_post_draw
	await snap(label)
func run():
	DirAccess.make_dir_recursive_absolute(output)
	game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_frames=100
	game.capture_directory=output;game.size=Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	normal_at(Vector2(0,-9));normal_at(Vector2(0,-9))
	focus_at(Vector2(0,-10.8),Vector3(0,25,24),22.0)
	for animation in game.world.find_children("*","AnimationPlayer",true,false): animation.pause()
	var water: MeshInstance3D=game.outpost_view.lake
	var original: ShaderMaterial=water.material_override
	var code: String=original.shader.code
	await stable_snap("baseline")
	for node in game.world.find_children("*","GeometryInstance3D",true,false):
		if node!=water:node.visible=false
	await stable_snap("water-only-original")
	var no_normal: String=code
	var start: int=no_normal.find(" NORMAL_MAP=")
	var end: int=no_normal.find(" NORMAL_MAP_DEPTH=.4;",start)+" NORMAL_MAP_DEPTH=.4;".length()
	no_normal=no_normal.substr(0,start)+no_normal.substr(end)
	var variants={
		"constant-albedo":code.replace("ALBEDO=pow(base,vec3(2.2));","ALBEDO=vec3(.001,.16,.55);"),
		"flat-normal":no_normal,
		"constant-albedo-flat-normal":no_normal.replace("ALBEDO=pow(base,vec3(2.2));","ALBEDO=vec3(.001,.16,.55);"),
		"unlit-constant":"shader_type spatial;render_mode unshaded;void fragment(){ALBEDO=vec3(.001,.16,.55);}",
		"original-unlit":code.replace("render_mode diffuse_burley, specular_disabled, ambient_light_disabled;","render_mode unshaded;").replace("EMISSION=ALBEDO*stable_ambient_color.rgb*clamp(stable_ambient_energy,0.,1.);","")
	}
	for label in variants:
		var mat: ShaderMaterial=original.duplicate();mat.shader=Shader.new();mat.shader.code=variants[label]
		water.material_override=mat;await stable_snap(label)
	var standard:=StandardMaterial3D.new();standard.albedo_color=Color(.002,.44,.77);standard.roughness=.54;standard.metallic_specular=.0
	water.material_override=standard;await stable_snap("standard-lit-constant")
	var report={"task":"T02-water-geometry-isolation","captures":records,"water_faces":water.mesh.get_faces().size()/3,"water_transform":str(water.global_transform),"surface_count":water.mesh.get_surface_count(),"renderer":RenderingServer.get_current_rendering_method(),"diagnostic_only":true}
	var file=FileAccess.open(output.path_join("diagnostic.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t"));file.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
