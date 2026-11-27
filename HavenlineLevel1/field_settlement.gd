extends RefCounted
## Receipts produced by Level 1's survivor, kitchen and trading counter.

const Crew=preload("res://field_crew.gd")
const Logistics=preload("res://field_logistics.gd")
const LEGACY := {"survivor_paid":false, "survivor_wood":0, "processed_wood":0, "processed_stone":0, "owl_hits":0, "rescued":false, "worker_carry_token":"", "worker_deliveries":0, "worker_receipts":[], "cooked":0, "served":0, "level":1}
const KINDS := ["wood", "stone", "meat"]
const WORKER_LOAD := {"wood":0,"stone":0,"meat":0,"coal":0,"slate":0,"metal":0}
# Balances use ten-unit physical bundles, exactly as the player's HUD does.
const WORKER_LIMIT := 500 / preload("res://field_progression.gd").UNITS_PER_BUNDLE
const HOPPER_CAPACITY := 4
const ROAST_RACK_CAPACITY := 4
const COUNTER_RACK_CAPACITY := 2
const LINE_EMPTY := Logistics.TRANSIT
const LINE_CLOCK := Logistics.CLOCK
const CYCLE_SECONDS := {"wood":1.45, "stone":1.45, "meat":1.65}
const HAND_PRODUCTS := {"planks":0,"blocks":0}
const EMPTY := {
	"owl_meat":0, "owl_legacy":false, "hand_products":HAND_PRODUCTS, "pocket_cash":0, "house_cash":0, "withdrawn":{},
	"survivor_paid":false, "survivor_wood":0, "processed_wood":0, "processed_stone":0,
	"owl_hits":0, "rescued":false, "worker_carry_token":"", "worker_deliveries":0,
	"worker_receipts":[], "cooked":0, "served":0, "level":1,
	"hoppers":{"wood":0, "stone":0, "meat":0},
	"work_seconds":{"wood":0.0, "stone":0.0, "meat":0.0}, "held_meal":0, "worker_supply":"",
	"worker_load":WORKER_LOAD,"worker_meal":0,
	"line_load":LINE_EMPTY, "line_progress":LINE_CLOCK, "counter_stock":0,"product_store":Logistics.STORE, "dispatch_cursor":0,
}

# An unserved v4 roast was already on the player's hand. Preserve its location.
static func from_legacy(previous: Variant) -> Variant:
	if not previous is Dictionary or previous.size() != LEGACY.size() or not previous.has_all(LEGACY.keys()):
		return null
	if not _count(previous.cooked) or not _count(previous.served):
		return null
	var in_hand := int(previous.cooked) - int(previous.served)
	if in_hand < 0 or in_hand > 1: return null
	var updated: Dictionary = EMPTY.duplicate(true)
	updated.merge(previous.duplicate(true), true)
	updated.held_meal = in_hand
	for key in ["line_load","line_progress","counter_stock","product_store","dispatch_cursor","hand_products","pocket_cash","house_cash","withdrawn","owl_meat","owl_legacy"]: updated.erase(key)
	return updated

static func from_pre_worker(previous: Variant) -> Variant:
	if not previous is Dictionary: return null
	var next: Dictionary = previous.duplicate(true)
	if not next.has("worker_load"): next.worker_load = WORKER_LOAD.duplicate()
	if not next.has("worker_meal"): next.worker_meal = 0
	return next

static func from_pre_conveyors(previous: Variant) -> Variant:
	if not previous is Dictionary: return null
	for key in ["line_load","line_progress","counter_stock"]:
		if previous.has(key): return null
	var next: Dictionary = previous.duplicate(true)
	next.line_load={"wood":0,"stone":0,"meat":0,"meal":0}
	next.line_progress={"wood":0.,"stone":0.,"meat":0.,"meal":0.}
	next.counter_stock=0
	return next

# Prior sales were recorded directly as owned earnings. Bank each existing
# receipt once, preserving the existing hand meal and outstanding belt stock.
static func from_pre_register(previous:Variant,paid_order:Array) -> Variant:
	if not previous is Dictionary: return null
	for key in ["hand_products","pocket_cash","house_cash","withdrawn","owl_meat","owl_legacy"]:
		if previous.has(key): return null
	# These earlier versions could only fill shelves and the counter via
	# bought belts. Validate their old physical capacities before widening
	# them to include the deeper, manually stocked warehouse and counter.
	if not _count(previous.get("held_meal")) or previous.held_meal>1:return null
	if not _count(previous.get("counter_stock")) or not previous.get("line_load") is Dictionary:return null
	for lane in ["meal","stored_meal"]:
		if not _count(previous.line_load.get(lane)):return null
	if previous.counter_stock+previous.line_load.meal+previous.line_load.stored_meal>COUNTER_RACK_CAPACITY:return null
	if previous.counter_stock>0 and Logistics.P.FOOD_LINE not in paid_order:return null
	if not previous.get("product_store") is Dictionary:return null
	for product:String in Logistics.STORE:
		var lane:String="meal_to_store" if product=="meal" else product
		var stock:Variant=previous.product_store.get(product)
		if not _count(stock) or not _count(previous.line_load.get(lane)):return null
		if stock+previous.line_load[lane]>Logistics.SPACE[product]:return null
		if stock>0 and not Logistics.allowed(lane,paid_order):return null
	var next:Dictionary = Crew.migrate(previous)
	next.hand_products = HAND_PRODUCTS.duplicate()
	next.pocket_cash = 0
	next.house_cash = next.get("served",0)
	next.withdrawn = {}
	return next

static func _count(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value == int(value) and value >= 0

static func waiting_meals(state: Dictionary) -> int:
	return Logistics.rack(state,"meat")


static func is_wood_drop(token: String) -> bool:
	var suffix := token.trim_prefix("wood-")
	return token.begins_with("wood-") and suffix.is_valid_int() and suffix.to_int() > 0 and suffix == str(suffix.to_int())

static func valid(state: Variant, paid_order: Array, credits: Dictionary, survivor_cost: int) -> bool:
	if not state is Dictionary or state.size() != EMPTY.size():
		return false
	if not state.get("survivor_paid") is bool or not state.get("rescued") is bool or not state.get("worker_carry_token") is String:
		return false
	for key in ["worker_deliveries", "cooked", "served", "level", "survivor_wood", "processed_wood", "processed_stone", "owl_hits", "held_meal", "worker_meal"]:
		var value: Variant = state.get(key)
		if not _count(value):
			return false
	if not _count(state.get("counter_stock")): return false
	for column in ["line_load","line_progress"]:
		if not state.get(column) is Dictionary or state[column].size()!=LINE_EMPTY.size() or not state[column].has_all(LINE_EMPTY.keys()): return false
	for lane:String in LINE_EMPTY:
		var amount:Variant=state.line_load[lane]
		var t:Variant=state.line_progress[lane]
		if not _count(amount) or amount>1 or not (t is float or t is int) or not is_finite(t) or t<0. or t>1.: return false
		if amount==0 and t!=0.:return false
	if not Crew.valid(state,paid_order): return false
	if not state.get("hand_products") is Dictionary or state.hand_products.size()!=HAND_PRODUCTS.size() or not state.hand_products.has_all(HAND_PRODUCTS.keys()): return false
	for amount in state.hand_products.values():
		if not _count(amount): return false
	if not _count(state.get("pocket_cash")) or not _count(state.get("house_cash")) or state.pocket_cash>state.served or state.house_cash>state.served-state.pocket_cash: return false
	if not state.get("withdrawn") is Dictionary: return false
	for kind in state.withdrawn:
		if not (kind in WORKER_LOAD or kind in Logistics.STORE or kind=="money") or not _count(state.withdrawn[kind]): return false
	if not Logistics.valid(state,paid_order): return false
	if state.counter_stock>0 and not "expansion_2" in paid_order:return false
	if (state.level != 1 and state.level != 2) or state.worker_meal > 1 or waiting_meals(state) < 0 or waiting_meals(state) > ROAST_RACK_CAPACITY:
		return false
	if not state.get("worker_load") is Dictionary or state.worker_load.size() != WORKER_LOAD.size() or not state.worker_load.has_all(WORKER_LOAD.keys()): return false
	for kind: String in WORKER_LOAD:
		var bundles: Variant = state.worker_load[kind]
		var single := (1 if state.worker_carry_token != "" and kind == "wood" else 0) + (1 if state.get("worker_supply") == kind else 0)
		if not _count(bundles) or bundles+single > WORKER_LIMIT: return false
		if bundles > 0 and not state.rescued: return false
	if state.worker_meal > 0 and not state.rescued: return false
	for column in ["hoppers","work_seconds"]:
		if not state.get(column) is Dictionary or state[column].size() != KINDS.size() or not state[column].has_all(KINDS):
			return false
	for kind: String in KINDS:
		var units: Variant = state.hoppers[kind]
		var elapsed: Variant = state.work_seconds[kind]
		if not _count(units) or units + state.line_load[kind] > HOPPER_CAPACITY: return false
		if not (elapsed is float or elapsed is int) or not is_finite(float(elapsed)) or elapsed < 0 or elapsed > CYCLE_SECONDS[kind]: return false
		if units == 0 and elapsed != 0: return false
		if units > 0 and "expansion_2" not in paid_order: return false
	if not state.get("worker_supply") is String or (state.worker_supply != "" and (
			state.worker_supply not in KINDS or not state.rescued or "expansion_2" not in paid_order or state.worker_carry_token != "")):
		return false
	if state.survivor_wood > survivor_cost or state.survivor_paid != (state.survivor_wood == survivor_cost): return false
	if state.survivor_wood > 0 and "center_hearth" not in paid_order: return false
	if state.rescued and not state.survivor_paid: return false
	if state.owl_hits > 0 and not Crew.owns_owl(state): return false
	if (state.processed_wood > 0 or state.processed_stone > 0) and "expansion_2" not in paid_order: return false
	if state.cooked > 0 and "expansion_2" not in paid_order: return false
	if not state.get("worker_receipts") is Array or state.worker_receipts.size() != state.worker_deliveries:
		return false
	if state.worker_deliveries > 0 or state.worker_carry_token != "":
		if not state.rescued or "storage_wood" not in paid_order: return false
	if state.worker_carry_token != "" and (not is_wood_drop(state.worker_carry_token) or credits.has(state.worker_carry_token)):
		return false
	var unique := {}
	for id in state.worker_receipts:
		if not id is String or not is_wood_drop(id) or unique.has(id) or credits.get(id) != "wood": return false
		unique[id] = true
	return state.level == 1 or _original_receipts(state,paid_order)

static func ready_to_continue(state: Dictionary, paid_order: Array) -> bool:
	return _original_receipts(state,paid_order) and ["camp_cooker","saw_bench","quarry_drill"].all(func(id): return id in paid_order)

# Previous trials could already have reached Level 2 with the original eight
# purchases. Preserve that earned level when those saves reopen.
static func _original_receipts(state: Dictionary, paid_order: Array) -> bool:
	return state.rescued and state.worker_deliveries > 0 and state.served > 0 and state.processed_wood > 0 and state.processed_stone > 0 and state.owl_hits > 0 and ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","watchtower","orbit_upgrade"].all(func(id): return id in paid_order)
