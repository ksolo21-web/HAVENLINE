extends "res://tests/field_route.gd"

const Session = preload("res://tests/lifecycle_test_profile.gd")
var compass
var checks := {}
var samples := {}
var capture_dir := OS.get_environment("HAVENLINE_COMPASS_CAPTURE")

func verify(id: String, ok: bool) -> void:
	checks[id] = ok
	if not ok: push_error(id)

func place(feet: Vector3) -> void:
	field.actor.global_position = feet
	field.actor.velocity = Vector3.ZERO
	field.camera.global_position = feet + field.camera_follow_offset
	compass.refresh()

func sample(id: String) -> void:
	samples[id] = {"gate":compass.route.gate_index,"distance":compass.route.distance,
		"waypoint":str(compass.route.direction_target),"arrow_degrees":rad_to_deg(compass.needle.rotation),
		"visible":compass.visible,"label":compass.label.text}

func trace_route(from: Vector2, paid: bool) -> bool:
	var p := from
	var route = compass.route
	for i in 1500:
		if not route.update(field,p): return false
		if not paid and route.distance<.3: return true
		var t: Vector2 = route.direction_target
		var next := p.move_toward(t,.205)
		if next.is_equal_approx(p): return false
		var feet := Vector3(next.x,0,next.y)
		var physical: Vector3 = field.lakeshore.constrain_motion(Vector3(p.x,0,p.y),feet,float(field.layout.actor_radius))
		if physical.distance_to(feet)>.012: return false
		if paid and field.field_env.is_inside_camp(feet):
			var entrance: Vector3 = field.gates[route.gate_index].global_position
			return feet.distance_to(entrance)<.85
		p = next
	return false

func walk_gate(which: int) -> bool:
	var gate: Node3D = field.gates[which]
	var outward := Vector3.BACK if which==0 else Vector3.RIGHT
	place(gate.global_position+outward*3.05)
	for i in 180:
		compass.refresh()
		if field.field_env.is_inside_camp(field.actor.global_position):
			steer(Vector2.ZERO)
			return not compass.visible and gate.angle > .85
		if compass.route.gate_index != which or not compass.visible: break
		# Follow exactly the displayed angle using touchscreen input and the real gate colliders.
		steer(Vector2.RIGHT.rotated(compass.needle.rotation))
		await physics_frame
	steer(Vector2.ZERO)
	return false

func screen_check(id: String,pixels: Vector2i,ratio: float) -> void:
	if DisplayServer.get_name() == "headless":
		# The root headless window has no OS resize events. Update the same project
		# display handler before querying the real gameplay camera and HUD.
		root.size = pixels
		field.graphics.refresh_window()
	else:
		root.size = pixels
	for i in 4: await process_frame
	field.set_zoom_ratio(ratio)
	place(Vector3(500,0,500))
	compass.reflow()
	compass.refresh()
	var hud = field.opening_hud
	var safe: Rect2 = hud._safe_rect()
	var chip: Rect2 = compass.get_global_rect()
	verify(id+" fits safe canvas and clears controls", safe.encloses(chip) and not chip.intersects(hud.quality.get_global_rect()) and not chip.intersects(hud.objective.get_global_rect()) and not chip.intersects(hud.level_continue.get_global_rect()))
	var all_text_fits := true
	var max_width := 0.
	for caption in ["Camp plot", "Camp gate"]:
		for count in [1,9,99,101,724,9999]:
			var width: float = compass.label.get_theme_font("font").get_string_size("%s  %d m"%[caption,count], HORIZONTAL_ALIGNMENT_LEFT,-1,compass.label.get_theme_font_size("font_size")).x
			max_width=maxf(max_width,width)
			all_text_fits = all_text_fits and compass.label.position.x+width+compass.LABEL_RIGHT <= compass.size.x
	verify(id+" both complete labels fit at 1, 101, world limit and 9999 metres",all_text_fits)
	verify(id+" rotated arrow clears the distance in all eight directions",compass.needle.position.x+13.<compass.label.position.x and compass.needle.position.y>13. and compass.needle.position.y+13.<compass.size.y)
	var mid: Vector2 = field.camera.unproject_position(field.actor.global_position)
	var aim: Vector2 = compass.route.direction_target
	var actual: Vector2 = mid.direction_to(field.camera.unproject_position(Vector3(aim.x,0,aim.y)))
	verify(id+" uses real camera heading", actual.dot(Vector2.RIGHT.rotated(compass.needle.rotation))>.999)
	verify(id+" arrow and distance are accessible without color", "metres" in compass.label.accessibility_name and compass.mouse_filter==Control.MOUSE_FILTER_IGNORE and not compass.label.text.is_empty())
	if not capture_dir.is_empty() and DisplayServer.get_name()!="headless":
		# Allow both the font server and the existing objective HUD to commit the
		# current scene position before reading the native framebuffer.
		field._refresh_hud_field(false)
		await process_frame
		await process_frame
		RenderingServer.force_draw()
		var img := root.get_texture().get_image()
		img.save_jpg(capture_dir.path_join(id+".jpg"),.94)
	sample(id)
	samples[id]["font_max_advance"]=max_width
	samples[id]["panel_width"]=compass.size.x
	samples[id]["physical_window"]=str(root.size)

func run() -> void:
	if Session.isolated(self,"res://tests/qa_field_navigation.gd"): return
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	for i in 4: await physics_frame
	camera = field.camera
	compass = field.opening_hud.get_node("HomeCompass")
	var plot: Vector3 = field.field_env.buy_anchor.global_position
	place(Vector3(0,0,63))
	verify("unpaid marker leads to exact first plot", compass.visible and compass.destination=="Camp plot" and compass.route.direction_target.is_equal_approx(Vector2(plot.x,plot.z)) and absf(compass.route.distance-field.actor.position.distance_to(plot))<.01)
	sample("first-plot")
	place(plot)
	verify("plot arrival hides marker", not compass.visible)
	verify("unpaid route goes around west inlet", trace_route(Vector2(-52,19),false))
	for i in int(field.inventory.costs.center_hearth.wood):
		field.inventory.collect("compass-camp-fixture-"+str(i),"wood")
		field.inventory.payment("center_hearth","wood",false)
	field._finish_purchase("center_hearth")
	field._apply_hearth(true,false)
	field.reveal_countdown = -1.
	for stage in [1,2,3]:
		field.field_env.set_perimeter(stage,false)
		for i in 2:
			var gate: Node3D = field.gates[i]
			var outward := Vector3.BACK if i==0 else Vector3.RIGHT
			place(gate.global_position+outward*5.)
			verify("stage %d gate %d current position and distance"%[stage,i],compass.visible and compass.route.gate_index==i and absf(compass.route.distance-5.)<.1)
			sample("stage-%d-gate-%d"%[stage,i])
		var all_clear:=true
		for origin_: Vector2 in [Vector2(-52,19),Vector2(-44,36),Vector2(-6,-12),Vector2(2,-25),Vector2(-15,1),Vector2(3,45),Vector2(22,-9)]:
			all_clear = trace_route(origin_,true) and all_clear
		verify("stage %d all 7 outside routes stay dry and enter a real doorway"%stage,all_clear)
	place(Vector3(0,0,14))
	field.gates[0].set_earned(false)
	compass.refresh()
	verify("disabled gate reroutes to remaining real entrance",compass.visible and compass.route.gate_index==1)
	field.gates[1].set_earned(false)
	compass.refresh()
	verify("no offered gate with both entrances unavailable",not compass.visible)
	field.gates[0].set_earned(true)
	field.gates[1].set_earned(true)
	field.field_env.set_perimeter(1,false)
	for i in 2:
		verify("following displayed heading opens and enters physical gate %d"%i,await walk_gate(i))
	field.set_physics_process(false)
	place(Vector3(0,0,0))
	verify("home hides guide", not compass.visible)
	place(Vector3(500,0,500))
	verify("far corner has a reach distance",compass.visible and compass.meters>690 and compass.meters<710)
	field.player_hp=0
	compass.refresh()
	verify("dead player has no guide",not compass.visible)
	field.player_hp=field.MAX_HP
	await screen_check("Fold7-cover",Vector2i(360,840),1.)
	await screen_check("Fold7-inner",Vector2i(492,546),2.)
	await screen_check("Fold7-landscape",Vector2i(840,360),1.)
	var last: float = compass.needle.rotation
	field.camera.rotate_y(.38)
	compass.refresh()
	verify("heading reacts to live camera yaw",absf(angle_difference(last,compass.needle.rotation))>.15)
	print("FIELD_NAVIGATION ",JSON.stringify({"checks":checks,"samples":samples}))
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 3: await process_frame
	quit(int(checks.values().has(false)))
