extends Node3D
## The journal owns every physical load. Meshes follow its normalized travel
## distance so a restart or a moved station cannot spend a bundle twice.
const Rules = preload("res://field_settlement.gd")
const Progress = preload("res://field_progression.gd")
const Art = preload("res://field_art.gd")
const Dish = preload("res://assets/customer_counter/cooked_game_meat.glb")
const Route = preload("res://field_conveyor_route.gd")
const LANES := ["wood","stone","meat","meal"]
const SPEED := 3.6
var world
var loop
var goods := {}
var paths := {}
var lengths := {}
# Visual rail modules can subscribe without becoming owners of transactional cargo.
signal route_changed(lane:String, world_points:PackedVector3Array)
var purchase_count:=-1
var counter_connected:=false
var menu=preload("res://field_automation_menu.gd").new()
var counter_rack:Array[Node3D]=[]

func setup(host,settlement) -> void:
	world=host
	loop=settlement
	name="PaidCampConveyors"
	world.opening_hud.add_child(menu)
	menu.install(world)
	for lane: String in LANES:
		var item:Node3D = Dish.instantiate() if lane=="meal" else Art.make(lane,.45)
		item.name=lane.capitalize()+"InTransit"
		add_child(item)
		item.hide()
		goods[lane]=item
	for i in Rules.COUNTER_RACK_CAPACITY:
		var portion:Node3D=Dish.instantiate()
		world.counter.add_child(portion)
		portion.position=world.counter.to_local(world.counter.delivery_position(i))
		portion.hide()
		counter_rack.append(portion)

func line_live(lane:String) -> bool:
	if lane=="meal":return world.inventory.complete(Progress.FOOD_LINE) and world.counter.active
	return world.inventory.complete(Progress.SUPPLY_LINE) and world.inventory.is_machine_owned(lane)

func _stops(lane:String) -> PackedVector3Array:
	var cook=world.lakeshore
	var shop=world.processors
	if lane=="meal":
		var output:Vector3=cook.cooker_output.global_position
		var apron:Vector3=cook.output_apron_position() if cook.has_method("output_apron_position") else cook.OUTPUT_APRON
		return PackedVector3Array([output,apron,world.counter.service_point.global_position,world.counter.delivery_position(0)])
	var bin:Vector3=world.depot.bins[lane].global_position
	var entrance:Vector3=world.depot.apron.global_position
	var port:Vector3
	var receive:Vector3
	if lane=="meat":
		port=cook.apron_position() if cook.has_method("apron_position") else cook.APRON
		receive=cook.cooker_input.global_position
	else:
		port=shop.apron_position(lane) if shop.has_method("apron_position") else shop.APRONS[lane]
		receive=shop.input_position(lane)
	return PackedVector3Array([bin,entrance,port,receive])

func _layout_changed() -> void:
	purchase_count=-1

func refresh_paths() -> void:
	var layout=world.camp_layout
	if not layout.layout_changed.is_connected(_layout_changed):
		layout.layout_changed.connect(_layout_changed)
	var count:int=world.inventory.build_order.size()
	if purchase_count==count and counter_connected==world.counter.active:return
	purchase_count=count
	counter_connected=world.counter.active
	var obstacles:Array[Rect2]=layout.obstacles()
	var court:Rect2=layout.bounds().grow(-.18)
	for lane:String in LANES:
		if not line_live(lane):
			goods[lane].hide()
			continue
		var ports:=_stops(lane)
		var route:=Route.connect_ports(ports,obstacles,court)
		if lane!="meal" and route.size()>1:
			# Stock first enters the central aisle inside the house, then
			# passes the two sliding leaves at the front threshold.
			route.insert(1,world.depot.house.to_global(Vector3(0.,.44,.42)))
		paths[lane]=route
		var length:=0.
		for i in range(1,route.size()):length+=route[i].distance_to(route[i-1])
		lengths[lane]=length
		route_changed.emit(lane,route)

func _sample(lane:String,progress:float) -> Vector3:
	var route:PackedVector3Array=paths[lane]
	var target:float=progress*lengths[lane]
	for i in range(1,route.size()):
		var section:=route[i].distance_to(route[i-1])
		if target<=section and section>.00001:return route[i-1].lerp(route[i],target/section)
		target-=section
	return route[route.size()-1]

func _launch(lane:String) -> bool:
	var book=world.inventory
	var journal:Dictionary=book.settlement
	if journal.line_load[lane]!=0:return false
	if lane=="meal":
		if Rules.waiting_meals(journal)<=0 or journal.counter_stock>=Rules.COUNTER_RACK_CAPACITY:return false
	else:
		if world.carry.available_on_shelf(lane)<1 or not loop.available_to_feeder(lane):return false
		book.stored[lane]-=1
	journal.line_load[lane]=1
	journal.line_progress[lane]=0.
	# Persist dispatch before allowing movement or another local claimant.
	return loop.commit_receipt("conveyor_dispatch",paths[lane][0],"carry")

func _arrive(lane:String) -> bool:
	var journal:Dictionary=world.inventory.settlement
	if journal.line_load[lane]!=1 or journal.line_progress[lane]<1.:return false
	if lane=="meal":
		if journal.counter_stock>=Rules.COUNTER_RACK_CAPACITY:return false
		journal.counter_stock+=1
	else:
		if journal.hoppers[lane]>=Rules.HOPPER_CAPACITY:return false
		journal.hoppers[lane]+=1
	journal.line_load[lane]=0
	journal.line_progress[lane]=0.
	var route:PackedVector3Array=paths[lane]
	return loop.commit_receipt("conveyor_delivery",route[-1],"deposit_meat" if lane=="meal" else "deposit_"+lane)

func advance(dt:float) -> void:
	if not world.inventory.complete(Progress.SUPPLY_LINE) and not world.inventory.complete(Progress.FOOD_LINE):return
	refresh_paths()
	for lane:String in LANES:
		if world.persist_blocked:break
		if not line_live(lane) or lengths.get(lane,0.)<=0.:continue
		var journal:Dictionary=world.inventory.settlement
		if journal.line_load[lane]==0:
			if not _launch(lane):continue
		elif dt>0:
			journal.line_progress[lane]=minf(1.,float(journal.line_progress[lane])+SPEED*dt/float(lengths[lane]))
			if journal.line_progress[lane]>=1.:_arrive(lane)
	present()

func present() -> void:
	var journal:Dictionary=world.inventory.settlement
	for lane:String in LANES:
		var unit:Node3D=goods[lane]
		unit.visible=line_live(lane) and journal.line_load[lane]>0 and lengths.get(lane,0.)>0.
		if not unit.visible:continue
		unit.global_position=_sample(lane,float(journal.line_progress[lane]))
		if lane!="meal":
			var in_house:Vector3=world.depot.house.to_local(unit.global_position)
			if absf(in_house.x)<1.65 and in_house.z>-1.15 and in_house.z<1.65:
				world.depot.house.supply_door_hold=.5
	var stock:int=journal.counter_stock
	if world.counter.belt_serving and not world.counter.sale_committed:stock-=1
	for i in counter_rack.size():
		counter_rack[i].visible=i<stock and world.counter.active
