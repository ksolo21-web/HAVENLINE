extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const TransformView = preload("res://scripts/world_transform_view.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func simulation_ack(intent: Dictionary) -> Dictionary:
	var receipt := intent.duplicate(true)
	receipt["authority_source"] = "simulation"
	receipt["authority_applied"] = true
	return receipt

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var contract := Transform.contract()
	check("T10 authority is exact", contract.authority_id == "T10-world-transform-v1")
	check("resource quantities remain simulation-owned", contract.simulation_owns_resource_counts and contract.presentation_may_not_grant_resources)
	check("preview purity is explicit", contract.preview_is_pure)
	check("commit prepares an idempotent debit transaction", contract.commit_prepares_idempotent_debit_transaction)
	check("world state waits for authoritative resource receipt", contract.state_advances_only_after_authoritative_receipt)
	check("exact-once receipts are explicit", contract.exactly_once_transaction_receipts)
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
	check("failed commit never submits debit", not failed_commit.passed and not failed_commit.submit_debit_transaction)
	check("failed commit leaves target unchanged", engine.descriptor().targets["anchor-A"].state == "seed" and engine.descriptor().prepared_count == 0 and engine.descriptor().receipt_count == 0)

	var first := engine.commit_transform("tx-001", "framework_anchor_seed_to_foundation", "anchor-A", inventory)
	check("first transaction prepares exactly one debit intent", first.passed and first.submit_debit_transaction and not first.replayed and not first.authoritative_applied, first)
	check("prepared debit intent is exact", first.debits == {"wood": 8, "stone": 4}, first)
	check("framework never mutates caller inventory", inventory == inventory_before)
	check("prepared intent does not advance world state", engine.descriptor().targets["anchor-A"].state == "seed" and engine.descriptor().targets["anchor-A"].revision == 0)
	check("prepared intent is retained until authority replies", engine.descriptor().prepared_count == 1 and engine.descriptor().receipt_count == 0)

	var pending_replay := engine.commit_transform("tx-001", "framework_anchor_seed_to_foundation", "anchor-A", inventory)
	check("same pending transaction is idempotent retry", pending_replay.passed and pending_replay.replayed and pending_replay.submit_debit_transaction and not pending_replay.authoritative_applied, pending_replay)
	check("pending retry cannot advance target", engine.descriptor().targets["anchor-A"].state == "seed" and engine.descriptor().targets["anchor-A"].revision == 0)
	check("pending retry cannot duplicate prepared transaction", engine.descriptor().prepared_count == 1 and engine.descriptor().receipt_count == 0)
	var pending_collision := engine.commit_transform("tx-001", "framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("transaction id reuse for different pending request fails closed", not pending_collision.passed and pending_collision.errors.has("transaction_id_collision"), pending_collision)

	var untrusted := first.duplicate(true)
	untrusted["authority_applied"] = true
	var untrusted_result := engine.accept_authoritative_receipt(untrusted)
	check("receipt without simulation authority fails closed", not untrusted_result.passed and untrusted_result.errors.has("invalid_authoritative_receipt"), untrusted_result)
	check("untrusted receipt leaves world state pending", engine.descriptor().targets["anchor-A"].state == "seed" and engine.descriptor().prepared_count == 1)
	var wrong_debit := simulation_ack(first)
	wrong_debit.debits["wood"] = 7
	var wrong_debit_result := engine.accept_authoritative_receipt(wrong_debit)
	check("authoritative receipt with altered debit fails closed", not wrong_debit_result.passed and wrong_debit_result.errors.has("receipt_debit_mismatch"), wrong_debit_result)
	check("mismatched receipt cannot consume prepared state", engine.descriptor().prepared_count == 1 and engine.descriptor().receipt_count == 0)

	var first_ack := simulation_ack(first)
	var first_accepted := engine.accept_authoritative_receipt(first_ack)
	check("valid simulation receipt is accepted by T10", first_accepted.passed and first_accepted.applied and first_accepted.accepted_by_world_transform, first_accepted)
	check("world state advances only after accepted debit receipt", engine.descriptor().targets["anchor-A"].state == "foundation" and engine.descriptor().targets["anchor-A"].revision == 1)
	check("accepted receipt moves transaction from prepared to completed", engine.descriptor().prepared_count == 0 and engine.descriptor().receipt_count == 1)
	var duplicate_ack := engine.accept_authoritative_receipt(first_ack)
	check("duplicate authoritative receipt is idempotent", duplicate_ack.passed and duplicate_ack.replayed and not duplicate_ack.applied and duplicate_ack.accepted_by_world_transform, duplicate_ack)
	check("duplicate authoritative receipt cannot advance target twice", engine.descriptor().targets["anchor-A"].revision == 1 and engine.descriptor().receipt_count == 1)
	var completed_retry := engine.commit_transform("tx-001", "framework_anchor_seed_to_foundation", "anchor-A", inventory)
	check("completed transaction retry never resubmits debit", completed_retry.passed and completed_retry.replayed and not completed_retry.submit_debit_transaction and completed_retry.authoritative_applied, completed_retry)
	var completed_collision := engine.commit_transform("tx-001", "framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("completed transaction id collision fails closed", not completed_collision.passed and completed_collision.errors.has("transaction_id_collision"), completed_collision)

	var second_no_prereq := engine.preview_transform("framework_anchor_foundation_to_reinforced", "anchor-A", inventory)
	check("required upstream prerequisite is enforced", not second_no_prereq.passed and second_no_prereq.errors.has("missing_prerequisite:harvesting_online"), second_no_prereq)
	var second_preview := engine.preview_transform("framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("second-stage preview succeeds with prerequisite", second_preview.passed and second_preview.costs == {"wood": 12, "stone": 8, "metal": 2}, second_preview)
	var second := engine.commit_transform("tx-002", "framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("second-stage transaction prepares debit", second.passed and second.submit_debit_transaction and second.target_revision == 2, second)
	check("second-stage prepare still leaves foundation visible", engine.descriptor().targets["anchor-A"].state == "foundation" and engine.descriptor().prepared_count == 1)
	var second_accepted := engine.accept_authoritative_receipt(simulation_ack(second))
	check("second-stage authoritative receipt commits", second_accepted.passed and second_accepted.applied and second_accepted.target_revision == 2, second_accepted)
	check("second-stage state is deterministic after authority", engine.descriptor().targets["anchor-A"].state == "reinforced" and engine.descriptor().receipt_count == 2)
	check("out-of-order source-state transform is blocked", not engine.preview_transform("framework_anchor_seed_to_foundation", "anchor-A", inventory).passed)

	var crash_engine := Transform.new()
	crash_engine.configure_from_file()
	crash_engine.register_target("crash-anchor", "seed")
	var crash_intent := crash_engine.commit_transform("tx-crash", "framework_anchor_seed_to_foundation", "crash-anchor", inventory)
	var crash_snapshot := crash_engine.export_component_state()
	check("pending transaction is included in component recovery snapshot", crash_snapshot.prepared.size() == 1 and crash_snapshot.receipts.is_empty() and crash_snapshot.targets["crash-anchor"].state == "seed")
	var crash_restored := Transform.new()
	check("crash restore loads same recipes", crash_restored.configure_from_file())
	check("crash restore imports pending transaction", crash_restored.import_component_state(crash_snapshot))
	var retry_after_crash := crash_restored.commit_transform("tx-crash", "framework_anchor_seed_to_foundation", "crash-anchor", inventory)
	check("pending debit intent survives crash for idempotent resubmission", retry_after_crash.passed and retry_after_crash.replayed and retry_after_crash.submit_debit_transaction, retry_after_crash)
	check("crash restore still does not advance before authority", crash_restored.descriptor().targets["crash-anchor"].state == "seed")
	var accepted_after_crash := crash_restored.accept_authoritative_receipt(simulation_ack(crash_intent))
	check("authoritative receipt closes recovered pending transaction", accepted_after_crash.passed and accepted_after_crash.applied and crash_restored.descriptor().targets["crash-anchor"].state == "foundation")

	var exported := engine.export_component_state()
	var restored := Transform.new()
	check("restored engine loads same recipes", restored.configure_from_file())
	check("completed component state imports after reload", restored.import_component_state(exported))
	check("component recovery preserves exact completed state", restored.export_component_state() == exported)
	var replay_after_reload := restored.commit_transform("tx-002", "framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("completed receipt replay protection survives reload", replay_after_reload.passed and replay_after_reload.replayed and not replay_after_reload.submit_debit_transaction)
	var before_bad_import := restored.export_component_state()
	var malformed := before_bad_import.duplicate(true)
	malformed["schema_version"] = 999
	check("unknown component schema fails closed", not restored.import_component_state(malformed))
	check("failed schema import is transactional", restored.export_component_state() == before_bad_import)
	var bad_receipt := before_bad_import.duplicate(true)
	bad_receipt.receipts["tx-002"].target_revision = 99
	check("receipt newer than target revision fails recovery", not restored.import_component_state(bad_receipt))
	check("failed receipt recovery keeps prior state", restored.export_component_state() == before_bad_import)
	var malformed_pending := crash_snapshot.duplicate(true)
	malformed_pending.prepared["tx-crash"].target_revision = 99
	var pending_restore_guard := Transform.new()
	pending_restore_guard.configure_from_file()
	check("pending transaction with impossible future revision fails recovery", not pending_restore_guard.import_component_state(malformed_pending))

	var view_contract := TransformView.contract()
	check("view lifecycle contains all frozen states", view_contract.lifecycle == ["locked", "ready", "preview", "committing", "complete"])
	check("view is presentation-only", view_contract.presentation_only and not view_contract.mutates_resources and not view_contract.advances_progression)
	check("view completion requires simulation and T10 acceptance", view_contract.complete_requires_simulation_receipt and view_contract.complete_requires_world_transform_acceptance)
	check("T11 retains final camp-content ownership", view_contract.t11_owns_final_camp_content)
	var view := TransformView.new()
	root.add_child(view)
	check("view target configures", view.configure("anchor-A"))
	view.set_ready()
	check("view enters ready lifecycle", view.descriptor().lifecycle == "ready")
	check("valid preview enters preview lifecycle", view.show_preview(preview) and view.descriptor().lifecycle == "preview")
	check("prepared intent enters committing lifecycle", view.show_commit(first) and view.descriptor().lifecycle == "committing")
	check("raw simulation receipt cannot complete before T10 accepts it", not view.mark_complete(first_ack) and view.descriptor().lifecycle == "committing")
	check("T10-accepted receipt completes lifecycle", view.mark_complete(first_accepted) and view.descriptor().lifecycle == "complete")
	var updates := view.update_count
	check("already complete lifecycle cannot be completed twice", not view.mark_complete(first_accepted))
	check("unchanged lifecycle does not rebuild presentation state", view.update_count == updates)
	check("completed replay cannot retrigger committing presentation", not view.show_commit(completed_retry))

	var deterministic_a := Transform.new()
	var deterministic_b := Transform.new()
	deterministic_a.configure_from_file(); deterministic_b.configure_from_file()
	deterministic_a.register_target("same", "seed"); deterministic_b.register_target("same", "seed")
	var intent_a := deterministic_a.commit_transform("same-tx", "framework_anchor_seed_to_foundation", "same", inventory)
	var intent_b := deterministic_b.commit_transform("same-tx", "framework_anchor_seed_to_foundation", "same", inventory)
	check("identical inputs produce identical prepared debit intents", intent_a == intent_b)
	check("identical prepared inputs produce identical pending component state", deterministic_a.export_component_state() == deterministic_b.export_component_state())
	var accepted_a := deterministic_a.accept_authoritative_receipt(simulation_ack(intent_a))
	var accepted_b := deterministic_b.accept_authoritative_receipt(simulation_ack(intent_b))
	check("identical authoritative receipts produce identical accepted receipts", accepted_a == accepted_b)
	check("identical authoritative receipts produce identical completed component state", deterministic_a.export_component_state() == deterministic_b.export_component_state())

	print(JSON.stringify({
		"suite": "T10_dependency_independent_prebuild",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"check_count": checks.size(),
		"prepared_count": engine.descriptor().prepared_count,
		"receipt_count": engine.descriptor().receipt_count,
		"integration_allowed": false,
		"task_approved": false,
		"t09_adapter_bound": false,
	}))
	quit(0 if failures.is_empty() else 1)
