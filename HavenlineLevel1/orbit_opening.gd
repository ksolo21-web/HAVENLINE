extends "res://opening.gd"
const ZoomCamera = preload("res://orbit_camera.gd")
const VisualQuality = preload("res://orbit_visual_quality.gd")
var trial_camera := ZoomCamera.new()
var graphics := VisualQuality.new()
var hud_fingers: Dictionary = {}
var gait_motor = preload("res://gait_motor.gd").new()

func move_actor(input: Vector2, dt: float) -> float:
	return gait_motor.step(self, input, dt)

const Orbit = preload("res://weapon_orbit.gd")
const FRESH_HERO = preload("res://assets/characters/Character1Fresh.glb")
@export var upgraded_orbit := false
const SURFACE_REACH := 3.15
const SNOW_STONE := preload("res://assets/reference_forest/mine-stone.glb")
var surfaces := {}
var contacts: Array[Dictionary] = []

func model(resource: PackedScene, parent: Node3D, height: float) -> Node3D:
	return super.model(FRESH_HERO if parent == actor and resource == HERO else resource, parent, height)

func create_opening_hud() -> OpeningHUD:
	return preload("res://orbit_hud.gd").new()

func refresh_hud() -> void:
	opening_hud.show_status(int(ledger.stock.wood), persist_error if persist_blocked else "Approach a resource to gather.")

func _ready() -> void:
	character_kit = Orbit.new()
	super()
	character_kit.set_upgraded(upgraded_orbit)
	resource_tree.set_meta("orbit_reach",SURFACE_REACH)
	resource_rock.set_meta("orbit_reach",SURFACE_REACH)
	# The trial preloads the same art, camera and resource mechanics as the equipment scene.
	var tree_parts := resource_tree._pivot.find_children("*", "MeshInstance3D", true, false)
	for part: MeshInstance3D in tree_parts:
		var triangles := PackedVector3Array()
		for surface in part.mesh.get_surface_count():
			var material := part.mesh.surface_get_material(surface)
			if material and material.resource_name.to_lower() == "trunk":
				var arrays := part.mesh.surface_get_arrays(surface)
				var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
				for index in arrays[Mesh.ARRAY_INDEX]:
					triangles.append(vertices[index])
		if not triangles.is_empty():
			var trunk := TriangleMesh.new()
			trunk.create_from_faces(triangles)
			surfaces[resource_tree] = [part, trunk]
			break
	# Keep hits on the visible native rock surface, including after depletion reduces its size.
	var mount := Node3D.new()
	resource_rock.add_child(mount)
	mount.scale = Vector3.ONE * ResourceRockScript.BANK_SCALE
	var stone := SNOW_STONE.instantiate() as Node3D
	mount.add_child(stone)
	var rock_part := stone as MeshInstance3D
	if rock_part == null:
		rock_part = stone.find_children("*", "MeshInstance3D", true, false)[0]
	resource_rock._mesh.queue_free()
	resource_rock._mesh = rock_part
	rock_part.position.y = -rock_part.mesh.get_aabb().position.y
	resource_rock.attach_bank_body()
	surfaces[resource_rock] = [rock_part, rock_part.mesh.generate_triangle_mesh()]
	opening_hud.show_status(0, "Approach a resource to gather.")
	tree_button.hide()
	add_child(graphics)
	graphics.install(self, opening_hud)
	set_zoom_ratio(1.0)
	get_window().focus_exited.connect(clear_touch)

func set_zoom_ratio(value: float) -> void:
	trial_camera.set_ratio(camera, value)

func get_zoom_ratio() -> float:
	return trial_camera.zoom_ratio

func clear_touch() -> void:
	super.clear_touch()
	trial_camera.reset_gesture()
	hud_fingers.clear()

func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch or event is InputEventScreenDrag:
		if event.device == InputEvent.DEVICE_ID_EMULATION:
			return
		if hud_fingers.has(event.index):
			if event is InputEventScreenTouch and (event.canceled or not event.pressed):
				hud_fingers.erase(event.index)
			return
		if event is InputEventScreenTouch and event.pressed and not event.canceled:
			var quality_hit := graphics.quality_button.get_global_rect().has_point(event.position)
			if quality_hit or touches_gate_button(event.position) or touches_tree_button(event.position):
				hud_fingers[event.index] = true
				if trial_camera.fingers.is_empty() and hud_fingers.size() == 1:
					if quality_hit:
						graphics.set_ultra(not graphics.ultra)
					else:
						super(event)
				return
		if trial_camera.consume(event, camera):
			if trial_camera.pinching:
				super.clear_touch()
			return
		if event is InputEventScreenTouch and (event.canceled or not event.pressed):
			if touch_id == event.index:
				super.clear_touch()
			return
		super(event)
		return
	if event is InputEventMouseButton and event.pressed and event.device != InputEvent.DEVICE_ID_EMULATION:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP or event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			var step := 1.15 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.15
			set_zoom_ratio(get_zoom_ratio() * pow(step, event.factor if event.factor > 0 else 1.0))
			return
		if event.button_index == MOUSE_BUTTON_LEFT and graphics.quality_button.get_global_rect().has_point(event.position):
			graphics.set_ultra(not graphics.ultra)
			return
	if event is InputEventMagnifyGesture and trial_camera.fingers.is_empty():
		set_zoom_ratio(get_zoom_ratio() * event.factor)
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_U:
		character_kit.set_upgraded(character_kit.count == 1)
		return
	if event is InputEventKey and event.physical_keycode == KEY_F:
		return
	super(event)

func request_tree_contact() -> void:
	pass

func request_rock_contact() -> void:
	pass

func step_tree(dt: float) -> void:
	super(dt)
	tree_button.hide()

func active_tool() -> String:
	return character_kit.equipped

func register_hostile(body: Node3D, geometry: MeshInstance3D) -> void:
	if body.is_in_group("swirl_hostiles") and body.has_method("take_swirl_hit") and body.has_method("can_receive_swirl") and (body == geometry or body.is_ancestor_of(geometry)):
		var triangle_surface: TriangleMesh = body.hit_surface if "hit_surface" in body and body.hit_surface else geometry.mesh.generate_triangle_mesh()
		surfaces[body] = [geometry, triangle_surface]
		body.tree_exiting.connect(func(): surfaces.erase(body), CONNECT_ONE_SHOT)

func reachable(body: Node3D) -> bool:
	if not is_instance_valid(body) or not body.is_inside_tree():
		return false
	var offset := body.global_position - actor.global_position
	if body == resource_tree:
		return body.can_address(actor.global_position, offset)
	if body == resource_rock:
		return body.can_address(actor.global_position, offset)
	return body.is_in_group("swirl_hostiles") and offset.length_squared() <= pow(SURFACE_REACH * character_kit.reach_scale, 2) and body.can_receive_swirl()

func selected_tool() -> String:
	var nearest := INF
	var result := ""
	for body: Node3D in surfaces:
		if reachable(body):
			var distance := actor.global_position.distance_squared_to(body.global_position)
			if distance < nearest:
				nearest = distance
				result = "pickaxe" if body is ResourceRockScript else "axe"
	return result

func accept_contact(body: Node3D) -> bool:
	var facing := (body.global_position - actor.global_position).normalized()
	if body == resource_tree:
		tree_input_sequence += 1
		return body.strike(ResourceTreeScript.TREE_ID, tree_input_sequence, actor.global_position, facing)
	if body == resource_rock:
		rock_input_sequence += 1
		var struck: bool = body.strike(ResourceRockScript.ROCK_ID, rock_input_sequence, actor.global_position, facing)
		return struck
	return body.take_swirl_hit(character_kit.turn_id)

## Field subclasses override this with the current paid gate perimeter.
func orbit_permitted_at(_world_position: Vector3) -> bool:
	return true

func _step_character(dt: float, speed: float) -> void:
	character_kit.locomotion.observe(speed, true, dt)
	resource_rock.advance(dt)
	if persist_blocked or not orbit_permitted_at(actor.global_position):
		character_kit.rest()
		return
	var reach: float = SURFACE_REACH * character_kit.reach_scale
	resource_tree.set_meta("orbit_reach",reach)
	resource_rock.set_meta("orbit_reach",reach)
	var tool := selected_tool()
	if tool.is_empty(): tool="axe"
	if not character_kit.active:
		character_kit.begin(tool)
	elif tool!=character_kit.equipped:
		character_kit.equipped=tool
		character_kit.show_tools()
		character_kit.pose()
	character_kit.advance(dt)
	for body: Node3D in surfaces:
		if character_kit.hit_this_turn.has(body) or not reachable(body):
			continue
		if (body == resource_rock and character_kit.equipped != "pickaxe") or (body == resource_tree and character_kit.equipped != "axe"):
			continue
		var part: MeshInstance3D = surfaces[body][0]
		var mesh: TriangleMesh = surfaces[body][1]
		if character_kit.crosses_surface(part, mesh) and accept_contact(body):
			character_kit.hit_this_turn[body] = true
			contacts.append({"target":body.name, "turn":character_kit.turn_id, "seconds":character_kit.elapsed})
			if contacts.size()>1024: contacts.pop_front()
