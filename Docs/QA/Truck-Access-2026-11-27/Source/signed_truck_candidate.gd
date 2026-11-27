extends SceneTree
var field
var camera: Camera3D
var origin: Vector2
var touch_held := false
var last_input := Vector2.ZERO
var out_dir := ""

func _initialize() -> void:
	run.call_deferred()

func touch(id:int,pos:Vector2,pressed:bool)->void:
	var e:=InputEventScreenTouch.new()
	e.index=id
	e.position=pos
	e.pressed=pressed
	root.push_input(e,true)

func steer(direction:Vector2)->void:
	if direction.is_zero_approx():
		if touch_held:
			touch(0,origin,false)
			touch_held=false
			last_input=Vector2.ZERO
		return
	if not touch_held:
		touch(0,origin,true)
		touch_held=true
	if last_input.distance_to(direction)<.006: return
	var e:=InputEventScreenDrag.new()
	e.index=0
	e.position=origin+direction*82.
	e.relative=(direction-last_input)*82.
	e.screen_relative=e.relative
	root.push_input(e,true)
	last_input=direction

func pt(x:Vector3)->Array:return [x.x,x.y,x.z]

func move_to(p:Array,tol:float)->bool:
	var pos:Vector3=field.actor.global_position
	var delta:=Vector3(float(p[0])-pos.x,0.,float(p[1])-pos.z)
	if delta.length()<=tol:
		steer(Vector2.ZERO);return true
	var right:=camera.global_basis.x
	var near:=right.cross(Vector3.UP)
	var d:=Vector2(delta.dot(right),delta.dot(near)).normalized()
	steer(d*clampf(delta.length()*1.25,.3,.98))
	return false



const Inventory = preload("res://field_inventory.gd")
const Progress = preload("res://field_progression.gd")

var check_results := {}
var evidence: Array[Dictionary] = []
var active_ticks := 0
var joystick_ticks := 0
var render_capture := false
var first_launch := {}

func _check(name: String, result: bool) -> void:
	check_results[name] = result
	if not result:
		push_error(name)

func _tick(moving := false) -> void:
	await physics_frame
	active_ticks += 1
	if is_instance_valid(field) and field.field_ready:
		for flight: Dictionary in field.carry.flights:
			var dest: String=flight.to
			if dest in [Progress.GARAGE,Progress.TRUCK] and not first_launch.has(dest):
				first_launch[dest]={"simulation_seconds":field.simulation_time,"tick":active_ticks,"source":flight.from,"kind":flight.kind}
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


func _purchase_timing(id: String, max_frames: int) -> Dictionary:
	var origin_tick := active_ticks
	var before: Dictionary=field.inventory.remaining(id)
	var result := {"first_commit_ticks":-1,"complete_ticks":-1}
	for step in max_frames:
		await _tick()
		if result.first_commit_ticks<0 and before != field.inventory.remaining(id):
			result.first_commit_ticks=active_ticks-origin_tick
		if field.inventory.complete(id):
			result.complete_ticks=active_ticks-origin_tick
			break
	return result

func _stocked(at_least: Dictionary, max_frames: int) -> bool:
	for step in max_frames:
		if at_least.keys().all(func(k):return field.inventory.carried[k]==0 and field.inventory.stored[k]>=at_least[k]):
			return true
		await _tick()
	return false

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
	_check("archived cooker-only camp loaded",not field.persist_blocked and field.inventory.complete(Progress.MACHINES.meat) and not field.inventory.complete(Progress.MACHINES.wood))
	_check("known raw goods staged without ore or coal",_fund_test_items() and field.inventory.carried.metal==0 and field.inventory.carried.coal==0)
	var dock=field.opening_hud.camp_dock
	_check("saved camp enters by touch through the south gate",await _follow(Vector3(0,0,4.10),.20) and field.field_env.is_inside_camp(field.actor.global_position))
	_check("physical south apron walk via the west lane",await _follow(Vector3(-2.20,0,2.80),.24) and await _follow(Vector3(-3.05,0,-1.18),.32))
	_check("normal storehouse walk-up banks all tender",await _stocked({"wood":42,"stone":28},425))
	_phase("01-bank-funded-by-walk-up")
	var stock_before: Dictionary=field.inventory.stored.duplicate()
	_check("normal Build touch surfaces garage first",await _dock_tap(dock.build) and not dock.commands.is_empty() and dock.commands[0][1]==Progress.GARAGE)
	_check("reachable garage guide selected by touch",await _select_row(Progress.GARAGE) and dock.tracking==Progress.GARAGE)
	var garage_plot: Node3D=field.offer_floors[Progress.GARAGE]
	_check("garage plot reached by walking outside the hearth radius",await _follow(Vector3(-1.90,0,2.80),.30) and await _follow(Vector3(1.85,0,3.77),.26) and await _follow(garage_plot.global_position,.45))
	var garage_timing:=await _purchase_timing(Progress.GARAGE,220)
	_phase("02-warehouse-funded-garage")
	_check("garage takes 180 wood and 120 stone entirely from storage",field.inventory.complete(Progress.GARAGE) and field.inventory.stored.wood==stock_before.wood-18 and field.inventory.stored.stone==stock_before.stone-12 and field.inventory.carried.wood==0 and field.inventory.carried.stone==0 and not field.inventory.complete(Progress.MACHINES.wood))
	_check("garage opens separate truck and it is first in Build",await _dock_tap(dock.build) and not dock.commands.is_empty() and dock.commands[0][1]==Progress.TRUCK)
	_phase("03-build-quote")
	var row: Button=dock.commands[0][0]
	var text_extent:=row.get_theme_font("font").get_string_size(row.text,HORIZONTAL_ALIGNMENT_LEFT,-1,row.get_theme_font_size("font_size")).x
	var min_width:=text_extent+row.get_theme_stylebox("normal").get_content_margin(SIDE_LEFT)+row.get_theme_stylebox("normal").get_content_margin(SIDE_RIGHT)
	_check("complete quote fits button and physical safe viewport",root.get_visible_rect().encloses(row.get_global_rect()) and min_width<=row.size.x and row.text.contains("240 wood") and row.text.contains("160 stone"))
	_check("truck guide selected by touch",await _select_row(Progress.TRUCK) and dock.tracking==Progress.TRUCK)
	var truck_plot: Node3D=field.offer_floors[Progress.TRUCK]
	_check("physical truck plot reached via normal touch",await _follow(truck_plot.global_position,.43))
	var truck_timing:=await _purchase_timing(Progress.TRUCK,220)
	_phase("04-warehouse-funded-truck")
	var whole_bill: Dictionary=field.inventory.costs[Progress.TRUCK].duplicate()
	_check("240 wood and 160 stone paid entirely from warehouse with ore-free quote",whole_bill=={"wood":24,"stone":16} and field.inventory.complete(Progress.TRUCK) and field.inventory.stored.wood==stock_before.wood-42 and field.inventory.stored.stone==stock_before.stone-28 and field.inventory.carried.wood==0 and field.inventory.carried.stone==0)
	var truck=field.snow_truck
	_check("truck parked at 80 HP while saw and drill remain unbuilt",truck.body.visible and truck.parked() and field.inventory.vehicle_state().hp==truck.MAX_HP and not field.inventory.complete(Progress.MACHINES.wood) and not field.inventory.complete(Progress.MACHINES.stone))
	var approach:=true
	for local:Vector3 in [Vector3(1.2,0,6.63),Vector3(0,0,6.12),Vector3(0,0,4.48)]:
		if not await _follow(truck.garage.to_global(local),.17):
			approach=false
			break
	_check("driver walks from paid pad to rear of installed garage",approach)
	await _coast(5)
	_phase("05-drive-button-1x")
	_check("Drive touch starts truck",truck.action.text=="Drive" and await _dock_tap(truck.action) and truck.mounted)
	await _coast(4)
	_phase("06-mounted-1x")
	_check("vehicle remains parked and scene has current gameplay camera",truck.parked() and camera==root.get_camera_3d())
	if render_capture:
		field.set_zoom_ratio(2.0)
		await _coast(2)
		_phase("07-mounted-2x")
	_check("saves still persist, no cold-profile block",not field.persist_blocked)
	var visible_spend: Array=field.events.filter(func(e):return e.event in ["spend_wood","spend_stone","upgrade_build","build","truck_enter"])
	var report:={"transfer_first_launch":first_launch,"spend_events":visible_spend,"checks":check_results,"checkpoints":evidence,"touch_move_ticks":joystick_ticks,"garage_timing":garage_timing,"truck_timing":truck_timing,"fixture_deposits_staged":["wood","stone","meat"],"stock_before_vehicle_payments":stock_before,"window":[root.size.x,root.size.y],"renderer":RenderingServer.get_video_adapter_name()}
	var f:=FileAccess.open(out_dir.path_join("witness.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"\t"))
	f.close()
	field.sound.stop_playback()
	for count in 12:
		OS.delay_msec(20)
		await process_frame
	field.queue_free()
	await process_frame
	await process_frame
	quit(1 if false in check_results.values() else 0)
