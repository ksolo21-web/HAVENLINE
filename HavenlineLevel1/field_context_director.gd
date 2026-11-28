class_name HavenlineContextDirector
extends RefCounted

# T07 owns selection and presentation state only. Simulation remains the sole
# authority for inventory, damage, rewards, position, facing and action impact.
const CONTRACT_VERSION := "t07_context_director_v1"
const MAX_INPUT_CANDIDATES := 128
const MAX_ELIGIBLE_CANDIDATES := 96
const ACQUIRE_DWELL_SECONDS := 0.12
const MINIMUM_HOLD_SECONDS := 0.18
const MOVEMENT_CANCEL_THRESHOLD := 0.0
const STOP_SPEED := 0.20
const RELEASE_MARGIN := 0.55
const SWITCH_MARGIN := 0.16
const RANK_COLUMNS := ["priority_band", "declared_priority", "distance_score", "target_relevance", "facing_score"]

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
var focus_actionable := false
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

static func _ranked(candidate: Dictionary, identity: String, delta: Vector2, distance: float, facing: Vector2) -> Dictionary:
	var radius := float(candidate.radius)
	var direction := delta / distance if distance > 0.00001 else facing
	var distance_score := clampf(1.0 - distance / radius, -1.0, 1.0)
	var facing_score := clampf(facing.dot(direction), -1.0, 1.0)
	var relevance := clampf(float(candidate.get("target_relevance", 0.0)), -1.0, 1.0)
	var declared := clampf(float(candidate.priority), -100.0, 100.0)
	var band := int(KIND_PRIORITY[candidate.kind])
	return {"kind":candidate.kind,"id":candidate.id,"position":candidate.position,
		"progress":candidate.get("progress",0.),"identity":identity,"radius":radius,"distance":distance,
		"priority_band":band,"declared_priority":declared,"target_relevance":relevance,
		"distance_score":distance_score,"facing_score":facing_score,
		"rank_score":float(band) * 100000000.0 + declared * 1000000.0 + distance_score * 10000.0 + relevance * 100.0 + facing_score,
		"switch_score":declared * 0.01 + distance_score * 2.0 + relevance * 0.8 + facing_score * 0.2}

static func _better(left: Dictionary, right: Dictionary) -> bool:
	if right.is_empty():
		return true
	for key in RANK_COLUMNS:
		var a := float(left[key])
		var b := float(right[key])
		# Exact finite comparison makes this a strict total ordering suitable for
		# adversarial near-equal inputs. Approximate equality is not transitive.
		if a != b:
			return a > b
	return String(left.identity) < String(right.identity)

static func _blocked(role: String, state: String, reason: String, metrics: Dictionary = {}) -> Dictionary:
	return {
		"kind": "", "id": "", "position": Vector2.ZERO, "progress": 0.0,
		"state": state, "reason": reason, "actionable": false,
		"activation_credit_seconds": 0.0,
		"role": role, "identity": "", "action_token": 0,
		"simulation_authoritative": true, "emits_gameplay_event": false,
		"metrics": metrics,
	}

static func _sanitize(candidates: Array, actor_position: Vector2, facing: Vector2,
		capabilities: Array, retained_identity := "") -> Dictionary:
	var counts := {}
	if candidates.size() > MAX_INPUT_CANDIDATES:
		return {
			"best": {}, "retained": {},
			"metrics": {
				"input_count": candidates.size(), "inspected_count": 0,
				"eligible_input_count": 0, "eligible_count": 0,
				"invalid_count": 0, "duplicate_identities": [],
				"input_overflow": true, "eligible_capped": false,
			}
		}
	var inspected := candidates.size()
	var invalid := 0
	var valid_indices: Array[int] = []
	var identities: Array[String] = []
	for index in inspected:
		var candidate: Variant = candidates[index]
		if not _valid_candidate(candidate):
			invalid += 1
			continue
		var identity := _identity(candidate)
		counts[identity] = int(counts.get(identity, 0)) + 1
		valid_indices.append(index)
		identities.append(identity)
	var best: Dictionary = {}
	var retained: Dictionary = {}
	var eligible_input_count := 0
	var duplicates: Array = []
	for identity in counts:
		if counts[identity] > 1:
			duplicates.append(identity)
	duplicates.sort()
	var heading := facing.normalized() if not facing.is_zero_approx() else Vector2.DOWN
	for index in valid_indices.size():
		var candidate: Dictionary = candidates[valid_indices[index]]
		var identity := identities[index]
		if counts[identity] > 1 or not candidate.eligible:
			continue
		if String(candidate.capability) not in capabilities:
			continue
		var expected := String(KIND_CAPABILITY.get(String(candidate.kind), ""))
		if expected.is_empty() or expected != String(candidate.capability):
			continue
		var delta: Vector2 = candidate.position-actor_position
		var distance := delta.length()
		var radius := float(candidate.radius)
		var keeps_focus := identity == retained_identity and distance <= radius + RELEASE_MARGIN
		if distance > radius and not keeps_focus:continue
		var ranked := _ranked(candidate,identity,delta,distance,heading)
		if keeps_focus:
			retained = ranked
		# Release-only rows cannot consume the acquire population. All in-range
		# rows are inspected so the winning result is independent of producer
		# order; only the winner and an optional retained focus are materialized.
		if distance <= radius:
			eligible_input_count += 1
			if _better(ranked, best):
				best = ranked
	return {
		"best": best,
		"retained": retained,
		"metrics": {
			"input_count": candidates.size(),
			"inspected_count": inspected,
			"eligible_input_count": eligible_input_count,
			"eligible_count": mini(eligible_input_count, MAX_ELIGIBLE_CANDIDATES),
			"materialized_rank_count": int(not best.is_empty()) + int(not retained.is_empty() and retained_identity != String(best.get("identity", ""))),
			"invalid_count": invalid,
			"duplicate_identities": duplicates,
			"input_overflow": false,
			"eligible_capped": eligible_input_count > MAX_ELIGIBLE_CANDIDATES,
		}
	}

static func preview(actor_position: Vector2, facing: Vector2, role: String,
		candidates: Array, actor_present := true, actor_ready := true) -> Dictionary:
	if not actor_position.is_finite() or not facing.is_finite():
		return _blocked(role, "blocked_input", "non_finite_input")
	if not ROLE_CAPABILITIES.has(role):
		return _blocked(role, "blocked_role", "unregistered_role")
	if not actor_present:
		return _blocked(role, "blocked_actor", "actor_not_presented")
	if not actor_ready:
		return _blocked(role, "blocked_actor", "actor_not_ready")
	var sanitized := _sanitize(candidates, actor_position, facing, capabilities_for_role(role))
	if bool(sanitized.metrics.input_overflow):
		return _blocked(role, "blocked_input", "candidate_input_overflow", sanitized.metrics)
	var best: Dictionary = sanitized.best
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
	_clear_focus()
	action_token = 0
	switch_count = 0
	last_descriptor = {}
	last_metrics = {}

func _clear_focus() -> void:
	current_identity = ""
	current_candidate = {}
	focus_elapsed = 0.0
	focus_actionable = false

func _should_switch(best: Dictionary, current: Dictionary) -> bool:
	if current.is_empty():
		return true
	if int(best.priority_band) != int(current.priority_band):
		return int(best.priority_band) > int(current.priority_band)
	if focus_elapsed < MINIMUM_HOLD_SECONDS:
		return false
	return float(best.switch_score) > float(current.switch_score) + SWITCH_MARGIN

func advance(dt: float, actor_position: Vector2, facing: Vector2,
		movement_input: Vector2, velocity: Vector2, role: String, candidates: Array,
		actor_present := true, actor_ready := true, instant_identity := "") -> Dictionary:
	if not is_finite(dt) or dt < 0.0 or not actor_position.is_finite() or not facing.is_finite() or not movement_input.is_finite() or not velocity.is_finite():
		_clear_focus()
		last_descriptor = _blocked(role, "blocked_input", "non_finite_input")
		return last_descriptor
	if not ROLE_CAPABILITIES.has(role):
		_clear_focus()
		last_descriptor = _blocked(role, "blocked_role", "unregistered_role")
		return last_descriptor
	if not actor_present or not actor_ready:
		_clear_focus()
		last_descriptor = _blocked(role, "blocked_actor", "actor_not_presented" if not actor_present else "actor_not_ready")
		return last_descriptor
	var sanitized := _sanitize(candidates, actor_position, facing, capabilities_for_role(role), current_identity)
	if bool(sanitized.metrics.input_overflow):
		_clear_focus()
		last_descriptor = _blocked(role, "blocked_input", "candidate_input_overflow", sanitized.metrics)
		return last_descriptor
	last_metrics = sanitized.metrics.duplicate(true)
	last_metrics["switch_count"] = switch_count
	var best: Dictionary = sanitized.best
	var retained: Dictionary = sanitized.retained
	if not retained.is_empty() and (best.is_empty() or not _should_switch(best, retained)):
		best = retained
	if best.is_empty():
		_clear_focus()
		last_descriptor = _blocked(role, "idle", "no_eligible_context", last_metrics)
		return last_descriptor
	var switched := String(best.identity) != current_identity
	if switched:
		current_identity = String(best.identity)
		current_candidate = best.duplicate(true)
		focus_elapsed = 0.0
		focus_actionable = false
		action_token += 1
		switch_count += 1
	else:
		current_candidate = best.duplicate(true)
	var moving := movement_input.length() > MOVEMENT_CANCEL_THRESHOLD or velocity.length() >= STOP_SPEED
	var in_range := float(best.distance) <= float(best.radius)
	var credited_step_seconds := minf(dt, 0.1)
	if moving or not in_range:
		focus_elapsed = 0.0
		focus_actionable = false
	else:
		focus_elapsed += credited_step_seconds
	var urgent := String(best.kind) in URGENT_KINDS
	var instant := urgent or current_identity == instant_identity
	var actionable := in_range and not moving and (instant or focus_elapsed + 0.000001 >= ACQUIRE_DWELL_SECONDS)
	# On the single acquiring->active edge, disclose only already-observed
	# stopped time. The simulation may credit it once when it authoritatively
	# advances an outcome; the director still emits no gameplay event itself.
	var activation_credit_seconds := 0.0
	if actionable and not focus_actionable and not instant:
		activation_credit_seconds = maxf(0.0, focus_elapsed - credited_step_seconds)
	focus_actionable = actionable
	var state := "blocked_movement" if moving else ("active" if actionable else "acquiring")
	var reason := "movement_owns_locomotion" if moving else ("urgent_preemption" if urgent and switched else ("focus_stable" if actionable else "acquire_dwell"))
	if not in_range and not moving:
		state = "blocked_range"
		reason = "focus_outside_action_range"
	last_metrics["switch_count"] = switch_count
	last_descriptor = {
		"kind": String(best.kind), "id": String(best.id), "position": Vector2(best.position),
		"progress": clampf(float(best.get("progress", 0.0)), 0.0, 1.0),
		"state": state, "reason": reason, "actionable": actionable,
		"activation_credit_seconds": activation_credit_seconds,
		"cancelled": moving, "cancel_reason": reason if moving else "",
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
	var state := String(descriptor.get("state", "idle"))
	var reason := String(descriptor.get("reason", "no_eligible_context"))
	var label: String = {
		"gather": "Gathering", "deposit": "Delivering", "build": "Building",
		"repair": "Repairing", "defense_repair": "Repairing",
		"rescue": "Rescuing", "npc_rescue": "Welcoming",
		"enemy": "Defending", "customer_service": "Serving",
	}.get(kind, "")
	var blocked := state.begins_with("blocked")
	var cancelled := bool(descriptor.get("cancelled", false))
	var status_text := label
	if cancelled:
		status_text = (label + " paused — stop moving") if not label.is_empty() else "Action paused — stop moving"
	elif state == "acquiring":
		status_text = label + " ready"
	elif state == "active" and not label.is_empty():
		status_text = label + " · %d%%" % int(round(clampf(float(descriptor.get("progress", 0.0)), 0.0, 1.0) * 100.0))
	elif state == "blocked_actor":
		status_text = "Actor unavailable"
	elif state == "blocked_role":
		status_text = "Action unavailable"
	elif state == "blocked_input":
		status_text = "Context unavailable"
	return {
		"visible": not kind.is_empty() or blocked,
		"label": label,
		"status_text": status_text,
		"state": state,
		"reason": reason,
		"blocked": blocked,
		"cancelled": cancelled,
		"cancel_reason": String(descriptor.get("cancel_reason", "")),
		"progress": clampf(float(descriptor.get("progress", 0.0)), 0.0, 1.0),
		"permanent_action_buttons": 0,
		"movement_control": "one_primary_joystick",
		"color_and_text_state": true,
	}
