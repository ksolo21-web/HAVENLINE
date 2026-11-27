extends SceneTree

const Rules = preload("res://vehicle_rules.gd")
const World = preload("res://tests/world_fixture.gd")
const Fuel = preload("res://fuel_rules.gd")
const Count = preload("res://exact_count.gd")
var checks: Array = []
var failures := 0

func check(value: bool, name: String, observed: Variant = null) -> void:
	checks.append({"name": name, "passed": value, "observed": observed})
	if not value:
		failures += 1
		push_error(name)

func fixture(tick := "0") -> Dictionary:
	var w := World.new()
	w.initial.resources.append("fuel")
	w.initial.accounts.player.items["fuel"] = "200"
	var r := Rules.new()
	var initialized: Dictionary = r.initialize(w)
	if not initialized.ok: print(JSON.stringify({"fixture_init_failure": initialized,"initial":w.initial}))
	assert(initialized.ok)
	w.facts = {"policy_id":Fuel.POLICY,"timeline_id":"critic-active-play","active_tick":tick,"migration_receipt_id":"critic-migration"}
	assert(r.activate_fuel_policy("activate").ok)
	return {"w":w,"r":r,"next":0}

func offer(p: Dictionary, id: String, garage_id: String, request: String, initial := true, fuel_bill := "60", tick := "0") -> Dictionary:
	p.w.garage.id = garage_id
	p.w.quote(request)
	p.w.facts.quote.vehicle_id = id
	p.w.facts.quote.garage_id = garage_id
	if initial:
		p.w.facts.quote["initial_tank_fuel_units"] = "60"
		p.w.facts.quote.bill["fuel"] = fuel_bill
	var admitted: Dictionary = p.r.admit_quote(request,"quote-"+request)
	assert(admitted.ok)
	p.w.buy()
	p.w.facts["fuel_clock"] = {"timeline_id":"critic-active-play","active_tick":tick}
	return p.r.purchase(request,"buy-"+request)

func setup(initial := true, tick := "0") -> Dictionary:
	var p := fixture(tick)
	assert(offer(p,"truck","garage","first",initial,"60",tick).ok)
	return p

func service(p: Dictionary) -> void:
	p.w.facts = {"contact_id":"critic-current-service","source_available":true,"speed":0,"blade_speed":0,"engine_running":false}

func power(p: Dictionary, id: String, usage: String, request: String, tick: String, ms: int, drive: bool, blade: bool, active := true) -> Dictionary:
	p.w.facts = {"timeline_id":"critic-active-play","from_tick":tick,"elapsed_ms":ms,"active_play":active,"driving":drive,"blades":blade}
	return p.r.grant_powered_use(id,1,usage,request)

func _initialize() -> void:
	denied_window_and_zero_clock()
	authority_and_atomicity()
	extra_paid_fuel_and_restore()
	frame_partition_and_large_clock()
	separate_estate_custody()
	cross_vehicle_usage_identity()
	arithmetic_oracle()
	var result := {"scope":"INDEPENDENT_FUEL_COMPONENT_ONLY","passed":checks.size()-failures,"failed":failures,"checks":checks,"game_integration":false,"consumer_exact_once_application_tested":false}
	var path: String = get_script().resource_path.get_base_dir().path_join("independent-fuel-result.json")
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(result,"\t")+"\n")
	print(JSON.stringify({"passed":checks.size()-failures,"failed":failures,"output":path}))
	quit(0 if failures == 0 else 1)

func denied_window_and_zero_clock() -> void:
	var p := setup(false)
	var first := power(p,"truck","empty-slice","deny","0",17,true,true)
	check(first.ok and first.powered_ms == 0 and first.cursor == "17","empty fuel records a denied window",first)
	service(p)
	assert(p.r.refuel("truck",1,"account","player",1,"1","fill").ok)
	var before: Dictionary = p.r.state()
	var replay := power(p,"truck","after-refill-old-window","old-window","0",17,true,true)
	check(not replay.ok and p.r.state() == before,"refill cannot power an already denied window",replay)
	var now := power(p,"truck","current","current","17",17,true,true)
	check(now.ok and now.powered_ms == 17 and now.burned_subunits == "51","new window after refill receives only affordable power",now)
	before = p.r.state()
	var empty := power(p,"truck","zero-active","zero-active","34",0,true,true)
	check(not empty.ok and p.r.state() == before,"zero active duration cannot create a successful powered grant",empty)
	var paused := power(p,"truck","pause","pause","34",0,false,false,false)
	check(paused.ok and not paused.powered_use_allowed and paused.burned_subunits == "0" and p.r.state().fuel.tanks["truck:1"].amount == "119949","paused zero-duration report cannot burn or grant",paused)
	before = p.r.state()
	var jump := power(p,"truck","paused-clock-jump","paused-clock-jump","35",0,false,false,false)
	check(not jump.ok and p.r.state() == before,"paused report cannot advance the active clock",jump)
	var gap := power(p,"truck","idle-gap","idle-gap","1000000000000000000000000000000",1,false,true)
	check(gap.ok and gap.burned_subunits == "1" and gap.powered_ms == 1,"unreported dormant gap grants and burns only new active duration",gap)
	check(p.r.audit().ok,"clock edge cases conserve all resource custody")

func authority_and_atomicity() -> void:
	var p := setup()
	var before: Dictionary = p.r.state()
	p.w.invalidate_after_first_check = true
	var stale := power(p,"truck","race","race","0",1,true,true)
	check(not stale.ok and p.r.state() == before,"failed precommit revalidation rolls back grant burn and cursor",stale)
	p.w.invalidate_after_first_check = false
	var retry := power(p,"truck","race","race","0",1,true,true)
	check(retry.ok and retry.burned_subunits == "3","same failed request can retry against a fresh valid observation",retry)
	before = p.r.state()
	p.w.forge_authority = true
	var forged := power(p,"truck","forged","forged","1",1,true,false)
	check(not forged.ok and p.r.state() == before,"wrong authority cannot issue a power grant",forged)
	p.w.forge_authority = false
	var conflict: Dictionary = p.r.grant_powered_use("truck",1,"different-use-id","race")
	check(not conflict.ok and p.r.state() == before,"changed usage payload under an existing request is rejected",conflict)
	var receipt: Dictionary = p.r.grant_powered_use("truck",1,"race","race")
	check(receipt == retry and p.r.state() == before,"same durable grant replay changes no fuel or cursor",receipt)
	var snap: Dictionary = JSON.parse_string(JSON.stringify(p.r.snapshot()))
	var replacement := World.new()
	replacement.permit_restore(snap)
	check(not p.r.restore(snap,replacement).ok and p.r.state() == before,"same-named replacement authority cannot take over existing ledger")
	p.w.permit_restore(snap)
	var restored := Rules.new()
	check(restored.restore(snap,p.w).ok and restored.state() == before,"exact current authorized grant history restores")
	var changed: Dictionary = snap.duplicate(true)
	changed.events[-1].facts.driving = false
	p.w.permit_restore(changed)
	check(not restored.restore(changed,p.w).ok and restored.state() == before,"modified power mode cannot restore under unchanged receipt/digest")
	var stale_epoch: Dictionary = snap.duplicate(true)
	p.w.allowed_restore = "world-revoked-this-epoch"
	check(not restored.restore(stale_epoch,p.w).ok,"save authority refusal blocks a stale otherwise-consistent grant history")
	check(restored.audit().ok,"authority failures preserve prior valid conservation")

func extra_paid_fuel_and_restore() -> void:
	var p := fixture()
	var paid := offer(p,"truck","garage","extra",true,"73")
	check(paid.ok and paid.debited_bill.fuel == "73" and paid.consumed.fuel == "13" and p.r.state().accounts.player.items.fuel == "127" and p.r.state().spent.fuel == "13" and p.r.state().fuel.tanks["truck:1"].amount == "7200000","fuel above the tank allocation remains actual material spending",paid)
	var saved: Dictionary = JSON.parse_string(JSON.stringify(p.r.snapshot()))
	p.w.permit_restore(saved)
	var r := Rules.new()
	check(r.restore(saved,p.w).ok and r.state() == p.r.state(),"mixed tank allocation and fuel spending survive JSON replay")
	var q := fixture("999")
	q.w.quote("clock-bound")
	q.w.facts.quote["initial_tank_fuel_units"] = "60"
	q.w.facts.quote.bill["fuel"] = "60"
	assert(q.r.admit_quote("clock-bound","quote-clock").ok)
	var before: Dictionary = q.r.state()
	q.w.buy()
	q.w.facts["fuel_clock"] = {"timeline_id":"critic-active-play","active_tick":"998"}
	var rejected: Dictionary = q.r.purchase("clock-bound","clock-purchase")
	check(not rejected.ok and q.r.state() == before,"invalid purchase clock rolls back quote use and every bill debit",rejected)
	q.w.facts.fuel_clock.active_tick = "999"
	check(q.r.purchase("clock-bound","clock-purchase").ok and q.r.audit().ok,"failed purchase can retry once at current authoritative clock")

func frame_partition_and_large_clock() -> void:
	var a := setup()
	var b := setup()
	var cursor := 0
	for ms in [1,999,7,993,317,683,1000,499,501,1000]:
		assert(power(a,"truck","u"+str(cursor),"r"+str(cursor),str(cursor),ms,true,true).ok)
		cursor += ms
	var second_cursor := 0
	while second_cursor < cursor:
		var ms := mini(1000,cursor-second_cursor)
		assert(power(b,"truck","u"+str(second_cursor),"r"+str(second_cursor),str(second_cursor),ms,true,true).ok)
		second_cursor += ms
	check(a.r.state().fuel.tanks["truck:1"] == b.r.state().fuel.tanks["truck:1"] and a.r.state().fuel.burned_subunits == b.r.state().fuel.burned_subunits,"different frame partitions produce the same exact fuel and cursor")
	var large_tick := "9".repeat(320)
	var huge := setup(true,large_tick)
	var grant := power(huge,"truck","huge-tick","huge-tick",large_tick,1,true,true)
	check(grant.ok and grant.cursor == "1"+"0".repeat(320) and grant.burned_subunits == "3","active clock increments across a 320-digit carry exactly",grant)
	var saved: Dictionary = JSON.parse_string(JSON.stringify(huge.r.snapshot()))
	huge.w.permit_restore(saved)
	var restored := Rules.new()
	check(restored.restore(saved,huge.w).ok and restored.state() == huge.r.state(),"large exact active clock survives JSON save replay")

func separate_estate_custody() -> void:
	var p := setup(false)
	service(p)
	assert(p.r.refuel("truck",1,"account","player",1,"1","fill").ok)
	assert(power(p,"truck","single","single","0",1,true,true).ok)
	p.w.load()
	assert(p.r.load_cargo("truck",1,"player",1,{"fuel":"2","wood":"3"},"load").ok)
	p.w.hit("inside-critic",false)
	var wreck: Dictionary = p.r.apply_contact_damage("truck",1,"inside-critic","wreck")
	assert(wreck.ok)
	p.w.claim()
	assert(p.r.claim_inside_salvage(wreck.disposition,"player",1,"claim").ok)
	check(p.r.state().salvage[wreck.disposition].is_empty() and p.r.state().fuel.estates[wreck.disposition] == "119997","ordinary estate claim leaves separate exact fractional estate intact")
	p.w.quote("replacement",2)
	assert(p.r.admit_quote("replacement","q-replacement").ok)
	p.w.buy()
	p.w.facts["fuel_clock"] = {"timeline_id":"critic-active-play","active_tick":"1"}
	assert(p.r.purchase("replacement","replacement").ok)
	service(p)
	var recovered: Dictionary = p.r.recover_tank_fuel("truck",2,wreck.disposition,"recover")
	check(recovered.ok and recovered.moved_subunits == "119997" and recovered.remaining_estate_subunits == "0" and p.r.state().fuel.tanks["truck:2"].amount == "119997","empty replacement tank recovers every surviving fraction exactly",recovered)
	var again: Dictionary = p.r.recover_tank_fuel("truck",2,wreck.disposition,"fresh-empty-recovery")
	check(again.ok and again.moved_subunits == "0" and p.r.audit().ok,"new request against emptied fractional estate cannot duplicate stock",again)
	p.w.hit("outside-critic",true)
	assert(p.r.apply_contact_damage("truck",2,"outside-critic","outside-wreck").ok)
	check(p.r.state().fuel.lost_subunits == "119997" and p.r.state().fuel.tanks["truck:2"].amount == "0" and p.r.state().fuel.burned_subunits == "3" and p.r.audit().ok,"recovered fraction later destroyed outside is lost once and still conserved")

func cross_vehicle_usage_identity() -> void:
	var p := fixture()
	assert(offer(p,"a","garage-a","first",true,"60","0").ok)
	var first := power(p,"a","x:1/u","use-a","0",1,true,false)
	assert(first.ok)
	assert(offer(p,"a:1/x","garage-b","second",true,"60","1").ok)
	var second := power(p,"a:1/x","u","use-b","1",1,true,false)
	check(second.ok and second.powered_ms == 1,"valid independent vehicle and usage IDs cannot collide through string concatenation",second)
	check(p.r.audit().ok,"cross-vehicle identity exercise preserves custody")

func arithmetic_oracle() -> void:
	var path: String = get_script().resource_path.get_base_dir().path_join("multiply-small-oracle.json")
	var cases: Array = JSON.parse_string(FileAccess.get_file_as_string(path))
	var passed := 0
	var failed: Array = []
	for c in cases:
		var actual: String = Count.multiply_small(c.value,int(c.factor))
		if actual == c.expected: passed += 1
		else: failed.append({"case":c,"actual":actual})
	check(failed.is_empty() and passed == cases.size(),"new arbitrary-precision multiplication matches independent Python integer oracle",{"passed":passed,"total":cases.size(),"failed":failed})
