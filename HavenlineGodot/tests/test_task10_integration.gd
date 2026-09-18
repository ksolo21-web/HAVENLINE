extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const TransformView = preload("res://scripts/world_transform_view.gd")
const Simulation = preload("res://scripts/simulation.gd")

class FakeSimulationAuthority:
	# Mirrors the shipping simulation authority split:
	# - inventory = carried/not-yet-delivered resources
	# - stored = delivered resources eligible for T10 affordability/debit
	var inventory: Dictionary
	var stored: Dictionary
	var receipts_by_target: Dictionary = {}
	var debit_count := 0

	func _init(initial_stored: Dictionary, initial_inventory: Dictionary = {}):
		stored = initial_stored.duplicate(true)
		inventory = initial_inventory.duplicate(true)

	func available_for_transform() -> Dictionary:
		return stored.duplicate(true)

	func harvest_to_carried(resource_id: String, quantity: int) -> bool:
		if resource_id.is_empty() or quantity <= 0:
			return false
		inventory[resource_id] = int(inventory.get(resource_id, 0)) + quantity
		return true

	func deposit(resource_id: String, quantity: int) -> bool:
		if resource_id.is_empty() or quantity <= 0 or int(inventory.get(resource_id, 0)) < quantity:
			return false
		inventory[resource_id] = int(inventory.get(resource_id, 0)) - quantity
		stored[resource_id] = int(stored.get(resource_id, 0)) + quantity
		return true

	func submit(intent: Dictionary) -> Dictionary:
		if not bool(intent.get("passed", false)) or not bool(intent.get("submit_debit_transaction", false)):
			return {"passed": false, "errors": ["invalid_debit_intent"]}
		var transaction_id := String(intent.get("transaction_id", ""))
		var authority_key := String(intent.get("authority_transaction_key", ""))
		var target_id := String(intent.get("target_id", ""))
		var target_revision := int(intent.get("target_revision", 0))
		if transaction_id.is_empty() or authority_key.is_empty() or target_id.is_empty() or target_revision <= 0:
			return {"passed": false, "errors": ["invalid_authority_transaction_key"]}
		if target_id in receipts_by_target:
			var prior: Dictionary = receipts_by_target[target_id]
			if String(prior.get("authority_transaction_key", "")) == authority_key:
				var replay: Dictionary = prior.duplicate(true)
				replay["simulation_replayed"] = true
				return replay
			if target_revision <= int(prior.get("target_revision", 0)):
				return {
					"passed": false,
					"errors": ["stale_authority_transaction"],
					"transaction_id": transaction_id,
					"authority_transaction_key": authority_key,
					"authority_applied": false,
				}
		for resource_id in intent.debits:
			if int(stored.get(resource_id, 0)) < int(intent.debits[resource_id]):
				return {
					"passed": false,
					"errors": ["insufficient_authoritative_stored"],
					"transaction_id": transaction_id,
					"authority_transaction_key": authority_key,
					"authority_applied": false,
				}
		for resource_id in intent.debits:
			stored[resource_id] = int(stored.get(resource_id, 0)) - int(intent.debits[resource_id])
		debit_count += 1
		var receipt := intent.duplicate(true)
		receipt["authority_source"] = "simulation"
		receipt["authority_applied"] = true
		receipt["simulation_replayed"] = false
		receipts_by_target[target_id] = receipt.duplicate(true)
		return receipt

	func export_receipt_state() -> Dictionary:
		return receipts_by_target.duplicate(true)

	func import_receipt_state(state: Dictionary) -> bool:
		var next := {}
		for target_id in state:
			var row: Variant = state[target_id]
			if String(target_id).is_empty() or not (row is Dictionary):
				return false
			if String(row.get("target_id", "")) != String(target_id):
				return false
			if String(row.get("authority_transaction_key", "")).is_empty() or int(row.get("target_revision", 0)) <= 0:
				return false
			next[String(target_id)] = row.duplicate(true)
		receipts_by_target = next
		return true

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
	run_real_authority()
	var contract := Transform.contract()
	check("contract locks one in-flight transaction per target", contract.one_inflight_transaction_per_target)
	check("contract requires matching prepared transaction for receipts", contract.receipt_must_match_prepared_transaction)
	check("contract publishes request-scoped simulation idempotency key", contract.authority_idempotency_key_is_request_scoped)
	check("contract bounds completed receipt history per target", contract.bounded_receipt_history_per_target)

	var delivered := {"wood": 100, "stone": 100, "metal": 100, "fuel": 100}
	var engine := configured_engine()
	check("target A registers", engine.register_target("target-A", "seed"))
	var simulation := FakeSimulationAuthority.new(delivered)
	var first := engine.commit_transform("A-1", "framework_anchor_seed_to_foundation", "target-A", simulation.available_for_transform())
	check("target A prepares first debit", first.passed and first.submit_debit_transaction and not String(first.authority_transaction_key).is_empty(), first)
	var racing := engine.commit_transform("A-2", "framework_anchor_seed_to_foundation", "target-A", simulation.available_for_transform())
	check("second transaction against same target is blocked before debit", not racing.passed and racing.errors.has("target_transaction_pending") and not racing.submit_debit_transaction, racing)
	check("blocked target race has not touched simulation", simulation.debit_count == 0 and simulation.stored == delivered)

	var ack := simulation.submit(first)
	check("simulation applies exact first debit to delivered stored resources", ack.get("authority_applied", false) and simulation.debit_count == 1 and simulation.stored.wood == 92 and simulation.stored.stone == 96, simulation.stored)
	var accepted := engine.accept_authoritative_receipt(ack)
	check("T10 accepts matching authoritative receipt", accepted.passed and accepted.applied and accepted.accepted_by_world_transform, accepted)
	check("target A advances after authoritative debit", engine.descriptor().targets["target-A"].state == "foundation" and engine.descriptor().targets["target-A"].revision == 1)
	var simulation_replay := simulation.submit(first)
	check("simulation retry uses authority key and cannot debit twice", simulation_replay.simulation_replayed and simulation.debit_count == 1 and simulation.stored.wood == 92 and simulation.stored.stone == 96)
	var t10_replay := engine.accept_authoritative_receipt(simulation_replay)
	check("T10 duplicate receipt is idempotent", t10_replay.passed and t10_replay.replayed and not t10_replay.applied)

	# R06: harvested/carried resources cannot pay for transformation until delivered.
	var delivery_engine := configured_engine()
	check("R06 delivered-resource target registers", delivery_engine.register_target("target-delivery", "seed"))
	var delivery_sim := FakeSimulationAuthority.new(
		{"wood": 0, "stone": 0, "metal": 0, "fuel": 0},
		{"wood": 8, "stone": 4, "metal": 0, "fuel": 0}
	)
	var carried_before := delivery_sim.inventory.duplicate(true)
	var stored_before := delivery_sim.stored.duplicate(true)
	var carried_only_preview := delivery_engine.preview_transform("framework_anchor_seed_to_foundation", "target-delivery", delivery_sim.available_for_transform())
	check("carried resources alone cannot satisfy T10 affordability", not carried_only_preview.passed and carried_only_preview.errors.has("insufficient_resources") and carried_only_preview.shortfalls == {"wood": 8, "stone": 4})
	check("R06 preview does not mutate carried or stored resources", delivery_sim.inventory == carried_before and delivery_sim.stored == stored_before)
	check("deposit moves wood from carried inventory to delivered stored", delivery_sim.deposit("wood", 8) and delivery_sim.inventory.wood == 0 and delivery_sim.stored.wood == 8)
	check("deposit moves stone from carried inventory to delivered stored", delivery_sim.deposit("stone", 4) and delivery_sim.inventory.stone == 0 and delivery_sim.stored.stone == 4)
	var delivered_preview := delivery_engine.preview_transform("framework_anchor_seed_to_foundation", "target-delivery", delivery_sim.available_for_transform())
	check("same transform becomes eligible only after deposit", delivered_preview.passed and delivered_preview.costs == {"wood": 8, "stone": 4}, delivered_preview)
	var delivery_intent := delivery_engine.commit_transform("delivery-1", "framework_anchor_seed_to_foundation", "target-delivery", delivery_sim.available_for_transform())
	var carried_at_debit := delivery_sim.inventory.duplicate(true)
	var delivery_ack := delivery_sim.submit(delivery_intent)
	check("authoritative transform debit consumes stored only", delivery_ack.get("authority_applied", false) and delivery_sim.stored.wood == 0 and delivery_sim.stored.stone == 0 and delivery_sim.inventory == carried_at_debit)
	var delivery_accept := delivery_engine.accept_authoritative_receipt(delivery_ack)
	check("delivered-resource receipt advances T10 exactly once", delivery_accept.passed and delivery_accept.applied and delivery_engine.descriptor().targets["target-delivery"].state == "foundation")

	# A valid simulation receipt that T10 never prepared must not advance a target.
	check("target B registers", engine.register_target("target-B", "seed"))
	var foreign := configured_engine()
	foreign.register_target("target-B", "seed")
	var foreign_sim := FakeSimulationAuthority.new(delivered)
	var foreign_intent := foreign.commit_transform("foreign-1", "framework_anchor_seed_to_foundation", "target-B", foreign_sim.available_for_transform())
	var foreign_ack := foreign_sim.submit(foreign_intent)
	var unsolicited := engine.accept_authoritative_receipt(foreign_ack)
	check("unsolicited but well-formed simulation receipt is rejected", not unsolicited.passed and unsolicited.errors.has("missing_prepared_transaction"), unsolicited)
	check("unsolicited receipt cannot advance target B", engine.descriptor().targets["target-B"].state == "seed" and engine.descriptor().targets["target-B"].revision == 0)

	# Preview/prepare can race a later authoritative stored-balance drop. T10 must stay pending.
	check("target C registers", engine.register_target("target-C", "seed"))
	var stale_snapshot := {"wood": 20, "stone": 20, "metal": 0, "fuel": 0}
	var depleted_sim := FakeSimulationAuthority.new({"wood": 0, "stone": 0, "metal": 0, "fuel": 0})
	var stale_intent := engine.commit_transform("C-1", "framework_anchor_seed_to_foundation", "target-C", stale_snapshot)
	check("stale snapshot can only prepare an intent", stale_intent.passed and stale_intent.submit_debit_transaction and engine.descriptor().targets["target-C"].state == "seed")
	var rejected_debit := depleted_sim.submit(stale_intent)
	check("simulation can reject stale delivered resource availability", not rejected_debit.passed and rejected_debit.errors.has("insufficient_authoritative_stored"))
	check("failed authoritative debit leaves target C pending and unchanged", engine.descriptor().targets["target-C"].state == "seed" and engine.descriptor().prepared_count == 1)
	depleted_sim.stored.wood = 20
	depleted_sim.stored.stone = 20
	var recovered_ack := depleted_sim.submit(stale_intent)
	var recovered_accept := engine.accept_authoritative_receipt(recovered_ack)
	check("same pending transaction can succeed after authoritative stored resources recover", recovered_accept.passed and recovered_accept.applied and engine.descriptor().targets["target-C"].state == "foundation")

	# Crash after simulation debit but before T10 accepts the receipt.
	var crash_engine := configured_engine()
	crash_engine.register_target("target-D", "seed")
	var crash_sim := FakeSimulationAuthority.new(delivered)
	var crash_intent := crash_engine.commit_transform("D-1", "framework_anchor_seed_to_foundation", "target-D", crash_sim.available_for_transform())
	var crash_ack := crash_sim.submit(crash_intent)
	check("simulation debit occurs before crash point", crash_sim.debit_count == 1 and crash_ack.authority_applied)
	var pending_snapshot := crash_engine.export_component_state()
	var simulation_receipt_snapshot := crash_sim.export_receipt_state()
	check("crash snapshot keeps debit intent pending", pending_snapshot.prepared.has("D-1") and pending_snapshot.targets["target-D"].state == "seed")
	check("simulation crash snapshot retains latest bounded debit receipt", simulation_receipt_snapshot.size() == 1 and simulation_receipt_snapshot.has("target-D"))
	var restored := configured_engine()
	check("pending state restores after crash", restored.import_component_state(pending_snapshot))
	var restored_sim := FakeSimulationAuthority.new(crash_sim.stored)
	check("simulation bounded receipt state restores after crash", restored_sim.import_receipt_state(simulation_receipt_snapshot))
	var post_crash_retry_receipt := restored_sim.submit(crash_intent)
	check("restored simulation replays prior debit without second mutation", post_crash_retry_receipt.get("simulation_replayed", false) and restored_sim.debit_count == 0 and restored_sim.stored == crash_sim.stored)
	var post_crash_accept := restored.accept_authoritative_receipt(post_crash_retry_receipt)
	check("restored T10 accepts already-applied simulation receipt without resubmitting debit", post_crash_accept.passed and post_crash_accept.applied)
	check("restored target D advances exactly once", restored.descriptor().targets["target-D"].state == "foundation" and restored.descriptor().targets["target-D"].revision == 1)
	var post_crash_sim_retry := restored_sim.submit(crash_intent)
	check("simulation also replays crash-window authority key without second debit", post_crash_sim_retry.simulation_replayed and restored_sim.debit_count == 0)

	# Different targets may be in-flight together and receipts may return out of order.
	var multi := configured_engine()
	multi.register_target("target-E", "seed")
	multi.register_target("target-F", "seed")
	var multi_sim := FakeSimulationAuthority.new(delivered)
	var e_intent := multi.commit_transform("E-1", "framework_anchor_seed_to_foundation", "target-E", multi_sim.available_for_transform())
	var f_intent := multi.commit_transform("F-1", "framework_anchor_seed_to_foundation", "target-F", multi_sim.available_for_transform())
	check("different targets can prepare concurrently", e_intent.passed and f_intent.passed and multi.descriptor().prepared_count == 2 and e_intent.authority_transaction_key != f_intent.authority_transaction_key)
	var e_ack := multi_sim.submit(e_intent)
	var f_ack := multi_sim.submit(f_intent)
	var f_first := multi.accept_authoritative_receipt(f_ack)
	check("target F receipt may arrive before target E", f_first.passed and f_first.applied and multi.descriptor().targets["target-F"].state == "foundation" and multi.descriptor().targets["target-E"].state == "seed")
	var e_second := multi.accept_authoritative_receipt(e_ack)
	check("target E later receipt still commits independently", e_second.passed and e_second.applied and multi.descriptor().targets["target-E"].state == "foundation")
	check("multi-target authoritative debit count is exact", multi_sim.debit_count == 2)
	check("simulation receipt history remains bounded one latest row per target", multi_sim.receipts_by_target.size() == 2)
	check("completed receipt history remains one per completed target", multi.descriptor().receipt_count == 2 and multi.descriptor().receipt_count <= multi.descriptor().receipt_history_bound)

	# A higher revision for a target may replace its simulation receipt; stale lower/equal revisions fail closed.
	var revision_engine := configured_engine()
	revision_engine.register_target("target-revision", "seed")
	var revision_sim := FakeSimulationAuthority.new(delivered)
	var revision_one := revision_engine.commit_transform("rev-1", "framework_anchor_seed_to_foundation", "target-revision", revision_sim.available_for_transform())
	var revision_one_ack := revision_sim.submit(revision_one)
	var revision_one_accept := revision_engine.accept_authoritative_receipt(revision_one_ack)
	check("first target revision commits through bounded simulation ledger", revision_one_accept.passed and revision_sim.receipts_by_target.size() == 1)
	var revision_two := revision_engine.commit_transform("rev-2", "framework_anchor_foundation_to_reinforced", "target-revision", revision_sim.available_for_transform(), ["harvesting_online"])
	var revision_two_ack := revision_sim.submit(revision_two)
	var revision_two_accept := revision_engine.accept_authoritative_receipt(revision_two_ack)
	check("higher target revision replaces bounded simulation receipt", revision_two_accept.passed and revision_sim.receipts_by_target.size() == 1 and revision_sim.receipts_by_target["target-revision"].target_revision == 2)
	var stale_revision_result := revision_sim.submit(revision_one)
	check("stale lower revision with old key fails closed after newer receipt", not stale_revision_result.passed and stale_revision_result.errors.has("stale_authority_transaction") and revision_sim.debit_count == 2)

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
	check("view uses shape and color redundancy", view_contract.shape_and_color_redundancy and view_contract.world_response_shapes == ["perimeter_ring", "preview_volume", "status_label"])
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
	var beacon := view.get_node_or_null("T10WorldResponse/StatusLabel") as Label3D
	var initial_view := view.descriptor()
	check("world-response visuals build exactly once", initial_view.visual_build_count == 1 and initial_view.visual_node_count == 4 and visual_root != null and visual_root.get_child_count() == 3, initial_view)
	check("locked lifecycle hides response geometry", not ring.visible and not ghost.visible and not beacon.visible)
	for glyph in [0xe000, 0xe001, 0xe002, 0xe003]:
		check("resource symbol is available through actual Godot font fallback: %s" % glyph, TransformView.RESOURCE_SYMBOLS.has_char(glyph) and beacon.font.has_char(glyph))
	var flow_texture_id: int = view._ring_material.emission_texture.get_instance_id()
	var ring_material_id: int = view._ring_material.get_instance_id()
	check("locked presentation never implies resource application", not view._ring_material.emission_enabled)
	check("readability below minimum is rejected", not view.configure_readability(0.5) and is_equal_approx(float(view.descriptor().readability_scale), 1.0))
	check("readability above maximum is rejected", not view.configure_readability(2.0) and is_equal_approx(float(view.descriptor().readability_scale), 1.0))
	check("minimum readability scale applies without rebuild", view.configure_readability(0.85) and is_equal_approx(float(view.descriptor().readability_scale), 0.85) and view.descriptor().visual_build_count == 1)
	check("maximum readability scale applies without rebuild", view.configure_readability(1.35) and is_equal_approx(float(view.descriptor().readability_scale), 1.35) and view.descriptor().visual_build_count == 1)
	check("default readability scale restores without rebuild", view.configure_readability(1.0) and is_equal_approx(float(view.descriptor().readability_scale), 1.0) and view.descriptor().visual_build_count == 1)

	view.set_ready()
	check("ready lifecycle shows low source form and readable status", view.descriptor().lifecycle == "ready" and ring.visible and beacon.visible and ghost.visible and ghost.scale.y < 0.2)
	var blocked_preview := visual_engine.preview_transform("framework_anchor_seed_to_foundation", "visual-A", {"wood": 7, "stone": 3})
	check("blocked fixture preview is authoritative failure", not blocked_preview.passed and blocked_preview.errors.has("insufficient_resources") and blocked_preview.shortfalls == {"wood": 1, "stone": 1})
	check("blocked world response preserves exact reasons and shortfalls", view.show_blocked(blocked_preview) and view.descriptor().lifecycle == "blocked" and view.descriptor().block_reasons.has("insufficient_resources") and view.descriptor().blocked_shortfalls == {"wood": 1, "stone": 1})
	var changed_blocked := visual_engine.preview_transform("framework_anchor_seed_to_foundation", "visual-A", {"wood": 0, "stone": 0})
	view.show_blocked(changed_blocked)
	check("same blocked state refreshes exact shortfall label", beacon.text.contains("Deliver 8 wood + 4 stone"))
	view.show_blocked(blocked_preview)
	var applies_before_noop := view.visual_apply_count
	view.show_blocked(blocked_preview)
	check("identical blocked payload does not reapply visuals", view.visual_apply_count == applies_before_noop)
	check("blocked lifecycle renders exact costs and shortfalls", ring.visible and beacon.visible and ghost.visible and beacon.text.contains("8 wood + 4 stone") and beacon.text.contains("Deliver 1 wood + 1 stone"))
	check("blocked primary instruction leads and exact missing resource symbols render", beacon.text.begins_with("Deliver 1 wood + 1 stone\n") and beacon.text.contains("Missing:") and beacon.text.contains("\ue000") and beacon.text.contains("\ue001") and not view._ring_material.emission_enabled)
	var multi_block := blocked_preview.duplicate(true)
	multi_block.shortfalls = {"wood": 1, "stone": 2, "metal": 3, "fuel": 4}
	multi_block.errors = ["insufficient_resources", "missing_prerequisite:harvesting_online"]
	view.show_blocked(multi_block)
	check("all four resource shortfalls and additional prerequisite remain visible", beacon.text.begins_with("Deliver 1 wood + 2 stone + 3 metal + 4 fuel") and beacon.text.contains("harvesting online") and beacon.text.contains("\ue002") and beacon.text.contains("\ue003"))
	multi_block.shortfalls = {}
	multi_block.errors = ["missing_prerequisite:harvesting_online"]
	view.show_blocked(multi_block)
	check("prerequisite-only block does not invent missing resources", beacon.text.begins_with("Requires harvesting online") and not beacon.text.contains("Missing:") and not beacon.text.contains("Deliver"))
	view.set_ready()
	check("leaving blocked state clears failure payload", view.descriptor().block_reasons.is_empty() and view.descriptor().blocked_shortfalls.is_empty())

	var visual_inventory := {"wood": 20, "stone": 12, "metal": 2, "fuel": 1}
	var visual_preview := visual_engine.preview_transform("framework_anchor_seed_to_foundation", "visual-A", visual_inventory)
	check("preview world response shows ring plus translucent preview volume", view.show_preview(visual_preview) and ring.visible and ghost.visible and beacon.visible and beacon.text.contains("Delivered stock:") and ghost.material_override.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA)
	var visual_intent := visual_engine.commit_transform("visual-tx", "framework_anchor_seed_to_foundation", "visual-A", visual_inventory)
	check("committing world response shows all three shapes", view.show_commit(visual_intent) and ring.visible and ghost.visible and beacon.visible)
	check("pending resources have exact named source-to-target cues without premature payment", beacon.text.begins_with("Applying delivered resources") and beacon.text.contains("8 wood") and beacon.text.contains("4 stone") and beacon.text.contains("→ Foundation") and not beacon.text.contains("Paid:") and view._ring_material.emission_enabled)
	var ring_arrays: Array = ring.mesh.surface_get_arrays(0)
	var ring_vertices: PackedVector3Array = ring_arrays[Mesh.ARRAY_VERTEX]
	var ring_normals: PackedVector3Array = ring_arrays[Mesh.ARRAY_NORMAL]
	var ring_uvs: PackedVector2Array = ring_arrays[Mesh.ARRAY_TEX_UV]
	var cap_center_uv := Vector2(-1.0, -1.0)
	for vertex_index in ring_vertices.size():
		if ring_normals[vertex_index].y > 0.9 and absf(ring_vertices[vertex_index].x) < 0.001 and absf(ring_vertices[vertex_index].z) < 0.001:
			cap_center_uv = ring_uvs[vertex_index]
	check("actual cylinder cap atlas maps to one centered clamped flow", cap_center_uv.is_equal_approx(Vector2(0.25, 0.75)) and not view._ring_material.texture_repeat and (cap_center_uv * Vector2(view._ring_material.uv1_scale.x, view._ring_material.uv1_scale.y) + Vector2(view._ring_material.uv1_offset.x, view._ring_material.uv1_offset.y)).is_equal_approx(Vector2(0.5, 0.5)))
	var pending_text := beacon.text
	var pending_apply_count := view.visual_apply_count
	var forged_visual_ack := visual_intent.duplicate(true)
	forged_visual_ack.authority_source = "simulation"
	forged_visual_ack.authority_applied = true
	forged_visual_ack.accepted_by_world_transform = false
	check("unaccepted receipt cannot stop pending flow or claim paid", not view.mark_complete(forged_visual_ack) and view.lifecycle == "committing" and view._ring_material.emission_enabled and beacon.text == pending_text)
	var beacon_before_pulse := ghost.scale
	view._process(0.12)
	check("committing target pulse changes shape without rebuilding nodes", ghost.scale != beacon_before_pulse and view.descriptor().visual_build_count == 1 and view.descriptor().visual_node_count == 4)
	check("committing pulse stays anchored to support", is_equal_approx(ghost.position.y - 0.75 * ghost.scale.y, 0.08))
	for pending_frame in 90:
		view._process(1.0 / 60.0)
	check("pending flow reuses material texture and text without visual rebuild", view._ring_material.uv1_scale.x > 1.0 and view._ring_material.get_instance_id() == ring_material_id and view._ring_material.emission_texture.get_instance_id() == flow_texture_id and beacon.text == pending_text and view.visual_apply_count == pending_apply_count and view.descriptor().visual_node_count == 4)
	check("animated flow remains centered on actual top cap", (cap_center_uv * Vector2(view._ring_material.uv1_scale.x, view._ring_material.uv1_scale.y) + Vector2(view._ring_material.uv1_offset.x, view._ring_material.uv1_offset.y)).is_equal_approx(Vector2(0.5, 0.5)))
	var visual_ack := visual_intent.duplicate(true)
	visual_ack["authority_source"] = "simulation"
	visual_ack["authority_applied"] = true
	var visual_accepted := visual_engine.accept_authoritative_receipt(visual_ack)
	var next_blocked_offer := visual_engine.preview_transform("framework_anchor_foundation_to_reinforced", "visual-A", {"wood": 0, "stone": 0, "metal": 0})
	check("complete world response requires accepted authority receipt", view.mark_complete(visual_accepted, next_blocked_offer) and view.descriptor().lifecycle == "complete")
	check("completion preserves both next-stage shortfalls and prerequisite", beacon.text.contains("Next: Reinforced") and beacon.text.contains("Deliver 12 wood + 8 stone + 2 metal") and beacon.text.contains("harvesting online"))
	check("complete lifecycle solidifies accepted target form", ring.visible and ghost.visible and beacon.visible and ghost.scale == Vector3.ONE and ghost.material_override.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED and beacon.text.contains("Paid:") and beacon.text.contains("8 wood") and beacon.text.contains("4 stone") and view.displayed_costs == {"wood": 8, "stone": 4})
	check("accepted receipt stops flow and resets its bounded phase", not view._ring_material.emission_enabled and view._ring_material.uv1_scale == Vector3.ONE and view._ring_material.uv1_offset == Vector3.ZERO and not view.is_processing())
	var completion_text := beacon.text
	check("repeated completion does not replay debit feedback", not view.mark_complete(visual_accepted) and beacon.text == completion_text and not view._ring_material.emission_enabled)
	var accepted_form := ghost.scale
	view.set_ready()
	check("ready after completion preserves accepted world form", ghost.scale == accepted_form)
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
		"simulation_models_carried_vs_stored_delivery": true,
		"simulation_debits_stored_only": true,
		"simulation_bounded_receipt_history_by_target": true,
		"bounded_completed_history": true,
		"r11_world_response_tested": true,
		"visual_node_budget": view_contract.visual_node_budget,
		"visual_build_count": view.descriptor().visual_build_count,
		"visual_node_count": view.descriptor().visual_node_count,
		"real_t09_adapter_bound": true,
		"fixture_simulation_only": false,
		"integration_allowed": false,
		"task_approved": false,
	}))
	quit(0 if failures.is_empty() else 1)

func run_real_authority() -> void:
	var sim := Simulation.new()
	var model := configured_engine()
	model.register_target("real-delivery", "seed")
	for kind in ["wood", "stone"]:
		var quantity := 8 if kind == "wood" else 4
		for i in quantity:
			sim.action = {"kind": "gather", "id": kind + "0", "position": Vector2.ZERO}
			sim.perform_action(float(sim.tuning.gatherSecondsPerUnit[kind]))
	check("real harvesting commits to carried inventory", sim.inventory.wood == 8 and sim.inventory.stone == 4 and sim.stored.wood == 0)
	check("real carried harvest cannot pay T10", not model.preview_transform("framework_anchor_seed_to_foundation", "real-delivery", sim.stored.duplicate(true)).passed)
	for i in 12:
		sim.action = {"kind": "deposit", "id": "furnace", "position": Vector2.ZERO}
		sim.perform_action(float(sim.tuning.furnaceDepositSecondsPerUnit))
	check("real deposit conserves delivered resources", sim.carried() == 0 and sim.stored.wood == 8 and sim.stored.stone == 4)
	var intent := model.commit_transform("real-1", "framework_anchor_seed_to_foundation", "real-delivery", sim.stored.duplicate(true))
	var pending: Dictionary = JSON.parse_string(JSON.stringify(model.export_component_state()))
	var ack := sim.commit_world_transform_debit(intent)
	check("real simulation exact stored debit", ack.get("authority_applied", false) and sim.stored.wood == 0 and sim.stored.stone == 0 and sim.carried() == 0)
	var saved: Dictionary = JSON.parse_string(JSON.stringify(sim.snapshot()))
	var recovered := Simulation.new()
	check("real snapshot restores after debit before acceptance", recovered.restore(saved))
	var restored_model := configured_engine()
	check("real pending component restores", restored_model.import_component_state(pending))
	var replay := recovered.commit_world_transform_debit(intent)
	check("real crash retry does not debit again", replay.get("simulation_replayed", false) and recovered.stored == sim.stored)
	var accepted := restored_model.accept_authoritative_receipt(replay)
	check("real recovered receipt advances once", accepted.passed and accepted.applied)
	check("real duplicate acceptance is idempotent", restored_model.accept_authoritative_receipt(replay).get("replayed", false))
	var baseline := recovered.snapshot()
	for field in ["authority_transaction_key", "request_identity", "debits", "target_revision", "progression_tags"]:
		var forged := intent.duplicate(true)
		if field == "debits": forged[field] = {"wood": 1}
		elif field == "target_revision": forged[field] = 0
		elif field == "progression_tags": forged[field] = [42]
		else: forged[field] = "forged"
		check("real forged intent rejected: " + field, not recovered.commit_world_transform_debit(forged).get("authority_applied", false) and recovered.snapshot() == baseline)
	var malformed := saved.duplicate(true)
	malformed.world_transform_debit_receipts["real-delivery"].debits = {"wood": -1}
	check("real malformed receipt restore is atomic", not recovered.restore(malformed) and recovered.snapshot() == baseline)
	var legacy := saved.duplicate(true)
	legacy.erase("world_transform_debit_receipts")
	var legacy_sim := Simulation.new()
	check("legacy snapshot has empty component receipts", legacy_sim.restore(legacy) and legacy_sim.world_transform_debit_receipts.is_empty())
	var insufficient := Simulation.new()
	var before := insufficient.snapshot()
	check("real insufficient stock cannot partially charge", not insufficient.commit_world_transform_debit(intent).get("authority_applied", false) and insufficient.snapshot() == before)
	for field in ["transaction_id", "debits", "progression_tags", "presentation_key", "source_state", "target_revision"]:
		var fresh := Simulation.new()
		fresh.stored = {"wood": 100, "stone": 100, "metal": 100, "fuel": 100}
		var forged := intent.duplicate(true)
		if field == "debits": forged[field] = {"wood": 1}
		elif field == "progression_tags": forged[field] = ["forged"]
		elif field == "target_revision": forged[field] = 2
		else: forged[field] = "forged"
		var unchanged := fresh.snapshot()
		check("fresh authority rejects changed payload with original key: " + field, not fresh.commit_world_transform_debit(forged).authority_applied and fresh.snapshot() == unchanged)
	for revision in [3, 5]:
		var jump := intent.duplicate(true)
		jump.transaction_id = "jump-" + str(revision)
		jump.target_revision = revision
		jump.authority_transaction_key = Simulation.transform_key(jump)
		check("authority rejects revision jump " + str(revision), not recovered.commit_world_transform_debit(jump).authority_applied and recovered.snapshot() == baseline)
	var discontinuous := intent.duplicate(true)
	discontinuous.transaction_id = "wrong-source"
	discontinuous.target_revision = 2
	discontinuous.authority_transaction_key = Simulation.transform_key(discontinuous)
	check("authority rejects source discontinuity", not recovered.commit_world_transform_debit(discontinuous).authority_applied and recovered.snapshot() == baseline)
	for mutation in ["replayed", "unknown", "tags", "oversized"]:
		var invalid_save := saved.duplicate(true)
		var row: Dictionary = invalid_save.world_transform_debit_receipts["real-delivery"]
		if mutation == "replayed": row.simulation_replayed = true
		elif mutation == "unknown": row["unexpected"] = {"unbounded": "payload"}
		elif mutation == "tags": row.progression_tags = ["same", "same"]
		else: row.presentation_key = "x".repeat(193)
		check("restore rejects malformed bounded payload: " + mutation, not recovered.restore(invalid_save) and recovered.snapshot() == baseline)
	var canonical_snapshot := recovered.snapshot()
	check("restored receipt canonical debit is integer", canonical_snapshot.world_transform_debit_receipts["real-delivery"].debits.wood is int)
	check("real ledger retains one canonical receipt", recovered.world_transform_debit_receipts.size() == 1 and not recovered.world_transform_debit_receipts["real-delivery"].has("submit_debit_transaction"))
	recovered.stored = {"wood": 100, "stone": 100, "metal": 100, "fuel": 100}
	var next_intent := restored_model.commit_transform("real-2", "framework_anchor_foundation_to_reinforced", "real-delivery", recovered.stored, ["harvesting_online"])
	var next_receipt := recovered.commit_world_transform_debit(next_intent)
	check("real exact next revision succeeds", next_receipt.get("authority_applied", false) and restored_model.accept_authoritative_receipt(next_receipt).passed)
	var next_snapshot := recovered.snapshot()
	check("real older revision remains rejected", not recovered.commit_world_transform_debit(intent).authority_applied and recovered.snapshot() == next_snapshot)
	var bounded := Simulation.new()
	bounded.stored = {"wood": 100000, "stone": 100000, "metal": 0, "fuel": 0}
	var all_committed := true
	for i in Simulation.MAX_TRANSFORM_TARGETS:
		var bounded_intent := intent.duplicate(true)
		bounded_intent.transaction_id = "bounded-" + str(i)
		bounded_intent.target_id = "bounded-target-" + str(i)
		bounded_intent.request_identity = "%s|%s|%s|%s" % [bounded_intent.recipe_id, bounded_intent.target_id, bounded_intent.source_state, bounded_intent.target_state]
		bounded_intent.authority_transaction_key = Simulation.transform_key(bounded_intent)
		all_committed = bounded.commit_world_transform_debit(bounded_intent).authority_applied and all_committed
	check("real maximum target stress retains bounded receipts", all_committed and bounded.world_transform_debit_receipts.size() == Simulation.MAX_TRANSFORM_TARGETS)
	var bounded_before := bounded.snapshot()
	check("real target overflow rejects without mutation", not bounded.commit_world_transform_debit(intent).authority_applied and bounded.snapshot() == bounded_before)
	check("stress retained serialized payload has finite budget", JSON.stringify(bounded.world_transform_debit_receipts).length() < Simulation.MAX_TRANSFORM_TARGETS * 2048)
	var duplicate_save := bounded.snapshot()
	var duplicate_row: Dictionary = duplicate_save.world_transform_debit_receipts["bounded-target-1"]
	duplicate_row.transaction_id = "bounded-0"
	duplicate_row.authority_transaction_key = Simulation.transform_key(duplicate_row)
	check("duplicate retained transaction ids reject atomically", not bounded.restore(duplicate_save) and bounded.snapshot() == bounded_before)
