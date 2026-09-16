extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const TransformView = preload("res://scripts/world_transform_view.gd")

class FakeSimulationAuthority:
	var inventory: Dictionary
	var receipts: Dictionary = {}
	var debit_count := 0

	func _init(initial_inventory: Dictionary):
		inventory = initial_inventory.duplicate(true)

	func submit(intent: Dictionary) -> Dictionary:
		if not bool(intent.get("passed", false)) or not bool(intent.get("submit_debit_transaction", false)):
			return {"passed": false, "errors": ["invalid_debit_intent"]}
		var transaction_id := String(intent.get("transaction_id", ""))
		var authority_key := String(intent.get("authority_transaction_key", ""))
		if transaction_id.is_empty() or authority_key.is_empty():
			return {"passed": false, "errors": ["invalid_authority_transaction_key"]}
		if authority_key in receipts:
			var replay: Dictionary = receipts[authority_key].duplicate(true)
			replay["simulation_replayed"] = true
			return replay
		for resource_id in intent.debits:
			if int(inventory.get(resource_id, 0)) < int(intent.debits[resource_id]):
				return {"passed": false, "errors": ["insufficient_authoritative_inventory"], "transaction_id": transaction_id, "authority_transaction_key": authority_key}
		for resource_id in intent.debits:
			inventory[resource_id] = int(inventory.get(resource_id, 0)) - int(intent.debits[resource_id])
		debit_count += 1
		var receipt := intent.duplicate(true)
		receipt["authority_source"] = "simulation"
		receipt["authority_applied"] = true
		receipt["simulation_replayed"] = false
		receipts[authority_key] = receipt.duplicate(true)
		return receipt

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func configured_engine() -> HavenlineWorldTransform:
	var engine := Transform.new()
	if not engine.configure_from_file():
		failures.append("fixture engine configure")
	return engine

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var contract := Transform.contract()
	check("contract locks one in-flight transaction per target", contract.one_inflight_transaction_per_target)
	check("contract requires matching prepared transaction for receipts", contract.receipt_must_match_prepared_transaction)
	check("contract publishes request-scoped simulation idempotency key", contract.authority_idempotency_key_is_request_scoped)
	check("contract bounds completed receipt history per target", contract.bounded_receipt_history_per_target)

	var inventory := {"wood": 100, "stone": 100, "metal": 100, "fuel": 100}
	var engine := configured_engine()
	check("target A registers", engine.register_target("target-A", "seed"))
	var simulation := FakeSimulationAuthority.new(inventory)
	var first := engine.commit_transform("A-1", "framework_anchor_seed_to_foundation", "target-A", simulation.inventory)
	check("target A prepares first debit", first.passed and first.submit_debit_transaction and not String(first.authority_transaction_key).is_empty(), first)
	var racing := engine.commit_transform("A-2", "framework_anchor_seed_to_foundation", "target-A", simulation.inventory)
	check("second transaction against same target is blocked before debit", not racing.passed and racing.errors.has("target_transaction_pending") and not racing.submit_debit_transaction, racing)
	check("blocked target race has not touched simulation", simulation.debit_count == 0 and simulation.inventory == inventory)

	var ack := simulation.submit(first)
	check("simulation applies exact first debit", ack.get("authority_applied", false) and simulation.debit_count == 1 and simulation.inventory.wood == 92 and simulation.inventory.stone == 96, simulation.inventory)
	var accepted := engine.accept_authoritative_receipt(ack)
	check("T10 accepts matching authoritative receipt", accepted.passed and accepted.applied and accepted.accepted_by_world_transform, accepted)
	check("target A advances after authoritative debit", engine.descriptor().targets["target-A"].state == "foundation" and engine.descriptor().targets["target-A"].revision == 1)
	var simulation_replay := simulation.submit(first)
	check("simulation retry uses authority key and cannot debit twice", simulation_replay.simulation_replayed and simulation.debit_count == 1 and simulation.inventory.wood == 92 and simulation.inventory.stone == 96)
	var t10_replay := engine.accept_authoritative_receipt(simulation_replay)
	check("T10 duplicate receipt is idempotent", t10_replay.passed and t10_replay.replayed and not t10_replay.applied)

	# A valid simulation receipt that T10 never prepared must not advance a target.
	check("target B registers", engine.register_target("target-B", "seed"))
	var foreign := configured_engine()
	foreign.register_target("target-B", "seed")
	var foreign_sim := FakeSimulationAuthority.new(inventory)
	var foreign_intent := foreign.commit_transform("foreign-1", "framework_anchor_seed_to_foundation", "target-B", foreign_sim.inventory)
	var foreign_ack := foreign_sim.submit(foreign_intent)
	var unsolicited := engine.accept_authoritative_receipt(foreign_ack)
	check("unsolicited but well-formed simulation receipt is rejected", not unsolicited.passed and unsolicited.errors.has("missing_prepared_transaction"), unsolicited)
	check("unsolicited receipt cannot advance target B", engine.descriptor().targets["target-B"].state == "seed" and engine.descriptor().targets["target-B"].revision == 0)

	# Preview/prepare can race a later authoritative inventory drop. T10 must stay pending.
	check("target C registers", engine.register_target("target-C", "seed"))
	var stale_snapshot := {"wood": 20, "stone": 20, "metal": 0, "fuel": 0}
	var depleted_sim := FakeSimulationAuthority.new({"wood": 0, "stone": 0, "metal": 0, "fuel": 0})
	var stale_intent := engine.commit_transform("C-1", "framework_anchor_seed_to_foundation", "target-C", stale_snapshot)
	check("stale snapshot can only prepare an intent", stale_intent.passed and stale_intent.submit_debit_transaction and engine.descriptor().targets["target-C"].state == "seed")
	var rejected_debit := depleted_sim.submit(stale_intent)
	check("simulation can reject stale resource availability", not rejected_debit.passed and rejected_debit.errors.has("insufficient_authoritative_inventory"))
	check("failed authoritative debit leaves target C pending and unchanged", engine.descriptor().targets["target-C"].state == "seed" and engine.descriptor().prepared_count == 1)
	depleted_sim.inventory.wood = 20
	depleted_sim.inventory.stone = 20
	var recovered_ack := depleted_sim.submit(stale_intent)
	var recovered_accept := engine.accept_authoritative_receipt(recovered_ack)
	check("same pending transaction can succeed after authoritative resources recover", recovered_accept.passed and recovered_accept.applied and engine.descriptor().targets["target-C"].state == "foundation")

	# Crash after simulation debit but before T10 accepts the receipt.
	var crash_engine := configured_engine()
	crash_engine.register_target("target-D", "seed")
	var crash_sim := FakeSimulationAuthority.new(inventory)
	var crash_intent := crash_engine.commit_transform("D-1", "framework_anchor_seed_to_foundation", "target-D", crash_sim.inventory)
	var crash_ack := crash_sim.submit(crash_intent)
	check("simulation debit occurs before crash point", crash_sim.debit_count == 1 and crash_ack.authority_applied)
	var pending_snapshot := crash_engine.export_component_state()
	check("crash snapshot keeps debit intent pending", pending_snapshot.prepared.has("D-1") and pending_snapshot.targets["target-D"].state == "seed")
	var restored := configured_engine()
	check("pending state restores after crash", restored.import_component_state(pending_snapshot))
	var post_crash_accept := restored.accept_authoritative_receipt(crash_ack)
	check("restored T10 accepts already-applied simulation receipt without resubmitting debit", post_crash_accept.passed and post_crash_accept.applied and crash_sim.debit_count == 1)
	check("restored target D advances exactly once", restored.descriptor().targets["target-D"].state == "foundation" and restored.descriptor().targets["target-D"].revision == 1)
	var post_crash_sim_retry := crash_sim.submit(crash_intent)
	check("simulation also replays crash-window authority key without second debit", post_crash_sim_retry.simulation_replayed and crash_sim.debit_count == 1)

	# Different targets may be in-flight together and receipts may return out of order.
	var multi := configured_engine()
	multi.register_target("target-E", "seed")
	multi.register_target("target-F", "seed")
	var multi_sim := FakeSimulationAuthority.new(inventory)
	var e_intent := multi.commit_transform("E-1", "framework_anchor_seed_to_foundation", "target-E", multi_sim.inventory)
	var f_intent := multi.commit_transform("F-1", "framework_anchor_seed_to_foundation", "target-F", multi_sim.inventory)
	check("different targets can prepare concurrently", e_intent.passed and f_intent.passed and multi.descriptor().prepared_count == 2 and e_intent.authority_transaction_key != f_intent.authority_transaction_key)
	var e_ack := multi_sim.submit(e_intent)
	var f_ack := multi_sim.submit(f_intent)
	var f_first := multi.accept_authoritative_receipt(f_ack)
	check("target F receipt may arrive before target E", f_first.passed and f_first.applied and multi.descriptor().targets["target-F"].state == "foundation" and multi.descriptor().targets["target-E"].state == "seed")
	var e_second := multi.accept_authoritative_receipt(e_ack)
	check("target E later receipt still commits independently", e_second.passed and e_second.applied and multi.descriptor().targets["target-E"].state == "foundation")
	check("multi-target authoritative debit count is exact", multi_sim.debit_count == 2)
	check("completed receipt history remains one per completed target", multi.descriptor().receipt_count == 2 and multi.descriptor().receipt_count <= multi.descriptor().receipt_history_bound)

	# Persisted state may never contain two pending transactions for one target.
	var malicious := multi.export_component_state()
	var malicious_identity := "framework_anchor_foundation_to_reinforced|target-E|foundation|reinforced"
	malicious.prepared["evil-1"] = {
		"transaction_id": "evil-1",
		"authority_transaction_key": "T10|%s|revision:2" % malicious_identity,
		"request_identity": malicious_identity,
		"recipe_id": "framework_anchor_foundation_to_reinforced",
		"target_id": "target-E",
		"source_state": "foundation",
		"target_state": "reinforced",
		"debits": {"wood": 12, "stone": 8, "metal": 2},
		"progression_tags": ["opening_transform", "reinforcement"],
		"presentation_key": "framework_reinforced",
		"target_revision": 2,
		"passed": true,
		"replayed": false,
		"submit_debit_transaction": true,
		"authoritative_applied": false,
	}
	malicious.prepared["evil-2"] = malicious.prepared["evil-1"].duplicate(true)
	malicious.prepared["evil-2"].transaction_id = "evil-2"
	var malicious_restore := configured_engine()
	check("component import rejects two in-flight transactions for one target", not malicious_restore.import_component_state(malicious))

	# R11 neutral reusable world-response layer: visuals are bounded and presentation-only.
	var view_contract := TransformView.contract()
	check("view retains frozen five-state core lifecycle", view_contract.lifecycle == ["locked", "ready", "preview", "committing", "complete"])
	check("view exposes explicit blocked lifecycle", view_contract.blocked_lifecycle == "blocked")
	check("view remains neutral and T11-safe", view_contract.neutral_framework_visuals_only and view_contract.t11_owns_final_camp_content)
	check("view uses shape and color redundancy", view_contract.shape_and_color_redundancy and view_contract.world_response_shapes == ["perimeter_ring", "preview_volume", "status_beacon"])
	check("view declares strict four-node visual budget", view_contract.visual_node_budget == 4)
	check("view exposes bounded readability range", view_contract.readability_scale_range == [0.85, 1.35])

	var visual_engine := configured_engine()
	check("visual fixture target registers", visual_engine.register_target("visual-A", "seed"))
	var view := TransformView.new()
	check("visual view target configures", view.configure("visual-A"))
	root.add_child(view)
	await process_frame
	var visual_root := view.get_node_or_null("T10WorldResponse")
	var ring := view.get_node_or_null("T10WorldResponse/StateRing") as MeshInstance3D
	var ghost := view.get_node_or_null("T10WorldResponse/PreviewVolume") as MeshInstance3D
	var beacon := view.get_node_or_null("T10WorldResponse/StatusBeacon") as MeshInstance3D
	var initial_view := view.descriptor()
	check("world-response visuals build exactly once", initial_view.visual_build_count == 1 and initial_view.visual_node_count == 4 and visual_root != null and visual_root.get_child_count() == 3, initial_view)
	check("locked lifecycle hides response geometry", not ring.visible and not ghost.visible and not beacon.visible)
	check("readability below minimum is rejected", not view.configure_readability(0.5) and is_equal_approx(float(view.descriptor().readability_scale), 1.0))
	check("readability above maximum is rejected", not view.configure_readability(2.0) and is_equal_approx(float(view.descriptor().readability_scale), 1.0))
	check("minimum readability scale applies without rebuild", view.configure_readability(0.85) and is_equal_approx(float(view.descriptor().readability_scale), 0.85) and view.descriptor().visual_build_count == 1)
	check("maximum readability scale applies without rebuild", view.configure_readability(1.35) and is_equal_approx(float(view.descriptor().readability_scale), 1.35) and view.descriptor().visual_build_count == 1)
	check("default readability scale restores without rebuild", view.configure_readability(1.0) and is_equal_approx(float(view.descriptor().readability_scale), 1.0) and view.descriptor().visual_build_count == 1)

	view.set_ready()
	check("ready lifecycle shows ring and beacon without ghost", view.descriptor().lifecycle == "ready" and ring.visible and beacon.visible and not ghost.visible)
	var blocked_preview := visual_engine.preview_transform("framework_anchor_seed_to_foundation", "visual-A", {"wood": 7, "stone": 3})
	check("blocked fixture preview is authoritative failure", not blocked_preview.passed and blocked_preview.errors.has("insufficient_resources") and blocked_preview.shortfalls == {"wood": 1, "stone": 1})
	check("blocked world response preserves exact reasons and shortfalls", view.show_blocked(blocked_preview) and view.descriptor().lifecycle == "blocked" and view.descriptor().block_reasons.has("insufficient_resources") and view.descriptor().blocked_shortfalls == {"wood": 1, "stone": 1})
	check("blocked lifecycle uses ring plus flattened beacon without preview ghost", ring.visible and beacon.visible and not ghost.visible and beacon.scale.x > 1.3 and beacon.scale.y < 0.6)
	view.set_ready()
	check("leaving blocked state clears failure payload", view.descriptor().block_reasons.is_empty() and view.descriptor().blocked_shortfalls.is_empty())

	var visual_inventory := {"wood": 20, "stone": 12, "metal": 2, "fuel": 1}
	var visual_preview := visual_engine.preview_transform("framework_anchor_seed_to_foundation", "visual-A", visual_inventory)
	check("preview world response shows ring plus translucent preview volume", view.show_preview(visual_preview) and ring.visible and ghost.visible and not beacon.visible)
	var visual_intent := visual_engine.commit_transform("visual-tx", "framework_anchor_seed_to_foundation", "visual-A", visual_inventory)
	check("committing world response shows all three shapes", view.show_commit(visual_intent) and ring.visible and ghost.visible and beacon.visible)
	var beacon_before_pulse := beacon.scale
	view._process(0.12)
	check("committing beacon pulse changes shape without rebuilding nodes", beacon.scale != beacon_before_pulse and view.descriptor().visual_build_count == 1 and view.descriptor().visual_node_count == 4)
	var visual_ack := visual_intent.duplicate(true)
	visual_ack["authority_source"] = "simulation"
	visual_ack["authority_applied"] = true
	var visual_accepted := visual_engine.accept_authoritative_receipt(visual_ack)
	check("complete world response requires accepted authority receipt", view.mark_complete(visual_accepted) and view.descriptor().lifecycle == "complete")
	check("complete lifecycle removes preview ghost and emphasizes beacon", ring.visible and not ghost.visible and beacon.visible and beacon.scale.x >= 1.24)
	var builds_before_repeat := int(view.descriptor().visual_build_count)
	var children_before_repeat := int(view.descriptor().visual_node_count)
	for iteration in 250:
		view.set_ready()
		view.set_ready()
	check("repeated lifecycle calls create zero visual node growth", view.descriptor().visual_build_count == builds_before_repeat and view.descriptor().visual_node_count == children_before_repeat and children_before_repeat == 4)
	check("view remains presentation-only after full lifecycle", view.descriptor().presentation_only and not view.descriptor().mutates_resources and not view.descriptor().advances_progression)

	print(JSON.stringify({
		"suite": "T10_fixture_simulation_integration",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"check_count": checks.size(),
		"simulation_uses_authority_transaction_key": true,
		"bounded_completed_history": true,
		"r11_world_response_tested": true,
		"visual_node_budget": view_contract.visual_node_budget,
		"visual_build_count": view.descriptor().visual_build_count,
		"visual_node_count": view.descriptor().visual_node_count,
		"real_t09_adapter_bound": false,
		"fixture_simulation_only": true,
		"integration_allowed": false,
		"task_approved": false,
	}))
	quit(0 if failures.is_empty() else 1)
