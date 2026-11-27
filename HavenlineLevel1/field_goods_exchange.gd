extends Node3D
## The journal owns the whole batch at receipt time. A bounded number of actual
## game meshes makes each family and its direction legible, even for a large load.
const Rules=preload("res://field_settlement.gd")
const Logistics=preload("res://field_logistics.gd")
const Art=preload("res://field_art.gd")
const Models=preload("res://field_production_transfer.gd")
const Cash=preload("res://assets/customer_counter/banded_notes.glb")
# The rear-right rack in camp_storehouse.glb has a horizontal shelf at .745 m.
const CASH_BAY:=Vector3(1.15,.746,-.77)
const MAX_SHELF_NOTES=8
var cash_bay:=Node3D.new()
var shelf_notes:Array[Node3D]=[]
var last_shelf_count:=-1
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
		note.scale=Vector3.ONE*.60
		note.position=Vector3((index%2-.5)*.222,.102*floori(index/4.),(floori(index/2.)%2-.5)*.135)
		cash_bay.add_child(note)
		shelf_notes.append(note)
	for index in shelf_notes.size():
		shelf_notes[index].visible=index<amount

func _pack_point()->Vector3:
	return world.actor.to_global(Vector3(.02,1.10,-.22))

func _shelf(kind:String)->Vector3:
	if kind=="money":return cash_bay.global_position+Vector3.UP*.055
	if kind in Logistics.STORE:return world.settlement_loop.conveyors.shelf_position(kind)
	return world.depot.bins[kind].global_position

func _draw(kind:String,amount:int,local_point:Vector3,to_pack:bool)->void:
	var count:=mini(mini(amount,MAX_PER_STREAM),MAX_FLYING-flights.size())
	for i in count:
		var mesh:Node3D
		if kind=="money":mesh=Cash.instantiate()
		elif RAW_FOR.has(kind):mesh=Models.FINISHED[RAW_FOR[kind]].instantiate()
		else:mesh=Art.make(kind,.46)
		add_child(mesh)
		mesh.hide()
		var launch:Vector3=local_point if to_pack else _pack_point()
		var delay:=RELEASE_SECONDS*i/maxi(1,count-1)
		flights.append({"mesh":mesh,"from":launch,"dock":local_point,"to_pack":to_pack,"t":-delay})
	set_process(not flights.is_empty())

func _process(dt:float)->void:
	for i in range(flights.size()-1,-1,-1):
		var f:=flights[i]
		f.t+=dt
		if f.t<0.:continue
		var unit:Node3D=f.mesh
		unit.show()
		var u:=clampf(float(f.t)/FLY_SECONDS,0.,1.)
		var target:Vector3=_pack_point() if f.to_pack else f.dock
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
	for kind:String in staged:_draw(kind,staged[kind],_shelf(kind),false)

func withdraw(kind:String,amount:int)->bool:
	if not world.settlement_loop.can_transact() or not at_loading_area() or amount<0:return false
	var book=world.inventory
	var j:Dictionary=book.settlement
	var from_house:int=0
	if kind in book.KINDS:
		if not book.storage_open(kind):return false
		from_house=world.carry.available_on_shelf(kind)
	elif kind in GOODS:from_house=int(book.house_goods()[kind])
	else:return false
	var taken:=from_house if amount==0 else mini(from_house,amount)
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

func _counter()->void:
	var c=world.counter
	var j:Dictionary=world.inventory.settlement
	var meals:int=j.held_meal
	# An order already in the player's hand has a dedicated hand-to-guest animation.
	if c.sale_order!=0 and not c.belt_serving and not c.worker_serving and not c.sale_committed: meals=maxi(0,meals-1)
	# The customer's newly paid note travels to the till; older notes are free
	# to collect on this same approach while the dinner moves the other way.
	var cash:int=world.inventory.till_balance()-c.cash_in_exchange()
	if meals==0 and cash<=0:return
	j.held_meal-=meals
	j.counter_stock+=meals
	j.pocket_cash+=maxi(0,cash)
	if not world.settlement_loop.commit_receipt("counter_pickup" if cash>0 else "counter_dropoff",c.payment_rest.global_position,"meal_served" if cash>0 else "deposit_meat"):return
	if cash>0:_draw("money",cash,c.payment_rest.global_position,true)
	if meals>0:_draw("meal",meals,c.delivery_position(),false)

func at_station()->bool:
	var at:Vector3=world.actor.global_position
	var raw:=_machine_at(at)
	return not raw.is_empty() and _pickup_machine(raw)

func visit()->void:
	var j:Dictionary=world.inventory.settlement
	world.carry.storage_protected=j.withdrawn
	var at:Vector3=world.actor.global_position
	if not at_loading_area() and not j.withdrawn.is_empty():
		j.withdrawn.clear()
		world._inventory_changed()
		if world.persist_blocked:return
	if world.counter.at_service(at):_counter()
	elif _machine_at(at).is_empty() and at_loading_area() and world.depot.target_at(at)==world.carry.STOCK:_deposit()
