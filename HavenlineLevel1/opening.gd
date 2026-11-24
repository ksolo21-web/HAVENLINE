extends Node3D
const Ledger = preload("res://opening_ledger.gd")
const Save = preload("res://opening_save.gd")
const Gate = preload("res://technical_gate.gd")
const PadView = preload("res://purchase_pad_visual.gd")
const OpeningHUD = preload("res://opening_hud.gd")
const StarterGroundWoodView = preload("res://starter_ground_wood_view.gd")
const WoodStockScript = preload("res://wood_stock_view.gd")
const ResourceTreeScript = preload("res://resource_tree.gd")
const HERO = preload("res://assets/characters/Character1.glb")
const HEARTH = preload("res://assets/studio/hearth_trial_02.glb")
const CONIFERS := [
	preload("res://assets/reference_forest/pine_1.glb"),
	preload("res://assets/reference_forest/pine_2.glb"),
	preload("res://assets/reference_forest/pine_3.glb"),
]
var ledger = Ledger.new()
var save = Save.new()
var persist_requested := false
var persist_blocked := false
var persist_error := ""
var layout: Dictionary
var actor: CharacterBody3D
var camera: Camera3D
var camp_built: Node3D
var opening_hud: OpeningHUD
var gate_button: Button
var purchase_pad_view: PadView
var wood_stock_view: WoodStockScript
var tree_button: Button
var resource_tree: ResourceTreeScript
var tree_input_sequence := 0
var gates: Array[Gate] = []
var nearest_gate: Gate
var wood_visuals: Dictionary = {}
var camp_colliders: Array[StaticBody3D] = []
var touch_id := -1
var touch_origin := Vector2.ZERO
var touch_now := Vector2.ZERO

func point(csv: Array, height := 0.0) -> Vector3:
	return Vector3(float(csv[0]), height, float(csv[1]))

func block(parent: Node3D, dims: Vector3, at: Vector3, color: Color, solid := false) -> Node3D:
	var body: Node3D = StaticBody3D.new() if solid else Node3D.new()
	parent.add_child(body)
	body.position = at
	var vis := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = dims
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.94
	vis.material_override = mat
	vis.mesh = mesh
	body.add_child(vis)
	if solid:
		var c := CollisionShape3D.new()
		var b := BoxShape3D.new()
		b.size = dims
		c.shape = b
		body.add_child(c)
	return body

func meshes(node: Node, out: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D and node.mesh:
		out.append(node)
	for child in node.get_children():
		meshes(child, out)

func model(resource: PackedScene, parent: Node3D, height: float) -> Node3D:
	var model_root := resource.instantiate() as Node3D
	parent.add_child(model_root)
	var pieces: Array[MeshInstance3D] = []
	meshes(model_root, pieces)
	assert(not pieces.is_empty())
	var bounds := AABB()
	for i in range(pieces.size()):
		var piece := pieces[i]
		var local_box: AABB = (parent.global_transform.affine_inverse() * piece.global_transform) * piece.get_aabb()
		bounds = local_box if i == 0 else bounds.merge(local_box)
	var factor := height / maxf(0.01, bounds.size.y)
	model_root.scale *= factor
	model_root.position = Vector3(-bounds.get_center().x, -bounds.position.y, -bounds.get_center().z) * factor
	return model_root

func constrain_private_snow_travel() -> void:
	# Rehearsal-only boundary. Keep the entire moving capsule on the snow.
	# No physical camp openings, wall shapes, or snowy surface treatment changes.
	var travel_limit := float(layout.snow_extent_half) - float(layout.private_travel_inset) - float(layout.actor_radius)
	var foot := actor.position
	foot.x = clampf(foot.x, -travel_limit, travel_limit)
	foot.z = clampf(foot.z, -travel_limit, travel_limit)
	actor.position = foot

func _ready() -> void:
	layout = JSON.parse_string(FileAccess.get_file_as_string("res://layout.json"))
	var world_light := DirectionalLight3D.new()
	world_light.rotation_degrees = Vector3(-48, -28, 0)
	world_light.shadow_enabled = true
	add_child(world_light)
	var snow_width := float(layout.snow_extent_half) * 2.0
	var external_snow := block(self, Vector3(snow_width, 0.30, snow_width), Vector3(0, -0.15, 0), Color("#d7e5ed"), true)
	external_snow.name = "SnowGround_NoPaintedPaths"
	setup_exterior_conifers()
	camp_built = Node3D.new()
	camp_built.name = "GrantOnlyCamp"
	add_child(camp_built)
	setup_camp()
	camp_built.visible = false
	camp_built.process_mode = Node.PROCESS_MODE_DISABLED
	for body in camp_colliders:
		body.collision_layer = 0

	actor = CharacterBody3D.new()
	actor.name = "ExactCharacter1"
	add_child(actor)
	actor.position = point(layout.start_xz)
	actor.motion_mode = CharacterBody3D.MOTION_MODE_FLOATING
	var capsule := CapsuleShape3D.new()
	capsule.radius = float(layout.actor_radius)
	capsule.height = float(layout.actor_height)
	var shape := CollisionShape3D.new()
	shape.position.y = capsule.height * 0.5 + 0.035
	shape.shape = capsule
	actor.add_child(shape)
	var hero_visual := model(HERO, actor, float(layout.actor_height))
	wood_stock_view = WoodStockScript.new()
	wood_stock_view.name = "TechnicalPublishedWoodStockView"
	actor.add_child(wood_stock_view)
	wood_stock_view.install(hero_visual)
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 13.0
	add_child(camera)
	camera.current = true
	camera.position = actor.position + Vector3(7, 11, 11)
	camera.look_at(actor.position)

	for row in layout.wood_nodes:
		if row.id == ResourceTreeScript.TREE_ID:
			resource_tree = ResourceTreeScript.new()
			resource_tree.name = "StarterResourceTree_wood_a"
			add_child(resource_tree)
			resource_tree.position = point(row.xz)
			resource_tree.build(CONIFERS[0])
			continue
		var piece := StarterGroundWoodView.new()
		piece.name = "StarterGroundWood_%s" % String(row.id)
		piece.position = point(row.xz)
		add_child(piece)
		wood_visuals[row.id] = piece
	purchase_pad_view = PadView.new()
	purchase_pad_view.name = "ExactStudioV5_PresentationOnly"
	add_child(purchase_pad_view)
	purchase_pad_view.position = point(layout.pad_xz)
	if not purchase_pad_view.install_exact():
		push_warning("V5 pad presentation withheld: exact geometry or label binding failed.")
	var overlay := CanvasLayer.new()
	add_child(overlay)
	opening_hud = OpeningHUD.new()
	overlay.add_child(opening_hud)
	gate_button = opening_hud.gate
	tree_button = opening_hud.tree
	get_viewport().size_changed.connect(clear_touch)
	get_viewport().size_changed.connect(opening_hud.reflow)
	var args := OS.get_cmdline_user_args()
	persist_requested = save.requested(args)
	if persist_requested:
		if not save.configure(args):
			persist_blocked = true
			persist_error = "Disposable profile rejected."
		else:
			var recovered: Error = save.load_into(ledger)
			if recovered != OK and recovered != ERR_FILE_NOT_FOUND:
				persist_blocked = true
				persist_error = "Save rejected; no progress written."
	sync_progress_visuals()
	refresh_hud()

func setup_exterior_conifers() -> void:
	var placements: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://conifers.json"))
	var forest := Node3D.new()
	forest.name = "ExteriorExactT01Visuals"
	add_child(forest)
	for row in placements.instances:
		var scene: PackedScene = CONIFERS[int(row.variant) - 1]
		var pine := scene.instantiate() as Node3D
		forest.add_child(pine)
		pine.name = String(row.id)
		# Zero is the authored root datum, with native -0.18m mesh skirt below snow.
		pine.position = point(row.xz, float(row.root_y))
		pine.rotation_degrees.y = float(row.yaw_deg)
		pine.scale = Vector3.ONE * float(row.scale)

func setup_camp() -> void:
	var r: Array = layout.camp_rect_xz
	var w := float(r[2]) - float(r[0])
	var d := float(r[3]) - float(r[1])
	var ctr := Vector3((float(r[2]) + float(r[0])) * 0.5, 0.006, (float(r[3]) + float(r[1])) * 0.5)
	block(camp_built, Vector3(w, .012, d), ctr, Color("#68747a")).name = "CampOnlySurface"
	for row in layout.walls_xz:
		var wall := block(camp_built, Vector3(float(row[2]), .95, float(row[3])), Vector3(float(row[0]), .475, float(row[1])), Color("#5d5148"), true) as StaticBody3D
		camp_colliders.append(wall)
	for gate in layout.gates:
		var at := point(gate.center_xz)
		var mechanism := Gate.new()
		camp_built.add_child(mechanism)
		mechanism.position = at
		mechanism.rotation_degrees.y = 0.0 if gate.orientation == "x" else 90.0
		mechanism.build(String(gate.id))
		gates.append(mechanism)
		var axis := Vector3.RIGHT if gate.orientation == "x" else Vector3.BACK
		for side in [-1, 1]:
			var marker_at := at + axis * float(gate.clear_span) * .52 * float(side)
			marker_at.y = .72
			block(camp_built, Vector3(.20, 1.44, .20), marker_at, Color("#47687a")).name = String(gate.id) + "-technical-marker"
	var vessel_root := Node3D.new()
	vessel_root.name = "CenteredHearth_StudioTrialOnly"
	camp_built.add_child(vessel_root)
	vessel_root.position = point(layout.furnace_xz)
	model(HEARTH, vessel_root, 1.8)
	var obstacle := StaticBody3D.new()
	vessel_root.add_child(obstacle)
	var footprint := CollisionShape3D.new()
	var cylinder := CylinderShape3D.new()
	cylinder.height = 1.35
	cylinder.radius = .85
	footprint.position.y = .675
	footprint.shape = cylinder
	obstacle.add_child(footprint)
	camp_colliders.append(obstacle)

func clear_touch() -> void:
	touch_id = -1
	touch_origin = Vector2.ZERO
	touch_now = Vector2.ZERO

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F:
		request_tree_contact()
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_E:
		toggle_nearest_gate()
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if handle_gate_pointer_press(event, event.position):
			return
		if touches_tree_button(event.position):
			if event.device != InputEvent.DEVICE_ID_EMULATION:
				request_tree_contact()
		return
	if event is InputEventScreenTouch:
		if event.pressed and touches_tree_button(event.position):
			if event.device != InputEvent.DEVICE_ID_EMULATION:
				request_tree_contact()
			return
		if event.pressed and handle_gate_pointer_press(event, event.position):
			return
		if event.pressed and touch_id < 0:
			touch_id = event.index
			touch_origin = event.position
			touch_now = event.position
		elif not event.pressed and event.index == touch_id:
			clear_touch()
	elif event is InputEventScreenDrag and event.index == touch_id:
		touch_now = event.position

func _physics_process(dt: float) -> void:
	var direction := Vector2.ZERO
	if touch_id >= 0:
		direction = ((touch_now - touch_origin) / 82.0).limit_length()
	else:
		direction.x = float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT))
		direction.y = float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP))
	direction = direction.limit_length()
	var flat := Vector3(direction.x, 0, direction.y).rotated(Vector3.UP, atan2(7.0, 11.0))
	actor.velocity = flat * 4.0
	actor.move_and_slide()
	constrain_private_snow_travel()
	step_technical_gates(dt)
	if flat.length() > .05:
		actor.rotation.y = atan2(flat.x, flat.z)
	camera.position = camera.position.lerp(actor.position + Vector3(7, 11, 11), minf(dt * 8.0, 1.0))
	step_tree(dt)
	if persist_blocked:
		return
	for row in layout.wood_nodes:
		if row.id == ResourceTreeScript.TREE_ID:
			continue
		var marker: Node3D = wood_visuals[row.id]
		if marker.visible and actor.position.distance_to(point(row.xz)) < .68:
			_collect_wood_source(String(row.id))
	fund_opening_receiver(Ledger.OFFER, "wood")

func fund_opening_receiver(receiver_id: Variant = null, material_id: Variant = null) -> bool:
	# Authorize the exact scene target, not caller-provided substitutions or quantities.
	if typeof(receiver_id) != TYPE_STRING or typeof(material_id) != TYPE_STRING:
		return false
	if receiver_id != Ledger.OFFER or material_id != "wood" or persist_blocked:
		return false
	if actor == null or not ledger.receipt.is_empty():
		return false
	# The scene may retain the bridge after its exact asset installation failed.
	# Only charge against the currently attached, installed and offered pad.
	if not is_instance_valid(purchase_pad_view) or not purchase_pad_view.binding_ready or purchase_pad_view.get_parent() != self:
		return false
	var live_pad = purchase_pad_view.scene_view
	if not is_instance_valid(live_pad) or not live_pad.installed or live_pad.get_parent() != purchase_pad_view or not live_pad.is_visible_in_tree():
		return false
	if not actor.position.is_finite() or actor.position.distance_to(point(layout.pad_xz)) >= .72:
		return false
	var next := Ledger.new()
	if not next.restore(ledger.snapshot()) or not next.pay_center_hearth():
		return false
	return _commit_opening_progress(next)

func _collect_wood_source(source: String) -> bool:
	if persist_blocked:
		return false
	var next := Ledger.new()
	if not next.restore(ledger.snapshot()) or not next.collect_wood(source):
		return false
	return _commit_opening_progress(next)

func _commit_opening_progress(next: Ledger) -> bool:
	if persist_requested:
		var result: Error = save.commit(next)
		if result != OK:
			persist_blocked = true
			persist_error = "Save failed (%d); action not applied." % int(result)
			refresh_hud()
			return false
	ledger = next
	sync_progress_visuals()
	refresh_hud()
	return true

func sync_progress_visuals() -> void:
	wood_stock_view.reflect_stock(int(ledger.stock.wood))
	if ResourceTreeScript.TREE_ID in ledger.collected and resource_tree.phase != "credited":
		if resource_tree.phase == "ready_to_credit":
			resource_tree.mark_credited()
		else:
			resource_tree.restore_collected()
	for row in layout.wood_nodes:
		if row.id == ResourceTreeScript.TREE_ID:
			continue
		var marker: Node3D = wood_visuals[row.id]
		marker.visible = row.id not in ledger.collected
	var built: bool = not ledger.receipt.is_empty()
	camp_built.process_mode = Node.PROCESS_MODE_INHERIT if built else Node.PROCESS_MODE_DISABLED
	for body in camp_colliders:
		body.collision_layer = 1 if built else 0
	for gate in gates:
		gate.set_earned(built)
	camp_built.visible = built
	purchase_pad_view.reflect_published_state(built)

func tree_facing() -> Vector3:
	return actor.global_transform.basis.z.normalized()

func touches_tree_button(at: Vector2) -> bool:
	return is_instance_valid(tree_button) and tree_button.visible and tree_button.get_global_rect().has_point(at)

func request_tree_contact() -> void:
	if not is_instance_valid(resource_tree) or persist_blocked:
		return
	tree_input_sequence += 1
	resource_tree.strike(ResourceTreeScript.TREE_ID, tree_input_sequence, actor.global_position, tree_facing())

func step_tree(dt: float) -> void:
	if persist_blocked:
		tree_button.hide()
		return
	resource_tree.advance(dt, actor.global_position, float(layout.actor_radius))
	if resource_tree.phase == "ready_to_credit":
		_collect_wood_source(ResourceTreeScript.TREE_ID)
	tree_button.visible = not persist_blocked and resource_tree.can_address(actor.global_position, tree_facing())
	tree_button.text = tree_action_label(resource_tree.strikes)

func step_technical_gates(dt: float) -> void:
	nearest_gate = null
	var best := INF
	for gate in gates:
		gate.advance(dt, actor.global_position, float(layout.actor_radius))
		if gate.interaction_in_range(actor.global_position):
			var dist: float = gate.global_position.distance_to(actor.global_position)
			if dist < best:
				best = dist
				nearest_gate = gate
	gate_button.visible = nearest_gate != null
	if nearest_gate != null:
		gate_button.text = gate_action_label(nearest_gate.gate_id, nearest_gate.holding_for_occupancy, nearest_gate.target_open)

func gate_action_label(gate_id: String, held: bool, open: bool) -> String:
	var nameplate := "South" if gate_id == "gate-south" else ("East" if gate_id == "gate-east" else gate_id)
	var action := "Step away" if held else ("Close" if open else "Open")
	return "%s: %s [E]" % [nameplate, action]

func tree_action_label(strikes: int) -> String:
	return "Chop tree [F] %d/3" % strikes

func handle_gate_pointer_press(event: InputEvent, at: Vector2) -> bool:
	if not touches_gate_button(at):
		return false
	# Ignore Godot-tagged mirrors at this button only. A touch hit is still
	# consumed here so a rejected UI press cannot acquire the movement stick.
	if event.device != InputEvent.DEVICE_ID_EMULATION:
		toggle_nearest_gate()
	return true

func touches_gate_button(at: Vector2) -> bool:
	return is_instance_valid(gate_button) and gate_button.visible and gate_button.get_global_rect().has_point(at)

func toggle_nearest_gate() -> void:
	if nearest_gate != null:
		nearest_gate.request_toggle(actor.global_position)

func refresh_hud() -> void:
	var state := "Fell one tree (F), collect two pickups, then reach the build marker." if ledger.receipt.is_empty() else "Hearth paid once. Check the South and East passages."
	opening_hud.show_status(int(ledger.stock.wood), persist_error if persist_blocked else state)
