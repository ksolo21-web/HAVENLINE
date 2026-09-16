extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const TransformView = preload("res://scripts/world_transform_view.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var contract := Transform.contract()
	check("T10 authority is exact", contract.authority_id == "T10-world-transform-v1")
	check("resource quantities remain simulation-owned", contract.simulation_owns_resource_counts and contract.presentation_may_not_grant_resources)
	check("preview purity and exact-once receipts are explicit", contract.preview_is_pure and contract.exactly_once_transaction_receipts)
	check("T14 global save/versioning boundary is preserved", contract.global_save_versioning_owned_by_t14)
	check("T09 adapter remains required before integration", contract.t09_adapter_required_before_integration)

	var engine := Transform.new()
	check("prebuild recipe catalog loads", engine.configure_from_file())
	check("two deterministic framework fixtures load", engine.recipes.size() == 2)
	check("duplicate target registration is rejected", engine.register_target("anchor-A", "seed") and not engine.register_target("anchor-A", "seed"))

	var inventory := {"wood": 20, "stone": 12, "metal": 2, "fuel": 1}
	var inventory_before := inventory.duplicate(true)
	var descriptor_before := engine.descriptor()
	var preview := engine.preview_transform("framework_anchor_seed_to_foundation", "anchor-A", inventory)
	check("opening transform preview succeeds", preview.passed and preview.source_state == "seed" and preview.target_state == "foundation", preview)
	check("preview exposes normalized exact debit cost", preview.costs == {"wood": 8, "stone": 4}, preview)
	check("preview is pure for caller inventory", inventory == inventory_before)
	check("preview is pure for transform state", engine.descriptor() == descriptor_before)

	var insufficient := engine.preview_transform("framework_anchor_seed_to_foundation", "anchor-A", {"wood": 7, "stone": 3})
	check("insufficient resource preview fails closed", not insufficient.passed and insufficient.errors.has("insufficient_resources"), insufficient)
	check("shortfall quantities are exact", insufficient.shortfalls == {"wood": 1, "stone": 1}, insufficient)
	check("invalid inventory shape fails closed", not engine.preview_transform("framework_anchor_seed_to_foundation", "anchor-A", {"wood": -1}).passed)
	check("unknown inventory resource fails closed", not engine.preview_transform("framework_anchor_seed_to_foundation", "anchor-A", {"wood": 8, "fish": 3}).passed)
	check("unknown recipe fails closed", not engine.preview_transform("missing", "anchor-A", inventory).passed)
	check("unknown target fails closed", not engine.preview_transform("framework_anchor_seed_to_foundation", "missing", inventory).passed)

	var failed_commit := engine.commit_transform("tx-low", "framework_anchor_seed_to_foundation", "anchor-A", {"wood": 1, "stone": 1})
	check("failed commit never requests debit", not failed_commit.passed and not failed_commit.apply_debits)
	check("failed commit leaves target unchanged", engine.descriptor().targets["anchor-A"].state == "seed" and engine.descriptor().receipt_count == 0)

	var first := engine.commit_transform("tx-001", "framework_anchor_seed_to_foundation", "anchor-A", inventory)
	check("first transaction commits exactly once", first.passed and first.apply_debits and not first.replayed, first)
	check("first transaction debit intent is exact", first.debits == {"wood": 8, "stone": 4}, first)
	check("framework never mutates caller inventory", inventory == inventory_before)
	check("target state advances once", engine.descriptor().targets["anchor-A"].state == "foundation" and engine.descriptor().targets["anchor-A"].revision == 1)
	check("receipt ledger records one transaction", engine.descriptor().receipt_count == 1)

	var replay := engine.commit_transform("tx-001", "framework_anchor_seed_to_foundation", "anchor-A", inventory)
	check("same transaction is idempotent replay", replay.passed and replay.replayed and not replay.apply_debits, replay)
	check("replay cannot advance target twice", engine.descriptor().targets["anchor-A"].state == "foundation" and engine.descriptor().targets["anchor-A"].revision == 1)
	check("replay cannot create duplicate receipt", engine.descriptor().receipt_count == 1)
	var collision := engine.commit_transform("tx-001", "framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("transaction id reuse for different request fails closed", not collision.passed and collision.errors.has("transaction_id_collision"), collision)

	var second_no_prereq := engine.preview_transform("framework_anchor_foundation_to_reinforced", "anchor-A", inventory)
	check("required upstream prerequisite is enforced", not second_no_prereq.passed and second_no_prereq.errors.has("missing_prerequisite:harvesting_online"), second_no_prereq)
	var second_preview := engine.preview_transform("framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("second-stage preview succeeds with prerequisite", second_preview.passed and second_preview.costs == {"wood": 12, "stone": 8, "metal": 2}, second_preview)
	var second := engine.commit_transform("tx-002", "framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("second-stage transaction commits", second.passed and second.apply_debits and second.target_revision == 2, second)
	check("second-stage state is deterministic", engine.descriptor().targets["anchor-A"].state == "reinforced" and engine.descriptor().receipt_count == 2)
	check("out-of-order source-state transform is blocked", not engine.preview_transform("framework_anchor_seed_to_foundation", "anchor-A", inventory).passed)

	var exported := engine.export_component_state()
	var restored := Transform.new()
	check("restored engine loads same recipes", restored.configure_from_file())
	check("component state imports after reload", restored.import_component_state(exported))
	check("component recovery preserves exact target state", restored.export_component_state() == exported)
	var replay_after_reload := restored.commit_transform("tx-002", "framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("receipt replay protection survives reload", replay_after_reload.passed and replay_after_reload.replayed and not replay_after_reload.apply_debits)
	var before_bad_import := restored.export_component_state()
	var malformed := before_bad_import.duplicate(true)
	malformed["schema_version"] = 999
	check("unknown component schema fails closed", not restored.import_component_state(malformed))
	check("failed import is transactional", restored.export_component_state() == before_bad_import)
	var bad_receipt := before_bad_import.duplicate(true)
	bad_receipt.receipts["tx-002"].target_revision = 99
	check("receipt newer than target revision fails recovery", not restored.import_component_state(bad_receipt))
	check("failed receipt recovery keeps prior state", restored.export_component_state() == before_bad_import)

	var view_contract := TransformView.contract()
	check("view lifecycle contains all frozen states", view_contract.lifecycle == ["locked", "ready", "preview", "committing", "complete"])
	check("view is presentation-only", view_contract.presentation_only and not view_contract.mutates_resources and not view_contract.advances_progression)
	check("T11 retains final camp-content ownership", view_contract.t11_owns_final_camp_content)
	var view := TransformView.new()
	root.add_child(view)
	check("view target configures", view.configure("anchor-A"))
	view.set_ready()
	check("view enters ready lifecycle", view.descriptor().lifecycle == "ready")
	check("valid preview enters preview lifecycle", view.show_preview(preview) and view.descriptor().lifecycle == "preview")
	check("committed receipt enters committing lifecycle", view.show_commit(first) and view.descriptor().lifecycle == "committing")
	check("matching committed receipt completes lifecycle", view.mark_complete(first) and view.descriptor().lifecycle == "complete")
	var updates := view.update_count
	view.mark_complete(first)
	check("unchanged lifecycle does not rebuild presentation state", view.update_count == updates)
	check("replayed receipt cannot retrigger committing presentation", not view.show_commit(replay))

	var deterministic_a := Transform.new()
	var deterministic_b := Transform.new()
	deterministic_a.configure_from_file(); deterministic_b.configure_from_file()
	deterministic_a.register_target("same", "seed"); deterministic_b.register_target("same", "seed")
	var ra := deterministic_a.commit_transform("same-tx", "framework_anchor_seed_to_foundation", "same", inventory)
	var rb := deterministic_b.commit_transform("same-tx", "framework_anchor_seed_to_foundation", "same", inventory)
	check("identical inputs produce identical transaction receipts", ra == rb)
	check("identical inputs produce identical component state", deterministic_a.export_component_state() == deterministic_b.export_component_state())

	print(JSON.stringify({
		"suite": "T10_dependency_independent_prebuild",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"check_count": checks.size(),
		"receipt_count": engine.descriptor().receipt_count,
		"integration_allowed": false,
		"task_approved": false,
		"t09_adapter_bound": false,
	}))
	quit(0 if failures.is_empty() else 1)
