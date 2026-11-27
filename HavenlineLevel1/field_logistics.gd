extends RefCounted
## Typed reservations, each equal to one real ten-unit cargo bundle or one meal.
const P=preload("res://field_progression.gd")
const RAW=["wood","stone","meat"]
const PRODUCT={"wood":"planks","stone":"blocks","meat":"meal"}
const INPUT_FOR={"planks":"wood","blocks":"stone"}
const LANES=["wood","stone","meat","planks","blocks","meal","stored_meal","meal_to_store"]
const TRANSIT={"wood":0,"stone":0,"meat":0,"meal":0,"planks":0,"blocks":0,"stored_meal":0,"meal_to_store":0}
const CLOCK={"wood":0.,"stone":0.,"meat":0.,"meal":0.,"planks":0.,"blocks":0.,"stored_meal":0.,"meal_to_store":0.}
const STORE={"planks":0,"blocks":0,"meal":0}
const SPACE={"planks":48,"blocks":48,"meal":6}
const WORK_RACK=4

static func allowed(lane:String,purchases:Array)->bool:
	var meal:=P.FOOD_LINE in purchases
	var supply:=P.SUPPLY_LINE in purchases
	if lane=="meal":return meal and supply
	if lane=="stored_meal" or lane=="meal_to_store":return meal
	var input:String=INPUT_FOR.get(lane,lane)
	return supply and input in RAW and P.MACHINES[input] in purchases

static func rack(j:Dictionary,raw:String)->int:
	if raw=="meat":
		return int(j.cooked)-int(j.served)-int(j.held_meal)-int(j.worker_meal)-int(j.counter_stock)-int(j.product_store.meal)-int(j.line_load.meal)-int(j.line_load.stored_meal)-int(j.line_load.meal_to_store)
	var kind:String=PRODUCT[raw]
	return int(j["processed_"+raw])-int(j.product_store[kind])-int(j.line_load[kind])

static func receiving_space(j:Dictionary,product:String)->bool:
	var lane: String="meal_to_store" if product=="meal" else product
	return j.product_store[product]+j.line_load[lane]<SPACE[product]

static func merge_busy(j:Dictionary)->bool:
	return j.line_load.meal+j.line_load.stored_meal>0

static func from_previous(previous:Variant,purchases:Array)->Variant:
	if not previous is Dictionary or previous.has("product_store") or previous.has("dispatch_cursor"):return null
	var next:Dictionary=previous.duplicate(true)
	var old_keys:=["wood","stone","meat","meal"]
	for field in ["line_load","line_progress"]:
		if not next.get(field) is Dictionary or next[field].size()!=old_keys.size() or not next[field].has_all(old_keys):return null
		for lane:String in TRANSIT:
			if not next[field].has(lane):next[field][lane]=0
		# A real v8 direct delivery stays an already-claimed roast and reaches
		# the counter. On a serial-only install its remaining trip uses D06.
		if P.FOOD_LINE in purchases and P.SUPPLY_LINE not in purchases:
			next[field].stored_meal=next[field].meal
			next[field].meal=0
	next.product_store=STORE.duplicate()
	next.dispatch_cursor=0
	return next

static func valid(j:Dictionary,purchases:Array)->bool:
	if not j.get("product_store") is Dictionary or j.product_store.size()!=STORE.size() or not j.product_store.has_all(STORE.keys()):return false
	if not _count(j.get("dispatch_cursor")) or j.dispatch_cursor>=LANES.size():return false
	for product:String in STORE:
		var stock:Variant=j.product_store[product]
		if not _count(stock) or stock>SPACE[product]:return false
		var lane: String="meal_to_store" if product=="meal" else product
		if stock+j.line_load[lane]>SPACE[product] or (stock>0 and not allowed(lane,purchases)):return false
	for lane:String in TRANSIT:
		if j.line_load[lane]>0 and not allowed(lane,purchases):return false
	for raw:String in RAW:
		if rack(j,raw)<0:return false
	return j.line_load.meal+j.line_load.stored_meal<=1

static func _count(value:Variant)->bool:
	return (value is float or value is int) and is_finite(float(value)) and value>=0 and int(value)==value
