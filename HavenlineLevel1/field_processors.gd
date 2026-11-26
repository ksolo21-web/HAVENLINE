extends Node3D
## Workshop state is presentation only. The settlement ledger owns all goods.
const CENTERS = {"wood":Vector3(-17.,0.,20.5),"stone":Vector3(-20.4,0.,24.9)}
const APRONS = {"wood":Vector3(-15.19,0.,21.2),"stone":Vector3(-18.57,0.,25.55)}
const MACHINES = {
	"wood":preload("res://assets/shore_workshops/shore_saw_bench.glb"),
	"stone":preload("res://assets/shore_workshops/shore_quarry_drill.glb"),
}
const PRODUCTS = {
	"wood":preload("res://assets/shore_workshops/finished_planks.glb"),
	"stone":preload("res://assets/shore_workshops/dressed_block.glb"),
}
const INPUT = {"wood":Vector3(1.13,1.25,-.14),"stone":Vector3(.27,.29,.46)}
const OUTPUT = {"wood":Vector3(-.91,.568,.81),"stone":Vector3(-.99,.378,-.05)}
const FOOTPRINT = {"wood":Rect2(-1.38,-.73,2.76,1.81),"stone":Rect2(-1.34,-.91,2.77,1.80)}
var world:Node3D
var wheels:Dictionary={}
var trays:Dictionary={}
var balances:Dictionary={"wood":-1,"stone":-1}
var active_kind:=""
var phase:=0.

func setup(host:Node3D) -> void:
	world=host
	name="ShoreWorkshops"
	for kind:String in CENTERS:
		var rig:Node3D=MACHINES[kind].instantiate()
		rig.name="SawBench" if kind=="wood" else "QuarryDrill"
		add_child(rig)
		rig.position=CENTERS[kind]+Vector3.UP*.025
		var head:Node3D=rig.find_child("SawRotor" if kind=="wood" else "DrillHead",true,false)
		head.position=Vector3(.06,1.15,.56) if kind=="wood" else Vector3(0,.96,.19)
		wheels[kind]=head
		var base:=StaticBody3D.new()
		base.name="MachineGuard"
		rig.add_child(base)
		var shape:=CollisionShape3D.new()
		var box:=BoxShape3D.new()
		var rect:Rect2=FOOTPRINT[kind]
		var height:=1.66 if kind=="wood" else 2.82
		box.size=Vector3(rect.size.x,height,rect.size.y)
		shape.position=Vector3(rect.get_center().x,height*.5,rect.get_center().y)
		shape.shape=box
		base.add_child(shape)
		var stock:=Node3D.new()
		stock.name="Outfeed"
		rig.add_child(stock)
		stock.position=OUTPUT[kind]
		trays[kind]=stock
	sync_outputs()

func input_position(kind:String) -> Vector3:
	return to_global(CENTERS[kind]+INPUT[kind]+Vector3.UP*.025)

func output_position(kind:String) -> Vector3:
	return trays[kind].global_position

func at_station(at:Vector3) -> String:
	var p:=Vector2(at.x,at.z)
	for kind:String in APRONS:
		var apron:Vector3=APRONS[kind]
		if p.distance_to(Vector2(apron.x,apron.z))<=1.12 and not _rect(kind,0.).has_point(p):
			return kind
	return ""

func set_active_kind(kind:String) -> void:
	if kind==active_kind or (kind!="" and not CENTERS.has(kind)):return
	active_kind=kind
	phase=0.
	if wheels.has("stone"):
		wheels.stone.position.y=.96
		wheels.stone.rotation.y=0.

func sync_outputs() -> void:
	if not world or not world.get("inventory"):return
	var settlement:Dictionary=world.inventory.settlement
	for kind:String in CENTERS:
		var count:=int(settlement.get("processed_"+kind,0))
		if balances[kind]==count:continue
		balances[kind]=count
		var stock:Node3D=trays[kind]
		# Four representative lots fit the bin. The HUD keeps exact totals.
		var visible_lots:=mini(count,4)
		for i in maxi(stock.get_child_count(),visible_lots):
			if i>=visible_lots:
				stock.get_child(i).visible=false
			else:
				var item:Node3D
				if i>=stock.get_child_count():
					item=PRODUCTS[kind].instantiate()
					stock.add_child(item)
				else:item=stock.get_child(i)
				item.visible=true
				item.position=Vector3(0,i*.25,0) if kind=="wood" else Vector3(0,(i/2)*.235,(i%2-.5)*.33)

func tick(dt:float) -> void:
	sync_outputs()
	phase=fmod(phase+dt,300.)
	if active_kind=="wood":
		wheels.wood.rotate_z(7.4*dt)
	elif active_kind=="stone":
		wheels.stone.position.y=.97-.22*pow(absf(sin(phase*5.8)),1.4)
		wheels.stone.rotate_y(dt*5.8)

func _rect(kind:String,radius:float) -> Rect2:
	var rect:Rect2=FOOTPRINT[kind]
	var c:Vector3=CENTERS[kind]
	return Rect2(rect.position+Vector2(c.x,c.z),rect.size).grow(radius)

func reserves(at:Vector3) -> bool:
	var p:=Vector2(at.x,at.z)
	for kind:String in APRONS:
		if _rect(kind,1.25).has_point(p) or at.distance_to(APRONS[kind])<2.:return true
	return false

func constrain_motion(from:Vector3,to:Vector3,radius:float) -> Vector3:
	var start:=Vector2(from.x,from.z)
	var end:=Vector2(to.x,to.z)
	var path:=Rect2(start,Vector2.ZERO).expand(end).grow(.01)
	for kind:String in CENTERS:
		var box:=_rect(kind,radius)
		if not path.intersects(box):continue
		var steps:=maxi(1,ceili(start.distance_to(end)/.15))
		var delta:=(end-start)/steps
		var point:=start
		for i in steps:
			point+=delta
			if not box.has_point(point):continue
			var c:=point-box.get_center()
			var overlap:=box.size*.5-c.abs()
			if overlap.x<overlap.y:point.x=box.end.x+.001 if c.x>=0 else box.position.x-.001
			else:point.y=box.end.y+.001 if c.y>=0 else box.position.y-.001
		end=point
	return Vector3(end.x,to.y,end.y)
