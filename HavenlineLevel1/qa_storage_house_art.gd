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
	results.covered_full_leaves=house.parts.DoorLeft.visible and house.parts.DoorRight.visible and not house.parts.CutDoorLeft.visible and not house.parts.CutawayTrack.visible
	for entry_side in [-.55,.55]:
		actor.position=Vector3(entry_side,0,2.27)
		for i in 30:house._physics_process(1.0/60.0)
		results["arrival %.2f"%entry_side]=house.is_interior_visible() and house.open_amount==1.0 and house.parts.DoorLeft.position.x<-.6 and house.parts.DoorRight.position.x>.6 and not house.parts.Roof.visible and house.parts.CutawayPanels.visible
		results.sectioned_front=house.parts.CutDoorLeft.visible and house.parts.CutDoorRight.visible and house.parts.CutawayTrack.visible and not house.parts.DoorLeft.visible and not house.parts.DoorRightArmor.visible
		actor.position=Vector3(0,0,-.35)
		house._physics_process(.1)
		results.interior_remains_open=house.is_interior_visible()
		actor.position=Vector3(0,0,4.2)
		for i in 30:house._physics_process(1.0/60.0)
		results["departure %.2f"%entry_side]=house.parts.Roof.visible and house.open_amount==0.0 and house.parts.DoorRight.position.x==0.0
	results.motion_cues_once=cues==[true,false,true,false]
	results.six_zones=house.shelves.size()==6
	results.stock_segregation=house.bay_position("wood").distance_to(house.bay_position("stone"))>.60 and house.bay_position("stone").distance_to(house.bay_position("meat"))>.95
	house.configure_connections(["meal"])
	results.direct_counter_preserves_shell=not house.connection_roof.visible and house.parts.Roof.visible
	house.configure_connections(["wood","stored_meal"])
	results.paid_meshed_roof=house.connection_roof.visible and not house.parts.Roof.visible and not house.parts.Signs.visible
	results.authored_roof_and_vent=house.connection_roof.get_node("ConnectedRoof").mesh!=null and house.connection_roof.get_node("RearVent").mesh!=null
	var utility:MeshInstance3D=house.connection_frame(false)
	var food:MeshInstance3D=house.connection_frame(true,true)
	results.distinct_typed_mouths=utility.mesh!=food.mesh and utility.get_aabb().size.x>.48 and food.get_aabb().size.x>.48
	results.direction_labels=utility.get_node("Direction").text=="OUT" and food.get_node("Direction").text=="IN" and not food.get_node("Direction").shaded
	utility.free()
	food.free()
	actor.position=Vector3(0,0,2.3)
	for i in 30:house._physics_process(1.0/60.0)
	results.connected_section=not house.connection_roof.visible and not house.parts.Roof.visible and house.parts.Headers.visible and house.open_amount==1.
	actor.position=Vector3(0,0,5)
	for i in 30:house._physics_process(1.0/60.0)
	results.connected_door_closes=house.connection_roof.visible and house.open_amount==0.
	house.configure_connections([])
	results.unconnected_roof_recovers=house.parts.Roof.visible and not house.connection_roof.visible
	house.update_state(0,{})
	results.unbuilt_collision_removed=house.collision.collision_layer==0 and not house.visible
	print(JSON.stringify({"suite":"storehouse_art","checks":results}))
	house.free()
	actor.free()
	quit(1 if results.values().has(false) else 0)
