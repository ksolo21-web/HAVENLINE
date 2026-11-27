extends SceneTree
var field
var checks := {}
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	field=load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	root.add_child(field)
	for i in 5: await physics_frame
	var nav=field.opening_hud.get_node("HomeCompass")
	checks["guide hidden within established perimeter"]=field.camp_active and not nav.visible
	field.actor.global_position=Vector3(112,0,32)
	field.camera.position=field.actor.position+field.camera_follow_offset
	for i in 3: await physics_frame
	nav.refresh()
	var title: String=nav.label.text
	var area: Rect2=nav.get_global_rect()
	var visible_width: float=nav.TYPE.get_string_size(title,HORIZONTAL_ALIGNMENT_LEFT,-1,nav.TYPE_SIZE).x
	checks["three-digit distance to an actual gate"]=nav.visible and nav.route.gate_index>=0 and nav.meters>=100 and title.ends_with(" m")
	checks["every glyph fits the shipping panel"]=visible_width<=nav.label.size.x and (nav.label.position.x+visible_width < nav.size.x-6)
	checks["guide remains clear of touch steering"]=nav.mouse_filter==Control.MOUSE_FILTER_IGNORE
	var result={"text":title,"meters":nav.meters,"glyph_advance":visible_width,"panel_width":area.size.x,"content_width":nav.label.size.x,"checks":checks,"passed":not checks.values().has(false)}
	print("GUIDE ",JSON.stringify(result))
	field.sound.stop_playback()
	for i in 14:
		OS.delay_msec(20)
		await process_frame
	field.queue_free()
	for i in 4: await process_frame
	quit(int(not result.passed))
