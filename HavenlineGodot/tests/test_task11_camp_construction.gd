extends SceneTree

const Domain = preload("res://scripts/camp_construction.gd")

class MockT10Port:
	extends RefCounted
	var state := "seed"
	var revision := 0
	var prepared := {}
	var completed := {}
	var recipe_states := {
		"framework_anchor_seed_to_foundation": ["seed", "foundation"],
		"framework_anchor_foundation_to_reinforced": ["foundation", "reinforced"],
	}

	func preview_transform(recipe_id: String, target_id: String, inventory: Dictionary, available_prerequisites: Array = []) -> Dictionary:
		if recipe_id not in recipe_states:
			return {"passed": false, "errors": ["unknown_recipe"], "mutated": false}
		var states: Array = recipe_states[recipe_id]
		if state != String(states[0]):
			return {"passed": false, "errors": ["source_state_mismatch"], "mutated": false}
		if recipe_id.ends_with("reinforced") and "harvesting_online" not in available_prerequisites:
			return {"passed": false, "errors": ["missing_prerequisite:harvesting_online"], "mutated": false}
		return {
			"passed": true,
			"errors": [],
			"recipe_id": recipe_id,
			"target_id": target_id,
			"source_state": String(states[0]),
			"target_state": String(states[1]),
			"target_revision": revision,
			"costs": {},
			"shortfalls": {},
			"mutated": false,
		}

	func commit_transform(transaction_id: String, recipe_id: String, target_id: String, inventory: Dictionary, available_prerequisites: Array = []) -> Dictionary:
		if transaction_id in completed:
			var replay: Dictionary = completed[transaction_id].duplicate(true)
			replay["passed"] = true
			replay["replayed"] = true
			replay["submit_debit_transaction"] = false
			return replay
		if transaction_id in prepared:
			var pending: Dictionary = prepared[transaction_id].duplicate(true)
			pending["passed"] = true
			pending["replayed"] = true
			pending["submit_debit_transaction"] = true
			return pending
		var preview := preview_transform(recipe_id, target_id, inventory, available_prerequisites)
		if not bool(preview.get("passed", false)):
			return {"passed": false, "errors": preview.get("errors", []), "replayed": false, "submit_debit_transaction": false}
		var intent := {
			"passed": true,
			"transaction_id": transaction_id,
			"authority_transaction_key": "mock|%s|%d" % [recipe_id, revision + 1],
			"request_identity": "%s|%s|%s|%s" % [recipe_id, target_id, preview.source_state, preview.target_state],
			"recipe_id": recipe_id,
			"target_id": target_id,
			"source_state": preview.source_state,
			"target_state": preview.target_state,
			"target_revision": revision + 1,
			"debits": {},
			"progression_tags": [],
			"presentation_key": "mock",
			"replayed": false,
			"submit_debit_transaction": true,
			"authoritative_applied": false,
		}
		prepared[transaction_id] = intent.duplicate(true)
		return intent

	func accept_authoritative_receipt(receipt: Dictionary) -> Dictionary:
		var transaction_id := String(receipt.get("transaction_id", ""))
		if transaction_id in completed:
			var replay: Dictionary = completed[transaction_id].duplicate(true)
			replay["passed"] = true
			replay["applied"] = false
			replay["replayed"] = true
			return replay
		if transaction_id not in prepared:
			return {"passed": false, "errors": ["missing_prepared_transaction"], "applied": false, "replayed": false}
		if not bool(receipt.get("authority_applied", false)) or String(receipt.get("authority_source", "")) != "simulation":
			return {"passed": false, "errors": ["invalid_authoritative_receipt"], "applied": false, "replayed": false}
		var intent: Dictionary = prepared[transaction_id]
		if String(receipt.get("recipe_id", "")) != String(intent.recipe_id) or String(receipt.get("target_state", "")) != String(intent.target_state):
			return {"passed": false, "errors": ["receipt_mismatch"], "applied": false, "replayed": false}
		state = String(intent.target_state)
		revision = int(intent.target_revision)
		prepared.erase(transaction_id)
		var accepted := intent.duplicate(true)
		accepted["passed"] = true
		accepted["applied"] = true
		accepted["replayed"] = false
		completed[transaction_id] = accepted.duplicate(true)
		return accepted

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var catalog := Domain.read_catalog()
	var validation := Domain.validate_catalog(catalog)
	check("build-pending catalog validates", bool(validation.get("passed", false)), validation)
	check("catalog has no shipping recipes", catalog.get("recipes", []).all(func(row): return row.shipping == false and row.test_only == true))
	check("T11 recipes do not duplicate numeric cost authority", catalog.get("recipes", []).all(func(row): return not row.has("costs") and not row.has("debits")))

	var port := MockT10Port.new()
	var domain := Domain.new()
	check("domain configures against injected semantic port", domain.configure(port, catalog, "site_unbuilt", "camp-main"))
	check("initial camp identity is stable", domain.camp_state_id() == "site_unbuilt")
	check("first T10 prebuild binding is selected", domain.t10_recipe_id() == "framework_anchor_seed_to_foundation")

	var inventory := {"wood": 99, "stone": 99, "metal": 99, "fuel": 99}
	var inventory_before := inventory.duplicate(true)
	var preview := domain.preview_camp_upgrade(inventory)
	check("preview is eligible through injected port", bool(preview.get("passed", false)) and preview.lifecycle == "ready", preview)
	check("preview cannot mutate caller inventory", inventory == inventory_before)
	check("preview does not advance authored camp state", domain.camp_state_id() == "site_unbuilt")

	var intent := domain.commit_camp_upgrade("t11-build-001", inventory)
	check("intent enters committing lifecycle", bool(intent.get("passed", false)) and intent.lifecycle == "committing", intent)
	check("intent preparation does not advance authored camp state", domain.camp_state_id() == "site_unbuilt")
	check("intent preparation cannot mutate caller inventory", inventory == inventory_before)

	var receipt := intent.duplicate(true)
	receipt["authority_applied"] = true
	receipt["authority_source"] = "simulation"
	var accepted := domain.accept_camp_receipt(receipt)
	check("authoritative receipt advances exactly one authored stage", bool(accepted.get("passed", false)) and accepted.get("camp_state_advanced", false) and domain.camp_state_id() == "camp_initial", accepted)
	var revision_after_first := domain.state_revision
	var replay := domain.accept_camp_receipt(receipt)
	check("receipt replay is idempotent in authored presentation state", bool(replay.get("passed", false)) and not replay.get("camp_state_advanced", true) and domain.state_revision == revision_after_first and domain.camp_state_id() == "camp_initial", replay)

	var blocked_upgrade := domain.preview_camp_upgrade(inventory)
	check("second upgrade respects semantic prerequisite", not bool(blocked_upgrade.get("passed", true)) and blocked_upgrade.lifecycle == "blocked", blocked_upgrade)
	var ready_upgrade := domain.preview_camp_upgrade(inventory, ["harvesting_online"])
	check("second upgrade becomes ready with prerequisite", bool(ready_upgrade.get("passed", false)) and ready_upgrade.target_camp_state == "camp_upgraded_01", ready_upgrade)
	var intent2 := domain.commit_camp_upgrade("t11-build-002", inventory, ["harvesting_online"])
	var receipt2 := intent2.duplicate(true)
	receipt2["authority_applied"] = true
	receipt2["authority_source"] = "simulation"
	var accepted2 := domain.accept_camp_receipt(receipt2)
	check("second authoritative receipt reaches visible upgrade state", bool(accepted2.get("passed", false)) and domain.camp_state_id() == "camp_upgraded_01", accepted2)
	check("terminal build-pending stage exposes no guessed next action", not bool(domain.preview_camp_upgrade(inventory).get("passed", true)))

	var duplicated_cost_catalog := catalog.duplicate(true)
	duplicated_cost_catalog.recipes[0]["costs"] = [{"resource_id": "wood", "quantity": 1}]
	check("T11 rejects duplicated local cost authority", not bool(Domain.validate_catalog(duplicated_cost_catalog).passed))
	var unproven_shipping := catalog.duplicate(true)
	unproven_shipping.recipes[0]["shipping"] = true
	unproven_shipping.recipes[0]["test_only"] = false
	check("shipping recipe without price provenance fails closed", not bool(Domain.validate_catalog(unproven_shipping).passed))

	var descriptor := domain.descriptor()
	check("domain owns no resource counts", descriptor.owns_resource_counts == false)
	check("domain owns no transform state", descriptor.owns_transform_state == false)
	check("domain owns no progression", descriptor.owns_progression == false)
	check("final T10 reconciliation remains explicit", descriptor.final_t10_reconciliation_required == true)

	var report := {
		"task": "T11",
		"suite": "camp_construction_domain_build_pending",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"build_pending_dependency": true,
		"task_approved": false,
	}
	print(JSON.stringify(report))
	quit(0 if failures.is_empty() else 1)
