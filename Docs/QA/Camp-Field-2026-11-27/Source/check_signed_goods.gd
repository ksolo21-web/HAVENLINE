extends SceneTree
# Desktop replay of the exact Android data pack with a private save.
const P=preload("res://field_progression.gd")
const Store=preload("res://field_save.gd")
var field
var results:Dictionary={}
func _initialize()->void:run.call_deferred()
func check(title:String,value:bool) -> void:
	results[title]=value
	if not value:push_error(title)

func park(at:Vector3) -> void:
	field.actor.global_position=at
	field.previous_dry_position=at
	field.actor.velocity=Vector3.ZERO

func ticks(n:int) -> void:
	for i in n:await physics_frame

func until(fn:Callable,limit:=1500) ->bool:
	for i in limit:
		if fn.call():return true
		if field.persist_blocked:return false
		await physics_frame
	return fn.call()


## Replays public station/warehouse/counter interactions in field_opening.tscn.
const Cargo=preload("res://field_logistics.gd")
const Group=["wood","stone","meat"]
var bank
var j:Dictionary
var loop
var visits:Array=[]
var anchor:=Vector3(1.15,0.,.90)
var observed:=false

func inspect_state(label:String)->void:
	visits.append({"step":label,"t":snappedf(field.simulation_time,.001),"pack":bank.hand_goods(),"house":bank.house_goods(),"cash_in_register":bank.till_balance(),"raw_pack":bank.carried.duplicate(),"counter_meals":j.counter_stock,"cooked":j.cooked,"served":j.served,"saw":j.processed_wood,"drill":j.processed_stone})

func station_floor(kind:String)->Vector3:
	var r:Rect2=field.lakeshore._footprint(0.) if kind=="meat" else field.processors._rect(kind,0.)
	var c:=r.get_center()
	var candidates:=[c+Vector2(0.,r.size.y*.5+.40),c+Vector2(r.size.x*.5+.40,0.),c-Vector2(r.size.x*.5+.40,0.),c-Vector2(0.,r.size.y*.5+.40)]
	var net=loop.conveyors.network
	for candidate:Vector2 in candidates:
		var point:=Vector3(candidate.x,0.,candidate.y)
		if loop.exchange._machine_at(point)==kind and net.pedestrian_clear(point,point,field.layout.actor_radius):return point
	return Vector3.INF

func supply_personally(kind:String,amount:int,lot:="")->void:
	var spot:=station_floor(kind)
	check(kind+" has a physical intake-and-output approach",spot.is_finite())
	if not spot.is_finite():return
	for i in amount:
		bank.collect("level13-personal-"+lot+kind+"-"+str(i),kind)
	field.carry.sync(true)
	park(spot)
	var previous:int=int(j.cooked if kind=="meat" else j["processed_"+kind])
	check(kind+" hand-fed through normal proximity",await until(func():return int(bank.carried[kind])==0,480))
	park(anchor)
	check(kind+" cycles complete without the carrier",await until(func():return int(j.cooked if kind=="meat" else j["processed_"+kind])>=previous+amount,1200))
	inspect_state("processed "+kind)

func at_bay(kind:String)->void:
	park(loop.exchange.pickup_position(kind))
	await ticks(26)

func cash_on_shelf()->int:
	var visible_notes:=0
	for note:Node3D in loop.exchange.shelf_notes:
		if note.is_visible_in_tree():visible_notes+=1
	return visible_notes

func manual()->void:
	check("all three purchased machines start without belts",not bank.complete(P.FOOD_LINE) and not bank.complete(P.SUPPLY_LINE) and Group.all(func(k):return bank.is_machine_owned(k)))
	field.counter.arrival_clock=200.
	for kind:String in Group:await supply_personally(kind,1 if kind=="meat" else 3)
	for kind:String in Group:
		var ready:=Cargo.rack(j,kind)
		var before:int=int(bank.hand_goods()[Cargo.PRODUCT[kind]])
		# The carrier may already have picked up the fixture's one cooked roast
		# while loading the first raw meat. The new roast is still on the output.
		check(kind+" has a physical batch ready",ready>=1 and before+ready>=2)
		var spot:=station_floor(kind)
		if not spot.is_finite():continue
		park(spot)
		await ticks(3)
		check(kind+" entire output lot transferred once",Cargo.rack(j,kind)==0 and int(bank.hand_goods()[Cargo.PRODUCT[kind]])==before+ready)
		park(anchor)
		await ticks(4)
	inspect_state("finished goods on back")
	check("unlimited-quantity ledger rejects fabricated finishes",not forged_stock())
	check("remote shelf withdrawal rejects",not loop.withdraw_goods("meal"))
	park(field.depot.apron.global_position)
	await ticks(5)
	check("mixed goods unload together into individual storehouse bays",bank.house_goods().planks==3 and bank.house_goods().blocks==3 and bank.house_goods().meal==2 and bank.hand_goods()=={"planks":0,"blocks":0,"meal":0,"money":0})
	var stored_stone:int=bank.stored.stone
	await at_bay("meal")
	check("standing at the interior food bay picks up its two prepared servings",j.held_meal==2 and j.product_store.meal==0)
	await at_bay("stone")
	check("standing by actual stored stone retrieves the whole available lot",stored_stone>0 and bank.carried.stone==stored_stone and bank.stored.stone==0)
	await ticks(34)
	check("house leaves intentionally withdrawn goods on the visitor",bank.hand_goods().meal==2 and bank.carried.stone==stored_stone and bank.house_goods().meal==0)
	park(anchor)
	await ticks(3)
	park(field.counter.service_point.global_position)
	await ticks(4)
	check("counter takes a whole prepared stack before buyers arrive",j.counter_stock==2 and j.held_meal==0 and j.served==0 and field.counter.queue.is_empty())
	park(anchor)
	field.counter.arrival_clock=0.
	check("cashier serves two actual queued buyers",await until(func():return j.served==2,2000))
	check("sold meals create two uncollected notes",bank.till_balance()==2 and bank.hand_goods().money==0)
	await ticks(70)
	await supply_personally("meat",2,"second-")
	park(station_floor("meat"))
	await ticks(4)
	park(anchor)
	await ticks(4)
	park(field.depot.apron.global_position)
	await ticks(4)
	await at_bay("meal")
	check("second genuine pair of cooked meals collected from its shelf",j.held_meal==2)
	park(anchor)
	await ticks(2)
	park(field.counter.service_point.global_position)
	await ticks(2)
	check("one approach collects both notes while dropping both meals",j.held_meal==0 and j.counter_stock==2 and j.pocket_cash==2 and bank.till_balance()==0)
	inspect_state("simultaneous meat and money")
	park(anchor)
	await ticks(2)
	park(field.depot.apron.global_position)
	await ticks(4)
	check("two deposited notes appear on the physical warehouse shelf",j.pocket_cash==0 and j.house_cash==2 and cash_on_shelf()==2)
	await at_bay("money")
	check("standing by the notes takes the stored cash",j.pocket_cash==2 and j.house_cash==0)
	await ticks(30)
	check("empty money shelf clears after withdrawal",cash_on_shelf()==0)
	field._checkpoint_lifecycle()
	check("cash retrieval is durable near the warehouse",j.pocket_cash==2 and int(j.withdrawn.get("money",0))==2)

func forged_stock()->bool:
	var fake:Dictionary=bank.snapshot()
	fake.settlement.hand_products.planks+=1
	var separate=field.Inventory.new()
	separate.configure(P.offers())
	return separate.restore(fake)

func cold()->void:
	check("cold restore preserves withdrawn notes, products, and settled sales",j.pocket_cash==2 and j.house_cash==0 and j.served>=2 and bank.house_goods().planks==3 and bank.house_goods().blocks==3)
	park(field.depot.apron.global_position)
	await ticks(60)
	check("cold restore of an empty bay shows zero notes and keeps owner withdrawal",j.pocket_cash==2 and j.house_cash==0 and cash_on_shelf()==0)
	park(anchor)
	await ticks(5)
	park(field.depot.apron.global_position)
	await ticks(4)
	check("returning visibly deposits exactly two loose notes",j.house_cash==2 and j.pocket_cash==0 and cash_on_shelf()==2)
	inspect_state("unloaded cash after reload")

func connected()->void:
	check("old paid lines retain seven historical owned earnings",bank.complete(P.FOOD_LINE) and bank.complete(P.SUPPLY_LINE) and j.served==7 and j.house_cash==7 and bank.till_balance()==0)
	park(field.depot.apron.global_position)
	await ticks(5)
	check("old sales render seven distinct owned notes at paid warehouse after restore",cash_on_shelf()==7)
	await supply_personally("wood",3)
	var from_first:int=bank.hand_goods().planks
	var output_before:int=j.processed_wood
	# Hand-feed a second real load while waiting by the saw. This time the
	# pickup wins the output before the belt can reserve it.
	check("saw returns the unattended lot on real rollers",await until(func():return int(j.product_store.planks)==int(j.processed_wood)-from_first and j.line_load.planks==0,900))
	park(station_floor("wood"))
	for i in 4:bank.collect("personal-extra-"+str(i),"wood")
	field.carry.sync(true)
	check("paid inlet still accepts personal raw and nearby output",await until(func():return j.processed_wood==output_before+4 and bank.hand_goods().planks==from_first+4,1500))
	check("no reconnect or sale was necessary",bank.build_order.count(P.SUPPLY_LINE)==1 and j.served==7)
	inspect_state("manual plus automated")
	park(anchor)
	await ticks(8)

func bulk()->void:
	# This is a synthetic historical stockpile for quantity stress only.
	# Each prepared portion and paid meal is backed by its own raw receipt.
	var pantry:=1207
	var past_sales:=1021
	for i in pantry+past_sales:bank.collect("earned-bulk-meat-"+str(i),"meat")
	bank.carried.meat-=pantry+past_sales
	j.cooked+=pantry+past_sales
	j.served+=past_sales
	j.product_store.meal+=pantry
	field._inventory_changed()
	field.counter.arrival_clock=200.
	check("quantity fixture passed the production object validator",not field.persist_blocked)
	park(field.depot.apron.global_position)
	await ticks(3)
	await at_bay("meal")
	check("withdraws all 1207 physical servings in one visit",j.held_meal==pantry and j.product_store.meal==0)
	park(anchor)
	await ticks(2)
	park(field.counter.service_point.global_position)
	await ticks(2)
	check("one visit exchanges 1207 meals for 1021 already paid notes",j.counter_stock==pantry and j.held_meal==0 and j.served==past_sales and j.pocket_cash==past_sales and bank.till_balance()==0)
	check("large shipments use bounded freight meshes",loop.exchange.flights.size()<=loop.exchange.MAX_FLYING)
	check("empty register cannot pay twice",bank.till_balance()==0)
	inspect_state("bulk receipt")
	park(anchor)
	await ticks(3)
	park(field.depot.apron.global_position)
	await ticks(4)
	check("warehouse receives all 1021 notes and renders bounded shelf stock",j.pocket_cash==0 and j.house_cash==past_sales and cash_on_shelf()==8)
	field._checkpoint_lifecycle()

func run()->void:
	var args:=OS.get_cmdline_user_args()
	var guard=Store.Profile.new()
	if not guard.configure(args):quit(2);return
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	bank=field.inventory
	j=bank.settlement
	loop=field.settlement_loop
	var mode:="manual"
	for arg in args:
		if arg.begins_with("--personal-goods="):mode=arg.trim_prefix("--personal-goods=")
	check("normal paid scene restored",field.field_ready and not field.persist_blocked and bank.snapshot().version==10)
	match mode:
		"manual":park(anchor);await manual()
		"cold":await cold()
		"connected":park(anchor);await connected()
		"bulk":park(anchor);await bulk()
	check("conservation and serialization hold",not field.persist_blocked and bank.restore(bank.snapshot()))
	print("PERSONAL_GOODS ",JSON.stringify({"mode":mode,"checks":results,"visits":visits}))
	field.set_physics_process(false)
	field.sound.stop_playback()
	for i in 12:
		OS.delay_msec(20)
		await process_frame
	field.queue_free()
	await process_frame
	quit(1 if false in results.values() else 0)
