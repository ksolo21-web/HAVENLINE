extends SceneTree

const Simulation = preload("res://scripts/outpost_simulation.gd")
const Carry = preload("res://scripts/carry_stack.gd")
const Stockpile = preload("res://scripts/storage_stockpile.gd")
const Transfer = preload("res://scripts/transfer_feedback.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func commit_next_action(sim, position: Vector2, expected_kind: String, duration: float) -> Array:
	sim.position = position
	sim.velocity = Vector2.ZERO
	sim.context_director.reset()
	sim.step(0.06, Vector2.ZERO)
	sim.step(0.07, Vector2.ZERO)
	if String(sim.action.get("kind", "")) != expected_kind or not bool(sim.action.get("actionable", false)):
		return []
	var key := expected_kind + ":" + String(sim.action.get("id", ""))
	sim.action_clocks[key] = duration - 0.05
	sim.step(0.05, Vector2.ZERO)
	return sim.events.duplicate(true)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var sim := Simulation.new()
	var carry := Carry.new()
	var stockpile := Stockpile.new()
	var transfer := Transfer.new()
	root.add_child(carry)
	root.add_child(stockpile)
	root.add_child(transfer)
	sim.threats_enabled = false

	var resource: Dictionary = sim.resources[0]
	var before_units := int(resource.units)
	sim.facing = (Vector2(resource.position) - (Vector2(resource.position) + Vector2(0, 1.1))).normalized()
	var gather_events := commit_next_action(sim, resource.position + Vector2(0, 1.1), "gather", float(sim.tuning.gatherSecondsPerUnit[String(resource.kind)]))
	check("authoritative simulation commits one gather before presentation", sim.inventory[resource.kind] == 1 and resource.units == before_units - 1)
	gather_events = gather_events.filter(func(event): return event.type == "gather")
	check("committed gather event identifies resource and source", gather_events.size() == 1 and gather_events[0].resource == resource.kind)
	var inventory_before_view := sim.inventory.duplicate(true)
	check("player stack derives from committed logical inventory", carry.update_inventory(sim.inventory) and carry.descriptor().logical_total == 1)
	check("stack derivation does not mutate authoritative inventory", sim.inventory == inventory_before_view)
	var source := Vector3(resource.position.x, 0.75, resource.position.y)
	var actor := Vector3(sim.position.x, 1.0, sim.position.y)
	check("gather receipt routes source to selected actor", transfer.transfer(resource.kind, source, actor, "frame1:gather:0", "source_to_actor", sim.lead, "actor:%d" % sim.lead))
	check("visual gather receipt cannot duplicate logical value", sim.inventory == inventory_before_view)

	var storage := sim.point(sim.contract.world.storage)
	var carried_before := int(sim.inventory[resource.kind])
	var deposit_events := commit_next_action(sim, storage, "deposit", float(sim.tuning.furnaceDepositSecondsPerUnit))
	deposit_events = deposit_events.filter(func(event): return event.type == "deposit")
	check("automatic contextual deposit commits exactly one unit", carried_before == 1 and sim.inventory[resource.kind] == 0 and sim.stored[resource.kind] == 1 and deposit_events.size() == 1)
	var stored_before_view := sim.stored.duplicate(true)
	check("ground destination derives from authoritative stored counts", stockpile.configure("camp_storage", sim.stored) and stockpile.descriptor().logical_total == 1)
	check("destination derivation does not mutate stored counts", sim.stored == stored_before_view)
	check("deposit receipt routes actor to real destination", transfer.transfer(resource.kind, actor, Vector3(storage.x, 0.75, storage.y), "frame2:deposit:0", "actor_to_destination", sim.lead, "camp_storage"))
	check("visual deposit receipt cannot debit stored value", sim.stored == stored_before_view)

	var snapshot := sim.snapshot()
	var restored := Simulation.new()
	check("save restore retains exact authoritative inventory", restored.restore(snapshot) and restored.inventory == sim.inventory and restored.stored == sim.stored)
	var restored_carry := Carry.new()
	root.add_child(restored_carry)
	restored_carry.update_inventory(restored.inventory)
	var restored_stockpile := Stockpile.new()
	root.add_child(restored_stockpile)
	restored_stockpile.configure("camp_storage", restored.stored)
	check("restored physical views rebuild without saved presentation state", restored_carry.descriptor().logical_counts == Carry.normalized_counts(restored.inventory) and restored_stockpile.descriptor().logical_counts == Carry.normalized_counts(restored.stored))
	check("T08 adds no save field", not snapshot.has("carry_layout") and not snapshot.has("transfer_receipts") and not snapshot.has("stockpile_layout"))

	var huge := sim.snapshot()
	huge.inventory = {"wood": 900000000000, "stone": 800000000000, "metal": 700000000000, "fuel": 600000000000}
	huge.stored = {"wood": 500000000000, "stone": 400000000000, "metal": 300000000000, "fuel": 200000000000}
	var huge_sim := Simulation.new()
	check("maximum-scale valid save retains unlimited logical counts", huge_sim.restore(huge) and huge_sim.inventory.wood == 900000000000 and huge_sim.stored.fuel == 200000000000)
	var huge_view := Carry.new()
	root.add_child(huge_view)
	huge_view.update_inventory(huge_sim.inventory)
	check("huge restored load remains visually bounded but numerically exact", huge_view.descriptor().visible_instances == Carry.VISIBLE_BUDGET and huge_view.descriptor().logical_total == 3000000000000)

	var action_before := restored.choose_action()
	restored_carry.update_inventory(restored.inventory)
	var action_after := restored.choose_action()
	check("inventory presentation cannot alter T07 context selection", action_after == action_before)
	check("one-joystick action contract remains intact", restored.context_director.contract().permanent_action_buttons == 0)

	var route_transfer := Transfer.new()
	root.add_child(route_transfer)
	check("routes committed build from player to exact defense", route_transfer.transfer("wood", Vector3.ZERO, Vector3(3, 1, 2), "build:lead", "actor_to_destination", 1, "defense:north"))
	check("routes committed build from helper without identity loss", route_transfer.transfer("stone", Vector3.ONE, Vector3(-3, 1, 2), "build:helper", "actor_to_destination", 2, "defense:south"))
	check("routes committed repair from player and helper", route_transfer.transfer("wood", Vector3.ZERO, Vector3(0, 1, 0.2), "repair:lead", "actor_to_destination", 1, "repair:furnace") and route_transfer.transfer("wood", Vector3.ONE, Vector3(3, 1, 2), "repair:helper", "actor_to_destination", 2, "repair:north"))
	var route_rows: Array = route_transfer.descriptor().flights
	check("build repair routes retain actor and destination identities", route_rows.map(func(row): return row.destination_id) == ["defense:north","defense:south","repair:furnace","repair:north"] and route_rows.map(func(row): return row.actor_id) == [1,2,1,2])

	var switch_sim := Simulation.new()
	switch_sim.inventory = {"wood":2,"stone":1,"metal":0,"fuel":0}
	var incoming: Dictionary = switch_sim.companions[0]
	incoming.cargo_kind = "wood"; incoming.cargo = 3
	var authority_before_switch := int(switch_sim.inventory.wood) + int(switch_sim.inventory.stone) + int(incoming.cargo)
	check("lead switch cannot duplicate visible or logical cargo", switch_sim.select_lead(2) and switch_sim.lead == 2 and int(switch_sim.inventory.wood) + int(switch_sim.inventory.stone) == authority_before_switch and int(incoming.cargo) == 0)
	var hidden_stack := Carry.new()
	root.add_child(hidden_stack)
	hidden_stack.update_inventory({"wood":4,"stone":0,"metal":0,"fuel":0})
	hidden_stack.visible = false
	hidden_stack.update_inventory({"wood":0,"stone":0,"metal":0,"fuel":0})
	check("hidden actor stack fails closed without secret cargo", not hidden_stack.visible and hidden_stack.descriptor().logical_total == 0)

	print(JSON.stringify({
		"suite": "T08_visible_inventory_integration",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"save_schema": snapshot.schema,
		"visual_save_fields_added": 0,
		"independent_critic": false,
		"physical_4k60_verified": false,
	}))
	quit(0 if failures.is_empty() else 1)
