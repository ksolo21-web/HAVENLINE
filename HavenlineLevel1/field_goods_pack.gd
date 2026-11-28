extends Node3D
## Four fixed bays underneath the raw-material tiers. Every visible piece is
## the real station output or register bundle; balances remain in the journal.
const Art = preload("res://field_art.gd")
const BAYS := {"planks": -.486, "blocks": -.162, "meal": .162, "money": .486}
const WIDTH := .304
const FLOOR := .585
const CEILING := .888
const DEPTH := -.72
var ledger
var support: MeshInstance3D
var pools := {}
var shown := {}
var totals: Array[int] = [-1, -1, -1, -1]
var raw_frame_loaded := false
var backpack_frame: Node3D

func configure(inventory, frame:Node3D, shelf:MeshInstance3D)->void:
	ledger=inventory
	backpack_frame=frame
	name="FinishedGoodsShelf"
	support=MeshInstance3D.new()
	support.name="CargoSupport"
	support.mesh=shelf.mesh
	support.material_override=shelf.material_override
	add_child(support)
	refresh()

func _physics_process(_dt:float)->void:
	if ledger:refresh()

func refresh()->void:
	var journal:Dictionary=ledger.settlement
	if totals[0]==journal.hand_products.planks and totals[1]==journal.hand_products.blocks and totals[2]==journal.held_meal and totals[3]==journal.pocket_cash:
		return
	var amounts:Dictionary=ledger.hand_goods()
	totals.assign([amounts.planks,amounts.blocks,amounts.meal,amounts.money])
	visible=totals.max()>0
	backpack_frame.visible=raw_frame_loaded or visible
	var left:=-.075
	var right:=.075
	for kind:String in BAYS:
		if amounts[kind]>0:
			left=minf(left,float(BAYS[kind])-WIDTH*.55)
			right=maxf(right,float(BAYS[kind])+WIDTH*.55)
	var bounds:=support.mesh.get_aabb()
	support.scale=Vector3(right-left,.036,.37)/bounds.size
	support.position=Vector3((left+right)*.5,FLOOR,DEPTH)-Vector3(bounds.get_center().x,bounds.end.y,bounds.get_center().z)*support.scale
	for kind:String in BAYS:
		var amount:int=amounts[kind]
		if shown.get(kind,0)==amount:continue
		shown[kind]=amount
		var pieces:Array=pools.get(kind,[])
		var height:=.1
		if pieces.is_empty() and amount>0:
			var first:=Art.make(kind,WIDTH)
			add_child(first)
			pieces.append(first)
		if pieces.is_empty():continue
		var art_bounds:AABB=Art.source_bounds[kind]
		height=maxf(.01,art_bounds.size.y*WIDTH/maxf(art_bounds.size.x,art_bounds.size.z))
		var count:=mini(amount,clampi(floori((CEILING-FLOOR)/height),1,4))
		while pieces.size()<count:
			var unit:=Art.make(kind,WIDTH)
			add_child(unit)
			pieces.append(unit)
		for i in pieces.size():
			var unit:Node3D=pieces[i]
			unit.visible=i<count
			unit.position=Vector3(BAYS[kind],FLOOR+height*i,DEPTH)
		pools[kind]=pieces
