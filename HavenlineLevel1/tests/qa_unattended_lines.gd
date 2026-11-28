extends "res://tests/qa_paid_conveyors.gd"
## A saved paid camp must run with the public counter empty, player parked,
## and no rescued worker. The second launch consumes the actual first save.
const Logistics = preload("res://field_logistics.gd")

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var profile = Store.Profile.new()
	if not profile.configure(args):
		quit(2)
		return
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera=field.camera
	origin=root.get_visible_rect().size*Vector2(.30,.72)
	var book=field.inventory
	var j:Dictionary=book.settlement
	var b=field.settlement_loop.conveyors
	var mode := "stock"
	for arg:String in args:
		if arg.begins_with("--automation="):mode=arg.trim_prefix("--automation=")
	b.refresh_paths()
	park(Vector3(1.15,0.,.9))
	var origin_at: Vector3 = field.actor.global_position
	field.counter.arrival_clock=180.
	check("normal paid scene opened in isolated save",field.field_ready and not field.persist_blocked and field.counter.queue.is_empty())
	check("no survivor or player carries production freight",not j.rescued and j.worker_supply=="" and j.held_meal==0 and j.worker_meal==0)
	var observations := {"mode":mode,"initial":snapshot_values(),"player_xz":[origin_at.x,origin_at.z]}
	if mode=="supply":
		if not book.complete(P.SUPPLY_LINE):await buy(P.SUPPLY_LINE)
		park(origin_at)
		check("only paid workshop supply installed",book.complete(P.SUPPLY_LINE) and not book.complete(P.FOOD_LINE))
		check("supply returns every purchased machine output",b.line_live("planks") and b.line_live("blocks") and b.line_live("meal_to_store") and not b.line_live("stored_meal"))
		var finished := await until(func():return j.product_store.meal==6 and j.product_store.planks==3 and j.product_store.blocks==3,6000)
		check("idle camp supplied, processed and stored all three types",finished and book.stored.wood==0 and book.stored.stone==0 and book.stored.meat==0)
		check("the full cold shelf leaves a surplus serving at the cooker",j.cooked==7 and Logistics.rack(j,"meat")+j.line_load.meal_to_store==1)
		check("no counter line creates an unpaid sale",j.served==0 and j.counter_stock==0 and field.counter.queue.is_empty())
	elif mode=="stock":
		check("meal-only install automatically feeds and empties the cooker",b.line_live("meat") and b.line_live("meal_to_store") and b.line_live("stored_meal") and not b.line_live("wood"))
		var expected:=mini(7,b.buffer_capacity())
		var staged := await until(func():return j.counter_stock==expected and j.product_store.meal==7-expected and j.cooked==7,6500)
		check("unattended public counter automatically stocks all available portions up to its capacity",staged and field.counter.queue.is_empty() and field.counter.sale_order==0 and j.served==0)
		check("unattended serial line accounts for six raw portions and the original roast",book.stored.meat==0 and j.hoppers.meat==0 and j.line_load==Logistics.TRANSIT and Logistics.rack(j,"meat")==0 and j.product_store.meal+j.counter_stock==7)
		check("unconnected timber and stone remain untouched",book.stored.wood==3 and book.stored.stone==3)
		await ticks(90)
		check("counter holds stock without selling or dispatching twice",j.counter_stock==mini(7,b.buffer_capacity()) and j.product_store.meal==7-mini(7,b.buffer_capacity()) and j.served==0)
		field._checkpoint_lifecycle()
	elif mode=="cold":
		check("cold launch restored the actual receiver and separate shelf",j.counter_stock==mini(7,b.buffer_capacity()) and j.product_store.meal==7-mini(7,b.buffer_capacity()) and j.cooked==7 and j.served==0)
		field.counter.arrival_clock=0.
		check("seven real customers collected and paid once",await until(func():return j.served==7,7400))
		await ticks(120)
		check("served inventory balanced after the restart",j.cooked==j.served and j.product_store.meal==0 and j.counter_stock==0 and j.line_load==Logistics.TRANSIT and Logistics.rack(j,"meat")==0)
		check("real cashier payment event occurred",field.events.any(func(e):return e.event=="meal_served"))
	else:
		check("recognized scenario",false)
	check("player remained at the original position",field.actor.global_position.distance_to(origin_at)<.025)
	check("no helper or player handled the connected loads",not j.rescued and j.worker_supply=="" and j.worker_meal==0 and j.held_meal==0 and field.settlement_loop.works.active=="")
	check("all persisted inventory invariants hold",not field.persist_blocked and book.restore(book.snapshot()))
	observations["final"]=snapshot_values()
	observations["checks"]=results
	print("UNATTENDED_QA ",JSON.stringify(observations))
	field.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(1 if false in results.values() else 0)
