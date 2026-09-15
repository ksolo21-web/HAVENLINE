class_name HavenlineContextDirector
extends RefCounted

# T07 owns selection and presentation state only. Simulation remains the sole
# authority for inventory, damage, rewards, position, facing and action impact.
const CONTRACT_VERSION := "t07_context_director_v1"
const MAX_INPUT_CANDIDATES := 128
const MAX_ELIGIBLE_CANDIDATES := 96
const ACQUIRE_DWELL_SECONDS := 0.12
const MINIMUM_HOLD_SECONDS := 0.18
const MOVEMENT_CANCEL_THRESHOLD := 0.10
const STOP_SPEED := 0.20
const RELEASE_MARGIN := 0.55
const SWITCH_MARGIN := 0.16

const ROLE_CAPABILITIES := {
	"player_lead": ["gather_with_tools", "carry", "deposit", "build", "repair", "rescue", "attack", "hunt"],
	"core_human_companion": ["follow", "gather_with_tools", "carry", "deposit", "build", "repair", "guard", "attack", "hunt"],
	"rescued_survivor_helper": ["gather_with_tools", "carry", "deposit", "build", "repair", "guard", "attack", "heal"],
}

const KIND_CAPABILITY := {
	"gather": "gather_with_tools",
	"deposit": "deposit",
	"build": "build",
	"repair": "repair",
	"defense_repair": "repair",
	"rescue": "rescue",
	"npc_rescue": "rescue",
	"enemy": "attack",
	"customer_service": "deposit",
}

# Safety ordering is frozen here and cannot be overridden by purchase, spend,
# VIP, telemetry or personalization fields supplied by a candidate producer.
const KIND_PRIORITY := {
	"enemy": 900,
	"rescue": 820,
	"npc_rescue": 800,
	"defense_repair": 700,
	"repair": 680,
	"build": 560,
	"deposit": 500,
	"customer_service": 440,
	"gather": 300,
}
const URGENT_KINDS := ["enemy", "rescue", "npc_rescue"]

var current_identity := ""
var current_candidate: Dictionary = {}
var focus_elapsed := 0.0
var action_token := 0
var switch_count := 0
var last_descriptor: Dictionary = {}
var last_metrics: Dictionary = {}

static func contract() -> Dictionary:
	return {
		"version": CONTRACT_VERSION,
		"one_primary_movement_joystick": true,
		"permanent_action_buttons": 0,
		"simulation_authoritative": true,
		"emits_gameplay_events": false,
		"owns_position_or_facing": false,
		"saved_fields": [],
		"spend_blind": true,
		"roles": ["player_lead", "core_human_companion", "rescued_survivor_helper"],
		"canonical_fields": ["kind", "id", "position", "progress"],
		"maximum_input_candidates": MAX_INPUT_CANDIDATES,
		"maximum_eligible_candidates": MAX_ELIGIBLE_CANDIDATES,
	}

static func capabilities_for_role(role: String) -> Array:
	return Array(ROLE_CAPABILITIES.get(role, [])).duplicate()

static func _finite_number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

static func _valid_candidate(candidate: Variant) -> bool:
	if not candidate is Dictionary:
		return false
	if not candidate.get("kind") is String or String(candidate.get("kind")).is_empty():
		return false
	if not candidate.get("id") is String or String(candidate.get("id")).is_empty():
		return false
	if not candidate.get("position") is Vector2 or not Vector2(candidate.position).is_finite():
		return false
	if not candidate.get("eligible") is bool:
		return false
	if not _finite_number(candidate.get("priority")):
		return false
	if not candidate.get("capability") is String or String(candidate.capability).is_empty():
		return false
	if not _finite_number(candidate.get("radius")) or float(candidate.radius) <= 0.0:
		return false
	if candidate.has("progress") and (not _finite_number(candidate.progress) or float(candidate.progress) < 0.0 or float(candidate.progress) > 1.0):
		return false
	if candidate.has("target_relevance") and not _finite_number(candidate.target_relevance):
		return false
	return KIND_PRIORITY.has(String(candidate.kind))

static func _identity(candidate: Dictionary) -> String:
	return String(candidate.kind) + ":" + String(candidate.id)

static func _ranked(candidate: Dictionary, actor_position: Vector2, facing: Vector2) -> Dictionary:
	var delta: Vector2 = candidate.position - actor_position
	var distance := delta.length()
	var radius := float(candidate.radius)
	var direction := delta.normalized() if distance > 0.00001 else facing.normalized()
	var normalized_facing := facing.normalized() if facing.length() > 0.00001 else Vector2.DOWN
	var distance_score := clampf(1.0 - distance / radius, -1.0, 1.0)
	var facing_score := clampf(normalized_facing.dot(direction), -1.0, 1.0)
	var relevance := clampf(float(candidate.get("target_relevance", 0.0)), -1.0, 1.0)
	var declared := clampf(float(candidate.priority), -100.0, 100.0)
	var row := candidate.duplicate(true)
	row["identity"] = _identity(candidate)
	row["distance"] = distance
	row["priority_band"] = int(KIND_PRIORITY[String(candidate.kind)])
	row["declared_priority"] = declared
	row["target_relevance"] = relevance
	row["distance_score"] = distance_score
	row["facing_score"] = facing_score
	# rank_score is a trace value with the same precedence as _better().
	row["rank_score"] = float(row.priority_band) * 100000000.0 + declared * 1000000.0 + distance_score * 10000.0 + relevance * 100.0 + facing_score
	row["switch_score"] = distance_score * 2.0 + relevance * 0.8 + facing_score * 0.2
	return row

static func _better(left: Dictionary, right: Dictionary) -> bool:
	if right.is_empty():
		return true
	for key in ["priority_band", "declared_priority", "distance_score", "target_relevance", "facing_score"]:
		var a := float(left[key])
		var b := float(right[key])
		if not is_equal_approx(a, b):
			return a > b
	return String(left.identity) < String(right.identity)

static func _blocked(role: String, state: String, reason: String, metrics: Dictionary = {}) -> Dictionary:
	return {
		"kind": "", "id": "", "position": Vector2.ZERO, "progress": 0.0,
		"state": state, "reason": reason, "actionable": false,
		"role": role, "identity": "", "action_token": 0,
		"simulation_authoritative": true, "emits_gameplay_event": false,
		"metrics": metrics,
	}

static func _sanitize(candidates: Array, actor_position: Vector2, facing: Vector2,
		capabilities: Array) -> Dictionary:
	var counts := {}
	var inspected := mini(candidates.size(), MAX_INPUT_CANDIDATES)
	var invalid := 0
	for index in inspected:
		var candidate: Variant = candidates[index]
		if not _valid_candidate(candidate):
			invalid += 1
			continue
		var identity := _identity(candidate)
		counts[identity] = int(counts.get(identity, 0)) + 1
	var valid: Array = []
	var duplicates: Array = []
	for identity in counts:
		if counts[identity] > 1:
			duplicates.append(identity)
	duplicates.sort()
	for index in inspected:
		if valid.size() >= MAX_ELIGIBLE_CANDIDATES:
			break
		var candidate: Variant = candidates[index]
		if not _valid_candidate(candidate):
			continue
		var identity := _identity(candidate)
		if identity in duplicates or not bool(candidate.eligible):
			continue
		if String(candidate.capability) not in capabilities:
			continue
		var expected := String(KIND_CAPABILITY.get(String(candidate.kind), ""))
		if expected.is_empty() or expected != String(candidate.capability):
			continue
		var ranked := _ranked(candidate, actor_position, facing)
		if ranked.distance <= float(ranked.radius) + RELEASE_MARGIN:
			valid.append(ranked)
	return {
		"valid": valid,
		"metrics": {
			"input_count": candidates.size(),
			"inspected_count": inspected,
			"eligible_count": valid.size(),
			"invalid_count": invalid,
			"duplicate_identities": duplicates,
			"input_capped": candidates.size() > MAX_INPUT_CANDIDATES,
			"eligible_capped": valid.size() >= MAX_ELIGIBLE_CANDIDATES,
		}
	}

static func preview(actor_position: Vector2, facing: Vector2, role: String,
		candidates: Array, actor_present := true, actor_ready := true) -> Dictionary:
	if not ROLE_CAPABILITIES.has(role):
		return _blocked(role, "blocked_role", "unregistered_role")
	if not actor_present:
		return _blocked(role, "blocked_actor", "actor_not_presented")
	if not actor_ready:
		return _blocked(role, "blocked_actor", "actor_not_ready")
	var sanitized := _sanitize(candidates, actor_position, facing, capabilities_for_role(role))
	var best: Dictionary = {}
	for option in sanitized.valid:
		if _better(option, best):
			best = option
	if best.is_empty():
		return _blocked(role, "idle", "no_eligible_context", sanitized.metrics)
	return {
		"kind": String(best.kind), "id": String(best.id), "position": Vector2(best.position),
		"progress": clampf(float(best.get("progress", 0.0)), 0.0, 1.0),
		"state": "preview", "reason": "deterministic_rank", "actionable": false,
		"role": role, "identity": String(best.identity), "action_token": 0,
		"simulation_authoritative": true, "emits_gameplay_event": false,
		"rank": {
			"priority": best.priority_band, "declared": best.declared_priority,
			"target_relevance": best.target_relevance, "distance": best.distance,
			"distance_score": best.distance_score, "facing_score": best.facing_score,
			"score": best.rank_score,
		},
		"metrics": sanitized.metrics,
	}

func reset() -> void:
	current_identity = ""
	current_candidate = {}
	focus_elapsed = 0.0
	action_token = 0
	switch_count = 0
	last_descriptor = {}
	last_metrics = {}

func _should_switch(best: Dictionary, current: Dictionary) -> bool:
	if current.is_empty():
		return true
	if int(best.priority_band) != int(current.priority_band):
		return int(best.priority_band) > int(current.priority_band)
	if not is_equal_approx(float(best.declared_priority), float(current.declared_priority)):
		return float(best.declared_priority) > float(current.declared_priority)
	if String(best.kind) in URGENT_KINDS and String(current.kind) not in URGENT_KINDS:
		return true
	if focus_elapsed < MINIMUM_HOLD_SECONDS:
		return false
	return float(best.switch_score) > float(current.switch_score) + SWITCH_MARGIN

func advance(dt: float, actor_position: Vector2, facing: Vector2,
		movement_input: Vector2, velocity: Vector2, role: String, candidates: Array,
		actor_present := true, actor_ready := true) -> Dictionary:
	if not is_finite(dt) or dt < 0.0 or not actor_position.is_finite() or not facing.is_finite() or not movement_input.is_finite() or not velocity.is_finite():
		last_descriptor = _blocked(role, "blocked_input", "non_finite_input")
		return last_descriptor
	if not ROLE_CAPABILITIES.has(role):
		last_descriptor = _blocked(role, "blocked_role", "unregistered_role")
		return last_descriptor
	if not actor_present or not actor_ready:
		current_identity = ""
		current_candidate = {}
		focus_elapsed = 0.0
		last_descriptor = _blocked(role, "blocked_actor", "actor_not_presented" if not actor_present else "actor_not_ready")
		return last_descriptor
	var sanitized := _sanitize(candidates, actor_position, facing, capabilities_for_role(role))
	last_metrics = sanitized.metrics.duplicate(true)
	last_metrics["switch_count"] = switch_count
	var best: Dictionary = {}
	var retained: Dictionary = {}
	for option in sanitized.valid:
		if String(option.identity) == current_identity and float(option.distance) <= float(option.radius) + RELEASE_MARGIN:
			retained = option
		if float(option.distance) <= float(option.radius) and _better(option, best):
			best = option
	if not retained.is_empty() and (best.is_empty() or not _should_switch(best, retained)):
		best = retained
	if best.is_empty():
		current_identity = ""
		current_candidate = {}
		focus_elapsed = 0.0
		last_descriptor = _blocked(role, "idle", "no_eligible_context", last_metrics)
		return last_descriptor
	var switched := String(best.identity) != current_identity
	if switched:
		current_identity = String(best.identity)
		current_candidate = best.duplicate(true)
		focus_elapsed = 0.0
		action_token += 1
		switch_count += 1
	else:
		current_candidate = best.duplicate(true)
	var moving := movement_input.length() > MOVEMENT_CANCEL_THRESHOLD or velocity.length() >= STOP_SPEED
	if moving:
		focus_elapsed = 0.0
	else:
		focus_elapsed += minf(dt, 0.1)
	var urgent := String(best.kind) in URGENT_KINDS
	var actionable := not moving and (urgent or focus_elapsed + 0.000001 >= ACQUIRE_DWELL_SECONDS)
	var state := "blocked_movement" if moving else ("active" if actionable else "acquiring")
	var reason := "movement_owns_locomotion" if moving else ("urgent_preemption" if urgent and switched else ("focus_stable" if actionable else "acquire_dwell"))
	last_metrics["switch_count"] = switch_count
	last_descriptor = {
		"kind": String(best.kind), "id": String(best.id), "position": Vector2(best.position),
		"progress": clampf(float(best.get("progress", 0.0)), 0.0, 1.0),
		"state": state, "reason": reason, "actionable": actionable,
		"role": role, "identity": current_identity, "action_token": action_token,
		"simulation_authoritative": true, "emits_gameplay_event": false,
		"rank": {
			"priority": best.priority_band, "declared": best.declared_priority,
			"target_relevance": best.target_relevance, "distance": best.distance,
			"distance_score": best.distance_score, "facing_score": best.facing_score,
			"score": best.rank_score,
		},
		"metrics": last_metrics.duplicate(true),
	}
	return last_descriptor

func presentation() -> Dictionary:
	var descriptor := last_descriptor
	var kind := String(descriptor.get("kind", ""))
	var label: String = {
		"gather": "Gathering", "deposit": "Delivering", "build": "Building",
		"repair": "Repairing", "defense_repair": "Repairing",
		"rescue": "Rescuing", "npc_rescue": "Welcoming",
		"enemy": "Defending", "customer_service": "Serving",
	}.get(kind, "")
	return {
		"visible": not kind.is_empty(),
		"label": label,
		"state": String(descriptor.get("state", "idle")),
		"reason": String(descriptor.get("reason", "no_eligible_context")),
		"progress": clampf(float(descriptor.get("progress", 0.0)), 0.0, 1.0),
		"permanent_action_buttons": 0,
		"movement_control": "one_primary_joystick",
		"color_and_text_state": true,
	}

static func _progress(sim: Variant, kind: String, id: String, duration: float) -> float:
	if duration <= 0.0:
		return 0.0
	return clampf(float(sim.action_clocks.get(kind + ":" + id, 0.0)) / duration, 0.0, 1.0)

static func build_simulation_candidates(sim: Variant) -> Array:
	# Read-only adapter over the approved simulation. It creates possibilities;
	# it never performs an action or mutates gameplay state.
	var options: Array = []
	var player: Dictionary = sim.contract.player
	for enemy in sim.enemies:
		if sim.threats_enabled and float(enemy.health) > 0.0:
			options.append({"kind":"enemy", "id":String(enemy.id), "position":Vector2(enemy.position), "eligible":true, "priority":0.0, "capability":"attack", "radius":float(player.combatRadius), "target_relevance":1.0, "progress":_progress(sim,"enemy",String(enemy.id),float(sim.tuning.wolf.playerHitSeconds))})
	var furnace: Vector2 = sim.point(sim.contract.world.furnace)
	if sim.durability < sim.tuning.furnaceMaxDurability and sim.inventory.wood > 0:
		options.append({"kind":"repair", "id":"furnace", "position":furnace, "eligible":true, "priority":0.0, "capability":"repair", "radius":float(player.depositRadius), "target_relevance":1.0, "progress":_progress(sim,"repair","furnace",float(sim.tuning.furnaceRepairSecondsPerUnit))})
	elif sim.carried() > 0 and sim.durability > 0:
		options.append({"kind":"deposit", "id":"furnace", "position":furnace, "eligible":true, "priority":0.0, "capability":"deposit", "radius":float(player.depositRadius), "target_relevance":1.0, "progress":_progress(sim,"deposit","furnace",float(sim.tuning.furnaceDepositSecondsPerUnit))})
	if sim.carried() > 0 and sim.durability > 0:
		options.append({"kind":"deposit", "id":"storage", "position":sim.point(sim.contract.world.storage), "eligible":true, "priority":0.0, "capability":"deposit", "radius":float(player.depositRadius), "target_relevance":0.9, "progress":_progress(sim,"deposit","storage",float(sim.tuning.furnaceDepositSecondsPerUnit))})
	if sim.rescue_enabled and not sim.rescued and sim.level >= 2 and sim.durability > 0:
		options.append({"kind":"rescue", "id":"survivor", "position":sim.point(sim.contract.world.survivor), "eligible":true, "priority":0.0, "capability":"rescue", "radius":float(player.rescueRadius), "target_relevance":1.0, "progress":_progress(sim,"rescue","survivor",float(sim.tuning.survivorRescueSeconds))})
	for side in sim.defenses:
		var defense: Dictionary = sim.defenses[side]
		if not defense.built:
			var need: Dictionary = sim.tuning[String(side) + "BarricadeBuild"]
			var eligible: bool = (defense.delivered.wood < need.wood and sim.inventory.wood > 0) or (defense.delivered.stone < need.stone and sim.inventory.stone > 0)
			if eligible:
				options.append({"kind":"build", "id":String(side), "position":Vector2(defense.position), "eligible":true, "priority":0.0, "capability":"build", "radius":float(player.buildRadius), "target_relevance":1.0, "progress":_progress(sim,"build",String(side),float(sim.tuning.playerConstructionSecondsPerUnit))})
		elif defense.health < 160 and sim.inventory.wood > 0:
			options.append({"kind":"defense_repair", "id":String(side), "position":Vector2(defense.position), "eligible":true, "priority":0.0, "capability":"repair", "radius":float(player.buildRadius), "target_relevance":1.0, "progress":_progress(sim,"defense_repair",String(side),float(sim.tuning.furnaceRepairSecondsPerUnit))})
	for resource in sim.resources:
		if int(resource.units) > 0:
			var kind := "gather"
			var id := String(resource.id)
			var resource_kind := String(resource.kind)
			options.append({"kind":kind, "id":id, "position":Vector2(resource.position), "eligible":true, "priority":0.0, "capability":"gather_with_tools", "radius":float(player.interactionRadius), "target_relevance":0.5 if resource_kind in ["wood","stone"] else 0.25, "progress":_progress(sim,kind,id,float(sim.tuning.gatherSecondsPerUnit[resource_kind]))})
	return options
