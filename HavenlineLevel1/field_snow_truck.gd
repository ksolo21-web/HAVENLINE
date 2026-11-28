extends Node3D

const Art = preload("res://field_snow_truck_art.gd")
const LooseArt = preload("res://field_art.gd")
const Progress = preload("res://field_progression.gd")
const FieldEnemy = preload("res://field_enemy.gd")
const ResourceRock = preload("res://resource_rock.gd")
const MAX_HP := 80
const GARAGE_X := 5.85
const HALF_DOOR := 1.44
const BAY_WIDTH := 1.40
const BAY_DEPTH := 5.18
const VEHICLE_STOP_LAYER := 2
const FRONT := 2.38
const BACK := 1.48
const BODY_FRONT := 1.67
const HALF_WIDTH := 1.18
const BOARDING_REACH := 1.40
const BLADE_HALF_SPAN := .55
const BLADE_HEIGHT := .21
const BLADE_DEPTH := -1.78
const BLADE_RADIUS := .59
const MAX_SPEED := 8.2
const REVERSE_SPEED := 4.2
const TRACK_SPACING := .61
const PARK := Vector3(0,0,2.72)
const GARAGE_ALIGNMENT_POINT := Vector3(0,0,-3.68)

var world
var body: CharacterBody3D
var garage: Node3D
var art: Node3D
var door: StaticBody3D
var rear_stop: StaticBody3D
var control: HBoxContainer
var hud: VBoxContainer
var status: Label
var health: ProgressBar
var action: Button
var stow: Button
var mounted := false
var opening := 0.0
var drive_speed := 0.0
var wants_to_exit_bay := false
var bay_approach := ""
var bay_reverse := false
var wheel_angle := 0.0
var blade_angle := 0.0
var track_distance := 0.0
var damage_grace := 0.0
var attack_delay := 0.0
var park_elapsed := 0.0
var actor_layer := 0
var actor_mask := 0
var loaded_totals: Dictionary = {}
var initialized := false
var held_buttons: Dictionary = {}
var collision_probe: PhysicsShapeQueryParameters3D
var eject_probe: PhysicsShapeQueryParameters3D
var vehicle_nonblocking_enemies: Dictionary = {}

func install(host) -> void:
	world = host
	name = "SnowTruckWorkshop"
	garage = Art.garage()
	garage.name = "FenceLineGarage"
	add_child(garage)
	garage.rotation.y = PI
	garage.position = Vector3(GARAGE_X,0,world.field_env.COURTS[2].w)
	door = _wall(Vector3(0,1.12,0),Vector3(HALF_DOOR*2.0,2.24,.20))
	_wall(Vector3(-1.61,1.12,2.60),Vector3(.27,2.24,5.20))
	_wall(Vector3(1.61,1.12,2.60),Vector3(.27,2.24,5.20))
	rear_stop = _wall(Vector3(0,1.12,BAY_DEPTH+.10),Vector3(3.22,2.24,.20))
	rear_stop.name = "TruckOnlyBayStop"
	rear_stop.collision_mask = 0
	body = CharacterBody3D.new()
	body.name = "DriveableSnowTruck"
	body.motion_mode = CharacterBody3D.MOTION_MODE_FLOATING
	body.collision_mask = 1 | VEHICLE_STOP_LAYER
	body.collision_layer = 0
	add_child(body)
	var shape := BoxShape3D.new()
	shape.size = Vector3(HALF_WIDTH * 2.0,1.42, BODY_FRONT+BACK)
	var hull := CollisionShape3D.new()
	hull.shape = shape
	hull.position = Vector3(0,.72,(BACK-BODY_FRONT)*.5)
	body.add_child(hull)
	collision_probe = PhysicsShapeQueryParameters3D.new()
	collision_probe.shape = shape
	collision_probe.collision_mask = body.collision_mask
	collision_probe.exclude = [body.get_rid(),world.actor.get_rid()]
	var player_shape := CapsuleShape3D.new()
	player_shape.height = 1.32
	player_shape.radius = float(world.layout.actor_radius)
	eject_probe = PhysicsShapeQueryParameters3D.new()
	eject_probe.shape = player_shape
	eject_probe.collision_mask = 1
	eject_probe.exclude = collision_probe.exclude
	art = Art.truck()
	body.add_child(art)
	_install_hud()
	restore_scene()
	initialized = true

func _wall(at: Vector3, size: Vector3) -> StaticBody3D:
	var wall := StaticBody3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	var collider := CollisionShape3D.new()
	collider.shape = shape
	wall.add_child(collider)
	garage.add_child(wall)
	wall.position = at
	return wall

func _install_hud() -> void:
	hud = VBoxContainer.new()
	hud.name = "SnowTruckControls"
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	world.opening_hud.add_child(hud)
	hud.hide()
	hud.add_theme_constant_override("separation",6)
	hud.minimum_size_changed.connect(_place_hud.call_deferred)
	hud.visibility_changed.connect(_place_hud.call_deferred)
	world.get_viewport().size_changed.connect(_place_hud)
	status = Label.new()
	status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	status.add_theme_font_override("font",world.opening_hud.TYPE)
	status.add_theme_font_size_override("font_size",22)
	status.add_theme_color_override("font_color",Color("#f8fbff"))
	var banner:StyleBoxFlat = world.opening_hud._skin(Color("#203648"),Color("#588092"),10)
	banner.set_content_margin_all(5.)
	banner.content_margin_left = 10.
	banner.content_margin_right = 10.
	status.add_theme_stylebox_override("normal",banner)
	hud.add_child(status)
	health = ProgressBar.new()
	health.custom_minimum_size.y = 8
	health.show_percentage = false
	health.max_value = MAX_HP
	health.add_theme_stylebox_override("background",world.opening_hud._skin(Color("#294657"),Color("#3d6478"),4,false))
	health.add_theme_stylebox_override("fill",world.opening_hud._skin(Color("#69db96"),Color("#89e5ac"),4,false))
	hud.add_child(health)
	control = HBoxContainer.new()
	control.alignment = BoxContainer.ALIGNMENT_CENTER
	hud.add_child(control)
	action = Button.new()
	action.custom_minimum_size = Vector2(134,56)
	_style_truck_button(action,Color("#a15d22"),Color("#f7d994"),Color("#fff7e3"))
	action.focus_mode = Control.FOCUS_NONE
	control.add_child(action)
	action.pressed.connect(_context_action)
	stow = Button.new()
	stow.custom_minimum_size = Vector2(108,56)
	_style_truck_button(stow,Color("#fbf1e8"),Color("#c5bdbe"),Color("#142236"))
	stow.focus_mode = Control.FOCUS_NONE
	stow.text = "Load gear"
	control.add_child(stow)
	stow.pressed.connect(_secondary_action)

func _style_truck_button(button:Button,fill:Color,edge:Color,ink:Color) -> void:
	world.opening_hud._action(button,fill,edge,ink)
	for state_name in ["normal","hover","pressed","hover_pressed"]:
		var skin:StyleBoxFlat = button.get_theme_stylebox(state_name)
		skin.expand_margin_top = 0.
		skin.expand_margin_bottom = 0.

func _place_hud() -> void:
	if not is_instance_valid(hud) or not hud.is_visible_in_tree():return
	var safe:Rect2 = world.opening_hud._safe_rect()
	var natural := hud.get_combined_minimum_size()
	var width := maxf(252.,natural.x)
	var above_dock:float = world.opening_hud.camp_dock.touch_height(safe)
	hud.size = Vector2(width,natural.y)
	hud.position = Vector2(safe.get_center().x - width*.5,safe.end.y - above_dock - natural.y - 12.)

func state() -> Dictionary:
	if world.inventory.has_method("vehicle_state"):
		return world.inventory.vehicle_state()
	return {}

func owned() -> bool:
	return world.inventory.complete(Progress.TRUCK)

func garage_footprint(boundary:float) -> Rect2:
	return Rect2(GARAGE_X-2.16,boundary-5.20,4.32,5.20)

func can_build() -> bool:
	if not world.camp_layout:return false
	var footprint := garage_footprint(world.field_env.COURTS[2].w).grow(.12)
	for id in world.camp_layout.NAMES:
		if not world.camp_layout.owned(id):continue
		var at:Vector2 = world.camp_layout.center(id)
		if footprint.intersects(world.camp_layout.footprint(id,at)):return false
		for aisle:Rect2 in world.camp_layout.service_areas(id,at):
			if footprint.intersects(aisle):return false
	return true

func ready_garage() -> bool:
	return world.inventory.complete(Progress.GARAGE)

func garage_return_approach() -> Vector3:
	return garage.to_global(GARAGE_ALIGNMENT_POINT)

func garage_return_park() -> Vector3:
	return garage.to_global(PARK)

func garage_return_aligned() -> bool:
	var at := garage.to_local(body.global_position)
	return absf(at.x) < .55 and at.z > GARAGE_ALIGNMENT_POINT.z-.2 and at.z < BAY_DEPTH

func _river_clearance(basis: Basis) -> float:
	# The fore-aft chassis needs more lateral clearance while turning across
	# the ice. A truck facing along the crossing still fits its full body.
	return maxf(HALF_WIDTH,HALF_WIDTH*absf(basis.x.x) + BODY_FRONT*absf(basis.z.x))

func restore_scene() -> void:
	if not is_instance_valid(body): return
	wants_to_exit_bay = false
	bay_approach = ""
	garage.visible = ready_garage()
	var v := state()
	var has_wreck := not String(v.get("wreck","")).is_empty()
	body.visible = owned() and (int(v.get("hp",0))>0 or has_wreck)
	body.collision_layer = 1 if body.visible and not has_wreck else 0
	var at: Array = v.get("park",[])
	if at.size() == 3:
		body.position = Vector3(float(at[0]),0,float(at[1]))
		body.rotation.y = float(at[2])
		if garage.visible and body.visible:
			var local := garage.to_local(body.position)
			var hull := _garage_hull(body.position,body.basis)
			if absf(local.x)<BAY_WIDTH and local.z>0. and local.z<BAY_DEPTH and hull.end.y>BAY_DEPTH:
				body.position -= garage.global_basis.z * (hull.end.y-BAY_DEPTH)
				record_position()
		if world.river and body.visible:
			body.position = world.river.safe_feet(body.position,_river_clearance(body.basis))
			v.park = [body.position.x,body.position.z,body.rotation.y]
	else:
		_set_parked_transform()
	for child in garage.get_children():
		if child is StaticBody3D:
			child.collision_layer = (VEHICLE_STOP_LAYER if child == rear_stop else 1) if garage.visible else 0
	if has_wreck:
		Art.set_damage(art,1.)
		Art.set_load(art,{})
	elif body.visible:
		Art.set_damage(art,1.0-float(v.get("hp",0))/MAX_HP)
		Art.set_load(art,v.get("cargo",{}))
	if body.visible and world.actor.position.distance_to(body.position)<1.20:
		world.actor.position = _exit_position()

func _set_parked_transform() -> void:
	body.position = garage.to_global(PARK)
	body.rotation.y = garage.rotation.y

func set_purchased() -> void:
	var v := state()
	if v.is_empty(): return
	v.hp = MAX_HP
	v.purchases = maxi(1,int(v.purchases))
	v.wreck = ""
	_set_parked_transform()
	record_position()
	restore_scene()

func record_position() -> void:
	var v := state()
	if owned() and not v.is_empty() and body.visible:
		v.park = [snappedf(body.position.x,.002),snappedf(body.position.z,.002),snappedf(body.rotation.y,.001)]

func _exit_position() -> Vector3:
	var inside: bool = world.field_env.is_inside_camp(body.position)
	for offset in [Vector3(1.64,0,0), Vector3(-1.64,0,0), Vector3(0,0,2.05), Vector3(0,0,-2.94)]:
		var feet: Vector3 = body.to_global(offset)
		if world.field_env.is_inside_camp(feet) != inside: continue
		if world.river and not world.river.is_dry(Vector2(feet.x,feet.z),float(world.layout.actor_radius)): continue
		eject_probe.transform = Transform3D(Basis.IDENTITY,feet+Vector3.UP*.85)
		if world.get_world_3d().direct_space_state.intersect_shape(eject_probe,1).is_empty():
			return feet
	return world.lifecycle.safe_start()

func _dismount() -> void:
	if not mounted: return
	mounted = false
	world.actor.collision_layer = actor_layer
	world.actor.collision_mask = actor_mask
	world.actor.position = _exit_position()
	world.actor.velocity = Vector3.ZERO
	world.previous_dry_position = world.actor.position
	world.hero_model.show()
	world.carry.rack.show()
	drive_speed = 0.0
	wants_to_exit_bay = false
	bay_approach = ""
	track_distance = 0.0
	world.clear_touch()
	if world.tracks: world.tracks.reset_actor(world.actor)

func _commit() -> bool:
	record_position()
	world._checkpoint_lifecycle()
	return not world.persist_blocked

func interact() -> bool:
	if not initialized or world.persist_blocked or not body.visible or world.reset_time > 0.: return false
	if mounted:
		_dismount()
		_commit()
		return true
	if not _in_boarding_reach():return false
	var v := state()
	if v.is_empty(): return false
	if not String(v.wreck).is_empty():
		if v.wreck == "inside" and not v.get("salvage",{}).is_empty():
			if world.inventory.vehicle_recover_salvage() and _commit():
				world._event("truck_salvage",body.position,"pickup_full")
			return true
		return false
	actor_layer = world.actor.collision_layer
	actor_mask = world.actor.collision_mask
	world.actor.collision_layer = 0
	world.actor.collision_mask = 0
	world.hero_model.hide()
	world.carry.rack.hide()
	world.character_kit.rest()
	world.clear_touch()
	world.actor.position = body.position
	mounted = true
	world._event("truck_enter",body.position,"gate")
	return true

func repair_or_replace() -> bool:
	if world.persist_blocked or not owned() or not ready_garage():return false
	if world.actor.position.distance_to(garage.to_global(PARK))>4.0:return false
	var v := state()
	if v.is_empty():return false
	if v.wreck != "":
		if not v.get("salvage",{}).is_empty(): return false
		if not world.inventory.vehicle_repurchase():return false
		set_purchased()
		if _commit(): world._event("truck_rebuy",body.position,"build")
		return true
	if int(v.hp)>=MAX_HP or not parked():return false
	var deficit := MAX_HP-int(v.hp)
	var bill := {"wood":ceili(float(deficit)/10.0),"metal":ceili(float(deficit)/14.0)}
	if world.inventory.vehicle_pay_repair(bill):
		v.hp = MAX_HP
		if _commit(): world._event("truck_repair",body.position,"build")
	return true

func load_player_goods() -> void:
	if mounted or world.persist_blocked or not _in_boarding_reach():return
	if state().get("wreck","")!="":return
	var did_load := false
	for kind in world.inventory.KINDS:
		did_load = world.inventory.vehicle_load_from_player(kind,int(world.inventory.carried.get(kind,0))) or did_load
	for kind in ["planks","blocks","meal","money"]:
		var goods: Dictionary = world.inventory.hand_goods()
		did_load = world.inventory.vehicle_load_from_player(kind,int(goods.get(kind,0))) or did_load
	if did_load and _commit(): world._event("truck_load",body.position,"pickup_full")

func _hull_inside(test: Callable) -> bool:
	for x in [-HALF_WIDTH,HALF_WIDTH]:
		for z in [-FRONT,BACK]:
			if not test.call(body.to_global(Vector3(x,0,z))):return false
	return true

func parked() -> bool:
	if not body.visible or not ready_garage() or absf(drive_speed)>.07:return false
	return _inside_bay(_garage_hull(body.position,body.basis))

func _garage_hull(at: Vector3, axes: Basis) -> Rect2:
	var start := garage.to_local(at)
	var basis := garage.global_basis.inverse() * axes
	var middle := start + basis.z * ((BACK - FRONT) * .5)
	var half_length := (FRONT + BACK) * .5
	var half := Vector2(absf(basis.x.x),absf(basis.x.z)) * HALF_WIDTH
	half += Vector2(absf(basis.z.x),absf(basis.z.z)) * half_length
	return Rect2(Vector2(middle.x,middle.z)-half,half*2.)

func _inside_bay(hull: Rect2) -> bool:
	return hull.position.x >= -BAY_WIDTH and hull.end.x <= BAY_WIDTH and hull.position.y >= .15 and hull.end.y <= BAY_DEPTH+.002

func _near_pedestrian_gate() -> bool:
	for gate in world.gates:
		var at: Vector3 = gate.to_local(body.position)
		if absf(at.x) <= gate.HALF_SPAN + HALF_WIDTH and absf(at.z) <= gate.APPROACH_DEPTH + FRONT:
			return true
	return false

func _limit_bay_step(before: Vector3) -> void:
	if not garage.visible: return
	var previous := _garage_hull(before,body.basis)
	var next := _garage_hull(body.position,body.basis)
	# The steel blade extends beyond the chassis collider. Keep its visible
	# envelope behind the rear boundary in either docking orientation.
	if previous.position.y >= BAY_DEPTH or next.end.y <= BAY_DEPTH: return
	if next.position.x >= HALF_DOOR or next.end.x <= -HALF_DOOR: return
	if next.end.y <= previous.end.y: return
	body.position -= garage.global_basis.z * minf(next.end.y-BAY_DEPTH,next.end.y-previous.end.y)
	drive_speed = 0.
	body.velocity = Vector3.ZERO

func _dock_guidance(at: Vector3, wish: Vector3, requested: bool) -> Dictionary:
	var inward := garage.global_basis.z
	var local_wish := garage.global_basis.inverse()*wish
	if not garage.visible or at.z>=BAY_DEPTH or at.z<=-9. or absf(at.x)>=3.15:
		bay_approach = ""
		return {}
	if at.z>=.30 and bay_approach.is_empty():return {}
	if not requested:
		return {}
	var keeping_alignment := bay_approach=="enter" and at.z>=-.20
	if local_wish.z<(.15 if keeping_alignment else .62):
		bay_approach = ""
		return {}
	var forward := -body.global_basis.z
	var aligned := absf(forward.dot(inward))>.9999 and absf(at.x)<.12
	if bay_approach.is_empty():
		bay_reverse = forward.dot(inward)<0.
		bay_approach = "enter" if aligned else ("clear" if _garage_hull(body.position,body.basis).end.y>-.64 else "center")
	if bay_approach=="clear":
		if _garage_hull(body.position,body.basis).end.y>-.75:
			return {"wish":forward if bay_reverse else -forward,"reverse":not bay_reverse,"turn_only":false}
		bay_approach = "center"
	if bay_approach=="center":
		if absf(at.x)>=.07 or at.z> -2.96:
			var stage := garage_return_approach()
			var speed_limit := sqrt(34. * body.position.distance_to(stage))
			return {"wish":body.position.direction_to(stage),"reverse":bay_reverse,"turn_only":false,"speed_limit":speed_limit}
		bay_approach = "align"
	if bay_approach=="align" and absf(forward.dot(inward))<.99998:
		return {"wish":inward,"reverse":bay_reverse,"turn_only":true}
	bay_approach = "enter"
	return {"wish":inward,"reverse":bay_reverse,"turn_only":false}

func intersects_closed_door(a:Vector3,b:Vector3,radius:float) -> bool:
	if not garage.visible or door.collision_layer==0: return false
	var u := garage.to_local(a)
	var v := garage.to_local(b)
	return world.field_env._intersects_box(Vector2(u.x,u.z),Vector2(v.x,v.z),Vector2(-HALF_DOOR-radius,-.10-radius),Vector2(HALF_DOOR+radius,.10+radius))

func _step_door(dt:float) -> void:
	if not garage.visible:return
	var actor_at := garage.to_local(world.actor.position)
	var truck_at := garage.to_local(body.position)
	var player_near := not mounted and absf(actor_at.x)<2.0 and absf(actor_at.z)<1.55
	var hull := _garage_hull(body.position,body.basis)
	var truck_at_threshold: bool = body.visible and state().get("wreck","")=="" and hull.intersects(Rect2(-HALF_DOOR,-.15,HALF_DOOR*2.,.30),true)
	var approaching := mounted and absf(truck_at.x)<2.3 and absf(truck_at.z)<5.0 and not _inside_bay(hull)
	var departing := mounted and wants_to_exit_bay and absf(truck_at.x)<2.3 and truck_at.z>=0. and truck_at.z<BAY_DEPTH
	var before := opening
	opening = move_toward(opening,1. if player_near or truck_at_threshold or approaching or departing else 0.,dt*2.85)
	var was_open := door.collision_layer==0
	door.collision_layer = 0 if opening >= .94 or (was_open and truck_at_threshold) else 1
	if was_open != (door.collision_layer==0):
		world.field_env.wall_revision+=1
	if (is_zero_approx(before) and opening>0.) or (is_equal_approx(before,1.) and opening<1.):
		world._event("truck_garage_door",garage.position,"gate")
	Art.set_door(garage,opening)
	Art.set_roof_visibility(garage,not (absf(actor_at.x)<1.53 and actor_at.z>.44 and actor_at.z<5.25))

func nearest_hull_point(point: Vector3) -> Vector3:
	var local := body.to_local(point)
	return body.to_global(Vector3(clampf(local.x,-HALF_WIDTH,HALF_WIDTH),0.,clampf(local.z,-BODY_FRONT,BACK)))

func _in_boarding_reach() -> bool:
	if not body.visible:return false
	var feet: Vector3 = world.actor.global_position
	var edge := nearest_hull_point(feet)
	if feet.distance_squared_to(edge)>BOARDING_REACH*BOARDING_REACH:return false
	if garage.visible:
		var local := garage.to_local(feet)
		var hull := garage.to_local(edge)
		if absf(local.x)>HALF_DOOR and local.z>0. and local.z<BAY_DEPTH and absf(hull.x)<HALF_DOOR and hull.z>0. and hull.z<BAY_DEPTH:
			return false
	return world.field_env.travel_clear(feet,edge)

func _keep_enemies_from_pushing() -> void:
	var exclude: Array[RID] = [body.get_rid(),world.actor.get_rid()]
	for enemy: FieldEnemy in world.enemies:
		if not is_instance_valid(enemy.body):continue
		var key := enemy.body.get_rid()
		if not vehicle_nonblocking_enemies.has(key):
			body.add_collision_exception_with(enemy.body)
			vehicle_nonblocking_enemies[key] = weakref(enemy.body)
		exclude.append(key)
	for key in vehicle_nonblocking_enemies.keys():
		if not is_instance_valid(vehicle_nonblocking_enemies[key].get_ref()):
			vehicle_nonblocking_enemies.erase(key)
	collision_probe.exclude = exclude

func drive(input:Vector2,dt:float) -> void:
	_keep_enemies_from_pushing()
	var right:Vector3 = world.camera.global_basis.x
	var camera_depth := right.cross(Vector3.UP)
	var wish := (right*input.x+camera_depth*input.y).normalized()
	var requested := input.length()>.11
	var at := garage.to_local(body.position)
	var local_wish := garage.global_basis.inverse()*wish
	wants_to_exit_bay = requested and local_wish.z < -.30
	var guide := _dock_guidance(at,wish,requested)
	if not guide.is_empty(): wish = guide.wish
	var forward := -body.global_basis.z
	var turning_near_gate := requested and _near_pedestrian_gate()
	var backing_area := (absf(at.x)<2.15 and absf(at.z)<9.0) or turning_near_gate
	var backwards := requested and backing_area and forward.dot(wish)<(-.48 if turning_near_gate else -.72)
	if not guide.is_empty(): backwards = guide.reverse
	if requested:
		var face := -wish if backwards else wish
		var heading := atan2(-face.x,-face.z)
		var trial := rotate_toward(body.rotation.y,heading,dt*2.85)
		var basis := Basis(Vector3.UP,trial)
		collision_probe.transform = Transform3D(basis,body.position+basis*Vector3(0,.72,(BACK-BODY_FRONT)*.5))
		var river_clear: bool = not world.river or world.river.is_dry(Vector2(body.position.x,body.position.z),_river_clearance(basis))
		var proposed := _garage_hull(body.position,basis)
		var current := _garage_hull(body.position,body.basis)
		var turns_past_back := garage.visible and current.position.y < BAY_DEPTH and current.end.y > 0. and absf(at.x) < HALF_DOOR and proposed.end.y > maxf(BAY_DEPTH,current.end.y)
		if river_clear and not turns_past_back and world.get_world_3d().direct_space_state.intersect_shape(collision_probe,1).is_empty():
			body.rotation.y = trial
	var target_speed := 0.0
	if requested and not wish.is_zero_approx() and not guide.get("turn_only",false):
		var alignment := maxf(0.0,(-body.global_basis.z).dot(wish)*(-1. if backwards else 1.))
		target_speed = (-REVERSE_SPEED if backwards else MAX_SPEED)*input.length()*alignment
		if absf(at.x)<2.0 and absf(at.z)<5.35: target_speed = clampf(target_speed,-3.45,3.45)
		var guidance_limit := float(guide.get("speed_limit",MAX_SPEED))
		target_speed = clampf(target_speed,-guidance_limit,guidance_limit)
	drive_speed = move_toward(drive_speed,target_speed, dt*(17.0 if requested else 22.0))
	var previous := body.position
	body.velocity = -body.global_basis.z*drive_speed
	if absf(drive_speed)>.001: body.move_and_slide()
	body.position.y = 0.
	var safe:Vector3 = world.lakeshore.constrain_motion(previous,body.position,HALF_WIDTH) if world.lakeshore else body.position
	if world.river: safe = world.river.constrain_motion(previous,safe,_river_clearance(body.basis))
	if not safe.is_equal_approx(body.position): body.position = safe
	_limit_bay_step(previous)
	var advanced := body.position.distance_to(previous)
	if world.tracks and advanced > .001:
		track_distance += advanced
		if track_distance >= TRACK_SPACING:
			track_distance -= TRACK_SPACING
			var track_point := body.position.lerp(previous,clampf(track_distance/advanced,0.,1.))
			world.tracks.stamp_truck_tracks(track_point,body.global_basis)
	if body.get_slide_collision_count()>0 and advanced<.006 and absf(drive_speed)>.2 and requested: drive_speed = move_toward(drive_speed,0.,dt*28.)
	world.actor.position = body.position
	world.actor.rotation.y = body.rotation.y+PI
	wheel_angle += signf(drive_speed)*advanced*2.3
	if requested and not _touches_camp():
		blade_angle += dt*18.0
		_sweep_blades()
	Art.set_motion(art,wheel_angle,blade_angle)

func _touches_camp() -> bool:
	if world.field_env.is_inside_camp(body.position):return true
	for x in [-HALF_WIDTH,HALF_WIDTH]:
		for z in [-FRONT,BACK]:
			if world.field_env.is_inside_camp(body.to_global(Vector3(x,0,z))):return true
	return false

func _blade_origin(target: Vector3) -> Vector3:
	# Fill the cutting line between the two mounted disks. The contact
	# envelope keeps the same radius outside each blade pivot.
	var lateral := clampf(body.to_local(target).x,-BLADE_HALF_SPAN,BLADE_HALF_SPAN)
	return body.to_global(Vector3(lateral,BLADE_HEIGHT,BLADE_DEPTH))

func _hunt_with_blades() -> bool:
	if not world.survivor or not "wildlife" in world.survivor:return false
	var prey: Node3D = world.survivor.wildlife
	if not is_instance_valid(prey) or not prey.has_method("intersect_blade"):return false
	var origin := _blade_origin(prey.global_position)
	var direction := (prey.global_position-origin).slide(Vector3.UP).normalized()
	if direction.is_zero_approx(): direction = -body.global_basis.z
	var contact: Vector3 = prey.intersect_blade(origin,origin+direction*BLADE_RADIUS)
	if not contact.is_finite() or not prey.receive_hunting_contact(contact,origin,2): return false
	world._event("player_attack",contact)
	return true

func _sweep_blades() -> void:
	if attack_delay>0. or world.persist_blocked:return
	var contacted := _hunt_with_blades()
	for node in world.trees+world.rocks+world.enemies:
		if not is_instance_valid(node) or not node.visible or body.position.distance_squared_to(node.position)>12.4:continue
		var radius := .35
		if node is FieldEnemy:
			if node.hp<=0 or not node.active:continue
			radius = .39*node.size_factor()
		elif node is ResourceRock:
			radius = .48
		var center := _blade_origin(node.global_position)
		var point := Vector3(node.global_position.x,center.y,node.global_position.z)
		if center.distance_squared_to(point)>pow(BLADE_RADIUS+radius,2.):continue
		if not world.field_env.travel_clear(center,point,.08):continue
		if world.truck_contact(node,center,point): contacted = true
	if contacted:
		attack_delay = .28

func receive_damage(amount:int) -> bool:
	if world.persist_blocked or not body.visible or damage_grace>0.: return false
	var v := state()
	if int(v.get("hp",0))<=0:return false
	v.hp = maxi(0,int(v.hp)-amount)
	damage_grace = .62
	if v.hp==0:
		var inside: bool = _hull_inside(func(point:Vector3): return world.field_env.is_inside_camp(point))
		world.inventory.vehicle_wreck(inside)
		_dismount()
		body.collision_layer = 0
		Art.set_load(art,{})
		world._event("truck_wreck",body.position,"player_fall")
	else:
		world._event("truck_damage",body.position,"player_hurt")
		world._combat_number(body.position+Vector3.UP*2.2,"−%d" % amount,Color("#ff9975"))
	Art.set_damage(art,1.-float(v.hp)/MAX_HP)
	_commit()
	return true

func pickup_distance_squared(point:Vector3) -> float:
	var local := body.to_local(point)
	var near := Vector3(clampf(local.x,-HALF_WIDTH,HALF_WIDTH),0.,clampf(local.z,-FRONT,BACK))
	return local.distance_squared_to(near)

func collect_drops(rows:Array[Dictionary]) -> void:
	var claimed:Array[String] = []
	for row in rows:
		if world.inventory.vehicle_collect(row.token,row.kind):
			claimed.append(row.token)
	if claimed.is_empty() or not _commit():return
	for token in claimed:
		world._remove_drop(token)
	world._event("truck_load",body.position,"pickup_full")

func _show_unload(cargo:Dictionary) -> void:
	var exchange = world.settlement_loop.exchange
	for kind: String in cargo:
		var parcel := LooseArt.make(kind)
		if not is_instance_valid(parcel):continue
		add_child(parcel)
		var origin := body.to_global(Vector3(0,1.45,.8))
		var shelf: Vector3 = exchange._shelf(kind)
		var tween := create_tween()
		parcel.position = origin
		tween.tween_method(func(t:float):
			parcel.position = origin.lerp(shelf,smoothstep(0.,1.,t))+Vector3.UP*.75*sin(PI*t),0.,1.,.66)
		tween.tween_callback(parcel.queue_free)

func step(dt:float) -> void:
	if not initialized: return
	damage_grace = maxf(0.,damage_grace-dt)
	attack_delay = maxf(0.,attack_delay-dt)
	_step_door(dt)
	if not body.visible:
		hud.hide()
		return
	var v := state()
	var cargo:Dictionary = v.get("cargo",{})
	var stationary := parked() and int(v.get("hp",0))>0
	park_elapsed = park_elapsed+dt if stationary else 0.0
	if cargo!=loaded_totals:
		Art.set_load(art,cargo)
		loaded_totals = cargo.duplicate()
	if not world.persist_blocked and park_elapsed>=.34 and not cargo.is_empty() and world.depot.house.tier==3:
		var unloaded := cargo.duplicate()
		if world.inventory.vehicle_bank() and _commit():
			_show_unload(unloaded)
			world._event("truck_unload",garage.to_global(PARK),"deposit_wood")
		park_elapsed = 0.0
		cargo = state().get("cargo",{})
	var near := _in_boarding_reach()
	var near_bay: bool = world.actor.position.distance_to(garage.to_global(PARK))<4.0
	var wreck := String(v.get("wreck",""))
	var recovering: bool = wreck=="inside" and not v.get("salvage",{}).is_empty()
	var dock = world.opening_hud.camp_dock
	hud.visible = (mounted or near or (near_bay and not wreck.is_empty())) and not (dock.sheet.visible or world.camp_layout.active)
	var cargo_size := 0
	for kind in cargo:
		var amount := int(cargo[kind])
		cargo_size += Progress.units(amount) if kind in world.inventory.KINDS else amount
	status.text = "Snow truck  ·  %d HP  ·  %s aboard" % [int(v.get("hp",0)),str(cargo_size)]
	if stationary and not cargo.is_empty() and world.depot.house.tier<3: status.text = "Cargo held · Warehouse unavailable"
	if recovering: status.text = "Wreck · Cargo recoverable"
	elif not wreck.is_empty(): status.text = "Truck lost · Rebuy at garage"
	health.value = int(v.get("hp",0))
	health.visible = wreck.is_empty()
	action.text = "Exit truck" if mounted else ("Recover cargo" if recovering else ("Drive" if wreck.is_empty() else "Repurchase"))
	action.visible = mounted or near or (near_bay and not wreck.is_empty())
	stow.visible = near_bay and not mounted and (stationary or (not wreck.is_empty() and not recovering))
	stow.text = "Repurchase" if not wreck.is_empty() else "Repair"
	if stationary and int(v.get("hp",0))>=MAX_HP and wreck.is_empty():
		stow.text = "Load gear"

func handle_input(event: InputEvent) -> bool:
	if not initialized or not hud.visible:return false
	if event is InputEventKey and event.physical_keycode==KEY_T and event.pressed and not event.echo:
		_context_action()
		return true
	if event is InputEventScreenTouch:
		if not event.pressed:
			return held_buttons.erase(event.index)
		for button: Button in [action,stow]:
			if button.visible and button.get_global_rect().has_point(event.position):
				held_buttons[event.index] = true
				button.pressed.emit()
				return true
	if event is InputEventScreenDrag:
		return held_buttons.has(event.index)
	return false

func _context_action() -> void:
	if not interact():repair_or_replace()

func _secondary_action() -> void:
	if not repair_or_replace():load_player_goods()
