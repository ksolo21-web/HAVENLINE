extends "res://opening.gd"
const Orbit = preload("res://weapon_orbit.gd")
const FRESH_HERO = preload("res://assets/characters/Character1Fresh.glb")
@export var upgraded_orbit := false
const SURFACE_REACH := 3.15
const SNOW_STONE := preload("res://assets/reference_forest/mine-stone.glb")
var surfaces := {}
var contacts: Array[Dictionary] = []

func model(resource: PackedScene, parent: Node3D, height: float) -> Node3D:
	return super.model(FRESH_HERO if parent == actor and resource == HERO else resource, parent, height)

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
	mount.scale = Vector3.ONE * .68
	var stone := SNOW_STONE.instantiate() as Node3D
	mount.add_child(stone)
	var rock_part := stone as MeshInstance3D
	if rock_part == null:
		rock_part = stone.find_children("*", "MeshInstance3D", true, false)[0]
	resource_rock._mesh.queue_free()
	resource_rock._mesh = rock_part
	rock_part.position.y = -rock_part.mesh.get_aabb().position.y
	surfaces[resource_rock] = [rock_part, rock_part.mesh.generate_triangle_mesh()]
	opening_hud.show_status(0, "Approach a resource to gather.")
	tree_button.hide()

func _input(event: InputEvent) -> void:
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
		surfaces[body] = [geometry, geometry.mesh.generate_triangle_mesh()]
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
				result = "pickaxe" if body == resource_rock else "axe"
	return result

func accept_contact(body: Node3D) -> bool:
	var facing := (body.global_position - actor.global_position).normalized()
	if body == resource_tree:
		tree_input_sequence += 1
		return body.strike(ResourceTreeScript.TREE_ID, tree_input_sequence, actor.global_position, facing)
	if body == resource_rock:
		rock_input_sequence += 1
		var struck: bool = body.strike(ResourceRockScript.ROCK_ID, rock_input_sequence, actor.global_position, facing)
		if struck:
			body._mesh.position.y = -body._mesh.mesh.get_aabb().position.y * body._mesh.scale.y
		return struck
	return body.take_swirl_hit(character_kit.turn_id)

func _step_character(dt: float, speed: float) -> void:
	character_kit.locomotion.observe(speed, true)
	resource_rock.advance(dt)
	if persist_blocked:
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
