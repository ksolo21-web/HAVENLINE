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
	render_capture=OS.get_environment("HL15_CAPTURE")=="1"
	out_dir=OS.get_environment("HL15_PROBE_OUT")
	root.size=Vector2i(460,760)
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=Vector2(root.get_visible_rect().size)*Vector2(.25,.70)
	_phase("01-resumed-version12-partial")
	_check("actual funded Build15 profile loads without opening saw or drill",not field.persist_blocked and field.inventory.complete(Progress.GARAGE) and not field.inventory.complete(Progress.MACHINES.wood))
	_check("frozen old offer material refunded with no duplicated warehouse balances",field.inventory.carried.wood==128 and field.inventory.carried.stone==36 and field.inventory.stored.wood==3 and field.inventory.stored.stone==3 and field.inventory.carried.metal==0 and field.inventory.carried.coal==0)
	_check("raw quote offered immediately after historical pending funds refunded",field.inventory.remaining(Progress.TRUCK)=={"wood":24,"stone":16} and field.inventory.offer_open(Progress.TRUCK))
	var candidate_at: Vector3=field.offer_floors[Progress.TRUCK].global_position
	# A legacy save may reopen directly beside a buy marker. If already close,
	# leave its approach before initiating the new physical receipt.
	_check("returning player can walk clear and then reach existing truck plot",await _follow(Vector3(1.92,0,1.02),.20) and await _follow(candidate_at,.40))
	await _coast(88)
	_phase("02-paid-after-migration")
	_check("same refunded resources pay new bill exactly once",field.inventory.carried.wood==104 and field.inventory.carried.stone==20 and field.inventory.complete(Progress.TRUCK) and field.snow_truck.body.visible and field.inventory.vehicle_state().purchases==1)
	_check("no save quarantine",not field.persist_blocked)
	var data={"checks":check_results,"checkpoints":evidence,"uses_previous_native_funded_save":true,"new_fixture_grants":[]}
	var f:=FileAccess.open(out_dir.path_join("witness.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify(data,"\t"))
	f.close()
	field.sound.stop_playback()
	for count in 12:
		OS.delay_msec(20)
		await process_frame
	field.queue_free()
	await process_frame
	await process_frame
	quit(1 if false in check_results.values() else 0)
