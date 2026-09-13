extends "res://tests/capture_task02.gd"
# Diagnostic-only overrides. No production rendering settings or art are changed.
func run():
	DirAccess.make_dir_recursive_absolute(output)
	game=Main.new();game.qa_mode=true;game.render_review=true;game.capture_frames=100
	game.capture_directory=output;game.size=Vector2(1280,720)
	root.add_child(game);game.set_process(false);game.set_physics_process(false)
	normal_at(Vector2(0,-9))
	focus_at(Vector2(0,-13.85),Vector3(0,25,24),19.0)
	for a in game.world.find_children("*","AnimationPlayer",true,false):a.pause()
	await snap("baseline")
	game.environment.fog_enabled=false;await snap("no-fog")
	game.environment.fog_enabled=true
	game.sun.shadow_enabled=false;await snap("no-sun-shadow")
	game.sun.shadow_enabled=true
	var original: ShaderMaterial=game.outpost_view.lake_material
	var code: String=original.shader.code
	var no_normal: ShaderMaterial=original.duplicate()
	no_normal.shader=Shader.new()
	var start:=code.find(" NORMAL_MAP=")
	var finish:=code.find(" NORMAL_MAP_DEPTH=.4;",start)+" NORMAL_MAP_DEPTH=.4;".length()
	assert(start>=0 and finish>start)
	no_normal.shader.code=code.substr(0,start)+code.substr(finish)
	game.outpost_view.lake.material_override=no_normal
	await snap("no-normal-map")
	var flat: ShaderMaterial=original.duplicate();flat.shader=Shader.new()
	flat.shader.code=code.replace("render_mode diffuse_burley, specular_schlick_ggx;","render_mode unshaded;")
	game.outpost_view.lake.material_override=flat
	await snap("unlit-albedo")
	game.outpost_view.lake.material_override=original
	game.outpost_view.terrain.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	await snap("no-terrain-shadow")
	game.outpost_view.terrain.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for mesh in game.world.find_children("*","GeometryInstance3D",true,false):
		if mesh!=game.outpost_view.lake and mesh!=game.outpost_view.terrain:mesh.visible=false
	await snap("water-and-ground-only")
	var f=FileAccess.open(output.path_join("diagnostic.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"source_runtime":"0b75bd8366f680df31b708ed181a007de201eef1","renderer":RenderingServer.get_current_rendering_method(),"captures":records,"diagnostic_only":true,"no_quality_or_fps_approval":true,"lake_triangles":game.outpost_view.evidence(game.sim).lake_triangles},"\t"));f.close()
	game.outpost_audio.stop_all();await create_timer(.35).timeout;game.free();await process_frame;quit()
