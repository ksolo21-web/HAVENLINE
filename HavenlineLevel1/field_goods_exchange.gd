extends Node3D
## The journal owns the whole batch at receipt time. A bounded number of actual
## game meshes makes each family and its direction legible, even for a large load.
const Rules=preload("res://field_settlement.gd")
const Logistics=preload("res://field_logistics.gd")
const Art=preload("res://field_art.gd")
const Models=preload("res://field_production_transfer.gd")
const Market=preload("res://field_market.gd")
const Cash=preload("res://assets/customer_counter/banded_notes.glb")
# The rear-right rack in camp_storehouse.glb has a horizontal shelf at .745 m.
const CASH_BAY:=Vector3(1.15,.746,-.77)
const MAX_SHELF_NOTES=8
const CASH_SHELF_SCALE := .72
const CASH_FLIGHT_SCALE := 1.16
var cash_bay:=Node3D.new()
var shelf_notes:Array[Node3D]=[]
var last_shelf_count:=-1
# These are the aisle-side edges of the actual woodwork. The lower and
# upper trays share three rack faces, each approachable from either end.
const BAY_EDGE={
	"wood":Vector2(-.68,.50),"planks":Vector2(-.68,.13),
	"stone":Vector2(-.72,-.09),"blocks":Vector2(-.71,-.31),
	"slate":Vector2(-.44,-.31),"meat":Vector2(-.15,-.31),"meal":Vector2(.14,-.31),
	"metal":Vector2(.42,-.31),"money":Vector2(.72,-.27),"coal":Vector2(.70,.32)
}
const SAME_FACE={"wood":"planks","planks":"wood","stone":"blocks","blocks":"stone","meat":"meal","meal":"meat"}
const STOP_SECONDS:=.17
var sampled_bay:=""
var still_seconds:=0.
var responded:=false
var touch_bay:=""
var touch_pointer:=-3
var touch_start:=Vector2.ZERO
const GOODS=["planks","blocks","meal","money"]
const RAW_FOR={"planks":"wood","blocks":"stone","meal":"meat"}
const FLY_SECONDS=.29
const RELEASE_SECONDS=.55
const MAX_PER_STREAM=6
const MAX_FLYING=48
var world
var flights:Array[Dictionary]=[]

func setup(host)->void:
	world=host
	world.carry.storage_protected=world.inventory.settlement.withdrawn
	cash_bay.name="MoneyShelf"
	world.depot.house.add_child(cash_bay)
	cash_bay.position=CASH_BAY
	present_cash()

func present_cash()->void:
	cash_bay.visible=world.depot.house.is_interior_visible()
	var amount:=clampi(int(world.inventory.settlement.house_cash),0,MAX_SHELF_NOTES)
	if amount==last_shelf_count:return
	last_shelf_count=amount
	while shelf_notes.size()<amount:
		var index:=shelf_notes.size()
		var note:Node3D=Cash.instantiate()
		note.scale=Vector3.ONE*CASH_SHELF_SCALE
		note.position=Vector3((index%2-.5)*.259,.124*floori(index/4.),(floori(index/2.)%2-.5)*.145)
		cash_bay.add_child(note)
		shelf_notes.append(note)
	for index in shelf_notes.size():
		shelf_notes[index].visible=index<amount

func _pack_point(actor: Node3D = null)->Vector3:
	var owner: Node3D = actor if is_instance_valid(actor) else world.actor
	return owner.to_global(Vector3(.02,1.10,-.22))

func _shelf(kind:String)->Vector3:
	if kind=="money":return cash_bay.global_position+Vector3.UP*.055
	if kind in Logistics.STORE:return world.settlement_loop.conveyors.shelf_position(kind)
	return world.depot.bins[kind].global_position

func _draw(kind:String,amount:int,local_point:Vector3,to_pack:bool,actor:Node3D=null)->void:
	var count:=mini(mini(amount,MAX_PER_STREAM),MAX_FLYING-flights.size())
	for i in count:
		var mesh:Node3D
		if kind=="money":
			mesh=Cash.instantiate()
			mesh.scale=Vector3.ONE*CASH_FLIGHT_SCALE
		elif RAW_FOR.has(kind):mesh=Models.FINISHED[RAW_FOR[kind]].instantiate()
		else:mesh=Art.make(kind,.46)
		add_child(mesh)
		mesh.hide()
		var launch:Vector3=local_point if to_pack else _pack_point(actor)
		var delay:=RELEASE_SECONDS*i/maxi(1,count-1)
		flights.append({"mesh":mesh,"from":launch,"dock":local_point,"to_pack":to_pack,"actor":actor,"t":-delay})
	set_process(not flights.is_empty())

func draw_worker_transfer(kind: String, amount: int, destination: Vector3, to_pack: bool) -> void:
	_draw(kind,amount,destination,to_pack,world.survivor.actor)

func _process(dt:float)->void:
	for i in range(flights.size()-1,-1,-1):
		var f:=flights[i]
		f.t+=dt
		if f.t<0.:continue
		var unit:Node3D=f.mesh
		unit.show()
		var u:=clampf(float(f.t)/FLY_SECONDS,0.,1.)
		var target:Vector3=_pack_point(f.actor) if f.to_pack else f.dock
		var start:Vector3=f.from
		unit.global_position=start.lerp(target,smoothstep(0.,1.,u))+Vector3.UP*.95*u*(1.-u)
		unit.rotation.y=.35+.7*u
		if u>=1.:
			unit.queue_free()
			flights.remove_at(i)
	if flights.is_empty():set_process(false)

func _change_hand(kind:String,delta:int)->void:
	var j:Dictionary=world.inventory.settlement
	match kind:
		"money":j.pocket_cash+=delta
		"meal":j.held_meal+=delta
		_:j.hand_products[kind]+=delta

func at_loading_area()->bool:
	return world.camp_active and world.field_env.is_inside_camp(world.actor.global_position) and world.depot.at_loading_area(world.actor.global_position)

func pickup_position(kind:String)->Vector3:
	if not BAY_EDGE.has(kind):return Vector3.INF
	var p:Vector2=BAY_EDGE[kind]
	return world.depot.house.to_global(Vector3(p.x,0.,p.y))

func bay_at(at:Vector3)->String:
	if not world.field_env.is_inside_camp(at) or not world.depot.house.on_walkable_aisle(at,float(world.layout.actor_radius)):return ""
	var local:Vector3=world.depot.house.to_local(at)
	var feet:=Vector2(local.x,local.z)
	var best:=.39*.39
	var selected:=""
	for kind:String in BAY_EDGE:
		var distance:float=feet.distance_squared_to(BAY_EDGE[kind])
		if distance<best:
			selected=kind
			best=distance
	return selected

func _shelf_amount(kind:String)->int:
	if kind in world.inventory.KINDS:
		return world.carry.available_on_shelf(kind) if world.inventory.storage_open(kind) else 0
	return int(world.inventory.house_goods().get(kind,0))

func _close_to_stock(kind:String)->bool:
	var feet:Vector3=world.actor.global_position
	return at_loading_area() and world.depot.house.on_walkable_aisle(feet,float(world.layout.actor_radius)) and feet.distance_to(pickup_position(kind))<.72

func _walk_pickup(dt:float)->void:
	var kind:=bay_at(world.actor.global_position)
	if kind!=sampled_bay or world.runner_requested_motion or world.actor.velocity.length_squared()>.09:
		sampled_bay=kind
		still_seconds=0.
		responded=false
		return
	if kind.is_empty() or responded:return
	still_seconds+=dt
	if still_seconds<STOP_SECONDS:return
	responded=true
	if world.inventory.settlement.withdrawn.has(kind):return
	# If one tray on a shared face is empty, the occupant can naturally
	# collect the stocked tray from the same stop.
	if _shelf_amount(kind)==0:kind=SAME_FACE.get(kind,"")
	if not kind.is_empty() and not world.inventory.settlement.withdrawn.has(kind):withdraw(kind)

func _projected_stock(at:Vector2)->String:
	if not world.depot.house.is_interior_visible():return ""
	var best:=22.*22.
	var selected:=""
	for kind:String in BAY_EDGE:
		if not _close_to_stock(kind):continue
		var anchor:=_shelf(kind)+Vector3.UP*.06
		var screen:Vector2=world.camera.unproject_position(anchor)
		var distance:=screen.distance_squared_to(at)
		if distance<best:
			best=distance
			selected=kind
	# Empty trays retain their space, including after a repeated tap.
	return selected if not selected.is_empty() and _shelf_amount(selected)>0 else ""

func observe_stock_pointer(event:InputEvent)->void:
	if event.device==InputEvent.DEVICE_ID_EMULATION:return
	var pointer:=-2
	if event is InputEventScreenTouch:pointer=event.index
	elif event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:pointer=-1
	else:
		if event is InputEventScreenDrag and event.index==touch_pointer and event.position.distance_to(touch_start)>12.:touch_bay=""
		if event is InputEventMouseMotion and touch_pointer==-1 and event.position.distance_to(touch_start)>12.:touch_bay=""
		return
	if event.pressed:
		if touch_pointer!=-3 or (event is InputEventScreenTouch and not world.trial_camera.fingers.is_empty()):
			touch_bay=""
			return
		touch_bay=_projected_stock(event.position)
		if not touch_bay.is_empty():
			touch_pointer=pointer
			touch_start=event.position
		return
	if pointer!=touch_pointer:return
	touch_pointer=-3
	var kind:=touch_bay
	touch_bay=""
	if kind.is_empty() or event.canceled or event.position.distance_to(touch_start)>12. or not _close_to_stock(kind):return
	# The camera/joystick gets the same release event, including on a
	# touchscreen where that first finger also started locomotion.
	responded=true
	withdraw(kind)

func _machine_at(at:Vector3)->String:
	if not world.field_env.is_inside_camp(at):return ""
	var p:=Vector2(at.x,at.z)
	var best:=INF
	var selected:=""
	for raw:String in Rules.KINDS:
		if not world.inventory.is_machine_owned(raw):continue
		var wall:Rect2=world.lakeshore._footprint(0.) if raw=="meat" else world.processors._rect(raw,0.)
		var distance:float=world.Reach.distance_to_rect(p,wall)
		if not wall.has_point(p) and distance<=world.Reach.NEAR and distance<best:
			selected=raw
			best=distance
	if at_loading_area() and world.depot.loading_distance(at)<best:return ""
	return selected

func _pickup_machine(raw:String)->bool:
	var j:Dictionary=world.inventory.settlement
	var quantity:=Logistics.rack(j,raw)
	if quantity<=0:return false
	var product:String=Logistics.PRODUCT[raw]
	var outlet:Vector3=world.lakeshore.cooker_output.global_position if raw=="meat" else world.processors.output_position(raw)
	_change_hand(product,quantity)
	if not world.settlement_loop.commit_receipt("product_pickup",outlet,"pickup_full"):return false
	_draw(product,quantity,outlet,true)
	return true

func _deposit()->void:
	var book=world.inventory
	var j:Dictionary=book.settlement
	var staged:Dictionary={}
	var held:Dictionary=book.hand_goods()
	for kind:String in GOODS:
		var amount:int=maxi(0,int(held[kind])-int(j.withdrawn.get(kind,0)))
		if amount<=0:continue
		staged[kind]=amount
		_change_hand(kind,-amount)
		if kind=="money":j.house_cash+=amount
		else:j.product_store[kind]+=amount
	if staged.is_empty():return
	if not world.settlement_loop.commit_receipt("goods_stored",world.depot.apron.global_position,"deposit_wood"):return
	world.present_character_contact(&"deposit", world.depot.apron.global_position)
	for kind:String in staged:_draw(kind,staged[kind],_shelf(kind),false)

func withdraw(kind:String)->bool:
	if not world.settlement_loop.can_transact() or not BAY_EDGE.has(kind) or not _close_to_stock(kind):return false
	var book=world.inventory
	var j:Dictionary=book.settlement
	var taken:=_shelf_amount(kind)
	if taken<=0:return false
	if kind in book.KINDS:
		book.stored[kind]-=taken
		book.carried[kind]+=taken
	else:
		if kind=="money":j.house_cash-=taken
		else:j.product_store[kind]-=taken
		_change_hand(kind,taken)
	j.withdrawn[kind]=int(j.withdrawn.get(kind,0))+taken
	world.carry.storage_protected=j.withdrawn
	if not world.settlement_loop.commit_receipt("stock_withdrawn",_shelf(kind),"pickup_full"):return false
	_draw(kind,taken,_shelf(kind),true)
	return true

func visit_counter(worker: bool, at: Vector3) -> bool:
	if not world.settlement_loop.can_transact(): return false
	var counter = world.counter
	if not counter.at_service(at): return false
	var journal: Dictionary = world.inventory.settlement
	var delivered := {}
	for kind: String in Market.PRODUCTS:
		if not world.settlement_loop.counter_accepts(kind): continue
		var amount := Market.worker_stock(journal,kind) if worker else int(world.inventory.hand_goods()[kind])
		if amount == 0: continue
		if worker: Market.add_to_worker(journal,kind,-amount)
		else: _change_hand(kind,-amount)
		Market.add_to_counter(journal,kind,amount)
		delivered[kind] = amount
	var cash := maxi(0,world.inventory.till_balance() - counter.cash_in_exchange())
	if delivered.is_empty() and cash == 0: return false
	journal.market.counter_cash -= cash
	if worker: journal.market.worker_cash += cash
	else: journal.pocket_cash += cash
	var cue := "counter_pickup" if cash > 0 else "counter_dropoff"
	var audio := "meal_served" if cash > 0 else "deposit_meat"
	if not world.settlement_loop.commit_receipt(cue,counter.payment_rest.global_position,audio): return false
	if not worker: world.present_character_contact(&"service", counter.payment_rest.global_position)
	var carrier: Node3D = world.survivor.actor if worker else world.actor
	if cash > 0: _draw("money",cash,counter.payment_rest.global_position,true,carrier)
	for kind: String in delivered:
		_draw(kind,int(delivered[kind]),counter.stock_position(kind),false,carrier)
	return true

func collect_station(raw:String)->bool:
	return world.settlement_loop.works.can_operate(raw) and _pickup_machine(raw)

func at_station()->bool:
	var at:Vector3=world.actor.global_position
	var raw:=_machine_at(at)
	return not raw.is_empty() and world.settlement_loop.works.automatic_handoff(raw) and collect_station(raw)

func visit(dt:float)->void:
	var j:Dictionary=world.inventory.settlement
	world.carry.storage_protected=j.withdrawn
	var at:Vector3=world.actor.global_position
	if not at_loading_area() and not j.withdrawn.is_empty():
		j.withdrawn.clear()
		world._inventory_changed()
		if world.persist_blocked:return
	if world.depot.house.on_walkable_aisle(at,float(world.layout.actor_radius)):_walk_pickup(dt)
	else:
		sampled_bay=""
		responded=false
		still_seconds=0.
	if world.counter.at_service(at):visit_counter(false,at)
	elif _machine_at(at).is_empty() and at_loading_area() and world.depot.target_at(at)==world.carry.STOCK:_deposit()
