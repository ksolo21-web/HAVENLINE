extends "res://tests/qa_paid_conveyors.gd"
## This is a cold pair: stage an eight-place machine from a real field stock
## and earned drops, then reload that exact file, relocate it and sell it down.
var j:Dictionary
var belts
var observations:Dictionary={}
func _visible() -> Dictionary:
	var slots:={}
	for unit:Node3D in field.counter.public_piles.meal:
		if unit.visible:slots[str(unit.global_position.snapped(Vector3.ONE*.005))]=true
	return slots
func run() -> void:
	var profile=Store.Profile.new()
	if not profile.configure(OS.get_cmdline_user_args()):quit(2);return
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	field.set_physics_process(false)
	var loop=field.settlement_loop
	belts=loop.conveyors;belts.refresh_paths()
	j=field.inventory.settlement
	var cold:bool="--receiver=cold" in OS.get_cmdline_user_args()
	field.counter.arrival_clock=180.
	var wet:bool=not field.persist_blocked
	check("loaded a real paid receiver with eight individual places",wet and belts.buffer_capacity()==8 and belts.network.routes.size()==8)
	if not cold:
		if field.enemies.is_empty():field.encounters._add(Vector3(14.8,0.,1.5),false,740,Vector3(14.8,0.,1.5))
		var wolf=field.enemies[0]
		park(wolf.global_position)
		for turn in 14:
			if wolf.hp==0:break
			wolf.take_swirl_hit(9000+turn)
		var previous_meat:int=field.inventory.carried.meat
		for token:String in field.drops.keys():
			if not field.drops.has(token) or field.drops[token].kind!="meat":continue
			park(field.drops[token].at)
			field._step_drops(.36)
		check("collected actual field drops from a defeated wolf",wolf.hp==0 and field.inventory.carried.meat>=previous_meat+2)
		for step in 45:field.carry.advance(1./60.)
		park(field.depot.bins.meat.global_position)
		for step in 130:
			field.carry.deposit_storage("meat")
			field.carry.advance(1./60.)
		park(Vector3(3.,0,-3.1))
		var observed_rank:={}
		var delivery_errors:=[]
		for tick in 6300:
			var before:int=j.counter_stock
			for lane:String in ["meal","stored_meal"]:
				if j.line_load[lane] and j.line_progress[lane]>.98:
					var unit:Node3D=belts.goods[lane]
					var at:Vector3=field.counter.stock_position("meal",before)
					if unit.visible:
						var gap:=unit.global_position.distance_to(at)
						observed_rank[before]=minf(float(observed_rank.get(before,INF)),gap)
			loop.advance_unattended(1./60.)
			field.counter.show_goods(j)
			if j.counter_stock>before:
				var land:Vector3=field.counter.stock_position("meal",before)
				var hit:=false
				for event:Dictionary in field.events:
					if event.event=="conveyor_delivery" and Vector2(event.x,event.z).distance_to(Vector2(land.x,land.z))<.015:hit=true;break
				if not hit:delivery_errors.append(before)
			if j.counter_stock==8 and j.product_store.meal>=2 and j.line_load.meal_to_store==0:break
		check("eight earned servings accumulate without customers or a crew",j.counter_stock==8 and j.served==1 and field.counter.queue.is_empty() and _visible().size()==8)
		check("all eight real arrivals end at their own stationary stock slot",delivery_errors.is_empty())
		check("working gate holds the full rack and diverts further cooked stock into the house",belts.network.red_lamp.visible and not belts.network.green_lamp.visible and j.product_store.meal>=2 and j.line_load.meal==0)
		check("no source was fabricated and reserve plus table matches cooked less paid",j.counter_stock+j.product_store.meal+j.served==j.cooked)
		observations["minimum_last_transport_distance_m"]=observed_rank
		observations["missing_receipt"]=delivery_errors
		field._checkpoint_lifecycle()
	else:
		field.counter.show_goods(j)
		check("cold reload restores the same eight occupied slots and warehouse overflow",j.counter_stock==8 and j.product_store.meal>=2 and _visible().size()==8 and j.cooked==j.counter_stock+j.product_store.meal+j.served)
		var saved:Vector2=field.camp_layout.center("north_counter")
		var total:int=j.counter_stock+j.product_store.meal
		check("a full machine can be moved into a constrained paid counter bay",field.camp_layout.relocate("north_counter",Vector2(-2.,saved.y)))
		belts.refresh_paths()
		check("narrow bay keeps its two-place feeder and all pre-existing manually deep stock",belts.buffer_capacity()==2 and j.counter_stock==8 and belts.network.routes.size()==8)
		check("original workshop bay can be restored",field.camp_layout.relocate("north_counter",saved))
		belts.refresh_paths()
		check("return to the large receiver restores all eight physical positions",belts.buffer_capacity()==8 and j.counter_stock==8)
		var paid:int=j.served
		var credit:int=field.inventory.till_balance()
		var sold_records:={}
		var meal_count:=0
		var priced:=0
		var resumed:=false
		var observed_customer:=false
		field.counter.arrival_clock=0.
		for tick in 10300:
			var previous:int=j.served
			var receipt:Dictionary=j.market.order.duplicate(true)
			loop.advance(1./60.)
			if j.served>previous and receipt.get("id",-1)==j.served:
				sold_records[j.served]=receipt
				meal_count+=int(receipt.goods.get("meal",0))
				priced+=int(receipt.price)
			if belts.goods.stored_meal.visible:resumed=true
			if field.counter.sale_committed and is_instance_valid(field.counter.cash) and is_instance_valid(field.counter.meal):observed_customer=true
			if j.counter_stock==0 and j.market.sold.meal==j.cooked and j.product_store.meal==0:break
		check("warehouse feed restarted when paid space opened",resumed)
		check("every staged and overflow serving was sold and paid once",j.served==paid+sold_records.size() and meal_count==total and j.market.sold.meal==j.cooked and j.counter_stock==0 and j.product_store.meal==0 and field.inventory.till_balance()==credit+priced and observed_customer)
		observations["starting_meals"]=total;observations["meal_units_sold"]=meal_count;observations["paid_receipts"]=sold_records;observations["cash_delta"]=field.inventory.till_balance()-credit
	check("published journal remains valid and recoverable",not field.persist_blocked and field.inventory.restore(field.inventory.snapshot()))
	observations["cold"]=cold;observations["snapshot"]=snapshot_values()
	print("PRODUCTION_RECEIVER_QA ",JSON.stringify({"checks":results,"readings":observations}))
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 3:await process_frame
	quit(int(false in results.values()))
