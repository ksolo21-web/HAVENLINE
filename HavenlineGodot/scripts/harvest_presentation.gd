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

const RESOURCE_PROFILES := {
	"wood": {
		"method":"chop", "tool":"axe", "asset":"res://assets/harvesting_v1/axe.glb",
		"animation_profile":"human_player_chop", "contact_marker":"C1TwoHandContact",
		"impact_progress":0.56, "effect":"wood_chips", "fragment_count":6,
		"grip_offset":Vector3(0.0, -0.08, 0.0),
	},
	"stone": {
		"method":"mine", "tool":"pickaxe", "asset":"res://assets/harvesting_v1/pickaxe.glb",
		"animation_profile":"human_player_mine", "contact_marker":"C1TwoHandContact",
		"impact_progress":0.58, "effect":"stone_shards", "fragment_count":5,
		"grip_offset":Vector3(0.0, -0.06, 0.0),
	},
	"metal": {
		"method":"mine", "tool":"pickaxe", "asset":"res://assets/harvesting_v1/pickaxe.glb",
		"animation_profile":"human_player_mine", "contact_marker":"C1TwoHandContact",
		"impact_progress":0.58, "effect":"ore_glint", "fragment_count":4,
		"grip_offset":Vector3(0.0, -0.06, 0.0),
	},
	"fuel": {
		"method":"dismantle", "tool":"salvage_pry_tool", "asset":"res://assets/harvesting_v1/salvage_pry_tool.glb",
		"animation_profile":"human_player_dismantle", "contact_marker":"C1RightHandContact",
		"impact_progress":0.61, "effect":"salvage_sparks", "fragment_count":3,
		"grip_offset":Vector3(0.0, -0.30, 0.0),
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
		"action_token_policy":"monotonic_with_same_identity_reentry",
		"exactly_once_key":"authoritative_receipt_id",
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
	active = {
		"resource":String(action.resource), "source_id":String(action.source_id),
		"action_token":action_token, "actor_id":actor_id,
		"progress":float(action.progress), "profile":profile,
		"tool":tool, "last_cancel_reason":"",
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
	var grip_offset: Vector3 = profile.grip_offset
	tool.global_transform = attachment_transform * Transform3D(Basis.IDENTITY, grip_offset)
	active.progress = float(action.progress)
	active.target_position = target_position
	active.contact_ready = absf(float(active.progress) - float(profile.impact_progress)) <= CONTACT_TOLERANCE
	attachment_updates += 1
	return descriptor()

func _remember_receipt(receipt_id: String) -> void:
	receipts[receipt_id] = true
	receipt_order.append(receipt_id)
	while receipt_order.size() > RECEIPT_WINDOW:
		var expired: String = receipt_order.pop_front()
		receipts.erase(expired)

func accept_committed_impact(receipt: Dictionary) -> bool:
	if active.is_empty() or not receipt.get("committed") is bool or not bool(receipt.committed):
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
	var count := mini(int(profile.fragment_count), MAX_FRAGMENT_DESCRIPTORS - fragment_descriptors.size())
	for index in count:
		fragment_descriptors.append({
			"effect":String(profile.effect), "resource":String(active.resource),
			"position":target_position, "index":index, "age":0.0,
		})
	if impact_pulses.size() >= MAX_IMPACT_PULSES:
		impact_pulses.pop_front()
	impact_pulses.append({
		"effect":String(profile.effect), "resource":String(active.resource),
		"position":target_position, "age":0.0, "receipt_id":receipt_id,
	})
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
		fragment_descriptors[index].age = float(fragment_descriptors[index].age) + delta
		if float(fragment_descriptors[index].age) >= EFFECT_LIFETIME_SECONDS:
			fragment_descriptors.remove_at(index)
	for index in range(impact_pulses.size() - 1, -1, -1):
		impact_pulses[index].age = float(impact_pulses[index].age) + delta
		if float(impact_pulses[index].age) >= EFFECT_LIFETIME_SECONDS:
			impact_pulses.remove_at(index)

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
		"tool":String(active.get("profile", {}).get("tool", "")),
		"contact_marker":String(active.get("profile", {}).get("contact_marker", "")),
		"contact_ready":bool(active.get("contact_ready", false)),
		"last_cancel_reason":String(active.get("last_cancel_reason", "")),
		"active_fragment_descriptors":fragment_descriptors.size(),
		"active_impact_pulses":impact_pulses.size(),
		"remembered_receipts":receipts.size(),
		"accepted_impacts":accepted_impacts,
		"rejected_impacts":rejected_impacts,
		"attachment_updates":attachment_updates,
		"cancellation_count":cancellation_count,
		"mutates_inventory":false,
		"emits_gameplay_events":false,
	}
