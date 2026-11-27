extends Node3D
## The same routed centerline drives the real load and its rail hardware.
const Market=preload("res://field_market.gd")
const Rules=preload("res://field_settlement.gd")
const Logistics=preload("res://field_logistics.gd")
const Progress=preload("res://field_progression.gd")
const Art=preload("res://field_art.gd")
const Dish=preload("res://assets/customer_counter/cooked_game_meat.glb")
const Products={
	"planks":preload("res://assets/shore_workshops/finished_planks.glb"),
	"blocks":preload("res://assets/shore_workshops/dressed_block.glb"),
	"meal":Dish,"stored_meal":Dish,"meal_to_store":Dish
}
const LANES=Logistics.LANES
const SPEED:=3.6
const COOKER_HEADWAY:=.62
const SHELVES={"planks":Vector3(-1.15,.39,.25),"blocks":Vector3(-1.15,.39,-.56),"meal":Vector3(.04,.98,-.92)}
var world
var loop
var goods:Dictionary={}
var paths:Dictionary={}
var lengths:Dictionary={}
var shelf_items:Dictionary={}
var purchase_count:=-1
var counter_was_open:=false
var blocked_lane:String=""
var network
var menu=preload("res://field_automation_menu.gd").new()
signal route_changed(lane:String, world_points:PackedVector3Array)

func setup(host,settlement)->void:
	world=host
	loop=settlement
	name="PaidCampConveyors"
	world.opening_hud.add_child(menu)
	menu.install(world)
	network=preload("res://field_conveyor_network.gd").new()
	add_child(network)
	network.install(world)
	for lane:String in LANES:
		var item:Node3D=Products[lane].instantiate() if Products.has(lane) else Art.make(lane,.45)
		item.name=lane.capitalize()+"InTransit"
		add_child(item)
		item.hide()
		goods[lane]=item
	for product:String in SHELVES:
		var bay:=Node3D.new()
		bay.name=product.capitalize()+"Storage"
		world.depot.house.add_child(bay)
		bay.position=SHELVES[product]
		shelf_items[product]=bay
		for i in 4:
			var item:Node3D=Products[product].instantiate()
			bay.add_child(item)
			item.scale*=.40
			item.position=Vector3(0,(i/2)*.095,(i%2-.5)*.17)
			item.hide()

func buffer_position(slot:int=0)->Vector3:
	return network.counter_buffer_position(slot) if world.inventory.complete(Progress.FOOD_LINE) else world.counter.delivery_position(slot)

func line_live(lane:String)->bool:
	return Logistics.allowed(lane,world.inventory.build_order)

func _layout_changed()->void:
	purchase_count=-1

func shelf_position(product:String)->Vector3:
	return world.depot.house.to_global(SHELVES[product])

func refresh_paths()->void:
	if not network:return
	var layout=world.camp_layout
	if not layout.layout_changed.is_connected(_layout_changed):layout.layout_changed.connect(_layout_changed)
	var count:int=world.inventory.build_order.size()
	if purchase_count==count and counter_was_open==world.counter.active:return
	purchase_count=count
	counter_was_open=world.counter.active
	var live:Array[String]=[]
	for lane:String in LANES:
		if line_live(lane):live.append(lane)
	var previous_aisles = network.aisles
	var physical:Dictionary=network.rebuild(live)
	if world.field_ready and network.aisles and previous_aisles != network.aisles:
		# The last payment can install a bench or rail under the person paying.
		# Check only on an actual rebuild; retain the live joystick gesture.
		world.clear_installed_floor(network.aisles)
	blocked_lane=""
	for lane:String in LANES:
		var route:PackedVector3Array=physical.get(lane,PackedVector3Array()).duplicate()
		if route.size()>=2:
			var local:PackedVector3Array=network.local_transfer(lane)
			if local.size()>1:
				if lane in Logistics.RAW or lane=="stored_meal":
					local.append_array(route.slice(1))
					route=local
				else:
					route.append_array(local.slice(1))
		if lane in live and route.size()<2 and blocked_lane.is_empty():blocked_lane=lane
		paths[lane]=route
		var length:=0.
		for i in range(1,route.size()):length+=route[i].distance_to(route[i-1])
		lengths[lane]=length
		route_changed.emit(lane,route)

func _sample(lane:String,progress:float)->Vector3:
	var route:PackedVector3Array=paths[lane]
	var target:float=progress*lengths[lane]
	for i in range(1,route.size()):
		var section:=route[i].distance_to(route[i-1])
		if target<=section and section>.00001:return route[i-1].lerp(route[i],target/section)
		target-=section
	return route[-1]

func _place_cargo(lane:String,unit:Node3D,t:float)->void:
	unit.global_position=_sample(lane,t)
	var radius:float=.055/lengths[lane]
	var tangent:=_sample(lane,minf(1.,t+radius))-_sample(lane,maxf(0.,t-radius))
	var flat:=Vector3(tangent.x,0,tangent.z)
	# A vertical dock lift translates the carrier while keeping it upright.
	if flat.length_squared()<.00001:return
	if absf(tangent.y)>flat.length():tangent=flat
	var long_axis:=tangent.normalized()
	var across:=long_axis.cross(Vector3.UP).normalized()
	unit.global_basis=Basis(long_axis,across.cross(long_axis).normalized(),across)

func _demand(j:Dictionary)->int:
	var orders:=0
	for guest in world.counter.queue:
		if int(guest.order)<=int(j.served):continue
		if int(guest.order)==int(j.market.order.get("id",0)):
			orders+=int(j.market.order.goods.get("meal",0))
		else:
			orders+=1
	var promised:int=j.counter_stock+j.line_load.meal+j.line_load.stored_meal
	return maxi(0,orders-promised)

func unclaimed_orders()->int:
	return _demand(world.inventory.settlement)

func _buffer_needs_meal(j:Dictionary)->bool:
	return world.counter.active and j.counter_stock < Rules.COUNTER_RACK_CAPACITY and not Logistics.merge_busy(j)

func _launch(lane:String)->bool:
	var book=world.inventory
	var j:Dictionary=book.settlement
	if not line_live(lane) or lengths.get(lane,0.)<=0. or j.line_load[lane]!=0:return false
	if lane=="meal" or lane=="meal_to_store":
		# The two destinations share the cooker's physical discharge throat.
		var other:="meal_to_store" if lane=="meal" else "meal"
		if j.line_load[other]>0 and float(j.line_progress[other])*float(lengths.get(other,0.))<COOKER_HEADWAY:return false
	if lane in Logistics.RAW:
		if lane=="wood" and j.line_load.stone>0 or lane=="stone" and j.line_load.wood>0:return false
		if world.carry.available_on_shelf(lane)<1 or not loop.available_to_feeder(lane):return false
		book.stored[lane]-=1
	elif lane in Logistics.INPUT_FOR:
		if lane=="planks" and j.line_load.blocks>0 or lane=="blocks" and j.line_load.planks>0:return false
		if Logistics.rack(j,Logistics.INPUT_FOR[lane])<1 or not Logistics.receiving_space(j,lane):return false
	elif lane=="meal_to_store":
		if Rules.waiting_meals(j)<1 or not Logistics.receiving_space(j,"meal"):return false
		# A full buffer, an occupied merge or a disconnected express path
		# diverts the next roast to storage. Orders decide the sale only.
		if lengths.get("meal",0.)>0. and _buffer_needs_meal(j):return false
	else:
		if not _buffer_needs_meal(j):return false
		if lane=="stored_meal":
			if j.product_store.meal<1:return false
			j.product_store.meal-=1
		elif Rules.waiting_meals(j)<1:return false
	j.line_load[lane]=1
	j.line_progress[lane]=0.
	j.dispatch_cursor=(LANES.find(lane)+1)%LANES.size()
	return loop.commit_receipt("conveyor_dispatch",paths[lane][0],"carry")

func _arrive(lane:String)->bool:
	var j:Dictionary=world.inventory.settlement
	if j.line_load[lane]!=1 or j.line_progress[lane]<1.:return false
	if lane in Logistics.RAW:
		if world.encounters.is_machine_down(lane) or j.hoppers[lane]>=Rules.HOPPER_CAPACITY:return false
		j.hoppers[lane]+=1
	elif lane=="meal" or lane=="stored_meal":
		if j.counter_stock>=Rules.COUNTER_RACK_CAPACITY:return false
		Market.add_to_counter(j,"meal",1)
	else:
		var product: String="meal" if lane=="meal_to_store" else lane
		if j.product_store[product]>=Logistics.SPACE[product]:return false
		j.product_store[product]+=1
	j.line_load[lane]=0
	j.line_progress[lane]=0.
	var kind:String=Logistics.INPUT_FOR.get(lane,lane if lane in Logistics.RAW else "meat")
	return loop.commit_receipt("conveyor_delivery",paths[lane][-1],"deposit_"+kind)

func advance(dt:float)->void:
	if not world.inventory.complete(Progress.SUPPLY_LINE) and not world.inventory.complete(Progress.FOOD_LINE):
		present() # Show hand-delivered dishes and warehouse products before automation.
		return
	refresh_paths()
	var cursor:int=world.inventory.settlement.dispatch_cursor
	for i in LANES.size():
		var lane:String=LANES[(cursor+i)%LANES.size()]
		if world.persist_blocked:break
		if not line_live(lane) or lengths.get(lane,0.)<=0.:continue
		var j:Dictionary=world.inventory.settlement
		if j.line_load[lane]==0:_launch(lane)
		elif dt>0:
			j.line_progress[lane]=minf(1.,float(j.line_progress[lane])+SPEED*dt/float(lengths[lane]))
			if j.line_progress[lane]>=1.:_arrive(lane)
	present()

func present()->void:
	var j:Dictionary=world.inventory.settlement
	for lane:String in LANES:
		var unit:Node3D=goods[lane]
		unit.visible=j.line_load[lane]>0 and lengths.get(lane,0.)>0.
		if unit.visible:_place_cargo(lane,unit,float(j.line_progress[lane]))
	network.present_lifts(goods)
	network.set_buffer_full(j.counter_stock>=Rules.COUNTER_RACK_CAPACITY)
	for product:String in SHELVES:
		var bay:Node3D=shelf_items[product]
		bay.visible=world.depot.house.is_interior_visible()
		for i in bay.get_child_count():bay.get_child(i).visible=i<int(j.product_store[product])
