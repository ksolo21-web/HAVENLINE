extends Node3D
## Fixed bays for processed goods and cash beneath the raw-material tiers.
## The whole balance remains in the journal.
const Art = preload("res://field_art.gd")
const BAYS := {"planks": -.738, "blocks": -.246, "meal": .246, "money": .738}
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
	var right := .075
	var depth := .20
	for kind: String in BAYS:
		if amounts[kind] > 0:
			var size := Art.unit_extents(kind)
			left = minf(left, float(BAYS[kind]) - size.x * .5 - .012)
			right = maxf(right, float(BAYS[kind]) + size.x * .5 + .012)
			depth = maxf(depth, size.z + .024)
	var bounds := support.mesh.get_aabb()
	support.scale = Vector3(right - left, .036, depth) / bounds.size
	support.position=Vector3((left+right)*.5,FLOOR,DEPTH)-Vector3(bounds.get_center().x,bounds.end.y,bounds.get_center().z)*support.scale
	for kind:String in BAYS:
		var amount:int=amounts[kind]
		if shown.get(kind,0)==amount:continue
		shown[kind]=amount
		var pieces:Array=pools.get(kind,[])
		if pieces.is_empty() and amount>0:
			var first := Art.make(kind)
			add_child(first)
			pieces.append(first)
		if pieces.is_empty():continue
		var height := maxf(.01, Art.unit_extents(kind).y)
		var count:=mini(amount,clampi(floori((CEILING-FLOOR)/height),1,4))
		while pieces.size()<count:
			var unit := Art.make(kind)
			add_child(unit)
			pieces.append(unit)
		for i in pieces.size():
			var unit:Node3D=pieces[i]
			unit.visible=i<count
			unit.position=Vector3(BAYS[kind],FLOOR+height*i,DEPTH)
		pools[kind]=pieces
