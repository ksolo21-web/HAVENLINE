class_name HavenlineWorldTransform
extends RefCounted

## T10 dependency-independent transformation core.
## Resource quantities remain simulation-owned. This framework prepares exact,
## deterministic debit transactions and advances transform state only after an
## authoritative simulation receipt confirms that the debit committed.

const AUTHORITY_ID := "T10-world-transform-v1"
const RECIPE_PATH := "res://data/world_transform_recipes.json"
const RESOURCE_IDS := ["wood", "stone", "metal", "fuel"]
const MAX_SAFE_COUNT := 9223372036854775806
const COMPONENT_SCHEMA_VERSION := 1

var recipes: Dictionary = {}
var targets: Dictionary = {}
var prepared: Dictionary = {}
var receipts: Dictionary = {}

static func contract() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"component_schema_version": COMPONENT_SCHEMA_VERSION,
		"resource_ids": RESOURCE_IDS.duplicate(),
		"simulation_owns_resource_counts": true,
		"preview_is_pure": true,
		"commit_prepares_idempotent_debit_transaction": true,
		"state_advances_only_after_authoritative_receipt": true,
		"exactly_once_transaction_receipts": true,
		"one_inflight_transaction_per_target": true,
		"receipt_must_match_prepared_transaction": true,
		"presentation_may_not_grant_resources": true,
		"global_save_versioning_owned_by_t14": true,
		"t09_adapter_required_before_integration": true,
	}

static func _valid_nonnegative_integer(value: Variant) -> bool:
	if not (value is int or value is float):
		return false
	var number := float(value)
	return is_finite(number) and number >= 0.0 and number <= float(MAX_SAFE_COUNT) and is_zero_approx(fmod(number, 1.0))

static func valid_inventory(inventory: Dictionary) -> bool:
	for key in inventory:
		if not (key is String or key is StringName) or String(key) not in RESOURCE_IDS:
			return false
		if not _valid_nonnegative_integer(inventory[key]):
			return false
	return true

static func normalized_inventory(inventory: Dictionary) -> Dictionary:
	var result := {}
	for resource_id in RESOURCE_IDS:
		result[resource_id] = int(inventory.get(resource_id, 0))
	return result

static func _normalized_costs(costs: Array) -> Dictionary:
	var result := {}
	for row: Variant in costs:
		if not (row is Dictionary):
			return {}
		var resource_id := String(row.get("resource_id", ""))
		var quantity: Variant = row.get("quantity", null)
		if resource_id not in RESOURCE_IDS or resource_id in result:
			return {}
		if not _valid_nonnegative_integer(quantity) or int(quantity) <= 0:
			return {}
		result[resource_id] = int(quantity)
	return result

static func _duplicate_free_strings(values: Variant) -> bool:
	if not (values is Array):
		return false
	var seen := {}
	for value in values:
		if not (value is String or value is StringName):
			return false
		var text := String(value)
		if text.is_empty() or text in seen:
			return false
		seen[text] = true
	return true

static func validate_recipe(recipe: Dictionary) -> bool:
	var required := ["recipe_id", "source_state", "target_state", "costs", "prerequisites", "progression_tags", "presentation_key"]
	for field in required:
		if field not in recipe:
			return false
	if String(recipe.recipe_id).is_empty() or String(recipe.source_state).is_empty() or String(recipe.target_state).is_empty():
		return false
	if recipe.source_state == recipe.target_state and not bool(recipe.get("allow_self_transition", false)):
		return false
	if String(recipe.presentation_key).is_empty():
		return false
	if not _duplicate_free_strings(recipe.prerequisites) or not _duplicate_free_strings(recipe.progression_tags):
		return false
	var normalized := _normalized_costs(recipe.costs)
	return not normalized.is_empty() and normalized.size() == recipe.costs.size()

func configure(catalog: Dictionary) -> bool:
	var rows: Variant = catalog.get("recipes")
	if not (rows is Array) or rows.is_empty():
		return false
	var next := {}
	for row: Variant in rows:
		if not (row is Dictionary) or not validate_recipe(row):
			return false
		var recipe_id := String(row.recipe_id)
		if recipe_id in next:
			return false
		var copy: Dictionary = row.duplicate(true)
		copy["normalized_costs"] = _normalized_costs(copy.costs)
		next[recipe_id] = copy
	recipes = next
	return true

func configure_from_file(path := RECIPE_PATH) -> bool:
	if not FileAccess.file_exists(path):
		return false
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed is Dictionary and configure(parsed)

func register_target(target_id: String, initial_state: String, progression_tags: Array = []) -> bool:
	if target_id.is_empty() or initial_state.is_empty() or not _duplicate_free_strings(progression_tags):
		return false
	if target_id in targets:
		return false
	targets[target_id] = {
		"state": initial_state,
		"revision": 0,
		"progression_tags": progression_tags.duplicate(),
	}
	return true

func _recipe(recipe_id: String) -> Dictionary:
	return recipes.get(recipe_id, {})

func _target(target_id: String) -> Dictionary:
	return targets.get(target_id, {})

func preview_transform(recipe_id: String, target_id: String, inventory: Dictionary, available_prerequisites: Array = []) -> Dictionary:
	var errors: Array[String] = []
	if not valid_inventory(inventory):
		errors.append("invalid_inventory")
	if not _duplicate_free_strings(available_prerequisites):
		errors.append("invalid_prerequisites")
	var recipe := _recipe(recipe_id)
	if recipe.is_empty():
		errors.append("unknown_recipe")
	var target := _target(target_id)
	if target.is_empty():
		errors.append("unknown_target")
	if not errors.is_empty():
		return {"passed": false, "errors": errors, "shortfalls": {}, "mutated": false}
	if String(target.state) != String(recipe.source_state):
		errors.append("source_state_mismatch")
	var prerequisite_set := {}
	for value in available_prerequisites:
		prerequisite_set[String(value)] = true
	for required in recipe.prerequisites:
		if String(required) not in prerequisite_set:
			errors.append("missing_prerequisite:%s" % String(required))
	var counts := normalized_inventory(inventory)
	var shortfalls := {}
	for resource_id in recipe.normalized_costs:
		var need := int(recipe.normalized_costs[resource_id])
		var have := int(counts.get(resource_id, 0))
		if have < need:
			shortfalls[resource_id] = need - have
	if not shortfalls.is_empty():
		errors.append("insufficient_resources")
	return {
		"passed": errors.is_empty(),
		"errors": errors,
		"recipe_id": recipe_id,
		"target_id": target_id,
		"source_state": String(recipe.source_state),
		"target_state": String(recipe.target_state),
		"costs": recipe.normalized_costs.duplicate(true),
		"shortfalls": shortfalls,
		"progression_tags": recipe.progression_tags.duplicate(),
		"presentation_key": String(recipe.presentation_key),
		"target_revision": int(target.revision),
		"mutated": false,
	}

static func _request_identity(recipe_id: String, target_id: String, source_state: String, target_state: String) -> String:
	return "%s|%s|%s|%s" % [recipe_id, target_id, source_state, target_state]

func _collision_or_replay(transaction_id: String, recipe_id: String, target_id: String, table: Dictionary, completed: bool) -> Dictionary:
	if transaction_id not in table:
		return {}
	var existing: Dictionary = table[transaction_id]
	var identity := _request_identity(recipe_id, target_id, String(existing.get("source_state", "")), String(existing.get("target_state", "")))
	if identity != String(existing.get("request_identity", "")):
		return {"passed": false, "errors": ["transaction_id_collision"], "replayed": false, "submit_debit_transaction": false}
	var replay := existing.duplicate(true)
	replay["passed"] = true
	replay["replayed"] = true
	replay["submit_debit_transaction"] = not completed
	replay["authoritative_applied"] = completed
	return replay

func _pending_transaction_for_target(target_id: String) -> String:
	for transaction_id in prepared:
		var row: Dictionary = prepared[transaction_id]
		if String(row.get("target_id", "")) == target_id:
			return String(transaction_id)
	return ""

func commit_transform(transaction_id: String, recipe_id: String, target_id: String, inventory: Dictionary, available_prerequisites: Array = []) -> Dictionary:
	if transaction_id.is_empty():
		return {"passed": false, "errors": ["invalid_transaction_id"], "submit_debit_transaction": false, "replayed": false}
	var completed := _collision_or_replay(transaction_id, recipe_id, target_id, receipts, true)
	if not completed.is_empty():
		return completed
	var pending := _collision_or_replay(transaction_id, recipe_id, target_id, prepared, false)
	if not pending.is_empty():
		return pending
	var target_pending := _pending_transaction_for_target(target_id)
	if not target_pending.is_empty():
		return {
			"passed": false,
			"errors": ["target_transaction_pending"],
			"pending_transaction_id": target_pending,
			"submit_debit_transaction": false,
			"replayed": false,
		}

	var preview := preview_transform(recipe_id, target_id, inventory, available_prerequisites)
	if not bool(preview.passed):
		return {
			"passed": false,
			"errors": preview.errors.duplicate(),
			"shortfalls": preview.shortfalls.duplicate(true),
			"submit_debit_transaction": false,
			"replayed": false,
		}

	var intent := {
		"transaction_id": transaction_id,
		"request_identity": _request_identity(recipe_id, target_id, String(preview.source_state), String(preview.target_state)),
		"recipe_id": recipe_id,
		"target_id": target_id,
		"source_state": String(preview.source_state),
		"target_state": String(preview.target_state),
		"debits": preview.costs.duplicate(true),
		"progression_tags": preview.progression_tags.duplicate(),
		"presentation_key": String(preview.presentation_key),
		"target_revision": int(preview.target_revision) + 1,
		"passed": true,
		"replayed": false,
		"submit_debit_transaction": true,
		"authoritative_applied": false,
	}
	prepared[transaction_id] = intent.duplicate(true)
	return intent

static func _valid_transaction_row(transaction_id: String, row: Variant) -> bool:
	if transaction_id.is_empty() or not (row is Dictionary):
		return false
	if String(row.get("transaction_id", "")) != transaction_id:
		return false
	for field in ["request_identity", "recipe_id", "target_id", "source_state", "target_state", "presentation_key"]:
		if String(row.get(field, "")).is_empty():
			return false
	if not _valid_nonnegative_integer(row.get("target_revision", null)) or int(row.target_revision) <= 0:
		return false
	var debits: Variant = row.get("debits")
	if not (debits is Dictionary) or debits.is_empty():
		return false
	for resource_id in debits:
		if String(resource_id) not in RESOURCE_IDS or not _valid_nonnegative_integer(debits[resource_id]) or int(debits[resource_id]) <= 0:
			return false
	return _duplicate_free_strings(row.get("progression_tags", []))

static func _receipt_matches_prepared(receipt: Dictionary, intent: Dictionary) -> bool:
	for field in ["transaction_id", "request_identity", "recipe_id", "target_id", "source_state", "target_state", "presentation_key", "target_revision"]:
		if receipt.get(field) != intent.get(field):
			return false
	return receipt.get("debits", {}) == intent.get("debits", {}) and receipt.get("progression_tags", []) == intent.get("progression_tags", [])

func accept_authoritative_receipt(receipt: Dictionary) -> Dictionary:
	var transaction_id := String(receipt.get("transaction_id", ""))
	if transaction_id.is_empty() or not bool(receipt.get("authority_applied", false)) or String(receipt.get("authority_source", "")) != "simulation":
		return {"passed": false, "errors": ["invalid_authoritative_receipt"], "applied": false, "replayed": false}
	if transaction_id in receipts:
		var existing: Dictionary = receipts[transaction_id]
		if String(existing.get("request_identity", "")) != String(receipt.get("request_identity", "")):
			return {"passed": false, "errors": ["transaction_id_collision"], "applied": false, "replayed": false}
		var replay := existing.duplicate(true)
		replay["passed"] = true
		replay["applied"] = false
		replay["replayed"] = true
		return replay
	if not _valid_transaction_row(transaction_id, receipt):
		return {"passed": false, "errors": ["malformed_authoritative_receipt"], "applied": false, "replayed": false}
	if transaction_id not in prepared:
		return {"passed": false, "errors": ["missing_prepared_transaction"], "applied": false, "replayed": false}
	var intent: Dictionary = prepared[transaction_id]

	var recipe := _recipe(String(receipt.recipe_id))
	var target := _target(String(receipt.target_id))
	if recipe.is_empty() or target.is_empty():
		return {"passed": false, "errors": ["unknown_recipe_or_target"], "applied": false, "replayed": false}
	var expected_identity := _request_identity(String(receipt.recipe_id), String(receipt.target_id), String(recipe.source_state), String(recipe.target_state))
	if String(receipt.request_identity) != expected_identity:
		return {"passed": false, "errors": ["receipt_identity_mismatch"], "applied": false, "replayed": false}
	if receipt.debits != recipe.normalized_costs:
		return {"passed": false, "errors": ["receipt_debit_mismatch"], "applied": false, "replayed": false}
	if String(target.state) != String(recipe.source_state) or int(receipt.target_revision) != int(target.revision) + 1:
		return {"passed": false, "errors": ["receipt_state_mismatch"], "applied": false, "replayed": false}
	if not _receipt_matches_prepared(receipt, intent):
		return {"passed": false, "errors": ["prepared_receipt_mismatch"], "applied": false, "replayed": false}

	target["state"] = String(recipe.target_state)
	target["revision"] = int(receipt.target_revision)
	targets[String(receipt.target_id)] = target
	var canonical := receipt.duplicate(true)
	canonical["passed"] = true
	canonical["applied"] = true
	canonical["replayed"] = false
	canonical["submit_debit_transaction"] = false
	canonical["authoritative_applied"] = true
	canonical["accepted_by_world_transform"] = true
	receipts[transaction_id] = canonical.duplicate(true)
	prepared.erase(transaction_id)
	return canonical

func export_component_state() -> Dictionary:
	return {
		"schema_version": COMPONENT_SCHEMA_VERSION,
		"authority_id": AUTHORITY_ID,
		"targets": targets.duplicate(true),
		"prepared": prepared.duplicate(true),
		"receipts": receipts.duplicate(true),
	}

static func _valid_target_row(row: Variant) -> bool:
	if not (row is Dictionary):
		return false
	if String(row.get("state", "")).is_empty():
		return false
	if not _valid_nonnegative_integer(row.get("revision", null)):
		return false
	return _duplicate_free_strings(row.get("progression_tags", []))

func import_component_state(state: Dictionary) -> bool:
	if int(state.get("schema_version", -1)) != COMPONENT_SCHEMA_VERSION:
		return false
	if String(state.get("authority_id", "")) != AUTHORITY_ID:
		return false
	var next_targets: Variant = state.get("targets")
	var next_prepared: Variant = state.get("prepared")
	var next_receipts: Variant = state.get("receipts")
	if not (next_targets is Dictionary) or not (next_prepared is Dictionary) or not (next_receipts is Dictionary):
		return false
	for target_id in next_targets:
		if String(target_id).is_empty() or not _valid_target_row(next_targets[target_id]):
			return false
	var pending_targets := {}
	for transaction_id in next_prepared:
		if transaction_id in next_receipts or not _valid_transaction_row(String(transaction_id), next_prepared[transaction_id]):
			return false
		var pending: Dictionary = next_prepared[transaction_id]
		var pending_target_id := String(pending.target_id)
		if pending_target_id not in next_targets or pending_target_id in pending_targets:
			return false
		pending_targets[pending_target_id] = true
		var pending_target: Dictionary = next_targets[pending_target_id]
		if int(pending.target_revision) != int(pending_target.revision) + 1:
			return false
	for transaction_id in next_receipts:
		if not _valid_transaction_row(String(transaction_id), next_receipts[transaction_id]):
			return false
		var row: Dictionary = next_receipts[transaction_id]
		var target_id := String(row.target_id)
		if target_id not in next_targets:
			return false
		var target: Dictionary = next_targets[target_id]
		if int(row.target_revision) > int(target.revision):
			return false
	targets = next_targets.duplicate(true)
	prepared = next_prepared.duplicate(true)
	receipts = next_receipts.duplicate(true)
	return true

func descriptor() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"recipe_count": recipes.size(),
		"target_count": targets.size(),
		"prepared_count": prepared.size(),
		"receipt_count": receipts.size(),
		"targets": targets.duplicate(true),
		"simulation_owns_resource_counts": true,
		"integration_dependency_t09": "pending",
	}
