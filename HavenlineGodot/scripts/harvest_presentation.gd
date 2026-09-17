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
const EFFECT_LIFETIME_SECONDS := 0.12
const CONTACT_TOLERANCE := 0.035
const IMPACT_TARGET_TOLERANCE_METERS := 0.25
const RECOVERY_PORTION := 0.32
const SOURCE_RESPONSE_SECONDS := 0.34
const RESPAWN_RESPONSE_SECONDS := 0.42
const SOCKET_CONTACT_TOLERANCE_METERS := 0.025
const SECOND_HAND_TOLERANCE_METERS := 0.045
const TWO_HAND_GRIP_LIFT_METERS := 0.07
const MAX_GRIP_SETTLE_METERS := 0.16
const MAX_DISTRIBUTED_ARM_EXTENSION_METERS := 0.34
const CONTACT_ALIGNMENT_WINDOW := 0.20
const MAX_SOURCE_SURFACE_INSET_METERS := 0.75
const MIN_HEAD_CLEARANCE_METERS := 0.18

const RESOURCE_PROFILES := {
	"wood": {
		"method":"chop", "tool":"axe", "asset":"res://assets/harvesting_v1/axe.glb",
		"animation_profile":"human_player_chop", "contact_marker":"C1TwoHandContact",
		"primary_grip_marker":"C1RightHandContact", "secondary_grip_marker":"C1LeftHandContact",
		"impact_progress":0.56, "effect":"wood_chips", "fragment_count":2,
		"grip_socket":Vector3(0.0, -0.10, 0.0), "second_hand_socket":Vector3(0.0, -0.26, 0.0),
		"impact_socket":Vector3(0.29, 0.13, 0.0), "source_contact_height":0.84, "source_contact_radius":0.10,
		"impact_height_offset":0.0, "impact_surface_offset":0.34, "maximum_surface_adjust":0.0, "two_hand_grip_lift":0.0, "effect_color":Color("b96f38"),
	},
	"stone": {
		"method":"mine", "tool":"pickaxe", "asset":"res://assets/harvesting_v1/pickaxe.glb",
		"animation_profile":"human_player_mine", "contact_marker":"C1TwoHandContact",
		"primary_grip_marker":"C1RightHandContact", "secondary_grip_marker":"C1LeftHandContact",
		"impact_progress":0.58, "effect":"stone_shards", "fragment_count":2,
		"grip_socket":Vector3(0.0, -0.08, 0.0), "second_hand_socket":Vector3(0.0, -0.24, 0.0),
		"second_hand_grip_range":Vector2(-0.44,-0.22),
		"impact_socket":Vector3(0.28, 0.14, 0.0), "source_contact_height":0.56, "source_contact_radius":0.84,
		"impact_height_offset":0.0, "impact_surface_offset":0.30, "effect_color":Color("b8c4d1"),
	},
	"metal": {
		"method":"mine", "tool":"pickaxe", "asset":"res://assets/harvesting_v1/pickaxe.glb",
		"animation_profile":"human_player_mine", "contact_marker":"C1TwoHandContact",
		"primary_grip_marker":"C1RightHandContact", "secondary_grip_marker":"C1LeftHandContact",
		"impact_progress":0.58, "effect":"ore_glint", "fragment_count":1,
		"grip_socket":Vector3(0.0, -0.08, 0.0), "second_hand_socket":Vector3(0.0, -0.24, 0.0),
		"second_hand_grip_range":Vector2(-0.44,-0.22),
		"impact_socket":Vector3(0.28, 0.14, 0.0), "source_contact_height":0.56, "source_contact_radius":0.84,
		"impact_height_offset":0.0, "impact_surface_offset":0.30, "effect_color":Color("69e6ff"),
	},
	"fuel": {
		"method":"dismantle", "tool":"salvage_pry_tool", "asset":"res://assets/harvesting_v1/salvage_pry_tool.glb",
		"animation_profile":"human_player_dismantle", "contact_marker":"C1RightHandContact",
		"primary_grip_marker":"C1RightHandContact", "secondary_grip_marker":"",
		"impact_progress":0.61, "effect":"salvage_sparks", "fragment_count":1,
		"grip_socket":Vector3(0.0, -0.20, 0.0), "second_hand_socket":Vector3.ZERO,
		"impact_socket":Vector3(0.28, 0.43, 0.0), "source_contact_height":0.52, "source_contact_radius":0.68,
		"impact_height_offset":0.0, "impact_surface_offset":0.22, "effect_color":Color("ffad4d"),
	},
}

var loader: Callable
var active: Dictionary = {}
var tool_nodes: Dictionary = {}
var tool_palette_material: StandardMaterial3D
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
var bound_actor: Node3D
var last_committed_pose_identity := ""
var last_committed_tool_transform := Transform3D.IDENTITY
var last_rejected_impact_reason := ""
var last_commit_solution: Dictionary = {}

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
		"second_hand_tolerance_meters":SECOND_HAND_TOLERANCE_METERS,
		"maximum_grip_settle_meters":MAX_GRIP_SETTLE_METERS,
		"maximum_distributed_arm_extension_meters":MAX_DISTRIBUTED_ARM_EXTENSION_METERS,
		"minimum_head_clearance_meters":MIN_HEAD_CLEARANCE_METERS,
		"source_contact_policy":"authored_visible_surface_anchor",
		"recovery_portion":RECOVERY_PORTION,
		"action_token_policy":"monotonic_with_same_identity_reentry",
		"exactly_once_key":"authoritative_receipt_id",
		"authoritative_commit_arming_required":true,
		"source_visibility_authority":"simulation_units_and_respawn_only",
		"effect_geometry":"bounded_visible_mesh_pools",
		"effect_readability":"brief_non_occluding_contact_burst",
		"equipped_tool_shadow_mode":"disabled_micro_prop",
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

static func contact_transform(actor: Node3D, marker_name: String) -> Transform3D:
	var marker := contact_node(actor,marker_name)
	if not is_instance_valid(marker):
		return Transform3D.IDENTITY
	if actor.has_meta("t06_motion_skeleton") and marker_name in ["C1RightHandContact","C1LeftHandContact"]:
		var skeleton: Variant = actor.get_meta("t06_motion_skeleton")
		if skeleton is Skeleton3D:
			var bone_name := "R_Hand" if marker_name == "C1RightHandContact" else "L_Hand"
			var bone: int = skeleton.find_bone(bone_name)
			if bone >= 0:
				return skeleton.global_transform*skeleton.get_bone_global_pose(bone)
	return marker.global_transform

static func attachment_transform(actor: Node3D, profile: Dictionary) -> Transform3D:
	var result := contact_transform(actor,String(profile.get("contact_marker","")))
	if not String(profile.get("secondary_grip_marker","")).is_empty():
		var primary := contact_transform(actor,String(profile.get("primary_grip_marker","")))
		var secondary := contact_transform(actor,String(profile.get("secondary_grip_marker","")))
		# Palm contacts sit below the mitten center. Lift the shared handle axis by
		# the measured palm radius so both gloves close around, rather than under, it.
		result.origin = (primary.origin+secondary.origin)*0.5+Vector3.UP*float(profile.get("two_hand_grip_lift",TWO_HAND_GRIP_LIFT_METERS))
	return result

func bind_actor(actor: Node3D) -> bool:
	if not is_instance_valid(actor):
		bound_actor = null
		return false
	bound_actor = actor
	return is_instance_valid(contact_node(actor,"C1RightHandContact")) and is_instance_valid(contact_node(actor,"C1LeftHandContact"))

func prepare_actor_contact(actor: Node3D) -> bool:
	# Sample attachment transforms from the animation pose, never from the arm
	# overrides left by the previous harvest frame or committed impact.
	if not bind_actor(actor):
		return false
	_clear_grip_pose()
	return true

func _bound_skeleton() -> Skeleton3D:
	if not is_instance_valid(bound_actor) or not bound_actor.has_meta("t06_motion_skeleton"):
		return null
	var value: Variant = bound_actor.get_meta("t06_motion_skeleton")
	return value as Skeleton3D if value is Skeleton3D else null

func _head_position() -> Variant:
	var skeleton := _bound_skeleton()
	if not is_instance_valid(skeleton):
		return null
	var head := skeleton.find_bone("Head")
	if head < 0:
		return null
	return skeleton.global_transform*skeleton.get_bone_global_pose(head).origin

func _arm_reach(side: String) -> Dictionary:
	var skeleton := _bound_skeleton()
	if not is_instance_valid(skeleton):
		return {}
	var upper := skeleton.find_bone(side+"_Upperarm")
	var forearm := skeleton.find_bone(side+"_Forearm")
	var hand := skeleton.find_bone(side+"_Hand")
	if upper < 0 or forearm < 0 or hand < 0:
		return {}
	var shoulder_local := skeleton.get_bone_global_pose(upper).origin
	var elbow_local := skeleton.get_bone_global_pose(forearm).origin
	var wrist_local := skeleton.get_bone_global_pose(hand).origin
	return {
		"shoulder":skeleton.global_transform*shoulder_local,
		"reach":(skeleton.global_transform.basis*(elbow_local-shoulder_local)).length()+(skeleton.global_transform.basis*(wrist_local-elbow_local)).length(),
	}

func _clear_grip_pose() -> void:
	var skeleton := _bound_skeleton()
	if is_instance_valid(skeleton):
		skeleton.clear_bones_global_pose_override()
		skeleton.force_update_all_bone_transforms()

static func _safe_perpendicular(direction: Vector3, preferred: Vector3) -> Vector3:
	var result := preferred - direction * preferred.dot(direction)
	if result.length_squared() <= 0.000001:
		result = Vector3.UP.cross(direction)
	if result.length_squared() <= 0.000001:
		result = Vector3.RIGHT.cross(direction)
	return result.normalized()

func _pose_arm_contact(side: String, target_world: Vector3, weight: float) -> void:
	var skeleton := _bound_skeleton()
	if not is_instance_valid(skeleton) or weight <= 0.0001:
		return
	var upper := skeleton.find_bone(side + "_Upperarm")
	var forearm := skeleton.find_bone(side + "_Forearm")
	var hand := skeleton.find_bone(side + "_Hand")
	var marker := contact_node(bound_actor,"C1RightHandContact" if side == "R" else "C1LeftHandContact")
	if upper < 0 or forearm < 0 or hand < 0 or not is_instance_valid(marker):
		return
	var skeleton_inverse := skeleton.global_transform.affine_inverse()
	var upper_pose := skeleton.get_bone_global_pose(upper)
	var forearm_pose := skeleton.get_bone_global_pose(forearm)
	var hand_pose := skeleton.get_bone_global_pose(hand)
	var current_contact := skeleton_inverse * contact_transform(bound_actor,"C1RightHandContact" if side == "R" else "C1LeftHandContact").origin
	var target_contact := skeleton_inverse * target_world
	target_contact = current_contact.lerp(target_contact,clampf(weight,0.0,1.0))
	var contact_offset_local := hand_pose.basis.inverse() * (current_contact-hand_pose.origin)
	var target_wrist := target_contact - hand_pose.basis*contact_offset_local
	var shoulder := upper_pose.origin
	var elbow := forearm_pose.origin
	var wrist := hand_pose.origin
	var upper_length := shoulder.distance_to(elbow)
	var lower_length := elbow.distance_to(wrist)
	var reach := target_wrist - shoulder
	active[side+"_arm_target_distance_m"] = reach.length()
	var distance := clampf(reach.length(),absf(upper_length-lower_length)+0.0001,upper_length+lower_length-0.0001)
	active[side+"_arm_max_reach_m"] = upper_length+lower_length
	if distance <= 0.0001 or upper_length <= 0.0001 or lower_length <= 0.0001:
		return
	var direction := reach.normalized()
	var bend := _safe_perpendicular(direction,elbow-shoulder)
	var along := (upper_length*upper_length-lower_length*lower_length+distance*distance)/(2.0*distance)
	var height := sqrt(maxf(0.0,upper_length*upper_length-along*along))
	for iteration in 3:
		var solved_elbow := shoulder + direction*along + bend*height
		var upper_rotation := Quaternion((elbow-shoulder).normalized(),(solved_elbow-shoulder).normalized())
		var solved_upper := Transform3D(Basis(upper_rotation)*upper_pose.basis,shoulder)
		skeleton.set_bone_global_pose_override(upper,solved_upper,1.0,true)
		skeleton.force_update_all_bone_transforms()
		var moved_forearm := skeleton.get_bone_global_pose(forearm)
		moved_forearm.origin = solved_elbow
		var moved_hand := skeleton.get_bone_global_pose(hand)
		var lower_direction := (moved_hand.origin-skeleton.get_bone_global_pose(forearm).origin).normalized()
		var desired_lower := (target_wrist-moved_forearm.origin).normalized()
		if lower_direction.length_squared() <= 0.000001 or desired_lower.length_squared() <= 0.000001:
			return
		var forearm_rotation := Quaternion(lower_direction,desired_lower)
		var solved_forearm := Transform3D(Basis(forearm_rotation)*moved_forearm.basis,moved_forearm.origin)
		skeleton.set_bone_global_pose_override(forearm,solved_forearm,1.0,true)
		skeleton.force_update_all_bone_transforms()
		var solved_hand := skeleton.get_bone_global_pose(hand)
		solved_hand.origin = moved_forearm.origin+desired_lower*lower_length
		skeleton.set_bone_global_pose_override(hand,solved_hand,1.0,true)
		skeleton.force_update_all_bone_transforms()
		solved_hand = skeleton.get_bone_global_pose(hand)
		var solved_contact := solved_hand.origin + solved_hand.basis*contact_offset_local
		var residual := target_contact-solved_contact
		if residual.length() <= 0.0005:
			break
		target_wrist += residual
		reach = target_wrist-shoulder
		distance = clampf(reach.length(),absf(upper_length-lower_length)+0.0001,upper_length+lower_length-0.0001)
		direction = reach.normalized()
		bend = _safe_perpendicular(direction,elbow-shoulder)
		along = (upper_length*upper_length-lower_length*lower_length+distance*distance)/(2.0*distance)
		height = sqrt(maxf(0.0,upper_length*upper_length-along*along))
	# Distribute the small remaining mitten/palm offset across the sleeve and hand.
	# Larger unreachable targets are left untouched and fail the socket gate.
	var settled_hand := skeleton.get_bone_global_pose(hand)
	var settled_contact := settled_hand.origin+settled_hand.basis*contact_offset_local
	var settle_residual := target_contact-settled_contact
	var world_residual := skeleton.global_transform.basis*settle_residual
	active[side+"_arm_residual_m"] = world_residual.length()
	active[side+"_distributed_extension_m"] = 0.0
	if world_residual.length() > MAX_GRIP_SETTLE_METERS and world_residual.length() <= MAX_DISTRIBUTED_ARM_EXTENSION_METERS:
		var clavicle := skeleton.find_bone(side+"_Clavicle")
		var chain := [[clavicle,0.18],[upper,0.38],[forearm,0.68],[hand,1.0]]
		for row in chain:
			if int(row[0]) < 0:
				continue
			var chain_pose := skeleton.get_bone_global_pose(int(row[0]))
			chain_pose.origin += settle_residual*float(row[1])
			skeleton.set_bone_global_pose_override(int(row[0]),chain_pose,1.0,true)
		skeleton.force_update_all_bone_transforms()
		active[side+"_distributed_extension_m"] = world_residual.length()
		settled_hand = skeleton.get_bone_global_pose(hand)
		settled_contact = settled_hand.origin+settled_hand.basis*contact_offset_local
		settle_residual = target_contact-settled_contact
		world_residual = skeleton.global_transform.basis*settle_residual
	if world_residual.length() <= MAX_GRIP_SETTLE_METERS:
		var settled_forearm := skeleton.get_bone_global_pose(forearm)
		settled_forearm.origin += settle_residual*0.5
		skeleton.set_bone_global_pose_override(forearm,settled_forearm,1.0,true)
		skeleton.force_update_all_bone_transforms()
		settled_hand = skeleton.get_bone_global_pose(hand)
		settled_contact = settled_hand.origin+settled_hand.basis*contact_offset_local
		settled_hand.origin += target_contact-settled_contact
		skeleton.set_bone_global_pose_override(hand,settled_hand,1.0,true)
		skeleton.force_update_all_bone_transforms()

static func _contact_weight(progress: float, impact_progress: float) -> float:
	var proximity := 1.0 - clampf(absf(progress - impact_progress) / CONTACT_ALIGNMENT_WINDOW, 0.0, 1.0)
	return proximity * proximity * (3.0 - 2.0 * proximity)

static func _anchor_socket(profile: Dictionary) -> Vector3:
	var grip: Vector3 = profile.grip_socket
	return (grip+Vector3(profile.second_hand_socket))*0.5 if not String(profile.get("secondary_grip_marker","")).is_empty() else grip

static func contact_target(source_center: Vector3, attachment_transform: Transform3D,
		profile: Dictionary) -> Vector3:
	if not source_center.is_finite() or profile.is_empty():
		return source_center
	var target_center := source_center+Vector3.UP*float(profile.get("impact_height_offset",0.0))
	var toward_hand := attachment_transform.origin-target_center
	var local_reach: Vector3 = Vector3(profile.impact_socket)-_anchor_socket(profile)
	if toward_hand.length_squared() <= 0.000001 or local_reach.length_squared() <= 0.000001:
		return target_center
	# Each opening source exposes a bounded presentation surface. The logical
	# source center remains authoritative, while the tool head lands on the near
	# visible face instead of disappearing into the source mesh. Keep the authored
	# surface preference within the arm solver's bounded settle distance from the
	# exact fixed-length reach, so close and far interaction-annulus positions are
	# both anatomically reachable.
	var reach_fit_offset := toward_hand.length()-local_reach.length()
	var authored_offset := float(profile.get("impact_surface_offset",0.0))
	var adjustment_limit := minf(MAX_GRIP_SETTLE_METERS*0.75,float(profile.get("maximum_surface_adjust",MAX_GRIP_SETTLE_METERS*0.75)))
	var surface_offset := reach_fit_offset+clampf(authored_offset-reach_fit_offset,-adjustment_limit,adjustment_limit)
	surface_offset = clampf(surface_offset,-MAX_SOURCE_SURFACE_INSET_METERS,MAX_SOURCE_SURFACE_INSET_METERS)
	return target_center+toward_hand.normalized()*surface_offset

static func source_contact_target(source_visual: Node3D, attachment_transform: Transform3D,
		profile: Dictionary, actor_position := Vector3(INF,INF,INF)) -> Vector3:
	# Simulation selects the source; the selected rendered source owns the visible
	# impact point. These authored anchors describe the exposed trunk or near rock
	# face instead of pretending the logical center is rendered surface geometry.
	if not is_instance_valid(source_visual) or profile.is_empty():
		return contact_target(attachment_transform.origin,attachment_transform,profile)
	var root := source_visual.global_position
	var stable_actor_position: Vector3 = actor_position if actor_position is Vector3 and actor_position.is_finite() else attachment_transform.origin
	var toward_actor := stable_actor_position-root
	toward_actor.y = 0.0
	if toward_actor.length_squared() <= 0.000001:
		toward_actor = source_visual.global_basis.z
		toward_actor.y = 0.0
	if toward_actor.length_squared() <= 0.000001:
		toward_actor = Vector3.FORWARD
	var height := float(profile.get("source_contact_height",0.75))
	var radius := float(profile.get("source_contact_radius",0.30))
	return root+Vector3.UP*height+toward_actor.normalized()*radius

static func _point_segment_distance(point: Vector3, start: Vector3, end: Vector3) -> float:
	var segment := end-start
	if segment.length_squared() <= 0.000001:
		return point.distance_to(start)
	var amount := clampf((point-start).dot(segment)/segment.length_squared(),0.0,1.0)
	return point.distance_to(start+segment*amount)

static func _socket_solution(attachment_transform: Transform3D, target_position: Vector3,
		profile: Dictionary, force_contact := false) -> Dictionary:
	var grip_socket: Vector3 = profile.grip_socket
	var impact_socket: Vector3 = profile.impact_socket
	var anchor_socket := _anchor_socket(profile)
	var hand_basis := attachment_transform.basis.orthonormalized()
	var base_transform := Transform3D(hand_basis,attachment_transform.origin-hand_basis*anchor_socket)
	var local_reach := impact_socket-anchor_socket
	var world_reach := target_position - attachment_transform.origin
	if local_reach.length_squared() <= 0.000001 or world_reach.length_squared() <= 0.000001:
		return {"transform":base_transform,"grip_error_m":0.0,"impact_error_m":INF,"alignment_valid":false}
	# Build the socket axis directly in world space. Using a hand-space delta here
	# would compose the rotation twice and put both handle sockets on one side.
	var world_direction := world_reach.normalized()
	var solved_basis := Basis(Quaternion(local_reach.normalized(),world_direction)).orthonormalized()
	if not String(profile.get("secondary_grip_marker","")).is_empty():
		var handle_axis := (Vector3(profile.second_hand_socket)-grip_socket).normalized()
		var current_roll := _safe_perpendicular(world_direction,solved_basis*handle_axis)
		# Production two-hand tools follow Character 1's authored lateral hold. A
		# vertical handle can satisfy abstract sockets while crossing the face.
		# Marker-only fixtures keep their authored roll because they have no body.
		var roll_reference := current_roll
		if bool(profile.get("lateral_tool_roll",false)):
			var authored_roll: Variant = profile.get("lateral_roll_reference")
			roll_reference = authored_roll.normalized() if authored_roll is Vector3 and authored_roll.length_squared() > 0.000001 else -attachment_transform.basis.x.normalized()
		var desired_roll := _safe_perpendicular(world_direction,roll_reference)
		var roll_angle := current_roll.signed_angle_to(desired_roll,world_direction)
		solved_basis = (Basis(world_direction,roll_angle)*solved_basis).orthonormalized()
	# The authored impact socket is absolute at contact. Hands are then posed onto
	# the resulting handle sockets, so neither a short arm nor a long tool can bury
	# the head in the source while still claiming contact.
	var anchor_position := attachment_transform.origin
	var solved_origin := target_position-solved_basis*impact_socket
	var solved_transform := Transform3D(solved_basis,solved_origin)
	var weight := 1.0 if force_contact else _contact_weight(float(profile.get("presented_progress", 0.0)), float(profile.impact_progress))
	var presented := base_transform.interpolate_with(solved_transform, weight)
	var grip_error := (presented*anchor_socket).distance_to(anchor_position)
	var impact_error := (presented * impact_socket).distance_to(target_position)
	return {
		"transform":presented,
		"grip_error_m":grip_error,
		"impact_error_m":impact_error,
		"alignment_valid":grip_error <= SOCKET_CONTACT_TOLERANCE_METERS and impact_error <= SOCKET_CONTACT_TOLERANCE_METERS,
	}

func _apply_tool_contact(tool: Node3D, attachment_transform: Transform3D,
		target_position: Vector3, profile: Dictionary, force_contact := false,
		preserved_transform: Variant = null) -> Dictionary:
	var posed_profile := profile.duplicate(true)
	posed_profile.presented_progress = float(active.get("progress", 0.0))
	posed_profile.lateral_tool_roll = not String(profile.get("secondary_grip_marker","")).is_empty() and is_instance_valid(_bound_skeleton())
	if bool(posed_profile.lateral_tool_roll) and is_instance_valid(bound_actor):
		var authored_primary := contact_transform(bound_actor,String(profile.primary_grip_marker)).origin
		var authored_secondary := contact_transform(bound_actor,String(profile.secondary_grip_marker)).origin
		posed_profile.lateral_roll_reference = authored_secondary-authored_primary
	var solution: Dictionary
	if preserved_transform is Transform3D:
		var preserved: Transform3D = preserved_transform
		preserved.origin += target_position-preserved*Vector3(profile.impact_socket)
		solution = {
			"transform":preserved,
			"grip_error_m":0.0,
			"impact_error_m":(preserved*Vector3(profile.impact_socket)).distance_to(target_position),
			"alignment_valid":true,
		}
	else:
		if bool(posed_profile.lateral_tool_roll):
			var right_arm := _arm_reach("R")
			var left_arm := _arm_reach("L")
			var world_axis := (target_position-attachment_transform.origin).normalized()
			var seed: Vector3 = posed_profile.lateral_roll_reference
			var best_cost := INF
			for roll_index in 12:
				var candidate_profile := posed_profile.duplicate(true)
				candidate_profile.lateral_roll_reference = Basis(world_axis,TAU*float(roll_index)/12.0)*seed
				var candidate := _socket_solution(attachment_transform,target_position,candidate_profile,force_contact)
				var transform: Transform3D = candidate.transform
				var right_target := transform*Vector3(profile.grip_socket)
				var left_target := transform*Vector3(profile.second_hand_socket)
				var right_ratio := right_target.distance_to(Vector3(right_arm.shoulder))/maxf(0.001,float(right_arm.reach))
				var left_ratio := left_target.distance_to(Vector3(left_arm.shoulder))/maxf(0.001,float(left_arm.reach))
				var cost := maxf(right_ratio,left_ratio)+0.15*(right_ratio+left_ratio)
				var candidate_head: Variant = _head_position()
				if candidate_head is Vector3:
					var candidate_clearance := _point_segment_distance(candidate_head,transform*Vector3(0.0,-0.64,0.0),transform*Vector3(0.0,0.72,0.0))
					if candidate_clearance < MIN_HEAD_CLEARANCE_METERS:
						cost += 10.0+(MIN_HEAD_CLEARANCE_METERS-candidate_clearance)*10.0
				if cost < best_cost:
					best_cost = cost
					solution = candidate
		else:
			solution = _socket_solution(attachment_transform,target_position,posed_profile,force_contact)
	tool.global_transform = solution.transform
	var primary_error := 0.0
	var secondary_error := 0.0
	var secondary_name := String(profile.get("secondary_grip_marker",""))
	var second_socket: Vector3 = profile.get("second_hand_socket",Vector3.ZERO)
	var grip_range: Variant = profile.get("second_hand_grip_range")
	if not secondary_name.is_empty() and grip_range is Vector2 and is_instance_valid(_bound_skeleton()):
		var left_arm := _arm_reach("L")
		var best_second_cost := INF
		for grip_index in 12:
			var grip_y := lerpf(grip_range.x,grip_range.y,float(grip_index)/11.0)
			var candidate_socket := Vector3(0.0,grip_y,0.0)
			var candidate_target: Vector3 = tool.global_transform*candidate_socket
			var candidate_cost := candidate_target.distance_to(Vector3(left_arm.shoulder))/maxf(0.001,float(left_arm.reach))
			if candidate_cost < best_second_cost:
				best_second_cost = candidate_cost
				second_socket = candidate_socket
	var primary_name := String(profile.get("primary_grip_marker",""))
	var primary_target: Vector3 = tool.global_transform*Vector3(profile.grip_socket)
	var weight := 1.0 if force_contact else _contact_weight(float(posed_profile.presented_progress),float(profile.impact_progress))
	_pose_arm_contact("R",primary_target,weight)
	var primary := contact_node(bound_actor,primary_name) if is_instance_valid(bound_actor) else null
	primary_error = contact_transform(bound_actor,primary_name).origin.distance_to(primary_target) if is_instance_valid(primary) else float(solution.grip_error_m)
	if not secondary_name.is_empty():
		var secondary_target: Vector3 = tool.global_transform * second_socket
		_pose_arm_contact("L",secondary_target,weight)
		var secondary := contact_node(bound_actor,secondary_name) if is_instance_valid(bound_actor) else null
		secondary_error = contact_transform(bound_actor,secondary_name).origin.distance_to(secondary_target) if is_instance_valid(secondary) else INF
	var head_clearance := INF
	var head_position: Variant = _head_position()
	if head_position is Vector3:
		var handle_bottom: Vector3 = tool.global_transform*Vector3(0.0,-0.64,0.0)
		var handle_top: Vector3 = tool.global_transform*Vector3(0.0,0.72,0.0)
		head_clearance = _point_segment_distance(head_position,handle_bottom,handle_top)
	active.grip_error_m = primary_error
	active.impact_error_m = float(solution.impact_error_m)
	active.secondary_grip_error_m = secondary_error
	active.selected_second_hand_socket = second_socket
	active.head_clearance_m = head_clearance
	active.contact_reach_m = attachment_transform.origin.distance_to(target_position)
	active.contact_alignment_valid = float(solution.impact_error_m) <= SOCKET_CONTACT_TOLERANCE_METERS and primary_error <= SOCKET_CONTACT_TOLERANCE_METERS and secondary_error <= SECOND_HAND_TOLERANCE_METERS and head_clearance >= MIN_HEAD_CLEARANCE_METERS
	solution.grip_error_m = primary_error
	solution.secondary_grip_error_m = secondary_error
	solution.head_clearance_m = head_clearance
	solution.alignment_valid = active.contact_alignment_valid
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
	if not is_instance_valid(tool_palette_material):
		tool_palette_material = StandardMaterial3D.new()
		tool_palette_material.resource_name = "T09_shared_vertex_palette"
		tool_palette_material.albedo_color = Color.WHITE
		tool_palette_material.vertex_color_use_as_albedo = true
		tool_palette_material.vertex_color_is_srgb = true
		tool_palette_material.metallic = 0.18
		tool_palette_material.roughness = 0.42
	# The hand-sized tool is already shaded by the scene lights. Submitting its
	# palette surface again for the large world shadow map adds measurable cost
	# without a readable shadow at the shipping camera scale.
	for child in node.find_children("*", "MeshInstance3D", true, false):
		var geometry := child as GeometryInstance3D
		geometry.material_override = tool_palette_material
		geometry.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
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
	_clear_grip_pose()
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
	if is_instance_valid(bound_actor) and not bool(active.get("has_committed",false)):
		last_committed_pose_identity = "%d:%s:%s" % [int(active.actor_id),String(active.source_id),String(active.resource)]
		last_committed_tool_transform = tool.global_transform
	active.commit_contact_armed = false
	attachment_updates += 1
	return descriptor()

func synchronize_committed_contact(action: Dictionary, attachment_transform: Transform3D,
		target_position: Vector3, actor_id: int) -> Dictionary:
	if not valid_action(action) or actor_id < 0 or not target_position.is_finite():
		return descriptor()
	var same_identity := not active.is_empty() and int(active.get("action_token", -1)) == int(action.action_token) and String(active.get("source_id", "")) == String(action.source_id) and int(active.get("actor_id", -1)) == actor_id
	var preserve_validated_pose := same_identity and bool(active.get("contact_ready", false)) and bool(active.get("contact_alignment_valid", false))
	if not preserve_validated_pose:
		_clear_grip_pose()
	if not same_identity:
		if not begin_action(action, actor_id):
			return descriptor()
	var profile: Dictionary = active.profile
	var tool: Node3D = active.tool
	var pose_identity := "%d:%s:%s" % [actor_id,String(action.source_id),String(action.resource)]
	var preserved_pose: Variant = null
	if pose_identity == last_committed_pose_identity:
		preserved_pose = last_committed_tool_transform
	active.raw_progress = float(action.progress)
	active.progress = float(profile.impact_progress)
	active.target_position = target_position
	var solution := _apply_tool_contact(tool,attachment_transform,target_position,profile,true,preserved_pose)
	if preserved_pose is Transform3D and not bool(solution.alignment_valid):
		_clear_grip_pose()
		solution = _apply_tool_contact(tool,attachment_transform,target_position,profile,true)
	active.contact_ready = bool(solution.alignment_valid)
	active.commit_contact_armed = bool(solution.alignment_valid)
	active.last_committed_alignment_valid = bool(solution.alignment_valid)
	active.last_committed_grip_error_m = float(solution.grip_error_m)
	active.last_committed_secondary_error_m = float(solution.get("secondary_grip_error_m",0.0))
	active.last_committed_impact_error_m = float(solution.impact_error_m)
	active.last_committed_head_clearance_m = float(solution.get("head_clearance_m",INF))
	last_commit_solution = {
		"alignment_valid":bool(solution.alignment_valid),
		"grip_error_m":float(solution.grip_error_m),
		"secondary_error_m":float(solution.get("secondary_grip_error_m",0.0)),
		"impact_error_m":float(solution.impact_error_m),
		"head_clearance_m":float(solution.get("head_clearance_m",INF)),
		"right_arm_target_distance_m":float(active.get("R_arm_target_distance_m",INF)),
		"right_arm_max_reach_m":float(active.get("R_arm_max_reach_m",INF)),
		"right_arm_residual_m":float(active.get("R_arm_residual_m",INF)),
		"left_arm_target_distance_m":float(active.get("L_arm_target_distance_m",INF)),
		"left_arm_max_reach_m":float(active.get("L_arm_max_reach_m",INF)),
		"left_arm_residual_m":float(active.get("L_arm_residual_m",INF)),
		"right_distributed_extension_m":float(active.get("R_distributed_extension_m",0.0)),
		"left_distributed_extension_m":float(active.get("L_distributed_extension_m",0.0)),
	}
	if bool(solution.alignment_valid):
		last_committed_pose_identity = pose_identity
		last_committed_tool_transform = tool.global_transform
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
		last_rejected_impact_reason = "commit_contact_not_armed"
		rejected_impacts += 1
		return false
	var receipt_id := String(receipt.get("receipt_id", ""))
	if receipt_id.is_empty() or receipts.has(receipt_id):
		last_rejected_impact_reason = "missing_or_duplicate_receipt"
		rejected_impacts += 1
		return false
	if int(receipt.get("action_token", -1)) != int(active.action_token) or String(receipt.get("source_id", "")) != String(active.source_id) or String(receipt.get("resource", "")) != String(active.resource):
		last_rejected_impact_reason = "action_identity_mismatch"
		rejected_impacts += 1
		return false
	if not receipt.get("actor_id") is int or int(receipt.actor_id) != int(active.actor_id):
		last_rejected_impact_reason = "actor_mismatch"
		rejected_impacts += 1
		return false
	if not bool(active.get("contact_ready", false)):
		last_rejected_impact_reason = "contact_not_ready"
		rejected_impacts += 1
		return false
	var target: Variant = receipt.get("target_position")
	if not target is Vector3 or not target.is_finite():
		last_rejected_impact_reason = "invalid_target"
		rejected_impacts += 1
		return false
	var target_position: Vector3 = target
	var presented_target: Variant = active.get("target_position")
	if not presented_target is Vector3 or not presented_target.is_finite() or target_position.distance_to(presented_target) > IMPACT_TARGET_TOLERANCE_METERS:
		last_rejected_impact_reason = "target_mismatch"
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
	last_rejected_impact_reason = ""
	return true

func cancel(reason := "cancelled") -> void:
	_clear_grip_pose()
	if not active.is_empty():
		cancellation_count += 1
	_hide_tools()
	active = {"last_cancel_reason":reason} if not reason.is_empty() else {}

func reset() -> void:
	_clear_grip_pose()
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
	last_rejected_impact_reason = ""
	last_commit_solution.clear()
	attachment_updates = 0
	cancellation_count = 0
	highest_action_token = 0
	last_committed_pose_identity = ""
	last_committed_tool_transform = Transform3D.IDENTITY

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
	var target: Variant = active.get("target_position")
	var target_values: Array = [target.x,target.y,target.z] if target is Vector3 else []
	var selected_second: Variant = active.get("selected_second_hand_socket")
	var selected_second_values: Array = [selected_second.x,selected_second.y,selected_second.z] if selected_second is Vector3 else []
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
		"primary_grip_marker":String(active.get("profile", {}).get("primary_grip_marker", "")),
		"secondary_grip_marker":String(active.get("profile", {}).get("secondary_grip_marker", "")),
		"contact_ready":bool(active.get("contact_ready", false)),
		"commit_contact_armed":bool(active.get("commit_contact_armed", false)),
		"contact_alignment_valid":bool(active.get("contact_alignment_valid", false)),
		"grip_error_m":float(active.get("grip_error_m", INF)),
		"impact_error_m":float(active.get("impact_error_m", INF)),
		"secondary_grip_error_m":float(active.get("secondary_grip_error_m", INF)),
		"selected_second_hand_socket":selected_second_values,
		"head_clearance_m":float(active.get("head_clearance_m", INF)),
		"contact_reach_m":float(active.get("contact_reach_m", INF)),
		"minimum_head_clearance_m":MIN_HEAD_CLEARANCE_METERS,
		"source_contact_policy":"authored_visible_surface_anchor",
		"visible_source_target":target_values,
		"last_rejection_reason":last_rejected_impact_reason,
		"last_committed_alignment_valid":bool(active.get("last_committed_alignment_valid",false)),
		"last_committed_grip_error_m":float(active.get("last_committed_grip_error_m",INF)),
		"last_committed_secondary_error_m":float(active.get("last_committed_secondary_error_m",INF)),
		"last_committed_impact_error_m":float(active.get("last_committed_impact_error_m",INF)),
		"last_committed_head_clearance_m":float(active.get("last_committed_head_clearance_m",INF)),
		"last_commit_solution":last_commit_solution.duplicate(true),
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
