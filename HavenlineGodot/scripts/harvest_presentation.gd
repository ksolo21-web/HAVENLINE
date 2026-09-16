class_name HavenlineHarvestPresentation
extends Node3D

## T09 presentation-only harvesting contract. T07 selects the contextual action,
## T06 owns motion/contact, simulation commits the unit, and T08 owns transfer and
## carried inventory. This node never grants, debits or saves a resource.

const AUTHORITY_ID := "T09-harvest-presentation-v1"
const CATALOG_PATH := "res://assets/harvesting_v1/catalog.json"
const MAX_FRAGMENT_DESCRIPTORS := 32
const MAX_IMPACT_PULSES := 8
const RECEIPT_WINDOW := 256
const EFFECT_LIFETIME_SECONDS := 0.48
const CONTACT_TOLERANCE := 0.035
const IMPACT_TARGET_TOLERANCE_METERS := 0.25
const RECOVERY_PORTION := 0.32
const SOURCE_RESPONSE_SECONDS := 0.34
const RESPAWN_RESPONSE_SECONDS := 0.42
const SOCKET_CONTACT_TOLERANCE_METERS := 0.25
const CONTACT_ALIGNMENT_WINDOW := 0.20
const MAX_SOURCE_SURFACE_INSET_METERS := 0.55

const RESOURCE_PROFILES := {
	"wood": {
		"method":"chop", "tool":"axe", "asset":"res://assets/harvesting_v1/axe.glb",
		"animation_profile":"human_player_chop", "contact_marker":"C1TwoHandContact",
		"impact_progress":0.56, "effect":"wood_chips", "fragment_count":6,
		"grip_socket":Vector3(0.0, -0.30, 0.0), "second_hand_socket":Vector3(0.0, 0.05, 0.0),
		"impact_socket":Vector3(0.46, 0.56, 0.0), "effect_color":Color("b96f38"),
	},
	"stone": {
		"method":"mine", "tool":"pickaxe", "asset":"res://assets/harvesting_v1/pickaxe.glb",
		"animation_profile":"human_player_mine", "contact_marker":"C1TwoHandContact",
		"impact_progress":0.58, "effect":"stone_shards", "fragment_count":5,
		"grip_socket":Vector3(0.0, -0.32, 0.0), "second_hand_socket":Vector3(0.0, 0.04, 0.0),
		"impact_socket":Vector3(0.57, 0.59, 0.0), "effect_color":Color("b8c4d1"),
	},
	"metal": {
		"method":"mine", "tool":"pickaxe", "asset":"res://assets/harvesting_v1/pickaxe.glb",
		"animation_profile":"human_player_mine", "contact_marker":"C1TwoHandContact",
		"impact_progress":0.58, "effect":"ore_glint", "fragment_count":4,
		"grip_socket":Vector3(0.0, -0.32, 0.0), "second_hand_socket":Vector3(0.0, 0.04, 0.0),
		"impact_socket":Vector3(0.57, 0.59, 0.0), "effect_color":Color("69e6ff"),
	},
	"fuel": {
		"method":"dismantle", "tool":"salvage_pry_tool", "asset":"res://assets/harvesting_v1/salvage_pry_tool.glb",
		"animation_profile":"human_player_dismantle", "contact_marker":"C1RightHandContact",
		"impact_progress":0.61, "effect":"salvage_sparks", "fragment_count":3,
		"grip_socket":Vector3(0.0, -0.38, 0.0), "second_hand_socket":Vector3.ZERO,
		"impact_socket":Vector3(0.42, 0.61, 0.0), "effect_color":Color("ffad4d"),
	},
}

var loader: Callable
var active: Dictionary = {}
var tool_nodes: Dictionary = {}
var receipts: Dictionary = {}
var receipt_order: Array[String] = []
var highest_action_identity := ""
var fragment_descriptors: Array[Dictionary] = []
var impact_pulses: Array[Dictionary] = []
var fragment_pool: Array[MeshInstance3D] = []
var pulse_pool: Array[MeshInstance3D] = []
var effect_meshes: Dictionary = {}
var source_bindings: Dictionary = {}
var accepted_impacts := 0
var rejected_impacts := 0
var attachment_updates := 0
var cancellation_count := 0
var highest_action_token := 0

static func contract() -> Dictionary:
	return {
		"authority_id":AUTHORITY_ID,
		"catalog":CATALOG_PATH,
		"resources":["wood","stone","metal","fuel"],
		"profiles":RESOURCE_PROFILES.duplicate(true),
		"maximum_equipped_tools":1,
		"maximum_fragment_descriptors":MAX_FRAGMENT_DESCRIPTORS,
		"maximum_impact_pulses":MAX_IMPACT_PULSES,
		"receipt_window":RECEIPT_WINDOW,
		"impact_target_tolerance_meters":IMPACT_TARGET_TOLERANCE_METERS,
		"socket_contact_tolerance_meters":SOCKET_CONTACT_TOLERANCE_METERS,
		"recovery_portion":RECOVERY_PORTION,
		"action_token_policy":"monotonic_with_same_identity_reentry",
		"exactly_once_key":"authoritative_receipt_id",
		"authoritative_commit_arming_required":true,
		"source_visibility_authority":"simulation_units_and_respawn_only",
		"effect_geometry":"bounded_visible_mesh_pools",
		"simulation_authoritative":true,
		"emits_gameplay_events":false,
		"mutates_inventory":false,
		"adds_save_fields":false,
		"permanent_action_buttons":0,
		"accepted_roles":["player_lead"],
		"compatible_future_roles":["core_human_companion","rescued_survivor_helper"],
	}

static func profile_for_resource(resource: String) -> Dictionary:
	var value: Variant = RESOURCE_PROFILES.get(resource, {})
	return value.duplicate(true) if value is Dictionary else {}

static func resource_for_source_id(source_id: String) -> String:
	var lowered := source_id.to_lower()
	for resource in RESOURCE_PROFILES:
		if lowered.begins_with(resource):
			return resource
	return ""

static func presentation_progress(resource: String, raw_progress: float, after_commit := false) -> float:
	var profile := profile_for_resource(resource)
	if profile.is_empty() or not is_finite(raw_progress):
		return 0.0
	var raw := clampf(raw_progress, 0.0, 1.0)
	var contact := float(profile.impact_progress)
	if not after_commit:
		return raw * contact
	if raw <= RECOVERY_PORTION:
		return lerpf(contact, 1.0, raw / RECOVERY_PORTION)
	return contact * inverse_lerp(RECOVERY_PORTION, 1.0, raw)

static func canonical_action(action: Dictionary) -> Dictionary:
	if String(action.get("kind", "")) != "gather":
		return {}
	var source_id := String(action.get("source_id", action.get("id", "")))
	var resource := String(action.get("resource", resource_for_source_id(source_id)))
	return {
		"kind":"gather", "resource":resource, "source_id":source_id,
		"action_token":int(action.get("action_token", 0)),
		"progress":float(action.get("progress", 0.0)),
		"role":String(action.get("role", "player_lead")),
		"actionable":bool(action.get("actionable", false)),
	}

static func contact_node(actor: Node3D, marker_name: String) -> Node3D:
	if not is_instance_valid(actor):
		return null
	var marker := actor.find_child(marker_name, true, false) as Node3D
	if not is_instance_valid(marker):
		return null
	var tip := marker.find_child("Contact", false, false) as Node3D
	return tip if is_instance_valid(tip) else marker

static func _contact_weight(progress: float, impact_progress: float) -> float:
	var proximity := 1.0 - clampf(absf(progress - impact_progress) / CONTACT_ALIGNMENT_WINDOW, 0.0, 1.0)
	return proximity * proximity * (3.0 - 2.0 * proximity)

static func contact_target(source_center: Vector3, attachment_transform: Transform3D,
		profile: Dictionary) -> Vector3:
	if not source_center.is_finite() or profile.is_empty():
		return source_center
	var local_reach: Vector3 = Vector3(profile.impact_socket) - Vector3(profile.grip_socket)
	var toward_hand := attachment_transform.origin - source_center
	if toward_hand.length_squared() <= 0.000001 or local_reach.length_squared() <= 0.000001:
		return source_center
	# Resolve the visual hit on the near source surface rather than its center.
	# The inset is bounded so the simulation source remains the target authority.
	var inset := clampf(toward_hand.length() - local_reach.length(), 0.0, MAX_SOURCE_SURFACE_INSET_METERS)
	return source_center + toward_hand.normalized() * inset

static func _socket_solution(attachment_transform: Transform3D, target_position: Vector3,
		profile: Dictionary, force_contact := false) -> Dictionary:
	var grip_socket: Vector3 = profile.grip_socket
	var impact_socket: Vector3 = profile.impact_socket
	var hand_basis := attachment_transform.basis.orthonormalized()
	var base_transform := Transform3D(hand_basis, attachment_transform.origin - hand_basis * grip_socket)
	var local_reach := impact_socket - grip_socket
	var world_reach := target_position - attachment_transform.origin
	if local_reach.length_squared() <= 0.000001 or world_reach.length_squared() <= 0.000001:
		return {"transform":base_transform,"grip_error_m":0.0,"impact_error_m":INF,"alignment_valid":false}
	var target_in_hand_space := hand_basis.inverse() * world_reach.normalized()
	var alignment := Basis(Quaternion(local_reach.normalized(), target_in_hand_space)).orthonormalized()
	var solved_basis := (hand_basis * alignment).orthonormalized()
	# The least-squares origin keeps the authored grip and impact sockets equally
	# close to their two authorities without scaling or deforming the finished tool.
	var grip_origin := attachment_transform.origin - solved_basis * grip_socket
	var impact_origin := target_position - solved_basis * impact_socket
	var solved_transform := Transform3D(solved_basis, (grip_origin + impact_origin) * 0.5)
	var weight := 1.0 if force_contact else _contact_weight(float(profile.get("presented_progress", 0.0)), float(profile.impact_progress))
	var presented := base_transform.interpolate_with(solved_transform, weight)
	var grip_error := (presented * grip_socket).distance_to(attachment_transform.origin)
	var impact_error := (presented * impact_socket).distance_to(target_position)
	return {
		"transform":presented,
		"grip_error_m":grip_error,
		"impact_error_m":impact_error,
		"alignment_valid":grip_error <= SOCKET_CONTACT_TOLERANCE_METERS and impact_error <= SOCKET_CONTACT_TOLERANCE_METERS,
	}

func _apply_tool_contact(tool: Node3D, attachment_transform: Transform3D,
		target_position: Vector3, profile: Dictionary, force_contact := false) -> Dictionary:
	var posed_profile := profile.duplicate(true)
	posed_profile.presented_progress = float(active.get("progress", 0.0))
	var solution := _socket_solution(attachment_transform,target_position,posed_profile,force_contact)
	tool.global_transform = solution.transform
	active.grip_error_m = float(solution.grip_error_m)
	active.impact_error_m = float(solution.impact_error_m)
	active.contact_alignment_valid = bool(solution.alignment_valid)
	return solution

static func _finite_progress(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) >= 0.0 and float(value) <= 1.0

static func valid_action(action: Variant) -> bool:
	if not action is Dictionary or String(action.get("kind", "")) != "gather":
		return false
	if String(action.get("role", "player_lead")) != "player_lead":
		return false
	if not action.get("actionable") is bool or not bool(action.actionable):
		return false
	var resource := String(action.get("resource", ""))
	if resource not in RESOURCE_PROFILES:
		return false
	if String(action.get("source_id", "")).is_empty():
		return false
	if not action.get("action_token") is int or int(action.action_token) <= 0:
		return false
	return _finite_progress(action.get("progress"))

func _instantiate_tool(tool_id: String, asset_path: String) -> Node3D:
	if tool_nodes.has(tool_id) and is_instance_valid(tool_nodes[tool_id]):
		return tool_nodes[tool_id]
	var packed: Variant = loader.call(asset_path) if loader.is_valid() else load(asset_path)
	if not packed is PackedScene:
		return null
	var instance: Variant = packed.instantiate()
	if not instance is Node3D:
		return null
	var node := instance as Node3D
	node.name = "T09_" + tool_id
	node.visible = false
	node.set_meta("t09_authored_asset", asset_path)
	node.set_meta("t09_tool_profile", tool_id)
	add_child(node)
	tool_nodes[tool_id] = node
	return node

func _hide_tools() -> void:
	for node: Variant in tool_nodes.values():
		if is_instance_valid(node):
			node.visible = false

func _effect_material(color: Color, emissive := false) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.56
	if emissive:
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.emission_enabled = true
		material.emission = color
		material.emission_energy_multiplier = 2.2
	return material

func _effect_mesh(resource: String) -> Mesh:
	if effect_meshes.has(resource):
		return effect_meshes[resource]
	var profile := profile_for_resource(resource)
	var color: Color = profile.get("effect_color", Color.WHITE)
	var mesh: PrimitiveMesh
	match resource:
		"wood":
			var chip := BoxMesh.new()
			chip.size = Vector3(0.16, 0.045, 0.055)
			mesh = chip
		"stone":
			var shard := PrismMesh.new()
			shard.size = Vector3(0.12, 0.15, 0.08)
			mesh = shard
		"metal":
			var glint := BoxMesh.new()
			glint.size = Vector3(0.035, 0.18, 0.035)
			mesh = glint
		_:
			var spark := CylinderMesh.new()
			spark.top_radius = 0.015
			spark.bottom_radius = 0.035
			spark.height = 0.16
			spark.radial_segments = 6
			mesh = spark
	mesh.material = _effect_material(color, resource in ["metal", "fuel"])
	effect_meshes[resource] = mesh
	return mesh

func _ensure_effect_pools() -> void:
	while fragment_pool.size() < MAX_FRAGMENT_DESCRIPTORS:
		var fragment := MeshInstance3D.new()
		fragment.name = "T09ImpactFragment%02d" % fragment_pool.size()
		fragment.visible = false
		fragment.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(fragment)
		fragment_pool.append(fragment)
	while pulse_pool.size() < MAX_IMPACT_PULSES:
		var pulse := MeshInstance3D.new()
		pulse.name = "T09ImpactPulse%02d" % pulse_pool.size()
		var ring := TorusMesh.new()
		ring.inner_radius = 0.18
		ring.outer_radius = 0.24
		ring.rings = 12
		ring.ring_segments = 8
		ring.material = _effect_material(Color("79ecff"), true)
		pulse.mesh = ring
		pulse.visible = false
		pulse.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(pulse)
		pulse_pool.append(pulse)

func _available_pool_index(pool: Array, active_rows: Array) -> int:
	var used := {}
	for row in active_rows:
		used[int(row.get("pool_index", -1))] = true
	for index in pool.size():
		if not used.has(index):
			return index
	return -1

func bind_source(source_id: String, resource: String, visual: Node3D, units: int) -> bool:
	if source_id.is_empty() or resource not in RESOURCE_PROFILES or not is_instance_valid(visual) or units < 0:
		return false
	source_bindings[source_id] = {
		"resource":resource, "visual":visual, "base_transform":visual.transform,
		"units":units, "respawn":0.0, "response_age":SOURCE_RESPONSE_SECONDS,
		"respawn_age":RESPAWN_RESPONSE_SECONDS,
	}
	visual.visible = units > 0
	return true

func sync_source(source_id: String, units: int, respawn: float) -> bool:
	if not source_bindings.has(source_id) or units < 0 or not is_finite(respawn) or respawn < 0.0:
		return false
	var binding: Dictionary = source_bindings[source_id]
	var visual: Node3D = binding.visual
	if not is_instance_valid(visual):
		source_bindings.erase(source_id)
		return false
	var previous_units := int(binding.units)
	binding.units = units
	binding.respawn = respawn
	if previous_units <= 0 and units > 0:
		binding.respawn_age = 0.0
	visual.visible = units > 0
	if units <= 0:
		visual.transform = binding.base_transform
	source_bindings[source_id] = binding
	return true

func begin_action(action: Dictionary, actor_id := -1) -> bool:
	if not valid_action(action) or actor_id < 0:
		return false
	var action_token := int(action.action_token)
	var token_identity := "%d:%s:%s" % [actor_id, String(action.source_id), String(action.resource)]
	if action_token < highest_action_token:
		return false
	if action_token == highest_action_token and highest_action_identity != token_identity:
		return false
	var profile := profile_for_resource(String(action.resource))
	var tool := _instantiate_tool(String(profile.tool), String(profile.asset))
	if tool == null:
		return false
	_hide_tools()
	tool.visible = true
	var same_identity: bool = not active.is_empty() and int(active.get("action_token", -1)) == action_token and String(active.get("source_id", "")) == String(action.source_id) and int(active.get("actor_id", -1)) == actor_id
	var committed_before := bool(active.get("has_committed", false)) if same_identity else false
	active = {
		"resource":String(action.resource), "source_id":String(action.source_id),
		"action_token":action_token, "actor_id":actor_id,
		"raw_progress":float(action.progress), "progress":presentation_progress(String(action.resource), float(action.progress), committed_before), "profile":profile,
		"tool":tool, "last_cancel_reason":"", "has_committed":committed_before,
		"commit_contact_armed":false,
	}
	if action_token > highest_action_token:
		highest_action_token = action_token
		highest_action_identity = token_identity
	return true

func update_action(action: Dictionary, attachment_transform: Transform3D,
		target_position: Vector3, actor_present := true) -> Dictionary:
	if not actor_present:
		cancel("actor_not_presented")
		return descriptor()
	if not valid_action(action) or active.is_empty():
		cancel("invalid_or_inactive_action")
		return descriptor()
	if int(action.action_token) != int(active.action_token) or String(action.source_id) != String(active.source_id) or String(action.resource) != String(active.resource):
		cancel("action_identity_changed")
		return descriptor()
	if not target_position.is_finite():
		cancel("invalid_target")
		return descriptor()
	var profile: Dictionary = active.profile
	var tool: Node3D = active.tool
	active.raw_progress = float(action.progress)
	active.progress = presentation_progress(String(active.resource), float(action.progress), bool(active.get("has_committed", false)))
	active.target_position = target_position
	var solution := _apply_tool_contact(tool,attachment_transform,target_position,profile)
	active.contact_ready = absf(float(active.progress) - float(profile.impact_progress)) <= CONTACT_TOLERANCE and bool(solution.alignment_valid)
	active.commit_contact_armed = false
	attachment_updates += 1
	return descriptor()

func synchronize_committed_contact(action: Dictionary, attachment_transform: Transform3D,
		target_position: Vector3, actor_id: int) -> Dictionary:
	if not valid_action(action) or actor_id < 0 or not target_position.is_finite():
		return descriptor()
	if active.is_empty() or int(active.get("action_token", -1)) != int(action.action_token) or String(active.get("source_id", "")) != String(action.source_id) or int(active.get("actor_id", -1)) != actor_id:
		if not begin_action(action, actor_id):
			return descriptor()
	var profile: Dictionary = active.profile
	var tool: Node3D = active.tool
	active.raw_progress = float(action.progress)
	active.progress = float(profile.impact_progress)
	active.target_position = target_position
	var solution := _apply_tool_contact(tool,attachment_transform,target_position,profile,true)
	active.contact_ready = bool(solution.alignment_valid)
	active.commit_contact_armed = bool(solution.alignment_valid)
	attachment_updates += 1
	return descriptor()

func motion_action(action: Dictionary) -> Dictionary:
	var canonical := canonical_action(action)
	if canonical.is_empty() or not valid_action(canonical):
		return action.duplicate(true)
	var same_identity: bool = not active.is_empty() and int(active.get("action_token", -1)) == int(canonical.action_token) and String(active.get("source_id", "")) == String(canonical.source_id)
	var result := action.duplicate(true)
	result["progress"] = presentation_progress(String(canonical.resource), float(canonical.progress), same_identity and bool(active.get("has_committed", false)))
	return result

func _remember_receipt(receipt_id: String) -> void:
	receipts[receipt_id] = true
	receipt_order.append(receipt_id)
	while receipt_order.size() > RECEIPT_WINDOW:
		var expired: String = receipt_order.pop_front()
		receipts.erase(expired)

func accept_committed_impact(receipt: Dictionary) -> bool:
	if active.is_empty() or not receipt.get("committed") is bool or not bool(receipt.committed) or not bool(active.get("commit_contact_armed", false)):
		rejected_impacts += 1
		return false
	var receipt_id := String(receipt.get("receipt_id", ""))
	if receipt_id.is_empty() or receipts.has(receipt_id):
		rejected_impacts += 1
		return false
	if int(receipt.get("action_token", -1)) != int(active.action_token) or String(receipt.get("source_id", "")) != String(active.source_id) or String(receipt.get("resource", "")) != String(active.resource):
		rejected_impacts += 1
		return false
	if not receipt.get("actor_id") is int or int(receipt.actor_id) != int(active.actor_id):
		rejected_impacts += 1
		return false
	if not bool(active.get("contact_ready", false)):
		rejected_impacts += 1
		return false
	var target: Variant = receipt.get("target_position")
	if not target is Vector3 or not target.is_finite():
		rejected_impacts += 1
		return false
	var target_position: Vector3 = target
	var presented_target: Variant = active.get("target_position")
	if not presented_target is Vector3 or not presented_target.is_finite() or target_position.distance_to(presented_target) > IMPACT_TARGET_TOLERANCE_METERS:
		rejected_impacts += 1
		return false
	var profile: Dictionary = active.profile
	_remember_receipt(receipt_id)
	_ensure_effect_pools()
	var count := mini(int(profile.fragment_count), MAX_FRAGMENT_DESCRIPTORS - fragment_descriptors.size())
	for index in count:
		var pool_index := _available_pool_index(fragment_pool, fragment_descriptors)
		if pool_index < 0:
			break
		var effect_node := fragment_pool[pool_index]
		effect_node.mesh = _effect_mesh(String(active.resource))
		effect_node.global_position = target_position
		effect_node.scale = Vector3.ONE
		effect_node.visible = true
		var angle := TAU * float(index) / maxf(1.0, float(count)) + float(accepted_impacts) * 0.47
		var outward := Vector3(cos(angle), 0.0, sin(angle))
		fragment_descriptors.append({
			"effect":String(profile.effect), "resource":String(active.resource),
			"position":target_position, "index":index, "age":0.0, "node":effect_node, "pool_index":pool_index,
			"velocity":outward * (0.55 + 0.08 * index) + Vector3.UP * (1.35 + 0.12 * index),
			"spin":Vector3(4.0 + index, 7.0 - index * 0.3, 3.0 + index * 0.5),
		})
	if impact_pulses.size() >= MAX_IMPACT_PULSES:
		var expired_pulse: Dictionary = impact_pulses.pop_front()
		if is_instance_valid(expired_pulse.get("node")):
			expired_pulse.node.visible = false
	var pulse_pool_index := _available_pool_index(pulse_pool, impact_pulses)
	if pulse_pool_index < 0:
		return false
	var pulse_node := pulse_pool[pulse_pool_index]
	pulse_node.global_position = target_position + Vector3.UP * 0.03
	pulse_node.scale = Vector3.ONE
	pulse_node.visible = true
	impact_pulses.append({
		"effect":String(profile.effect), "resource":String(active.resource),
		"position":target_position, "age":0.0, "receipt_id":receipt_id, "node":pulse_node, "pool_index":pulse_pool_index,
	})
	if source_bindings.has(String(active.source_id)):
		var binding: Dictionary = source_bindings[String(active.source_id)]
		binding.response_age = 0.0
		source_bindings[String(active.source_id)] = binding
	active.has_committed = true
	active.commit_contact_armed = false
	accepted_impacts += 1
	return true

func cancel(reason := "cancelled") -> void:
	if not active.is_empty():
		cancellation_count += 1
	_hide_tools()
	active = {"last_cancel_reason":reason} if not reason.is_empty() else {}

func reset() -> void:
	_hide_tools()
	active = {}
	fragment_descriptors.clear()
	impact_pulses.clear()
	for node in fragment_pool:
		if is_instance_valid(node): node.visible = false
	for node in pulse_pool:
		if is_instance_valid(node): node.visible = false
	for binding in source_bindings.values():
		if is_instance_valid(binding.visual): binding.visual.transform = binding.base_transform
	receipts.clear()
	receipt_order.clear()
	highest_action_identity = ""
	accepted_impacts = 0
	rejected_impacts = 0
	attachment_updates = 0
	cancellation_count = 0
	highest_action_token = 0

func _process(delta: float) -> void:
	if delta <= 0.0 or not is_finite(delta):
		return
	for index in range(fragment_descriptors.size() - 1, -1, -1):
		var fragment: Dictionary = fragment_descriptors[index]
		fragment.age = float(fragment.age) + delta
		var node: MeshInstance3D = fragment.node
		if is_instance_valid(node):
			fragment.velocity += Vector3.DOWN * 4.8 * delta
			node.global_position += Vector3(fragment.velocity) * delta
			node.rotation += Vector3(fragment.spin) * delta
			node.scale = Vector3.ONE * (1.0 - 0.55 * clampf(float(fragment.age) / EFFECT_LIFETIME_SECONDS, 0.0, 1.0))
		if float(fragment.age) >= EFFECT_LIFETIME_SECONDS:
			if is_instance_valid(node): node.visible = false
			fragment_descriptors.remove_at(index)
	for index in range(impact_pulses.size() - 1, -1, -1):
		var pulse: Dictionary = impact_pulses[index]
		pulse.age = float(pulse.age) + delta
		var pulse_node: MeshInstance3D = pulse.node
		if is_instance_valid(pulse_node):
			var amount := clampf(float(pulse.age) / EFFECT_LIFETIME_SECONDS, 0.0, 1.0)
			pulse_node.scale = Vector3.ONE * lerpf(0.75, 2.35, amount)
		if float(pulse.age) >= EFFECT_LIFETIME_SECONDS:
			if is_instance_valid(pulse_node): pulse_node.visible = false
			impact_pulses.remove_at(index)
	for source_id in source_bindings:
		var binding: Dictionary = source_bindings[source_id]
		var visual: Node3D = binding.visual
		if not is_instance_valid(visual):
			continue
		binding.response_age = minf(SOURCE_RESPONSE_SECONDS, float(binding.response_age) + delta)
		binding.respawn_age = minf(RESPAWN_RESPONSE_SECONDS, float(binding.respawn_age) + delta)
		var response_t := float(binding.response_age) / SOURCE_RESPONSE_SECONDS
		var respawn_t := float(binding.respawn_age) / RESPAWN_RESPONSE_SECONDS
		var response_weight := (1.0 - response_t) * sin(response_t * PI)
		var respawn_scale := lerpf(0.58, 1.0, respawn_t * respawn_t * (3.0 - 2.0 * respawn_t))
		var base: Transform3D = binding.base_transform
		var wobble := Basis(Vector3.UP, response_weight * 0.10)
		visual.transform = Transform3D(base.basis * wobble.scaled(Vector3(1.0 + response_weight * 0.05, 1.0 - response_weight * 0.08, 1.0 + response_weight * 0.05) * respawn_scale), base.origin)
		source_bindings[source_id] = binding

func descriptor() -> Dictionary:
	var presented: bool = false
	if not active.is_empty() and active.has("tool") and is_instance_valid(active.tool):
		var active_tool: Node3D = active.tool
		presented = active_tool.visible
	return {
		"authority_id":AUTHORITY_ID,
		"active":presented,
		"resource":String(active.get("resource", "")),
		"source_id":String(active.get("source_id", "")),
		"action_token":int(active.get("action_token", 0)),
		"highest_action_token":highest_action_token,
		"tracked_action_tokens":0 if highest_action_identity.is_empty() else 1,
		"progress":float(active.get("progress", 0.0)),
		"raw_progress":float(active.get("raw_progress", 0.0)),
		"tool":String(active.get("profile", {}).get("tool", "")),
		"contact_marker":String(active.get("profile", {}).get("contact_marker", "")),
		"contact_ready":bool(active.get("contact_ready", false)),
		"commit_contact_armed":bool(active.get("commit_contact_armed", false)),
		"contact_alignment_valid":bool(active.get("contact_alignment_valid", false)),
		"grip_error_m":float(active.get("grip_error_m", INF)),
		"impact_error_m":float(active.get("impact_error_m", INF)),
		"has_committed_in_context":bool(active.get("has_committed", false)),
		"last_cancel_reason":String(active.get("last_cancel_reason", "")),
		"active_fragment_descriptors":fragment_descriptors.size(),
		"active_impact_pulses":impact_pulses.size(),
		"remembered_receipts":receipts.size(),
		"accepted_impacts":accepted_impacts,
		"rejected_impacts":rejected_impacts,
		"attachment_updates":attachment_updates,
		"cancellation_count":cancellation_count,
		"bound_sources":source_bindings.size(),
		"visible_fragment_nodes":fragment_descriptors.size(),
		"visible_pulse_nodes":impact_pulses.size(),
		"mutates_inventory":false,
		"emits_gameplay_events":false,
	}
