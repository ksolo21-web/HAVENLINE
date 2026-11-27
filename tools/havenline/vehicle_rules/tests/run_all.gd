extends SceneTree
const Rules = preload("res://vehicle_rules.gd")
const World = preload("res://tests/world_fixture.gd")
const Count = preload("res://exact_count.gd")
var passed := 0
var failed := 0
var checks: Array = []

func _initialize() -> void:
	counts()
	purchase_rules()
	cargo_and_docking()
	destruction_and_races()
	lifecycle_recovery()
	funding_owner_recovery()
	restore_rules()
	adapter_guards()
	if passed + failed != 107: check(false,"all107 expected legacy checks executed")
	var result := {"scope": "STANDALONE_NATIVE_VEHICLE_RULES_ONLY", "passed": passed, "failed": failed, "checks": checks, "game_integration": false, "physics_motion_audio_device_approved": false}
	var report := FileAccess.open("res://evidence/fuel-v2/legacy-regression.json", FileAccess.WRITE)
	report.store_string(JSON.stringify(result, "\t") + "\n")
	print(JSON.stringify(result))
	quit(0 if failed == 0 else 1)

func check(condition: bool, name: String) -> void:
	checks.append({"name": name, "passed": condition})
	if condition: passed += 1
	else:
		failed += 1
		push_error(name)

func setup() -> Dictionary:
	var w := World.new()
	var r := Rules.new()
	assert(r.initialize(w).ok)
	w.quote()
	assert(r.admit_quote("q1", "quote1").ok)
	w.buy()
	assert(r.purchase("q1", "buy1").ok)
	return {"w": w, "r": r}

func load_all(pair: Dictionary) -> Dictionary:
	var all: Dictionary = pair.r.state().accounts.player.items
	pair.w.load()
	assert(pair.r.load_cargo("truck",1,"player",1,all,"load1").ok)
	return all

func counts() -> void:
	for malformed in ["", "01", "-1", "+1", "1.0", "1e4", " 1", "１", 1, 1.0, true]:
		check(not Count.valid(malformed), "reject noncanonical decimal: " + str(malformed))
	check(Count.valid("0"), "canonical zero")
	check(Count.add("9007199254740993", "7") == "9007199254741000", "exact add beyond 2^53")
	check(Count.add("18446744073709551617", "4") == "18446744073709551621", "exact add beyond 2^64")
	var giant := "9".repeat(512)
	check(Count.add(giant,"1") == "1" + "0".repeat(512), "513 digit carry no numeric quantity cap")
	check(Count.subtract("1"+"0".repeat(512),"1") == giant, "513 digit borrow exact")
	check(Count.compare("99","100") < 0 and Count.compare("101","100") > 0, "decimal order by magnitude")

func purchase_rules() -> void:
	var w := World.new()
	var r := Rules.new()
	check(r.initialize(w).ok, "trusted initialize")
	w.quote()
	w.facts.garage.ready = false
	check(not r.admit_quote("q1","q-not-ready").ok, "garage prerequisite")
	w.quote()
	w.facts.garage.plot_inside_camp = false
	check(not r.admit_quote("q1","q-outside").ok, "purchase plot inside camp")
	w.quote()
	w.facts.acquisition_proof_id = ""
	check(not r.admit_quote("q1","q-no-proof").ok, "reachable acquisition proof required from adapter")
	w.quote()
	check(r.admit_quote("q1","q").ok, "valid freeze")
	w.quote("q2")
	check(not r.admit_quote("q2","reroll").ok, "second frozen quote cannot reroll same vehicle generation")
	w.buy()
	w.facts.garage.generation = 2
	check(not r.purchase("q1","stale-garage").ok, "stale purchased garage generation")
	w.buy()
	var buy: Dictionary = r.purchase("q1","buy")
	check(buy.ok and buy.tier == 1, "paid level1 vehicle")
	check(r.state().accounts.player.items.wood == "900" and r.state().spent.steel == "200", "single actual bill debit")
	check(r.purchase("q1","buy") == buy, "same request receipt replay")
	check(not r.purchase("q1","different-buy").ok, "spent quote cannot buy again with new request")
	check(not r.purchase("q2","buy").ok, "same request changed payload rejected")
	check(r.audit().ok, "purchase conservation")
	var poor := World.new()
	poor.initial.accounts.player.items.steel = "1"
	var poor_rules := Rules.new()
	assert(poor_rules.initialize(poor).ok)
	poor.quote()
	assert(poor_rules.admit_quote("q1","q").ok)
	poor.buy()
	check(not poor_rules.purchase("q1","buy").ok and poor_rules.state().spent.is_empty(), "insufficient funds no partial debit")

func cargo_and_docking() -> void:
	var p := setup()
	var all := load_all(p)
	check(p.r.state().vehicles.truck.cargo == all, "mixed raw processed cash and new mineral cargo")
	check(p.r.state().accounts.player.items.is_empty(), "load transfers unique ownership")
	p.w.load()
	check(not p.r.load_cargo("truck",1,"player",1,{"premium_gems":"1"},"premium").ok, "nonphysical entitlement not cargo")
	check(not p.r.load_cargo("truck",1,"warehouse",1,{"wood":1},"numeric").ok, "numeric resource quantity rejected")
	check(not p.r.load_cargo("truck",2,"warehouse",1,{"wood":"1"},"generation").ok, "stale truck generation rejected")
	p.w.dock()
	p.w.facts.hull_points[0][0] = -4
	check(not p.r.park_and_unload("truck",1,"hull-outside").ok, "whole hull inside garage")
	p.w.dock()
	p.w.facts.blade_points[7][0] = 4
	check(not p.r.park_and_unload("truck",1,"blade-outside").ok, "whole blade envelope inside garage")
	for field in ["speed","blade_speed"]:
		p.w.dock()
		p.w.facts[field] = 0.1
		check(not p.r.park_and_unload("truck",1,"moving-"+field).ok, "stopped requirement: " + field)
	for field in ["working","route_connected","accepts_all_resources","unbounded_logical_stock"]:
		p.w.dock()
		p.w.facts.receiver[field] = false
		check(not p.r.park_and_unload("truck",1,"blocked-"+field).ok and p.r.state().vehicles.truck.cargo == all, "all cargo HOLD on receiver " + field)
	p.w.dock()
	p.w.facts.receiver.id = "other-store"
	check(not p.r.park_and_unload("truck",1,"wrong-store").ok, "receiver must be linked warehouse")
	p.w.dock()
	p.w.facts.receiver.generation = 2
	check(not p.r.park_and_unload("truck",1,"stale-store").ok, "receiver generation validated")
	p.w.dock()
	var docked: Dictionary = p.r.park_and_unload("truck",1,"dock")
	check(docked.ok and docked.moved == all and p.r.state().vehicles.truck.cargo.is_empty(), "complete atomic garage unload")
	check(p.r.state().accounts.warehouse.items.money == "18446744073709551621", "warehouse aggregation exact above 2^64")
	check(p.r.park_and_unload("truck",1,"dock") == docked, "unload replay immutable receipt")
	check(p.r.park_and_unload("truck",1,"empty-dock").moved.is_empty(), "second docking cannot duplicate contents")
	check(p.r.audit().ok, "unload conservation")

func destruction_and_races() -> void:
	var outside := setup()
	var cargo := load_all(outside)
	outside.w.hit()
	var death: Dictionary = outside.r.apply_contact_damage("truck",1,"hit1","dead")
	check(death.ok and death.outside_camp and outside.r.state().lost == cargo, "boundary-straddling destruction loses ALL truck cargo")
	check(outside.r.state().salvage.is_empty() and outside.r.state().vehicles.truck.cargo.is_empty(), "outside loss has no salvage clone")
	check(outside.r.apply_contact_damage("truck",1,"hit1","dead") == death, "death replay immutable receipt")
	outside.w.dock()
	check(not outside.r.park_and_unload("truck",1,"too-late").ok, "death before docking cannot bank lost cargo")
	check(outside.r.audit().ok, "loss conservation includes destruction outflow")
	var inside := setup()
	inside.w.load()
	assert(inside.r.load_cargo("truck",1,"player",1,{"wood":"10"},"load").ok)
	inside.w.hit("hit-in",false)
	var interior: Dictionary = inside.r.apply_contact_damage("truck",1,"hit-in","inside-death")
	check(interior.ok and not interior.outside_camp and inside.r.state().lost.is_empty(), "inside camp retains selected salvage policy")
	check(inside.r.state().accounts.player.items.wood == "890", "driver inventory remains separate")
	inside.w.claim()
	check(inside.r.claim_inside_salvage(interior.disposition,"player",1,"claim").moved == {"wood":"10"}, "inside salvage actual single-owner claim")
	check(inside.r.claim_inside_salvage(interior.disposition,"player",1,"claim-again").moved.is_empty(), "new request cannot duplicate claimed salvage")
	inside.w.quote("replacement",2)
	check(inside.r.admit_quote("replacement","q2").ok, "replacement new generation quote")
	inside.w.buy()
	check(inside.r.purchase("replacement","buy2").generation == 2 and inside.r.state().vehicles.truck.tier == 1, "paid replacement new level1 generation")
	check(inside.r.state().vehicles.truck.cargo.is_empty() and inside.r.state().tombstones.has("truck:1"), "replacement keeps death tombstone and no cargo clone")
	inside.w.load()
	check(not inside.r.load_cargo("truck",1,"player",1,{"wood":"1"},"old-instance").ok, "dead generation cannot resume")
	var dockfirst := setup()
	load_all(dockfirst)
	dockfirst.w.dock()
	assert(dockfirst.r.park_and_unload("truck",1,"dock").ok)
	var before: Dictionary = dockfirst.r.state().accounts.warehouse.items
	dockfirst.w.hit()
	assert(dockfirst.r.apply_contact_damage("truck",1,"hit1","dead").ok)
	check(dockfirst.r.state().accounts.warehouse.items == before and dockfirst.r.state().lost.is_empty(), "dock before later exterior death preserves banked stock")
	var hits := setup()
	hits.w.hit("small-hit",true,20)
	check(hits.r.apply_contact_damage("truck",1,"small-hit","damage").hp == 80, "nonlethal HP")
	check(not hits.r.apply_contact_damage("truck",1,"small-hit","duplicate-contact").ok and hits.r.state().vehicles.truck.hp == 80, "same contact cannot redamage under different request")
	var concave := setup()
	load_all(concave)
	concave.w.hit()
	# Every corner is inside the two arms, but a connecting edge crosses the notch.
	concave.w.facts.camp_polygon = [[-5,-5],[5,-5],[5,5],[2,5],[2,0],[-2,0],[-2,5],[-5,5]]
	concave.w.facts.truck_footprint = [[-3,-1],[3,-1],[3,2],[-3,2]]
	check(concave.r.apply_contact_damage("truck",1,"hit1","concave").outside_camp, "full polygon containment catches concave boundary crossing")

func restore_rules() -> void:
	var p := setup()
	load_all(p)
	p.w.dock()
	assert(p.r.park_and_unload("truck",1,"dock").ok)
	var saved: Dictionary = p.r.snapshot()
	var parsed: Dictionary = JSON.parse_string(JSON.stringify(saved))
	p.w.permit_restore(parsed)
	var restored := Rules.new()
	var restore_result: Dictionary = restored.restore(parsed,p.w)
	check(restore_result.ok and restored.state() == p.r.state(), "JSON roundtrip exact replay including large cargo")
	check(restored.park_and_unload("truck",1,"dock") == p.r.park_and_unload("truck",1,"dock"), "restored request cannot duplicate unload")
	var unapproved := Rules.new()
	var stranger := World.new()
	check(not unapproved.restore(parsed,stranger).ok, "world must authorize exact restore epoch")
	var bad := saved.duplicate(true)
	bad.events[3].receipt.moved.money = "1"
	p.w.permit_restore(bad)
	var before: Dictionary = restored.snapshot()
	check(not restored.restore(bad,p.w).ok and restored.snapshot() == before, "forged receipt rejected without partial restore")
	bad = saved.duplicate(true)
	bad.events.append(bad.events[3].duplicate(true))
	p.w.permit_restore(bad)
	check(not restored.restore(bad,p.w).ok, "duplicate saved request rejected")
	bad = saved.duplicate(true)
	bad.events[2].parameters.items.money = "01"
	p.w.permit_restore(bad)
	check(not restored.restore(bad,p.w).ok, "invalid saved decimal rejected before arithmetic")
	bad = saved.duplicate(true)
	bad.state_digest = "bad"
	p.w.permit_restore(bad)
	check(not restored.restore(bad,p.w).ok, "state digest mismatch rejected")
	bad = saved.duplicate(true)
	bad.events[3].facts.receiver.working = false
	p.w.permit_restore(bad)
	check(not restored.restore(bad,p.w).ok, "impossible saved transition rejected")
	var dead := setup()
	load_all(dead)
	dead.w.hit()
	assert(dead.r.apply_contact_damage("truck",1,"hit1","death").ok)
	var dead_save: Dictionary = JSON.parse_string(JSON.stringify(dead.r.snapshot()))
	dead.w.permit_restore(dead_save)
	var dead_restored := Rules.new()
	check(dead_restored.restore(dead_save,dead.w).ok and dead_restored.state().lost == dead.r.state().lost, "outside-loss tombstone persists through JSON reload")
	dead.w.dock()
	check(not dead_restored.park_and_unload("truck",1,"resurrect").ok, "reload cannot resurrect destroyed truck")

func adapter_guards() -> void:
	var p := setup()
	p.w.load()
	p.w.invalidate_after_first_check = true
	var before: Dictionary = p.r.state()
	check(not p.r.load_cargo("truck",1,"player",1,{"wood":"1"},"race").ok and p.r.state() == before, "revision recheck prevents commit after world change")
	p.w.invalidate_after_first_check = false
	p.w.forge_authority = true
	check(not p.r.load_cargo("truck",1,"player",1,{"wood":"1"},"forged-authority").ok, "foreign authority observation rejected")
	p.w.forge_authority = false
	p.w.reentrant_target = p.r
	check(p.r.load_cargo("truck",1,"player",1,{"wood":"1"},"outer").ok and not p.w.reentrant_result.ok, "reentrant command rejected")
	p.w.reentrant_target = null
	var save: Dictionary = p.r.snapshot()
	var same_name := World.new()
	same_name.permit_restore(save)
	check(not p.r.restore(save,same_name).ok, "same-named adapter object cannot replace bound authority")
	var invalid := World.new()
	invalid.initial.accounts.player.items.money = 9007199254740992.0
	check(not Rules.new().initialize(invalid).ok, "unsafe numeric bootstrap quantities rejected")

func lifecycle_recovery() -> void:
	var w := World.new()
	var r := Rules.new()
	assert(r.initialize(w).ok)
	w.quote()
	assert(r.admit_quote("q1","quote").ok)
	w.quote("second")
	w.facts.quote.vehicle_id = "other-truck"
	check(not r.admit_quote("second","second-bay").ok, "pending quote reserves single garage bay across vehicle IDs")
	w.garage.generation = 2
	w.facts = {"garage": w.garage.duplicate(true), "replacement_receipt_id": "paid-garage-rebuild-2", "acquisition_proof_id": "current-recovery-path"}
	check(r.rebind_quote_garage("q1","rebind").unchanged_bill == {"wood":"100","steel":"200"}, "rebuilt garage rebind preserves frozen price")
	check(not r.rebind_quote_garage("q1","repeat-rebind").ok, "rebind requires newer garage generation")
	w.buy()
	check(r.purchase("q1","buy").ok, "garage recovery cannot strand frozen truck quote")
	w.quote("third")
	w.facts.quote.vehicle_id = "other-truck"
	check(not r.admit_quote("third","occupied-bay").ok, "one live vehicle per garage bay")
	w.load()
	assert(r.load_cargo("truck",1,"player",1,{"wood":"1","money":"100"},"load").ok)
	w.facts = {"destruction_receipt_id": "storage-hit-1", "destroyed": true}
	check(r.storage_destroyed("warehouse",1,"warehouse-destroyed").ok, "destroyed warehouse moves original stock once")
	check(r.state().salvage["storage-estate:warehouse:1"] == {"wood":"5","money":"4"} and r.state().accounts.warehouse.items.is_empty(), "warehouse ruin contents single-owner salvage")
	w.dock()
	check(not r.park_and_unload("truck",1,"ruin-dock").ok and r.state().vehicles.truck.cargo == {"wood":"1","money":"100"}, "ruined warehouse holds entire truck load")
	w.facts = {"replacement_receipt_id": "paid-storage-rebuild-2", "new_generation": 2, "working": true}
	check(r.reopen_storage("warehouse",1,"warehouse-rebuilt").ok and r.state().accounts.warehouse.items.is_empty(), "paid rebuild callback opens empty new storage generation")
	check(not r.reopen_storage("warehouse",1,"rebuild-again").ok, "storage rebuild cannot repeat under new request")
	w.dock()
	check(not r.park_and_unload("truck",1,"old-store-dock").ok, "rebuilt storage rejects stale physical generation")
	w.facts.receiver.generation = 2
	check(r.park_and_unload("truck",1,"recovered-dock").ok and r.state().vehicles.truck.cargo.is_empty(), "rebuilt storage accepts real current full unload")
	w.claim()
	check(not r.claim_inside_salvage("storage-estate:warehouse:1","warehouse",2,"claim-direct-to-store").ok, "salvage claim cannot bypass destination validation through storage")
	check(r.claim_inside_salvage("storage-estate:warehouse:1","player",1,"recover-storage-stock").ok, "actor can recover ruined warehouse stock separately")
	var save: Dictionary = JSON.parse_string(JSON.stringify(r.snapshot()))
	w.permit_restore(save)
	var restored := Rules.new()
	check(restored.restore(save,w).ok and restored.state() == r.state(), "garage rebind and storage lifecycle survive JSON replay")
	check(r.audit().ok, "recovery conservation")

func funding_owner_recovery() -> void:
	var w := World.new()
	w.initial.accounts.warehouse.items = {"wood":"200", "steel":"400"}
	var r := Rules.new()
	assert(r.initialize(w).ok)
	w.quote()
	w.facts.quote.payer_id = "warehouse"
	assert(r.admit_quote("q1","quote").ok)
	w.facts = {"destruction_receipt_id":"warehouse-destroyed", "destroyed":true}
	assert(r.storage_destroyed("warehouse",1,"destroyed").ok)
	w.facts = {"replacement_receipt_id":"warehouse-rebuilt", "new_generation":2, "working":true}
	assert(r.reopen_storage("warehouse",1,"reopened").ok)
	w.claim()
	assert(r.claim_inside_salvage("storage-estate:warehouse:1","player",1,"claim").ok)
	w.buy()
	check(not r.purchase("q1","old-payer").ok, "stale payment owner cannot debit replacement generation")
	w.facts = {"payment_authorization_id":"authorize-player-purchase", "payer_available":true}
	check(not r.rebind_quote_payer("q1","warehouse",1,"stale-rebind").ok, "payer rebind rejects stale destination generation")
	w.facts.payer_available = false
	check(not r.rebind_quote_payer("q1","player",1,"unavailable-rebind").ok, "payer rebind rejects unavailable source")
	w.facts.payer_available = true
	var rebind: Dictionary = r.rebind_quote_payer("q1","player",1,"rebind")
	check(rebind.ok and rebind.unchanged_bill == {"wood":"100","steel":"200"}, "funding owner changes without quote reroll or repricing")
	check(r.rebind_quote_payer("q1","player",1,"rebind") == rebind, "funding rebind request replay immutable")
	w.buy()
	check(r.purchase("q1","recovered-purchase").ok, "recovered resources fund original quote from authorized actor")
	var save: Dictionary = JSON.parse_string(JSON.stringify(r.snapshot()))
	w.permit_restore(save)
	var restored := Rules.new()
	check(restored.restore(save,w).ok and restored.state() == r.state(), "payer rebind and recovered purchase survive JSON replay")
	check(r.audit().ok, "funding recovery conserves original stock and spending")
