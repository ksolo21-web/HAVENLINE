extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const TransformView = preload("res://scripts/world_transform_view.gd")

const STRESS_TARGETS := 512
const STRESS_TIME_BUDGET_MS := 5000.0
const STRESS_MEMORY_BUDGET_BYTES := 64 * 1024 * 1024
const PREVIEW_STRESS_ITERATIONS := 5000
const REJECT_STRESS_ITERATIONS := 5000
const CATALOG_STRESS_RECIPES := 256

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

func expect_import_rejected(label: String, baseline: Dictionary, mutated: Dictionary) -> void:
	var probe := Transform.new()
	var configured := probe.configure_from_file()
	var rejected := configured and not probe.import_component_state(mutated)
	check(label, rejected)
	check(label + " leaves clean probe state", probe.descriptor().target_count == 0 and probe.descriptor().prepared_count == 0 and probe.descriptor().receipt_count == 0)

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
	check("one in-flight transaction per target is explicit", contract.one_inflight_transaction_per_target)
	check("simulation idempotency key is request scoped", contract.authority_idempotency_key_is_request_scoped)
	check("completed receipt history is bounded per target", contract.bounded_receipt_history_per_target and contract.receipt_history_policy == "latest_completed_receipt_per_target")
	check("recipe graph is monotonic except explicit inverse pairs", contract.recipe_graph_is_monotonic_except_explicit_inverse_pairs)
	check("reversible pairs require reciprocal inverse metadata", contract.reversible_pairs_require_reciprocal_inverse_metadata)
	check("T14 global save/versioning boundary is preserved", contract.global_save_versioning_owned_by_t14)
	check("T09 adapter remains required before integration", contract.t09_adapter_required_before_integration)

	# R01/R07 catalog validation must fail closed before any runtime target exists.
	var base_forward: Dictionary = {
		"recipe_id": "guard-forward",
		"source_state": "guard-a",
		"target_state": "guard-b",
		"costs": [{"resource_id": "wood", "quantity": 2}],
		"prerequisites": [],
		"progression_tags": ["guard-forward"],
		"presentation_key": "guard-fixture",
	}
	var duplicate_recipe: Dictionary = base_forward.duplicate(true)
	var duplicate_guard := Transform.new()
	check("duplicate recipe IDs are rejected", not duplicate_guard.configure({"recipes": [base_forward, duplicate_recipe]}))

	var missing_state: Dictionary = base_forward.duplicate(true)
	missing_state.erase("target_state")
	var missing_state_guard := Transform.new()
	check("recipe missing target state is rejected", not missing_state_guard.configure({"recipes": [missing_state]}))

	var zero_cost: Dictionary = base_forward.duplicate(true)
	zero_cost.costs = [{"resource_id": "wood", "quantity": 0}]
	var zero_cost_guard := Transform.new()
	check("zero recipe cost is rejected", not zero_cost_guard.configure({"recipes": [zero_cost]}))

	var negative_cost: Dictionary = base_forward.duplicate(true)
	negative_cost.costs = [{"resource_id": "wood", "quantity": -1}]
	var negative_cost_guard := Transform.new()
	check("negative recipe cost is rejected", not negative_cost_guard.configure({"recipes": [negative_cost]}))

	var duplicate_cost: Dictionary = base_forward.duplicate(true)
	duplicate_cost.costs = [{"resource_id": "wood", "quantity": 1}, {"resource_id": "wood", "quantity": 1}]
	var duplicate_cost_guard := Transform.new()
	check("duplicate resource cost rows are rejected", not duplicate_cost_guard.configure({"recipes": [duplicate_cost]}))

	var duplicate_prerequisite: Dictionary = base_forward.duplicate(true)
	duplicate_prerequisite.prerequisites = ["same", "same"]
	var duplicate_prerequisite_guard := Transform.new()
	check("duplicate recipe prerequisites are rejected", not duplicate_prerequisite_guard.configure({"recipes": [duplicate_prerequisite]}))

	var self_transition: Dictionary = base_forward.duplicate(true)
	self_transition.recipe_id = "guard-self"
	self_transition.source_state = "guard-self-state"
	self_transition.target_state = "guard-self-state"
	var self_guard := Transform.new()
	check("implicit self transition is rejected", not self_guard.configure({"recipes": [self_transition]}))
	self_transition.allow_self_transition = true
	var explicit_self_guard := Transform.new()
	check("explicit self transition may be modeled", explicit_self_guard.configure({"recipes": [self_transition]}))

	var undeclared_inverse: Dictionary = base_forward.duplicate(true)
	undeclared_inverse.inverse_recipe_id = "something"
	var undeclared_inverse_guard := Transform.new()
	check("inverse metadata without reversible opt-in is rejected", not undeclared_inverse_guard.configure({"recipes": [undeclared_inverse]}))

	var missing_inverse: Dictionary = base_forward.duplicate(true)
	missing_inverse.reversible = true
	missing_inverse.inverse_recipe_id = "guard-reverse"
	var missing_inverse_guard := Transform.new()
	check("reversible recipe with missing inverse is rejected", not missing_inverse_guard.configure({"recipes": [missing_inverse]}))

	var cycle_forward: Dictionary = base_forward.duplicate(true)
	cycle_forward.recipe_id = "cycle-a-b"
	cycle_forward.source_state = "cycle-a"
	cycle_forward.target_state = "cycle-b"
	var cycle_back: Dictionary = base_forward.duplicate(true)
	cycle_back.recipe_id = "cycle-b-a"
	cycle_back.source_state = "cycle-b"
	cycle_back.target_state = "cycle-a"
	var two_cycle_guard := Transform.new()
	check("undeclared two-state progression cycle is rejected", not two_cycle_guard.configure({"recipes": [cycle_forward, cycle_back]}))

	var cycle_mid: Dictionary = base_forward.duplicate(true)
	cycle_mid.recipe_id = "cycle-b-c"
	cycle_mid.source_state = "cycle-b"
	cycle_mid.target_state = "cycle-c"
	var cycle_close: Dictionary = base_forward.duplicate(true)
	cycle_close.recipe_id = "cycle-c-a"
	cycle_close.source_state = "cycle-c"
	cycle_close.target_state = "cycle-a"
	var three_cycle_guard := Transform.new()
	check("undeclared multi-state progression cycle is rejected", not three_cycle_guard.configure({"recipes": [cycle_forward, cycle_mid, cycle_close]}))

	var reversible_forward: Dictionary = {
		"recipe_id": "warm-up",
		"source_state": "cold",
		"target_state": "warm",
		"costs": [{"resource_id": "wood", "quantity": 2}],
		"prerequisites": [],
		"progression_tags": ["warming"],
		"presentation_key": "reversible-fixture",
		"reversible": true,
		"inverse_recipe_id": "cool-down",
	}
	var reversible_inverse: Dictionary = {
		"recipe_id": "cool-down",
		"source_state": "warm",
		"target_state": "cold",
		"costs": [{"resource_id": "stone", "quantity": 1}],
		"prerequisites": [],
		"progression_tags": ["cooling"],
		"presentation_key": "reversible-fixture",
		"reversible": true,
		"inverse_recipe_id": "warm-up",
	}
	var nonreciprocal_inverse: Dictionary = reversible_inverse.duplicate(true)
	nonreciprocal_inverse.inverse_recipe_id = "not-warm-up"
	var nonreciprocal_guard := Transform.new()
	check("nonreciprocal inverse declaration is rejected", not nonreciprocal_guard.configure({"recipes": [reversible_forward, nonreciprocal_inverse]}))
	var wrong_endpoint_inverse: Dictionary = reversible_inverse.duplicate(true)
	wrong_endpoint_inverse.source_state = "other-state"
	var endpoint_guard := Transform.new()
	check("inverse declaration with wrong endpoints is rejected", not endpoint_guard.configure({"recipes": [reversible_forward, wrong_endpoint_inverse]}))

	var reversible_engine := Transform.new()
	check("explicit reciprocal reversible pair configures", reversible_engine.configure({"recipes": [reversible_forward, reversible_inverse]}))
	check("reversible target registers", reversible_engine.register_target("reversible-target", "cold"))
	var reversible_preview := reversible_engine.preview_transform("warm-up", "reversible-target", {"wood": 2})
	check("reversible forward preview exposes inverse contract", reversible_preview.passed and reversible_preview.reversible and reversible_preview.inverse_recipe_id == "cool-down")
	var reversible_intent := reversible_engine.commit_transform("reversible-up", "warm-up", "reversible-target", {"wood": 2})
	var reversible_forward_result := reversible_engine.accept_authoritative_receipt(simulation_ack(reversible_intent))
	check("reversible forward transition commits once", reversible_forward_result.passed and reversible_engine.descriptor().targets["reversible-target"].state == "warm" and reversible_engine.descriptor().targets["reversible-target"].revision == 1)
	var inverse_preview := reversible_engine.preview_transform("cool-down", "reversible-target", {"stone": 1})
	check("explicit inverse preview uses declared inverse cost", inverse_preview.passed and inverse_preview.costs == {"stone": 1} and inverse_preview.inverse_recipe_id == "warm-up")
	var inverse_intent := reversible_engine.commit_transform("reversible-down", "cool-down", "reversible-target", {"stone": 1})
	var inverse_result := reversible_engine.accept_authoritative_receipt(simulation_ack(inverse_intent))
	check("explicit inverse returns to source without skipping revision", inverse_result.passed and reversible_engine.descriptor().targets["reversible-target"].state == "cold" and reversible_engine.descriptor().targets["reversible-target"].revision == 2)

	var transactional_guard := Transform.new()
	check("valid recipe configuration establishes transactional baseline", transactional_guard.configure({"recipes": [base_forward]}))
	var transactional_before := transactional_guard.recipes.duplicate(true)
	check("failed cyclic reconfiguration preserves prior catalog", not transactional_guard.configure({"recipes": [cycle_forward, cycle_back]}) and transactional_guard.recipes == transactional_before)

	var engine := Transform.new()
	check("formal recipe catalog loads", engine.configure_from_file())
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
	check("prepared debit carries request-scoped authority key", String(first.authority_transaction_key).contains(first.request_identity) and String(first.authority_transaction_key).ends_with("revision:1"), first)
	check("framework never mutates caller inventory", inventory == inventory_before)
	check("prepared intent does not advance world state", engine.descriptor().targets["anchor-A"].state == "seed" and engine.descriptor().targets["anchor-A"].revision == 0)
	check("prepared intent is retained until authority replies", engine.descriptor().prepared_count == 1 and engine.descriptor().receipt_count == 0)

	var pending_replay := engine.commit_transform("tx-001", "framework_anchor_seed_to_foundation", "anchor-A", inventory)
	check("same pending transaction is idempotent retry", pending_replay.passed and pending_replay.replayed and pending_replay.submit_debit_transaction and not pending_replay.authoritative_applied, pending_replay)
	check("pending retry preserves identical authority idempotency key", pending_replay.authority_transaction_key == first.authority_transaction_key)
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
	check("second-stage authority key differs from first stage", second.authority_transaction_key != first.authority_transaction_key and String(second.authority_transaction_key).ends_with("revision:2"))
	check("second-stage prepare still leaves foundation visible", engine.descriptor().targets["anchor-A"].state == "foundation" and engine.descriptor().prepared_count == 1)
	var second_accepted := engine.accept_authoritative_receipt(simulation_ack(second))
	check("second-stage authoritative receipt commits", second_accepted.passed and second_accepted.applied and second_accepted.target_revision == 2, second_accepted)
	check("second-stage state is deterministic after authority", engine.descriptor().targets["anchor-A"].state == "reinforced")
	check("completed receipt history is pruned to latest receipt for target", engine.descriptor().receipt_count == 1 and not engine.receipts.has("tx-001") and engine.receipts.has("tx-002"), engine.receipts)
	check("out-of-order source-state transform is blocked", not engine.preview_transform("framework_anchor_seed_to_foundation", "anchor-A", inventory).passed)
	var old_receipt_after_advance := engine.accept_authoritative_receipt(first_ack)
	check("pruned old authoritative receipt fails closed after later state", not old_receipt_after_advance.passed and old_receipt_after_advance.errors.has("missing_prepared_transaction"))
	var old_commit_after_advance := engine.commit_transform("tx-001", "framework_anchor_seed_to_foundation", "anchor-A", inventory)
	check("pruned old commit cannot resubmit debit after later state", not old_commit_after_advance.passed and not old_commit_after_advance.get("submit_debit_transaction", false))

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
	check("pending debit intent survives crash for idempotent resubmission", retry_after_crash.passed and retry_after_crash.replayed and retry_after_crash.submit_debit_transaction and retry_after_crash.authority_transaction_key == crash_intent.authority_transaction_key, retry_after_crash)
	check("crash restore still does not advance before authority", crash_restored.descriptor().targets["crash-anchor"].state == "seed")
	var accepted_after_crash := crash_restored.accept_authoritative_receipt(simulation_ack(crash_intent))
	check("authoritative receipt closes recovered pending transaction", accepted_after_crash.passed and accepted_after_crash.applied and crash_restored.descriptor().targets["crash-anchor"].state == "foundation")

	var exported := engine.export_component_state()
	var restored := Transform.new()
	check("restored engine loads same recipes", restored.configure_from_file())
	check("completed component state imports after reload", restored.import_component_state(exported))
	check("component recovery preserves exact completed state", restored.export_component_state() == exported)
	var replay_after_reload := restored.commit_transform("tx-002", "framework_anchor_foundation_to_reinforced", "anchor-A", inventory, ["harvesting_online"])
	check("latest completed receipt replay protection survives reload", replay_after_reload.passed and replay_after_reload.replayed and not replay_after_reload.submit_debit_transaction)
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

	# Adversarial component-state import cases that must fail closed.
	var wrong_authority := before_bad_import.duplicate(true)
	wrong_authority.authority_id = "forged"
	expect_import_rejected("forged component authority is rejected", before_bad_import, wrong_authority)
	var empty_target_state := before_bad_import.duplicate(true)
	empty_target_state.targets["anchor-A"].state = ""
	expect_import_rejected("empty target state is rejected", before_bad_import, empty_target_state)
	var duplicate_tags := before_bad_import.duplicate(true)
	duplicate_tags.targets["anchor-A"].progression_tags = ["x", "x"]
	expect_import_rejected("duplicate target progression tags are rejected", before_bad_import, duplicate_tags)
	var missing_target := before_bad_import.duplicate(true)
	missing_target.receipts["tx-002"].target_id = "ghost"
	expect_import_rejected("receipt for missing target is rejected", before_bad_import, missing_target)
	var bad_resource := before_bad_import.duplicate(true)
	bad_resource.receipts["tx-002"].debits["fish"] = 1
	expect_import_rejected("receipt with unknown resource is rejected", before_bad_import, bad_resource)
	var negative_debit := before_bad_import.duplicate(true)
	negative_debit.receipts["tx-002"].debits["wood"] = -1
	expect_import_rejected("receipt with negative debit is rejected", before_bad_import, negative_debit)
	var forged_key := before_bad_import.duplicate(true)
	forged_key.receipts["tx-002"].authority_transaction_key = "forged-key"
	expect_import_rejected("receipt with forged authority idempotency key is rejected", before_bad_import, forged_key)
	var overlap := crash_snapshot.duplicate(true)
	overlap.receipts["tx-crash"] = overlap.prepared["tx-crash"].duplicate(true)
	expect_import_rejected("same transaction cannot be pending and completed", crash_snapshot, overlap)
	var duplicate_receipt_target := before_bad_import.duplicate(true)
	var duplicate_receipt: Dictionary = duplicate_receipt_target.receipts["tx-002"].duplicate(true)
	duplicate_receipt.transaction_id = "duplicate-latest"
	duplicate_receipt.authority_transaction_key = "T10|%s|revision:%d" % [duplicate_receipt.request_identity, int(duplicate_receipt.target_revision)]
	duplicate_receipt_target.receipts["duplicate-latest"] = duplicate_receipt
	expect_import_rejected("component state cannot retain two completed receipts for one target", before_bad_import, duplicate_receipt_target)

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

	# R12 repeated preview and rejected-commit stress must create no history growth.
	var bounded := Transform.new()
	check("bounded-history stress engine loads recipes", bounded.configure_from_file())
	check("bounded-history stress target registers", bounded.register_target("bounded", "seed"))
	var bounded_before := bounded.export_component_state()
	var preview_started := Time.get_ticks_usec()
	var preview_stress_ok := true
	for iteration in PREVIEW_STRESS_ITERATIONS:
		var repeated := bounded.preview_transform("framework_anchor_seed_to_foundation", "bounded", inventory)
		preview_stress_ok = preview_stress_ok and repeated.passed
	var preview_elapsed_ms := float(Time.get_ticks_usec() - preview_started) / 1000.0
	check("5000 repeated previews all succeed", preview_stress_ok)
	check("repeated previews create zero component history growth", bounded.export_component_state() == bounded_before)
	var reject_started := Time.get_ticks_usec()
	var reject_stress_ok := true
	for iteration in REJECT_STRESS_ITERATIONS:
		var rejected := bounded.commit_transform("reject-%d" % iteration, "framework_anchor_seed_to_foundation", "bounded", {"wood": 0, "stone": 0})
		reject_stress_ok = reject_stress_ok and not rejected.passed and not rejected.get("submit_debit_transaction", false)
	var reject_elapsed_ms := float(Time.get_ticks_usec() - reject_started) / 1000.0
	check("5000 rejected commits all fail closed", reject_stress_ok)
	check("rejected commits create zero prepared/receipt history", bounded.descriptor().prepared_count == 0 and bounded.descriptor().receipt_count == 0 and bounded.export_component_state() == bounded_before)
	check("preview/reject stress stays inside conservative prebuild ceiling", preview_elapsed_ms + reject_elapsed_ms <= STRESS_TIME_BUDGET_MS, {"preview_ms": preview_elapsed_ms, "reject_ms": reject_elapsed_ms, "budget_ms": STRESS_TIME_BUDGET_MS})

	# R10/R12 branching + many-recipe catalog fixture without shipping T11 content.
	var catalog_rows: Array = []
	for index in CATALOG_STRESS_RECIPES:
		catalog_rows.append({
			"recipe_id": "bulk-%03d" % index,
			"source_state": "bulk-source-%03d" % index,
			"target_state": "bulk-target-%03d" % index,
			"costs": [{"resource_id": "wood", "quantity": 1 + index % 3}],
			"prerequisites": [],
			"progression_tags": ["bulk-tag-%03d" % index],
			"presentation_key": "bulk-fixture",
		})
	# Two explicit branches from the same neutral source prove branching semantics.
	catalog_rows.append({"recipe_id":"branch-left","source_state":"branch-root","target_state":"branch-left-state","costs":[{"resource_id":"stone","quantity":2}],"prerequisites":[],"progression_tags":["branch-left"],"presentation_key":"branch-fixture"})
	catalog_rows.append({"recipe_id":"branch-right","source_state":"branch-root","target_state":"branch-right-state","costs":[{"resource_id":"metal","quantity":1}],"prerequisites":[],"progression_tags":["branch-right"],"presentation_key":"branch-fixture"})
	var catalog_engine := Transform.new()
	var catalog_started := Time.get_ticks_usec()
	check("258-recipe neutral stress catalog configures", catalog_engine.configure({"recipes": catalog_rows}) and catalog_engine.recipes.size() == CATALOG_STRESS_RECIPES + 2)
	var catalog_preview_ok := true
	for index in CATALOG_STRESS_RECIPES:
		var target_id := "bulk-target-instance-%03d" % index
		catalog_preview_ok = catalog_preview_ok and catalog_engine.register_target(target_id, "bulk-source-%03d" % index)
		var bulk_preview := catalog_engine.preview_transform("bulk-%03d" % index, target_id, {"wood": 3})
		catalog_preview_ok = catalog_preview_ok and bulk_preview.passed
	catalog_engine.register_target("branch-A", "branch-root")
	catalog_engine.register_target("branch-B", "branch-root")
	var branch_left := catalog_engine.preview_transform("branch-left", "branch-A", {"stone": 2})
	var branch_right := catalog_engine.preview_transform("branch-right", "branch-B", {"metal": 1})
	var catalog_elapsed_ms := float(Time.get_ticks_usec() - catalog_started) / 1000.0
	check("256 bulk recipe previews remain deterministic", catalog_preview_ok)
	check("neutral branching recipes can diverge from one source without semantic changes", branch_left.passed and branch_right.passed and branch_left.target_state != branch_right.target_state)
	check("large recipe catalog preview produces no receipt/prepared history", catalog_engine.descriptor().prepared_count == 0 and catalog_engine.descriptor().receipt_count == 0)
	check("258-recipe catalog configure/preview stays bounded", catalog_elapsed_ms <= STRESS_TIME_BUDGET_MS, {"elapsed_ms": catalog_elapsed_ms, "budget_ms": STRESS_TIME_BUDGET_MS})

	# Bounded stress: two complete transformations for hundreds of independent targets.
	var stress := Transform.new()
	check("stress engine loads recipes", stress.configure_from_file())
	var stress_inventory := {"wood": 1000000, "stone": 1000000, "metal": 1000000, "fuel": 1000000}
	var memory_before := OS.get_static_memory_usage()
	var stress_started := Time.get_ticks_usec()
	var stress_ok := true
	for index in STRESS_TARGETS:
		var target_id := "stress-%04d" % index
		stress_ok = stress_ok and stress.register_target(target_id, "seed")
		var first_intent := stress.commit_transform("stress-%04d-a" % index, "framework_anchor_seed_to_foundation", target_id, stress_inventory)
		stress_ok = stress_ok and first_intent.passed and first_intent.submit_debit_transaction
		var first_result := stress.accept_authoritative_receipt(simulation_ack(first_intent))
		stress_ok = stress_ok and first_result.passed and first_result.applied
		var second_intent := stress.commit_transform("stress-%04d-b" % index, "framework_anchor_foundation_to_reinforced", target_id, stress_inventory, ["harvesting_online"])
		stress_ok = stress_ok and second_intent.passed and second_intent.submit_debit_transaction
		var second_result := stress.accept_authoritative_receipt(simulation_ack(second_intent))
		stress_ok = stress_ok and second_result.passed and second_result.applied
	var stress_elapsed_ms := float(Time.get_ticks_usec() - stress_started) / 1000.0
	var memory_delta := maxi(0, OS.get_static_memory_usage() - memory_before)
	var stress_descriptor := stress.descriptor()
	check("512-target two-stage stress completes without semantic failure", stress_ok)
	check("stress creates exact target cardinality with bounded latest-receipt history", stress_descriptor.target_count == STRESS_TARGETS and stress_descriptor.receipt_count == STRESS_TARGETS and stress_descriptor.prepared_count == 0 and stress_descriptor.receipt_history_bound == STRESS_TARGETS, stress_descriptor)
	var every_reinforced := true
	for target_id in stress_descriptor.targets:
		every_reinforced = every_reinforced and String(stress_descriptor.targets[target_id].state) == "reinforced" and int(stress_descriptor.targets[target_id].revision) == 2
	check("stress leaves every target at exact reinforced revision", every_reinforced)
	check("stress runtime stays inside conservative prebuild ceiling", stress_elapsed_ms <= STRESS_TIME_BUDGET_MS, {"elapsed_ms": stress_elapsed_ms, "budget_ms": STRESS_TIME_BUDGET_MS})
	check("stress static-memory growth stays bounded", memory_delta <= STRESS_MEMORY_BUDGET_BYTES, {"memory_delta_bytes": memory_delta, "budget_bytes": STRESS_MEMORY_BUDGET_BYTES})
	var stress_snapshot := stress.export_component_state()
	check("stress snapshot keeps no more than one completed receipt per target", stress_snapshot.receipts.size() == STRESS_TARGETS)
	var stress_restored := Transform.new()
	check("stress snapshot reload configures recipes", stress_restored.configure_from_file())
	check("stress snapshot round-trips exactly", stress_restored.import_component_state(stress_snapshot) and stress_restored.export_component_state() == stress_snapshot)

	print(JSON.stringify({
		"suite": "T10_world_transform_formal_prebuild",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"check_count": checks.size(),
		"prepared_count": engine.descriptor().prepared_count,
		"receipt_count": engine.descriptor().receipt_count,
		"preview_stress_iterations": PREVIEW_STRESS_ITERATIONS,
		"reject_stress_iterations": REJECT_STRESS_ITERATIONS,
		"catalog_stress_recipes": CATALOG_STRESS_RECIPES + 2,
		"preview_stress_elapsed_ms": preview_elapsed_ms,
		"reject_stress_elapsed_ms": reject_elapsed_ms,
		"catalog_stress_elapsed_ms": catalog_elapsed_ms,
		"stress_targets": STRESS_TARGETS,
		"stress_transactions": STRESS_TARGETS * 2,
		"stress_retained_receipts": stress_descriptor.receipt_count,
		"stress_elapsed_ms": stress_elapsed_ms,
		"stress_memory_delta_bytes": memory_delta,
		"integration_allowed": false,
		"task_approved": false,
		"t09_adapter_bound": false,
	}))
	quit(0 if failures.is_empty() else 1)
