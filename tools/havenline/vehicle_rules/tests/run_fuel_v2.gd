extends SceneTree
const Rules = preload("res://vehicle_rules.gd")
const World = preload("res://tests/world_fixture.gd")
const Fuel = preload("res://fuel_rules.gd")
const Count = preload("res://exact_count.gd")
var passed := 0
var failed := 0
var checks: Array = []

func _initialize() -> void:
	allocation()
	rates_and_exhaustion()
	usage_identity_and_save()
	refueling_and_garage()
	destruction_recovery()
	migration_and_save()
	var result := {"scope":"NATIVE_FUEL_V2_ONLY","passed":passed,"failed":failed,"checks":checks,"game_integration":false,"balance_measured":false}
	var output := FileAccess.open("res://evidence/fuel-v2/native-results.json",FileAccess.WRITE)
	output.store_string(JSON.stringify(result,"\t")+"\n")
	print(JSON.stringify(result))
	quit(0 if failed == 0 and passed == 80 else 1)

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})
	if value: passed += 1
	else:
		failed += 1
		push_error(name)

func fixture() -> Dictionary:
	var w := World.new()
	for id in ["fuel","sheet_metal","iron_bars"]: w.initial.resources.append(id)
	w.initial.accounts.player.items["fuel"] = "200"
	w.initial.accounts.player.items["sheet_metal"] = "1000"
	w.initial.accounts.player.items["iron_bars"] = "2000"
	var r := Rules.new()
	var initialized: Dictionary = r.initialize(w)
	assert(initialized.ok)
	return {"w":w,"r":r,"n":0}

func activate(p: Dictionary, tick := "0") -> Dictionary:
	p.w.facts = {"policy_id":Fuel.POLICY,"timeline_id":"active-play","active_tick":tick,"migration_receipt_id":"world-migration-receipt"}
	return p.r.activate_fuel_policy("activate-fuel")

func quote(p: Dictionary, id := "q1", generation := 1, funded := true) -> void:
	p.w.quote(id,generation)
	if funded:
		p.w.facts.quote["initial_tank_fuel_units"] = "60"
		p.w.facts.quote.bill["fuel"] = "60"
		p.w.facts.quote.bill["sheet_metal"] = "400"
		p.w.facts.quote.bill["iron_bars"] = "600"

func buy(p: Dictionary, id := "q1", tick := "0") -> Dictionary:
	p.w.buy()
	p.w.facts["fuel_clock"] = {"timeline_id":"active-play","active_tick":tick}
	return p.r.purchase(id,"buy-"+id)

func setup(funded := true) -> Dictionary:
	var p := fixture()
	assert(activate(p).ok)
	quote(p,"q1",1,funded)
	assert(p.r.admit_quote("q1","quote-q1").ok)
	assert(buy(p).ok)
	return p

func service(p: Dictionary) -> void:
	p.w.facts = {"contact_id":"actual-service-contact","source_available":true,"speed":0,"blade_speed":0,"engine_running":false}

func use(p: Dictionary, driving: bool, blades: bool, ms := 1000, generation := 1) -> Dictionary:
	p.n += 1
	var tank: Dictionary = p.r.state().fuel.tanks["truck:"+str(generation)]
	p.w.facts = {"timeline_id":"active-play","from_tick":tank.cursor,"elapsed_ms":ms,"active_play":true,"driving":driving,"blades":blades}
	return p.r.grant_powered_use("truck",generation,"use-"+str(p.n),"grant-"+str(p.n))

func amount(p: Dictionary, generation := 1) -> String:
	return p.r.state().fuel.tanks["truck:"+str(generation)].amount

func allocation() -> void:
	var p := fixture()
	quote(p)
	check(not p.r.admit_quote("q1","without-policy").ok,"funded tank requires explicit fuel policy")
	check(activate(p).ok,"fuel activation authorized with zero free value")
	check(not p.r.activate_fuel_policy("activate-again").ok,"policy cannot activate twice")
	quote(p)
	p.w.facts.quote.bill["fuel"] = "59"
	check(not p.r.admit_quote("q1","short-fuel-bill").ok,"60-unit tank cannot be funded by59-unit bill")
	quote(p)
	p.w.facts.quote["initial_tank_fuel_units"] = "61"
	check(not p.r.admit_quote("q1","oversized-initial").ok,"initial tank allocation must match60-unit fixture")
	quote(p)
	assert(p.r.admit_quote("q1","quote").ok)
	var receipt := buy(p)
	check(receipt.ok and receipt.initial_tank_fuel_units == "60" and receipt.tank_subunits == "7200000","paid new purchase fills60-unit tank")
	check(p.r.state().accounts.player.items.fuel == "140" and not p.r.state().spent.has("fuel"),"initial fuel moves to tank not duplicate construction spending")
	check(receipt.debited_bill.fuel == "60" and not receipt.consumed.has("fuel"),"purchase distinguishes debit from actual material consumption")
	check(p.r.state().spent.sheet_metal == "400" and p.r.state().spent.iron_bars == "600","varied processed test bill actually paid")
	check(p.r.purchase("q1","buy-q1") == receipt and amount(p) == "7200000","initial tank cannot refill through receipt replay")
	check(p.r.audit().ok,"funded tank exact conservation")
	var legacy := fixture()
	quote(legacy,"old-quote",1,false)
	assert(legacy.r.admit_quote("old-quote","oldquote").ok)
	assert(activate(legacy).ok)
	var old_receipt := buy(legacy,"old-quote")
	check(old_receipt.ok and old_receipt.initial_tank_fuel_units == "0" and legacy.r.state().accounts.player.items.fuel == "200","accepted old quote is not retrocharged fuel")
	check(amount(legacy) == "0","legacy accepted quote starts empty tank without free spawn fuel")
	var missing := World.new()
	var no_catalog := Rules.new()
	assert(no_catalog.initialize(missing).ok)
	missing.facts = {"policy_id":Fuel.POLICY,"timeline_id":"active-play","active_tick":"0","migration_receipt_id":"fixture"}
	check(not no_catalog.activate_fuel_policy("a").ok,"fuel policy cannot invent unregistered resource")
	check(Count.multiply_small("1"+"0".repeat(100),120000) == "120000"+"0".repeat(100),"fuel subunit scaling exact beyond machine integer")

func rates_and_exhaustion() -> void:
	var drive := setup()
	var complete := true
	for i in range(60):
		var r := use(drive,true,false)
		complete = complete and r.ok and r.powered_ms == 1000
	check(complete and amount(drive) == "7080000","60 seconds driving uses exactly1 fuel unit")
	var blades := setup()
	for i in range(120): assert(use(blades,false,true).ok)
	check(amount(blades) == "7080000","120 seconds blades uses exactly1 fuel unit")
	var both := setup()
	for i in range(40): assert(use(both,true,true).ok)
	check(amount(both) == "7080000","combined activity adds both low consumption rates")
	var frac := setup()
	var tiny := use(frac,true,true,1)
	check(tiny.burned_subunits == "3" and amount(frac) == "7199997","1ms keeps exact fractional fuel remainder")
	var before := amount(frac)
	check(use(frac,false,false).ok and amount(frac) == before,"active idle consumes zero fuel")
	frac.w.facts = {"timeline_id":"active-play","from_tick":frac.r.state().fuel.tanks["truck:1"].cursor,"elapsed_ms":0,"active_play":false,"driving":false,"blades":false}
	check(frac.r.grant_powered_use("truck",1,"paused","paused").ok and amount(frac) == before,"paused background consumes zero fuel")
	frac.w.facts.elapsed_ms = 1000
	frac.w.facts.driving = true
	check(not frac.r.grant_powered_use("truck",1,"offline","offline").ok and amount(frac) == before,"offline catch-up cannot burn fuel")
	frac.w.facts.active_play = true
	frac.w.facts.elapsed_ms = 1001
	check(not frac.r.grant_powered_use("truck",1,"oversized","oversized").ok,"large active catch-up window rejected")
	frac.w.facts.elapsed_ms = 0.5
	check(not frac.r.grant_powered_use("truck",1,"fractional-ms","fractional-ms").ok,"fractional milliseconds rejected to avoid floating accumulation")
	frac.w.facts.elapsed_ms = 1
	frac.w.facts.from_tick = "0"
	check(not frac.r.grant_powered_use("truck",1,"overlap","overlap").ok,"overlapping prior clock range rejected")
	frac.w.facts.from_tick = frac.r.state().fuel.tanks["truck:1"].cursor
	frac.w.facts.timeline_id = "wrong-world"
	check(not frac.r.grant_powered_use("truck",1,"wrong-time","wrong-time").ok,"different time authority rejected")
	var empty := setup(false)
	var denied := use(empty,true,true)
	check(denied.ok and not denied.powered_use_allowed and denied.powered_ms == 0 and denied.depleted,"zero tank durably denies powered action without deleting value")
	check(empty.r.audit().ok and empty.r.state().accounts.player.items.fuel == "200","empty tank does not secretly consume unlimited cargo or player fuel")
	service(empty)
	assert(empty.r.refuel("truck",1,"account","player",1,"1","fuel-one").ok)
	for i in range(39): assert(use(empty,true,true).powered_ms == 1000)
	var tail := use(empty,true,true,1000)
	check(tail.powered_ms == 1000 and amount(empty) == "0","exact final affordable activity ends at zero tank")
	check(use(empty,true,false).powered_ms == 0,"no continued movement allowance after depletion")
	var partial := setup(false)
	service(partial)
	assert(partial.r.refuel("truck",1,"account","player",1,"1","fill").ok)
	for i in range(59): assert(use(partial,true,false).powered_ms == 1000)
	assert(use(partial,true,false,999).powered_ms == 999)
	var final := use(partial,true,true,1000)
	check(final.powered_ms == 0 and amount(partial) == "2","unaffordable combined millisecond cannot overdraw fractional fuel")
	check(use(partial,true,false,1).powered_ms == 1 and amount(partial) == "0","remaining exact fraction can power affordable drive millisecond")
	var bounded := setup(false)
	service(bounded)
	assert(bounded.r.refuel("truck",1,"account","player",1,"1","fill").ok)
	for i in range(59): assert(use(bounded,true,false).ok)
	assert(use(bounded,true,false,500).ok)
	var shortened := use(bounded,true,true,1000)
	check(shortened.powered_ms == 333 and shortened.burned_subunits == "999" and amount(bounded) == "1","depletion grants only affordable partial milliseconds before physics")
	check(use(bounded,false,true,1).powered_ms == 1 and amount(bounded) == "0","fractional tail can power one blade millisecond without rounding loss")
	var replay := setup()
	var granted := use(replay,true,true,1)
	var once := amount(replay)
	check(replay.r.grant_powered_use("truck",1,"use-1","grant-1") == granted and amount(replay) == once,"grant receipt replay cannot burn fuel twice")
	replay.w.facts.from_tick = replay.r.state().fuel.tanks["truck:1"].cursor
	check(not replay.r.grant_powered_use("truck",1,"use-1","new-request").ok,"same usage identity with new request cannot consume another window")
	check(replay.r.audit().ok,"fractional active consumption exact conservation")

func usage_identity_and_save() -> void:
	var p := fixture()
	assert(activate(p).ok)
	p.w.garage.id = "garage-a"
	quote(p,"identity-a")
	p.w.facts.quote.vehicle_id = "a"
	p.w.facts.quote.garage_id = "garage-a"
	assert(p.r.admit_quote("identity-a","quote-identity-a").ok)
	assert(buy(p,"identity-a").ok)
	p.w.facts = {"timeline_id":"active-play","from_tick":"0","elapsed_ms":1,"active_play":true,"driving":true,"blades":false}
	var first: Dictionary = p.r.grant_powered_use("a",1,"x:1/u","identity-use-a")
	check(first.ok and first.powered_ms == 1,"delimiter-bearing usage ID receives first valid grant")
	p.w.garage.id = "garage-b"
	quote(p,"identity-b")
	p.w.facts.quote.vehicle_id = "a:1/x"
	p.w.facts.quote.garage_id = "garage-b"
	assert(p.r.admit_quote("identity-b","quote-identity-b").ok)
	assert(buy(p,"identity-b","1").ok)
	p.w.facts = {"timeline_id":"active-play","from_tick":"1","elapsed_ms":1,"active_play":true,"driving":true,"blades":false}
	var second: Dictionary = p.r.grant_powered_use("a:1/x",1,"u","identity-use-b")
	check(second.ok and second.powered_ms == 1,"distinct vehicle and usage tuple cannot collide through delimiters")
	var before: Dictionary = p.r.state()
	check(before.fuel.usage_ids.size() == 2 and before.fuel.tanks["a:1"].amount == "7199998" and before.fuel.tanks["a:1/x:1"].amount == "7199998" and before.fuel.burned_subunits == "4","independent grants burn only their own tanks once")
	var snapshot: Dictionary = JSON.parse_string(JSON.stringify(p.r.snapshot()))
	check(snapshot.events[-1].parameters.generation is float and snapshot.events[-1].parameters.generation == 1.0,"identity regression exercises JSON float generation metadata")
	p.w.permit_restore(snapshot)
	var restored := Rules.new()
	check(restored.restore(snapshot,p.w).ok and restored.state() == before,"delimiter-bearing usage history survives normalized JSON replay")
	check(restored.grant_powered_use("a",1,"x:1/u","identity-use-a") == first and restored.grant_powered_use("a:1/x",1,"u","identity-use-b") == second and restored.state() == before,"restored original receipts remain independent and immutable")
	p.w.facts.from_tick = "2"
	check(not restored.grant_powered_use("a",1,"x:1/u","new-request-a").ok and restored.state() == before,"restored first usage identity rejects new-request replay")
	check(not restored.grant_powered_use("a:1/x",1,"u","new-request-b").ok and restored.state() == before,"restored second usage identity rejects new-request replay")
	var shared_id := "same/:id[\"quoted\"]"
	var fresh_a: Dictionary = restored.grant_powered_use("a",1,shared_id,"fresh-a")
	var fresh_b: Dictionary = restored.grant_powered_use("a:1/x",1,shared_id,"fresh-b")
	check(fresh_a.ok and fresh_b.ok and fresh_a.powered_ms == 1 and fresh_b.powered_ms == 1 and restored.state().fuel.usage_ids.size() == 4,"same escaped usage ID remains independent for distinct vehicles")
	var second_save: Dictionary = JSON.parse_string(JSON.stringify(restored.snapshot()))
	p.w.permit_restore(second_save)
	var second_restore := Rules.new()
	check(second_restore.restore(second_save,p.w).ok and second_restore.state() == restored.state() and second_restore.audit().ok,"escaped tuple identities and exact custody survive second JSON save")

func refueling_and_garage() -> void:
	var p := setup(false)
	for field in ["speed","blade_speed","engine_running","source_available"]:
		service(p)
		p.w.facts[field] = false if field == "source_available" else (true if field == "engine_running" else 1)
		check(not p.r.refuel("truck",1,"account","player",1,"1","bad-"+field).ok,"refill service rejects " + field)
	service(p)
	check(not p.r.refuel("truck",1,"account","player",1,"61","too-big").ok,"tank cap does not accept oversized refill")
	check(not p.r.refuel("truck",1,"account","player",1,"01","bad-quantity").ok,"refill count canonical decimal")
	check(not p.r.refuel("truck",2,"account","player",1,"1","wrong-truck").ok,"refill rejects stale truck generation")
	p.w.load()
	assert(p.r.load_cargo("truck",1,"player",1,{"fuel":"7","wood":"9"},"load").ok)
	service(p)
	var filled: Dictionary = p.r.refuel("truck",1,"truck","truck",1,"2","refuel-cargo")
	check(filled.ok and amount(p) == "240000" and p.r.state().vehicles.truck.cargo.fuel == "5","refill atomically transfers cargo fuel into distinct tank")
	check(p.r.refuel("truck",1,"truck","truck",1,"2","refuel-cargo") == filled and amount(p) == "240000","refill replay cannot mint tank fuel")
	p.w.dock()
	assert(p.r.park_and_unload("truck",1,"dock").ok)
	check(amount(p) == "240000" and p.r.state().accounts.warehouse.items.fuel == "5" and p.r.state().vehicles.truck.cargo.is_empty(),"garage unloads all cargo fuel while tank remains")
	service(p)
	check(not p.r.refuel("truck",1,"truck","truck",1,"1","empty-cargo").ok,"docking first prevents later cargo refill using moved fuel")
	check(p.r.refuel("truck",1,"account","warehouse",1,"3","warehouse-refill").ok and p.r.state().accounts.warehouse.items.fuel == "2","reachable warehouse refill uses actual warehouse custody")
	var full := setup()
	assert(use(full,true,true,1).ok)
	service(full)
	check(not full.r.refuel("truck",1,"account","player",1,"1","overflow").ok and amount(full) == "7199997","whole-unit refuel never deletes fractional overflow")
	var huge := fixture()
	# Reinitialize only this brand-new fixture, before any gameplay or ownership.
	var w := World.new()
	w.initial.resources.append("fuel")
	w.initial.accounts.player.items["fuel"] = "1"+"0".repeat(100)
	var r := Rules.new()
	assert(r.initialize(w).ok)
	huge = {"w":w,"r":r,"n":0}
	assert(activate(huge).ok)
	quote(huge,"q1",1,false)
	assert(r.admit_quote("q1","quote").ok)
	assert(buy(huge).ok)
	w.load()
	assert(r.load_cargo("truck",1,"player",1,{"fuel":"1"+"0".repeat(100)},"huge-load").ok)
	service(huge)
	check(r.refuel("truck",1,"truck","truck",1,"60","small-from-huge").ok and r.audit().ok,"unlimited huge fuel cargo refuels bounded tank without integer conversion")

func destruction_recovery() -> void:
	var p := setup()
	assert(use(p,true,true,1).ok)
	p.w.load()
	assert(p.r.load_cargo("truck",1,"player",1,{"fuel":"7"},"load").ok)
	p.w.hit()
	var hit: Dictionary = p.r.apply_contact_damage("truck",1,"hit1","dead")
	check(hit.ok and hit.tank_fuel_subunits == "7199997" and p.r.state().fuel.lost_subunits == "7199997","outside destruction loses remaining fractional tank fuel")
	check(p.r.state().lost.fuel == "7" and p.r.state().fuel.estates.is_empty(),"outside loss includes whole cargo fuel with no recoverable clone")
	check(p.r.apply_contact_damage("truck",1,"hit1","dead") == hit and p.r.audit().ok,"outside fuel loss durable idempotent conservation")
	service(p)
	check(not p.r.refuel("truck",1,"account","player",1,"1","dead-refill").ok,"destroyed truck cannot refuel")
	var inside := setup(false)
	service(inside)
	assert(inside.r.refuel("truck",1,"account","player",1,"1","one").ok)
	assert(use(inside,true,false,1).ok)
	inside.w.hit("inside",false)
	var interior: Dictionary = inside.r.apply_contact_damage("truck",1,"inside","interior")
	check(inside.r.state().fuel.estates[interior.disposition] == "119998" and inside.r.state().fuel.lost_subunits == "0","inside destruction preserves exact fractional tank estate")
	quote(inside,"replacement",2,true)
	assert(inside.r.admit_quote("replacement","q2").ok)
	assert(buy(inside,"replacement","1").ok)
	assert(use(inside,true,true,1000,2).ok)
	service(inside)
	var recovered: Dictionary = inside.r.recover_tank_fuel("truck",2,interior.disposition,"recover")
	check(recovered.ok and recovered.moved_subunits == "3000" and recovered.remaining_estate_subunits == "116998","fuel estate partial tank recovery retains every unused fraction")
	check(inside.r.recover_tank_fuel("truck",2,interior.disposition,"recover") == recovered and amount(inside,2) == "7200000","fuel estate receipt replay cannot duplicate recovered fuel")
	check(inside.r.audit().ok,"replacement and fractional estate recovery preserve total fuel")
	var bank := setup()
	bank.w.load()
	assert(bank.r.load_cargo("truck",1,"player",1,{"fuel":"7"},"load").ok)
	bank.w.dock()
	assert(bank.r.park_and_unload("truck",1,"dock").ok)
	bank.w.hit()
	assert(bank.r.apply_contact_damage("truck",1,"hit1","dead").ok)
	check(bank.r.state().accounts.warehouse.items.fuel == "7" and not bank.r.state().lost.has("fuel"),"banked cargo fuel survives subsequent exterior truck loss")

func migration_and_save() -> void:
	var saved: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://evidence/fuel-v2/legacy-v1-snapshot.json"))
	var w := World.new()
	w.permit_restore(saved)
	var r := Rules.new()
	check(r.restore(saved,w).ok and not r.state().has("fuel"),"actual pre-change v1 snapshot replays without new fuel fields")
	var p := {"w":w,"r":r,"n":0}
	check(activate(p).ok and amount(p) == "0" and r.state().vehicles.truck.cargo.fuel == "5","explicit migration adds empty tank and preserves legacy cargo")
	service(p)
	assert(r.refuel("truck",1,"truck","truck",1,"1","refill").ok)
	assert(use(p,true,true,1).ok)
	var snapshot: Dictionary = JSON.parse_string(JSON.stringify(r.snapshot()))
	w.permit_restore(snapshot)
	var restored := Rules.new()
	check(restored.restore(snapshot,w).ok and restored.state() == r.state(),"v1 migration refuel fractional consumption survive exact JSON replay")
	check(restored.grant_powered_use("truck",1,"use-1","grant-1") == r.grant_powered_use("truck",1,"use-1","grant-1"),"saved fuel grant receipt replay immutable")
	var bad := snapshot.duplicate(true)
	bad.events[-1].receipt.burned_subunits = "0"
	w.permit_restore(bad)
	check(not restored.restore(bad,w).ok,"edited fuel consumption receipt rejected")
	bad = snapshot.duplicate(true)
	bad.events[-1].facts.elapsed_ms = 1001
	w.permit_restore(bad)
	check(not restored.restore(bad,w).ok,"saved oversized consumption window rejected")
	bad = snapshot.duplicate(true)
	bad.events[-1].facts.active_play = false
	w.permit_restore(bad)
	check(not restored.restore(bad,w).ok,"saved offline burn transition rejected")
	check(restored.audit().ok and restored.state() == r.state(),"rejected fuel restore leaves previous valid state unchanged")
	var q := setup()
	var before: Dictionary = q.r.state()
	service(q)
	q.w.invalidate_after_first_check = true
	# Start from an empty legacy tank so the revalidation, not capacity, is tested.
	var empty := setup(false)
	service(empty)
	empty.w.invalidate_after_first_check = true
	before = empty.r.state()
	check(not empty.r.refuel("truck",1,"account","player",1,"1","world-race").ok and empty.r.state() == before,"world change between validation and commit rolls back refill")
	var paid := setup()
	var paid_save: Dictionary = JSON.parse_string(JSON.stringify(paid.r.snapshot()))
	paid.w.permit_restore(paid_save)
	var paid_restore := Rules.new()
	check(paid_restore.restore(paid_save,paid.w).ok and paid_restore.state() == paid.r.state(),"paid full initial tank allocation survives JSON roundtrip")
