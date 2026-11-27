extends "res://tests/field_route.gd"

const Inventory = preload("res://field_inventory.gd")
const Profile = preload("res://tests/lifecycle_test_profile.gd")
const Progress = preload("res://field_progression.gd")

var check_results := {}
var evidence: Array[Dictionary] = []
var active_ticks := 0
var joystick_ticks := 0
var render_capture := false

func _check(name: String, result: bool) -> void:
	check_results[name] = result
	if not result:
		push_error(name)

func _tick(moving := false) -> void:
	await physics_frame
	active_ticks += 1
	if moving:
		joystick_ticks += 1

func _coast(frames: int) -> void:
	steer(Vector2.ZERO)
	for frame in frames:
		await _tick()

func _follow(target: Vector3, distance: float, time_limit := 500) -> bool:
	for frame in time_limit:
		if move_to([target.x, target.z], distance):
			return true
		if field.persist_blocked or field.reset_time > 0.0:
			break
		await _tick(true)
	steer(Vector2.ZERO)
	return false

func _snapshot(label: String) -> void:
	var machines := {}
	for raw: String in Progress.MACHINES:
		var offer: String = Progress.MACHINES[raw]
		machines[raw] = {"paid":field.inventory.complete(offer),"open":field.inventory.offer_open(offer)}
	var stage := {
		"label":label, "tick":active_ticks, "position":pt(field.actor.global_position),
		"house_raw":field.inventory.stored.duplicate(),
		"carried":field.inventory.carried.duplicate(), "hand_products":field.inventory.hand_goods(),
		"houses_products":field.inventory.house_goods(),
		"garage_quote":field.inventory.costs[Progress.GARAGE],
		"garage_remaining":field.inventory.remaining(Progress.GARAGE),
		"garage_open":field.inventory.offer_open(Progress.GARAGE),
		"garage_built":field.inventory.complete(Progress.GARAGE),
		"garage_plot_visible":field.offer_floors[Progress.GARAGE].visible,
		"truck_offer_open":field.inventory.offer_open(Progress.TRUCK),
		"machines":machines, "objective":field.opening_hud.prompt.text,
		"blocked":field.persist_blocked, "error":field.persist_error,
		"zoom":field.get_zoom_ratio(), "native_camera":camera==root.get_camera_3d(),
	}
	evidence.append(stage)
	print("PLAYTEST ",JSON.stringify(stage))
	if render_capture:
		RenderingServer.force_draw(false, 1.0/60.0)
		root.get_texture().get_image().save_jpg(out_dir.path_join(label + ".jpg"),.90)

func _fund_test_items() -> bool:
	var desired := {"wood":146, "stone":13, "meat":36}
	var stone := OS.get_environment("HL15_RAW_STONE")
	if stone.is_valid_int():
		desired.stone = int(stone)
	for kind: String in desired:
		for index in range(int(field.inventory.carried[kind]), int(desired[kind])):
			if not field.inventory.collect("independent-early-garage:%s:%d"%[kind,index],kind):
				return false
	field._inventory_changed()
	return not field.persist_blocked


func _dock_tap(control: Control) -> bool:
	var r := control.get_global_rect()
	if not control.is_visible_in_tree() or not root.get_visible_rect().encloses(r):
		return false
	touch(6,r.get_center(),true)
	await _tick()
	touch(6,r.get_center(),false)
	await _tick()
	return true

func _dock_rows() -> Array:
	var result := []
	var dock = field.opening_hud.camp_dock
	for row in dock.commands:
		var button: Button = row[0]
		var width: float = button.get_theme_font("font").get_string_size(button.text,HORIZONTAL_ALIGNMENT_LEFT,-1,button.get_theme_font_size("font_size")).x
		result.append({"id":row[1],"label":button.text,"row_width":button.size.x,"approx_text_width":width,"global_rect":str(button.get_global_rect())})
	return result

func _select_row(id: String) -> bool:
	for row in field.opening_hud.camp_dock.commands:
		if row[1]==id:
			return await _dock_tap(row[0])
	return false

func _phase(label: String) -> void:
	_snapshot(label)
	var dock=field.opening_hud.camp_dock
	var truck_plot: Node3D=field.offer_floors[Progress.TRUCK]
	var e: Dictionary=evidence.back()
	e.truck_quote=field.inventory.costs[Progress.TRUCK].duplicate()
	e.truck_due=field.inventory.remaining(Progress.TRUCK)
	e.truck_position=pt(truck_plot.global_position)
	e.truck_plot_visible=truck_plot.visible
	e.truck_plot_distance=field.Reach.plot_distance(truck_plot,field.actor.global_position)
	e.truck_owned=field.inventory.complete(Progress.TRUCK)
	e.dock_title=dock.title.text if dock.sheet.visible else ""
	e.tracking=dock.tracking
	e.tracked_at=pt(dock.tracked_point()) if dock.tracked_point().is_finite() else []
	e.visit=field.carry.visit_target
	e.at_storehouse=field.depot.at_loading_area(field.actor.global_position)
	e.build_rows=_dock_rows() if dock.sheet.visible else []

func _closest_minerals() -> Dictionary:
	var source = field.get_node("WorldOneLandscape")
	var nearest := {"metal":{},"coal":{},"slate":{}}
	for x in range(-8,9):
		for z in range(-8,9):
			for row: Dictionary in source.describe_chunk(Vector2i(x,z)):
				if not nearest.has(row.kind):continue
				var p: Vector3=row.position
				var d:=p.length()
				if nearest[row.kind].is_empty() or d<float(nearest[row.kind].distance_m):
					nearest[row.kind]={"id":row.id,"position":pt(p),"distance_m":d}
	return nearest

func run() -> void:
	render_capture = OS.get_environment("HL15_CAPTURE")=="1"
	out_dir = OS.get_environment("HL15_PROBE_OUT")
	root.size = Vector2i(460,760)
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene = field
	camera = field.camera
	origin = Vector2(root.get_visible_rect().size)*Vector2(.25,.70)
	await _coast(16)
	_check("archived returning cooker-only profile opens", not field.persist_blocked and field.inventory.complete(Progress.MACHINES.meat) and not field.inventory.complete(Progress.MACHINES.wood))
	_check("conserved known wood and stone staged, ore and coal unavailable in pack",_fund_test_items() and field.inventory.carried.coal==0 and field.inventory.carried.metal==0)
	var dock=field.opening_hud.camp_dock
	_check("normal south gate touch route enters camp",await _follow(Vector3(0,0,4.10),.20) and field.field_env.is_inside_camp(field.actor.global_position))
	_check("Build button accepts touch",await _dock_tap(dock.build))
	_phase("01-build-menu-before-garage")
	_check("Camp offers garage navigation",await _dock_tap(dock.tabs.Camp) and await _select_row(Progress.GARAGE) and dock.tracking==Progress.GARAGE)
	var garage_plot: Node3D=field.offer_floors[Progress.GARAGE]
	_check("touch route reaches garage price pad",await _follow(garage_plot.global_position,.41))
	await _coast(155)
	_check("180 wood and 120 stone buys garage with no workshop unlocks required",field.inventory.complete(Progress.GARAGE) and field.snow_truck.garage.visible and not field.inventory.complete(Progress.MACHINES.wood))
	_phase("02-garage-bought")
	_check("after-garage Build touch",await _dock_tap(dock.build))
	_phase("03-build-menu-after-garage")
	_check("the archived fixture exposes truck in the Build list",_dock_rows().any(func(row):return row.id==Progress.TRUCK))
	_check("after-garage Camp touch",await _dock_tap(dock.tabs.Camp))
	_phase("04-camp-menu-truck-quote")
	_check("Camp offer remains touch-selectable",await _select_row(Progress.TRUCK) and dock.tracking==Progress.TRUCK)
	var truck_plot: Node3D=field.offer_floors[Progress.TRUCK]
	_check("actual touch reaches distinct truck plot", await _follow(truck_plot.global_position,.43))
	_phase("05-truck-physical-plot")
	await _coast(160)
	_phase("06-truck-unfunded-minerals")
	_check("truck consumed available wood and stone without storehouse intercept",field.inventory.remaining(Progress.TRUCK).wood==0 and field.inventory.remaining(Progress.TRUCK).stone==0 and not field.depot.at_loading_area(field.actor.global_position) and field.inventory.stored==evidence[0].house_raw)
	_check("uncollected mineral costs are the only unpaid portion",field.inventory.remaining(Progress.TRUCK).metal==24 and field.inventory.remaining(Progress.TRUCK).coal==12 and not field.snow_truck.owned())
	_check("saves persist cleanly",not field.persist_blocked)
	var report := {"checks":check_results,"checkpoints":evidence,"touch_move_ticks":joystick_ticks,"nearest_banks":_closest_minerals(),"fixture_deposits_staged":["wood","stone","meat"],"separate_phone_device":false,"window":[root.size.x,root.size.y],"renderer":RenderingServer.get_video_adapter_name()}
	var f:=FileAccess.open(out_dir.path_join("witness.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"\t"))
	f.close()
	await Profile.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	await process_frame
	quit(1 if false in check_results.values() else 0)
