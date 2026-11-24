extends "res://opening.gd"
## Opt-in candidate with no save path and no default launch change.
const HeroLocomotion = preload("res://previews/hero_locomotion.gd")
const CompactHUD = preload("res://previews/compact_opening_hud.gd")
const LooseWoodContrast = preload("res://previews/loose_wood_contrast.gd")
const GateArtReview = preload("res://previews/gate_pair_study/gate_art_review.gd")
const Terrain = preload("res://terrain_source.gd")
const DrySweep = preload("res://previews/fixture_dry_shore_sweep.gd")
const WORLD = preload("res://previews/terrain_water_preview.tscn")
const FLOOR_SHADE = preload("res://previews/integrated_camp_floor.gdshader")
# Provisional, prior screened rigid relocation of the full V8 camp/woods module.
const CAMP_SHIFT := Vector2(-3.25, 5.80)
const ACTIVE_HALF := Vector2(14.2, 16.2)
var hero_locomotion := HeroLocomotion.new()
var ground: StaticBody3D
var bound := false
var bank_side := 0.0
var pad_anchor := Vector3(INF, INF, INF)
var wood_anchors: Dictionary = {}

func _pin_placement() -> bool:
	var start := point(layout.start_xz)
	var sample := Terrain.sample(Vector2(start.x, start.z))
	if not start.is_finite() or not sample.get("valid", false):
		return false
	bank_side = float(sample.bank_side)
	pad_anchor = point(layout.pad_xz)
	if not _supported_anchor(pad_anchor):
		return false
	for row in layout.wood_nodes:
		var anchor := point(row.xz)
		if not _supported_anchor(anchor):
			return false
		wood_anchors[String(row.id)] = anchor
	return _supported_anchor(start)

func _supported_anchor(anchor: Vector3) -> bool:
	if not anchor.is_finite():
		return false
	var xz := Vector2(anchor.x, anchor.z)
	return _inside_motion_bounds(xz) and DrySweep.dry_footprint(xz, float(layout.actor_radius), bank_side, DrySweep.SWEEP_PAD)

func point(csv: Array, height := 0.0) -> Vector3:
	var xz := Vector2(float(csv[0]), float(csv[1])) + CAMP_SHIFT
	var source := Terrain.sample(xz)
	if not source.get("valid", false) or not is_finite(float(source.height)):
		return Vector3(INF, INF, INF)
	return Vector3(xz.x, float(source.height) + height, xz.y)

func _inside_motion_bounds(p: Vector2) -> bool:
	var r := float(layout.actor_radius)
	return p.is_finite() and absf(p.x) <= ACTIVE_HALF.x - r and absf(p.y) <= ACTIVE_HALF.y - r

func _bounded_dry_delta(start: Vector2, requested: Vector2) -> Vector2:
	if not _inside_motion_bounds(start):
		return Vector2.ZERO
	var r := float(layout.actor_radius)
	var limit := ACTIVE_HALF - Vector2.ONE * (r + .001)
	var target := (start + requested).clamp(-limit, limit)
	return DrySweep.allowed_delta(start, target - start, r, bank_side)

func _within_logical_reach(anchor: Vector3, radius: float) -> bool:
	if not is_instance_valid(actor) or not anchor.is_finite() or not actor.global_position.is_finite():
		return false
	return actor.global_position.distance_to(to_global(anchor)) < radius

func _in_pickup_reach(id: String) -> bool:
	return wood_anchors.has(id) and _within_logical_reach(wood_anchors[id], .68)

func _ready() -> void:
	layout = JSON.parse_string(FileAccess.get_file_as_string("res://layout.json"))
	var world_light := DirectionalLight3D.new()
	world_light.rotation_degrees = Vector3(-48, -28, 0)
	world_light.shadow_enabled = true
	add_child(world_light)
	var surface := WORLD.instantiate()
	add_child(surface)
	if not surface.get("water_bound"):
		return
	ground = surface.get_node("AcceptedGround/GroundBody") as StaticBody3D
	if not _pin_placement():
		push_error("Combined candidate cannot bind exact terrain placement.")
		return
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
	actor.motion_mode = CharacterBody3D.MOTION_MODE_GROUNDED
	actor.floor_snap_length = .22
	actor.floor_max_angle = PI / 4.0
	actor.collision_mask = 1 | (1 << 11)
	var capsule := CapsuleShape3D.new()
	capsule.radius = float(layout.actor_radius)
	capsule.height = float(layout.actor_height)
	var shape := CollisionShape3D.new()
	shape.position.y = capsule.height * 0.5 + 0.035
	shape.shape = capsule
	actor.add_child(shape)
	var hero_visual := model(HERO, actor, float(layout.actor_height))
	hero_locomotion.bind(hero_visual)
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
		if LooseWoodContrast.REVIEW_FLAG in OS.get_cmdline_user_args():
			if not LooseWoodContrast.apply(piece):
				push_warning("Loose wood contrast candidate withheld: exact surface binding failed.")
		wood_visuals[row.id] = piece
	purchase_pad_view = PadView.new()
	purchase_pad_view.name = "ExactStudioV5_PresentationOnly"
	add_child(purchase_pad_view)
	purchase_pad_view.position = point(layout.pad_xz)
	if not purchase_pad_view.install_exact():
		push_warning("V5 pad presentation withheld: exact geometry or label binding failed.")
	var overlay := CanvasLayer.new()
	add_child(overlay)
	opening_hud = CompactHUD.new()
	overlay.add_child(opening_hud)
	gate_button = opening_hud.gate
	tree_button = opening_hud.tree
	get_viewport().size_changed.connect(clear_touch)
	get_viewport().size_changed.connect(opening_hud.reflow)
	sync_progress_visuals()
	refresh_hud()
	bound = true

func setup_camp() -> void:
	var r: Array = layout.camp_rect_xz
	var floor := MeshInstance3D.new()
	floor.name = "CampOnlySurface"
	floor.mesh = Terrain.terrain_mesh()
	var tint := ShaderMaterial.new()
	tint.shader = FLOOR_SHADE
	tint.set_shader_parameter("bounds", Vector4(float(r[0]) + CAMP_SHIFT.x, float(r[1]) + CAMP_SHIFT.y, float(r[2]) + CAMP_SHIFT.x, float(r[3]) + CAMP_SHIFT.y))
	floor.material_override = tint
	floor.position.y = .012
	floor.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	camp_built.add_child(floor)
	for row in layout.walls_xz:
		var wall := block(camp_built, Vector3(float(row[2]), .95, float(row[3])), point([row[0], row[1]], .475), Color("#5d5148"), true) as StaticBody3D
		camp_colliders.append(wall)
	for gate in layout.gates:
		var at := point(gate.center_xz)
		var mechanism := Gate.new()
		camp_built.add_child(mechanism)
		mechanism.position = at
		mechanism.rotation_degrees.y = 0.0 if gate.orientation == "x" else 90.0
		mechanism.build(String(gate.id))
		gates.append(mechanism)
		var axis := mechanism.basis.x
		for side in [-1, 1]:
			var marker_at := at + axis * float(gate.clear_span) * .52 * float(side)
			var hinge := mechanism.get_node("HingeLeft" if side < 0 else "HingeRight") as Node3D
			var hinge_on_terrain := Terrain.sample(Vector2(at.x + axis.x * Gate.HALF_SPAN * side, at.z + axis.z * Gate.HALF_SPAN * side))
			hinge.position.y = float(hinge_on_terrain.height) - at.y
			marker_at.y = float(Terrain.sample(Vector2(marker_at.x, marker_at.z)).height) + .72
			block(camp_built, Vector3(.20, 1.44, .20), marker_at, Color("#47687a")).name = String(gate.id) + "-technical-marker"
	if GateArtReview.REVIEW_FLAG in OS.get_cmdline_user_args():
		if not GateArtReview.apply_all(gates, self, ground):
			push_warning("Gate art candidate withheld: no technical gate visuals were changed.")
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

func _physics_process(dt: float) -> void:
	if not bound or not is_finite(dt) or dt <= 0.0:
		return
	var direction := Vector2.ZERO
	if touch_id >= 0:
		direction = ((touch_now - touch_origin) / 82.0).limit_length()
	else:
		direction.x = float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT))
		direction.y = float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP))
	direction = direction.limit_length()
	var flat := Vector3(direction.x, 0, direction.y).rotated(Vector3.UP, atan2(7.0, 11.0))
	var here := Vector2(actor.position.x, actor.position.z)
	var requested := Vector2(flat.x, flat.z) * minf(4.0 * dt, 4.0 / 30.0)
	var allowed := _bounded_dry_delta(here, requested)
	actor.velocity = Vector3(allowed.x / dt, 0.0 if actor.is_on_floor() else actor.velocity.y - 9.8 * dt, allowed.y / dt)
	actor.move_and_slide()
	var observed := Vector2(actor.position.x, actor.position.z)
	if not _inside_motion_bounds(observed) or not DrySweep.dry_footprint(observed, float(layout.actor_radius), bank_side):
		# Don't transact from unexpected post-collision feet or teleport them back.
		bound = false
		push_error("Combined candidate foot ownership stopped outside admitted dry surface.")
		return
	hero_locomotion.observe(here.distance_to(observed) / dt, actor.is_on_floor())
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
		if marker.is_visible_in_tree() and _in_pickup_reach(String(row.id)):
			_collect_wood_source(String(row.id))
	fund_opening_receiver(Ledger.OFFER, "wood")

func fund_opening_receiver(receiver_id: Variant = null, material_id: Variant = null) -> bool:
	# Authorize the exact scene target, not caller-provided substitutions or quantities.
	if not bound or typeof(receiver_id) != TYPE_STRING or typeof(material_id) != TYPE_STRING:
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
	if not _within_logical_reach(pad_anchor, .72):
		return false
	var next := Ledger.new()
	if not next.restore(ledger.snapshot()) or not next.pay_center_hearth():
		return false
	return _commit_opening_progress(next)

func _input(event: InputEvent) -> void:
	if bound:
		super._input(event)
