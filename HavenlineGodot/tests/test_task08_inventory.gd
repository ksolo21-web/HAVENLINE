extends SceneTree

const Carry = preload("res://scripts/carry_stack.gd")
const Stockpile = preload("res://scripts/storage_stockpile.gd")
const Transfer = preload("res://scripts/transfer_feedback.gd")
const StationKit = preload("res://scripts/station_kit.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func represented(layout: Array) -> int:
	var total := 0
	for row in layout:
		total += int(row.represented_count)
	return total

func percentile(values: Array[float], ratio: float) -> float:
	if values.is_empty(): return 0.0
	var ordered := values.duplicate()
	ordered.sort()
	return ordered[clampi(ceili(float(ordered.size()) * ratio) - 1, 0, ordered.size() - 1)]

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var contract := Carry.contract()
	check("T08 carry authority is exact", contract.authority_id == "T08-physical-inventory-v1")
	check("logical inventory is explicitly unlimited by presentation", contract.unlimited_logical_inventory and not contract.mutates_inventory)
	check("no inventory control or save field is introduced", contract.manual_inventory_controls == 0 and not contract.adds_save_fields)
	check("four current production kinds are exact", contract.kinds == ["wood", "stone", "metal", "fuel"])
	check("future resources fail visibly without generic fallback", contract.future_resource_fallback == "fail_visible_not_generic")

	var catalog := StationKit.read_catalog()
	var t08_assets := {}
	for row: Dictionary in catalog.entries:
		if row.get("later_task") == "T08":
			t08_assets[String(row.id)] = String(row.asset)
	check("wood uses approved T05 authored stack", contract.authored_assets.wood == t08_assets.wood_stack)
	check("stone uses approved T05 authored stack", contract.authored_assets.stone == t08_assets.stone_stack)
	check("metal uses approved T05 authored stack", contract.authored_assets.metal == t08_assets.metal_stack)
	check("fuel uses approved T05 authored canister", contract.authored_assets.fuel == t08_assets.fuel_canister)
	for kind in Carry.KINDS:
		check(kind + " authored asset resolves", ResourceLoader.exists(contract.authored_assets[kind]))

	check("negative inventory fails closed", not Carry.valid_inventory({"wood": -1}))
	check("fractional inventory fails closed", not Carry.valid_inventory({"wood": 1.5}))
	check("nonfinite inventory fails closed", not Carry.valid_inventory({"wood": INF}))
	check("non-numeric inventory fails closed", not Carry.valid_inventory({"wood": "7"}))
	check("missing kinds normalize to zero", Carry.normalized_counts({"wood": 2}) == {"wood": 2, "stone": 0, "metal": 0, "fuel": 0})

	var empty := Carry.layout_for({})
	check("zero inventory has no physical pieces", empty.is_empty())
	var exact := Carry.layout_for({"wood": 2, "stone": 1, "metal": 1, "fuel": 0})
	check("small load shows one authored piece per unit", exact.size() == 4 and represented(exact) == 4)
	check("small mixed load preserves deterministic kind order", exact.map(func(row): return row.kind) == ["wood", "wood", "stone", "metal"])
	check("actor load is raised into a readable attached rack", exact.all(func(row): return row.position.y >= Carry.CARRY_BASE_HEIGHT - 0.001 and absf(row.position.x) <= 0.8), exact)
	var huge_counts := {"wood": 1000000000000, "stone": 2000000000000, "metal": 3000000000000, "fuel": 4000000000000}
	var huge := Carry.layout_for(huge_counts)
	check("huge logical load stays inside physical instance budget", huge.size() == Carry.VISIBLE_BUDGET)
	check("compressed pieces conserve exact represented count", represented(huge) == 10000000000000)
	check("every nonzero kind remains visible after compression", Carry.KINDS.all(func(kind): return huge.any(func(row): return row.kind == kind)))
	check("compressed layout is deterministic", huge == Carry.layout_for(huge_counts))
	check("all layouts use finite positions and positive scale", huge.all(func(row): return row.position.is_finite() and row.scale > 0.0))
	var grounded := Carry.layout_for({"wood": 100, "stone": 80, "metal": 60, "fuel": 40}, true)
	check("ground stack is bounded and resource-complete", grounded.size() == Carry.VISIBLE_BUDGET and Carry.KINDS.all(func(kind): return grounded.any(func(row): return row.kind == kind)))
	check("ground layout differs from actor attachment", grounded[0].position != Carry.layout_for({"wood": 100, "stone": 80, "metal": 60, "fuel": 40})[0].position)

	var carry := Carry.new()
	root.add_child(carry)
	var live_counts := {"wood": 4, "stone": 2, "metal": 1, "fuel": 1}
	var before := live_counts.duplicate(true)
	check("authored carry update succeeds", carry.update_inventory(live_counts))
	var first_descriptor := carry.descriptor()
	check("carry update cannot mutate caller inventory", live_counts == before)
	check("carry descriptor conserves exact total", first_descriptor.logical_total == 8 and first_descriptor.represented_total == 8)
	check("every live piece is authored rather than primitive fallback", carry.slots.slice(0, first_descriptor.visible_instances).all(func(node): return String(node.get_meta("t08_authored_asset", "")).begins_with("res://assets/stations_v2/")))
	var rebuilds := carry.rebuild_count
	check("unchanged counts do not rebuild presentation", carry.update_inventory(live_counts) and carry.rebuild_count == rebuilds)
	check("invalid update is transactional", not carry.update_inventory({"wood": -1}) and carry.descriptor() == first_descriptor)
	carry.update_inventory(huge_counts)
	check("runtime huge count remains exact while instances stay bounded", carry.descriptor().logical_total == 10000000000000 and carry.descriptor().visible_instances == Carry.VISIBLE_BUDGET)

	var stockpile := Stockpile.new()
	root.add_child(stockpile)
	check("destination stockpile configures from authoritative stored counts", stockpile.configure("furnace_storage", {"wood": 18, "stone": 6, "metal": 0, "fuel": 0}))
	var storage_descriptor := stockpile.descriptor()
	check("stockpile is grounded and simulation-authoritative", storage_descriptor.grounded and storage_descriptor.simulation_authoritative)
	check("stockpile preserves destination identity and exact total", storage_descriptor.destination_id == "furnace_storage" and storage_descriptor.logical_total == 24)

	var transfer := Transfer.new()
	root.add_child(transfer)
	var transfer_contract := Transfer.contract()
	check("transfer authority and two directions are exact", transfer_contract.authority_id == "T08-transfer-feedback-v1" and transfer_contract.directions == ["source_to_actor", "actor_to_destination"])
	check("transfer presentation exposes readable duration scale and arc", transfer_contract.duration_seconds >= 0.7 and transfer_contract.flight_scale_multiplier >= 1.7 and transfer_contract.arc_height >= 1.0)
	check("transfer presentation cannot mutate inventory", transfer_contract.simulation_authoritative and not transfer_contract.mutates_inventory)
	check("unknown resource transfer fails closed", not transfer.transfer("fish", Vector3.ZERO, Vector3.ONE, "bad-kind"))
	check("zero-length transfer fails closed", not transfer.transfer("wood", Vector3.ZERO, Vector3.ZERO, "bad-route"))
	check("invalid direction fails closed", not transfer.transfer("wood", Vector3.ZERO, Vector3.ONE, "bad-direction", "sideways"))
	check("committed source-to-actor receipt starts", transfer.transfer("wood", Vector3.ZERO, Vector3(1, 1, 1), "gather:1", "source_to_actor", 1, "actor:1"))
	check("same receipt cannot replay", not transfer.transfer("wood", Vector3.ZERO, Vector3(1, 1, 1), "gather:1", "source_to_actor", 1, "actor:1"))
	check("committed actor-to-destination receipt starts", transfer.transfer("stone", Vector3(1, 1, 1), Vector3(2, 0, 2), "deposit:2", "actor_to_destination", 1, "furnace"))
	var active := transfer.descriptor()
	check("active flights retain direction actor and destination", active.active_flights == 2 and active.flights[0].direction == "source_to_actor" and active.flights[1].destination_id == "furnace")
	transfer._process(Transfer.DURATION_SECONDS)
	var completed := transfer.descriptor()
	check("completed transfers return to pools", completed.active_flights == 0 and completed.completed_receipts == 2 and transfer.pools.wood.size() == 1 and transfer.pools.stone.size() == 1)
	check("receipt history survives visual completion", not transfer.transfer("stone", Vector3.ZERO, Vector3.ONE, "deposit:2", "source_to_actor"))

	var bounded := Transfer.new()
	root.add_child(bounded)
	var accepted := true
	for index in Transfer.MAX_FLIGHTS:
		accepted = accepted and bounded.transfer("fuel", Vector3(index, 0, 0), Vector3(index, 1, 1), "load:%d" % index)
	check("maximum simultaneous transfer budget is accepted exactly", accepted and bounded.flights.size() == Transfer.MAX_FLIGHTS)
	check("flight above budget fails closed", not bounded.transfer("fuel", Vector3.ZERO, Vector3.ONE, "overflow"))

	var memory_before := OS.get_static_memory_usage()
	var layout_samples: Array[float] = []
	for iteration in 2000:
		var started := Time.get_ticks_usec()
		Carry.layout_for(huge_counts)
		layout_samples.append(float(Time.get_ticks_usec() - started))
	var update_samples: Array[float] = []
	for iteration in 400:
		var counts: Dictionary = huge_counts if iteration % 2 == 0 else live_counts
		var started := Time.get_ticks_usec()
		carry.update_inventory(counts)
		update_samples.append(float(Time.get_ticks_usec() - started))
	var memory_delta := maxi(0, OS.get_static_memory_usage() - memory_before)
	var retained_nodes := carry.get_child_count()
	var performance := {
		"layout_iterations":2000, "update_iterations":400,
		"layout_average_usec":layout_samples.reduce(func(total, value): return total + value, 0.0) / layout_samples.size(),
		"layout_p95_usec":percentile(layout_samples, 0.95), "layout_maximum_usec":percentile(layout_samples, 1.0),
		"update_average_usec":update_samples.reduce(func(total, value): return total + value, 0.0) / update_samples.size(),
		"update_p95_usec":percentile(update_samples, 0.95), "update_maximum_usec":percentile(update_samples, 1.0),
		"retained_nodes":retained_nodes, "retained_node_budget":Carry.VISIBLE_BUDGET * Carry.KINDS.size(),
		"static_memory_delta_bytes":memory_delta, "static_memory_delta_budget_bytes":16 * 1024 * 1024,
		"layout_p95_budget_usec":2500.0, "update_p95_budget_usec":5000.0,
	}
	check("huge layout p95 remains bounded", performance.layout_p95_usec <= performance.layout_p95_budget_usec, performance)
	check("alternating authored updates remain bounded", performance.update_p95_usec <= performance.update_p95_budget_usec, performance)
	check("retained authored nodes remain bounded", retained_nodes <= performance.retained_node_budget, performance)
	check("component memory growth remains bounded", memory_delta <= performance.static_memory_delta_budget_bytes, performance)

	print(JSON.stringify({
		"suite": "T08_visible_inventory_component",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"huge_logical_total": represented(huge),
		"visible_budget": Carry.VISIBLE_BUDGET,
		"flight_budget": Transfer.MAX_FLIGHTS,
		"performance": performance,
		"independent_critic": false,
		"physical_4k60_verified": false,
	}))
	quit(0 if failures.is_empty() else 1)
