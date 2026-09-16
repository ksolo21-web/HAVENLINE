class_name HavenlineCampConstruction
extends RefCounted

## T11 content-domain adapter. T10 remains authoritative for eligibility,
## resource debit, transaction idempotency and transform state. The injected
## port may be a deterministic build-pending mock or the accepted T10 runtime.

const RECIPE_PATH := "res://data/camp_upgrade_recipes.json"
const AUTHORITY_ID := "T11-camp-construction-v1"

var transform_port: Variant = null
var recipes: Array[Dictionary] = []
var recipes_by_source: Dictionary = {}
var recipes_by_t10: Dictionary = {}
var _camp_state_id := ""
var target_id := ""
var state_revision := 0

static func read_catalog(path := RECIPE_PATH) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}

static func _nonempty_string(value: Variant) -> bool:
	return (value is String or value is StringName) and not String(value).is_empty()

static func validate_catalog(catalog: Dictionary) -> Dictionary:
	var errors: Array[String] = []
	var rows: Variant = catalog.get("recipes")
	if not (rows is Array) or rows.is_empty():
		errors.append("missing_recipes")
		return {"passed": false, "errors": errors}
	var seen_states := {}
	var seen_t10 := {}
	for index in range(rows.size()):
		var raw: Variant = rows[index]
		if not (raw is Dictionary):
			errors.append("recipe_%d_not_dictionary" % index)
			continue
		var row: Dictionary = raw
		for field in ["camp_state_id", "t10_recipe_id", "source_camp_state", "target_camp_state", "presentation_key", "asset_manifest_key", "shipping", "route_clearance_profile", "camera_readability_profile"]:
			if field not in row:
				errors.append("recipe_%d_missing_%s" % [index, field])
		for field in ["camp_state_id", "t10_recipe_id", "source_camp_state", "target_camp_state", "presentation_key", "asset_manifest_key", "route_clearance_profile", "camera_readability_profile"]:
			if field in row and not _nonempty_string(row[field]):
				errors.append("recipe_%d_invalid_%s" % [index, field])
		if not (row.get("shipping") is bool):
			errors.append("recipe_%d_shipping_not_bool" % index)
		if row.has("costs") or row.has("debits"):
			errors.append("recipe_%d_duplicates_t10_cost_authority" % index)
		var camp_state := String(row.get("camp_state_id", ""))
		var t10_recipe := String(row.get("t10_recipe_id", ""))
		if not camp_state.is_empty():
			if camp_state in seen_states:
				errors.append("duplicate_camp_state:%s" % camp_state)
			seen_states[camp_state] = true
		if not t10_recipe.is_empty():
			if t10_recipe in seen_t10:
				errors.append("duplicate_t10_recipe:%s" % t10_recipe)
			seen_t10[t10_recipe] = true
		if String(row.get("source_camp_state", "")) == String(row.get("target_camp_state", "")) and not bool(row.get("allow_self_transition", false)):
			errors.append("implicit_self_transition:%s" % camp_state)
		if bool(row.get("shipping", false)):
			if not _nonempty_string(row.get("price_source", "")) and not _nonempty_string(row.get("tuning_record", "")):
				errors.append("shipping_price_provenance_missing:%s" % camp_state)
			if bool(row.get("test_only", false)):
				errors.append("shipping_recipe_marked_test_only:%s" % camp_state)
		else:
			if not bool(row.get("test_only", false)):
				errors.append("nonshipping_recipe_must_be_test_only:%s" % camp_state)
		if not _nonempty_string(row.get("t10_source_state", "")) or not _nonempty_string(row.get("t10_target_state", "")):
			errors.append("t10_semantic_state_binding_missing:%s" % camp_state)
	return {"passed": errors.is_empty(), "errors": errors}

func configure(port: Variant, catalog: Dictionary, initial_camp_state: String, transform_target_id: String) -> bool:
	var validation := validate_catalog(catalog)
	if not bool(validation.passed) or initial_camp_state.is_empty() or transform_target_id.is_empty():
		return false
	if port == null or not port.has_method("preview_transform") or not port.has_method("commit_transform") or not port.has_method("accept_authoritative_receipt"):
		return false
	transform_port = port
	recipes.clear()
	recipes_by_source.clear()
	recipes_by_t10.clear()
	for raw: Variant in catalog.recipes:
		var row: Dictionary = raw.duplicate(true)
		recipes.append(row)
		var source := String(row.source_camp_state)
		if recipes_by_source.has(source):
			return false
		recipes_by_source[source] = row
		recipes_by_t10[String(row.t10_recipe_id)] = row
	_camp_state_id = initial_camp_state
	target_id = transform_target_id
	state_revision = 0
	return true

func configure_from_file(port: Variant, initial_camp_state: String, transform_target_id: String, path := RECIPE_PATH) -> bool:
	return configure(port, read_catalog(path), initial_camp_state, transform_target_id)

func camp_state_id() -> String:
	return _camp_state_id

func next_recipe() -> Dictionary:
	return recipes_by_source.get(_camp_state_id, {}).duplicate(true)

func t10_recipe_id() -> String:
	return String(next_recipe().get("t10_recipe_id", ""))

func preview_camp_upgrade(inventory: Dictionary, available_prerequisites: Array = []) -> Dictionary:
	var recipe := next_recipe()
	if recipe.is_empty():
		return {"passed": false, "errors": ["no_camp_upgrade_from_state"], "camp_state_id": _camp_state_id, "mutated": false, "lifecycle": "blocked"}
	var result: Dictionary = transform_port.preview_transform(String(recipe.t10_recipe_id), target_id, inventory, available_prerequisites)
	var output := result.duplicate(true)
	output["camp_state_id"] = _camp_state_id
	output["target_camp_state"] = String(recipe.target_camp_state)
	output["t10_recipe_id"] = String(recipe.t10_recipe_id)
	output["presentation_key"] = String(recipe.presentation_key)
	output["asset_manifest_key"] = String(recipe.asset_manifest_key)
	output["shipping"] = bool(recipe.shipping)
	output["test_only"] = bool(recipe.get("test_only", false))
	output["mutated"] = false
	output["lifecycle"] = "ready" if bool(output.get("passed", false)) else "blocked"
	return output

func commit_camp_upgrade(transaction_id: String, inventory: Dictionary, available_prerequisites: Array = []) -> Dictionary:
	if transaction_id.is_empty():
		return {"passed": false, "errors": ["invalid_transaction_id"], "camp_state_id": _camp_state_id, "lifecycle": "error"}
	var recipe := next_recipe()
	if recipe.is_empty():
		return {"passed": false, "errors": ["no_camp_upgrade_from_state"], "camp_state_id": _camp_state_id, "lifecycle": "blocked"}
	var before_state := _camp_state_id
	var result: Dictionary = transform_port.commit_transform(transaction_id, String(recipe.t10_recipe_id), target_id, inventory, available_prerequisites)
	var output := result.duplicate(true)
	output["camp_state_id"] = before_state
	output["target_camp_state"] = String(recipe.target_camp_state)
	output["t10_recipe_id"] = String(recipe.t10_recipe_id)
	output["presentation_key"] = String(recipe.presentation_key)
	output["asset_manifest_key"] = String(recipe.asset_manifest_key)
	output["lifecycle"] = "committing" if bool(output.get("passed", false)) else "blocked"
	# T11 never advances authored state on intent/preparation alone.
	output["camp_state_advanced"] = false
	return output

func accept_camp_receipt(receipt: Dictionary) -> Dictionary:
	var accepted: Dictionary = transform_port.accept_authoritative_receipt(receipt)
	var output := accepted.duplicate(true)
	if not bool(output.get("passed", false)):
		output["camp_state_id"] = _camp_state_id
		output["camp_state_advanced"] = false
		output["lifecycle"] = "error"
		return output
	var recipe_id := String(receipt.get("recipe_id", output.get("recipe_id", "")))
	var recipe: Dictionary = recipes_by_t10.get(recipe_id, {})
	if recipe.is_empty():
		return {"passed": false, "errors": ["unknown_t10_recipe_receipt"], "camp_state_id": _camp_state_id, "camp_state_advanced": false, "lifecycle": "error"}
	var target_camp_state := String(recipe.target_camp_state)
	var source_camp_state := String(recipe.source_camp_state)
	var advanced := false
	if _camp_state_id == source_camp_state and (bool(output.get("applied", false)) or bool(output.get("replayed", false))):
		_camp_state_id = target_camp_state
		state_revision += 1
		advanced = true
	elif _camp_state_id == target_camp_state and bool(output.get("replayed", false)):
		advanced = false
	else:
		return {"passed": false, "errors": ["camp_state_receipt_mismatch"], "camp_state_id": _camp_state_id, "camp_state_advanced": false, "lifecycle": "error"}
	output["camp_state_id"] = _camp_state_id
	output["camp_state_advanced"] = advanced
	output["camp_state_revision"] = state_revision
	output["presentation_key"] = String(recipe.presentation_key)
	output["asset_manifest_key"] = String(recipe.asset_manifest_key)
	output["lifecycle"] = "complete"
	return output

func descriptor() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"camp_state_id": _camp_state_id,
		"target_id": target_id,
		"state_revision": state_revision,
		"recipe_count": recipes.size(),
		"t10_recipe_id": t10_recipe_id(),
		"build_pending_dependency": true,
		"owns_resource_counts": false,
		"owns_transform_state": false,
		"owns_progression": false,
		"final_t10_reconciliation_required": true,
	}
