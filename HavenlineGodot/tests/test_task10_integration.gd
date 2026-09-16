extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")

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
		if transaction_id in receipts:
			var replay: Dictionary = receipts[transaction_id].duplicate(true)
			replay["simulation_replayed"] = true
			return replay
		for resource_id in intent.debits:
			if int(inventory.get(resource_id, 0)) < int(intent.debits[resource_id]):
				return {"passed": false, "errors": ["insufficient_authoritative_inventory"], "transaction_id": transaction_id}
		for resource_id in intent.debits:
			inventory[resource_id] = int(inventory.get(resource_id, 0)) - int(intent.debits[resource_id])
		debit_count += 1
		var receipt := intent.duplicate(true)
		receipt["authority_source"] = "simulation"
		receipt["authority_applied"] = true
		receipt["simulation_replayed"] = false
		receipts[transaction_id] = receipt.duplicate(true)
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

	var inventory := {"wood": 100, "stone": 100, "metal": 100, "fuel": 100}
	var engine := configured_engine()
	check("target A registers", engine.register_target("target-A", "seed"))
	var simulation := FakeSimulationAuthority.new(inventory)
	var first := engine.commit_transform("A-1", "framework_anchor_seed_to_foundation", "target-A", simulation.inventory)
	check("target A prepares first debit", first.passed and first.submit_debit_transaction, first)
	var racing := engine.commit_transform("A-2", "framework_anchor_seed_to_foundation", "target-A", simulation.inventory)
	check("second transaction against same target is blocked before debit", not racing.passed and racing.errors.has("target_transaction_pending") and not racing.submit_debit_transaction, racing)
	check("blocked target race has not touched simulation", simulation.debit_count == 0 and simulation.inventory == inventory)

	var ack := simulation.submit(first)
	check("simulation applies exact first debit", ack.get("authority_applied", false) and simulation.debit_count == 1 and simulation.inventory.wood == 92 and simulation.inventory.stone == 96, simulation.inventory)
	var accepted := engine.accept_authoritative_receipt(ack)
	check("T10 accepts matching authoritative receipt", accepted.passed and accepted.applied and accepted.accepted_by_world_transform, accepted)
	check("target A advances after authoritative debit", engine.descriptor().targets["target-A"].state == "foundation" and engine.descriptor().targets["target-A"].revision == 1)
	var simulation_replay := simulation.submit(first)
	check("simulation retry is idempotent and cannot debit twice", simulation_replay.simulation_replayed and simulation.debit_count == 1 and simulation.inventory.wood == 92 and simulation.inventory.stone == 96)
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
	check("simulation also replays crash-window transaction without second debit", post_crash_sim_retry.simulation_replayed and crash_sim.debit_count == 1)

	# Different targets may be in-flight together and receipts may return out of order.
	var multi := configured_engine()
	multi.register_target("target-E", "seed")
	multi.register_target("target-F", "seed")
	var multi_sim := FakeSimulationAuthority.new(inventory)
	var e_intent := multi.commit_transform("E-1", "framework_anchor_seed_to_foundation", "target-E", multi_sim.inventory)
	var f_intent := multi.commit_transform("F-1", "framework_anchor_seed_to_foundation", "target-F", multi_sim.inventory)
	check("different targets can prepare concurrently", e_intent.passed and f_intent.passed and multi.descriptor().prepared_count == 2)
	var e_ack := multi_sim.submit(e_intent)
	var f_ack := multi_sim.submit(f_intent)
	var f_first := multi.accept_authoritative_receipt(f_ack)
	check("target F receipt may arrive before target E", f_first.passed and f_first.applied and multi.descriptor().targets["target-F"].state == "foundation" and multi.descriptor().targets["target-E"].state == "seed")
	var e_second := multi.accept_authoritative_receipt(e_ack)
	check("target E later receipt still commits independently", e_second.passed and e_second.applied and multi.descriptor().targets["target-E"].state == "foundation")
	check("multi-target authoritative debit count is exact", multi_sim.debit_count == 2)

	# Persisted state may never contain two pending transactions for one target.
	var malicious := multi.export_component_state()
	malicious.prepared["evil-1"] = {
		"transaction_id": "evil-1",
		"request_identity": "framework_anchor_foundation_to_reinforced|target-E|foundation|reinforced",
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

	print(JSON.stringify({
		"suite": "T10_fixture_simulation_integration",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"check_count": checks.size(),
		"real_t09_adapter_bound": false,
		"fixture_simulation_only": true,
		"integration_allowed": false,
		"task_approved": false,
	}))
	quit(0 if failures.is_empty() else 1)
