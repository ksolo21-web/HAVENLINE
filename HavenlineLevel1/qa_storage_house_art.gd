extends SceneTree
## Affordable isolated regression for shell tiers, paired doors and display anchors.
const Storehouse := preload("res://field_storage_house.gd")
var results := {}
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var house:=Storehouse.new()
	var actor:=Node3D.new()
	root.add_child(actor)
	root.add_child(house)
	actor.position=Vector3(0,0,5)
	house.configure(actor)
	results.unpaid=not house.visible and house.collision.collision_layer==0
	house.update_state(1,{})
	results.starter=house.visible and house.parts.StarterRope.visible and not house.parts.Footing.visible and house.collision.collision_layer==1
	house.update_state(2,{})
	results.reinforced=house.parts.Footing.visible and not house.parts.StarterRope.visible and not house.parts.LeftArmor.visible
	house.update_state(3,{"wood":2,"stone":1,"meat":0})
	results.advanced=house.parts.LeftArmor.visible and house.parts.FacadeArmor.visible and house.parts.AdvancedShelves.visible
	var cues:Array[bool]=[]
	house.door_motion.connect(func(opening:bool,_at:Vector3):cues.append(opening))
	actor.position=Vector3(0,0,3.45)
	for i in 30:house._physics_process(1.0/60.0)
	results.covered_loading=house.parts.Roof.visible and house.open_amount==1.0 and not house.is_interior_visible()
	for entry_side in [-.55,.55]:
		actor.position=Vector3(entry_side,0,2.27)
		for i in 30:house._physics_process(1.0/60.0)
		results["arrival %.2f"%entry_side]=house.is_interior_visible() and house.open_amount==1.0 and house.parts.DoorLeft.position.x<-.6 and house.parts.DoorRight.position.x>.6 and not house.parts.Roof.visible and house.parts.CutawayPanels.visible
		actor.position=Vector3(0,0,-.35)
		house._physics_process(.1)
		results.interior_remains_open=house.is_interior_visible()
		actor.position=Vector3(0,0,4.2)
		for i in 30:house._physics_process(1.0/60.0)
		results["departure %.2f"%entry_side]=house.parts.Roof.visible and house.open_amount==0.0 and house.parts.DoorRight.position.x==0.0
	results.motion_cues_once=cues==[true,false,true,false]
	results.six_zones=house.shelves.size()==6
	results.stock_segregation=house.bay_position("wood").distance_to(house.bay_position("stone"))>.60 and house.bay_position("stone").distance_to(house.bay_position("meat"))>.95
	house.update_state(0,{})
	results.unbuilt_collision_removed=house.collision.collision_layer==0 and not house.visible
	print(JSON.stringify({"suite":"storehouse_art","checks":results}))
	house.free()
	actor.free()
	quit(1 if results.values().has(false) else 0)
