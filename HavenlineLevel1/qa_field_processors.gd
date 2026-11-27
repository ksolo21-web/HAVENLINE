extends SceneTree
const Workshops=preload("res://field_processors.gd")
class Fixture:
	extends Node3D
	var inventory = preload("res://field_inventory.gd").new()
	func _init():
		inventory.configure(preload("res://field_progression.gd").offers())
		inventory.settlement.processed_wood = 7
		inventory.settlement.processed_stone = 2
	func purchase(id: String):
		for kind: String in inventory.costs[id]:
			var price: int = inventory.costs[id][kind]
			for i in price: inventory.collect(id + kind + str(i), kind)
			assert(inventory.payment(id,kind,false,price))
var checks:={}
func _initialize():run.call_deferred()
func run():
	var h:=Fixture.new()
	root.add_child(h)
	var m:=Workshops.new()
	h.add_child(m)
	m.setup(h)
	checks.unpaid_interior=m.at_station(m.APRONS.wood)=="" and m.at_station(m.APRONS.stone)=="" and m.guards.wood.collision_layer==0 and m.guards.stone.collision_layer==0
	for id: String in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","camp_cooker","saw_bench","quarry_drill"]: h.purchase(id)
	m.refresh_ownership(false)
	await physics_frame
	for kind:String in m.CENTERS:
		var apron:Vector3=m.APRONS[kind]
		var center:Vector3=m.CENTERS[kind]
		checks[kind+"_service"]=m.at_station(apron)==kind and m.at_station(center)==""
		checks[kind+"_reserve"]=m.reserves(center) and m.reserves(apron)
		checks[kind+"_approach"]=m.constrain_motion(apron+Vector3.BACK*1.5,apron,.31).distance_to(apron)<.005
		checks[kind+"_guard"]=m.constrain_motion(apron,center,.31).distance_to(center)>1.
		checks[kind+"_sockets"]=m.input_position(kind).distance_to(m.output_position(kind))>1.
		var n:Node3D=m.wheels[kind]
		var initial:=n.transform
		m.tick(.15)
		checks[kind+"_still"]=initial.is_equal_approx(n.transform)
		m.set_running(kind,true)
		m.tick(.18)
		checks[kind+"_driven"]=not initial.is_equal_approx(n.transform)
		m.set_running(kind,false)
	var saw_before:Transform3D=m.wheels.wood.transform
	var drill_before:Transform3D=m.wheels.stone.transform
	m.set_running("wood",true)
	m.set_running("stone",true)
	m.tick(.12)
	checks.both_drives_run=not saw_before.is_equal_approx(m.wheels.wood.transform) and not drill_before.is_equal_approx(m.wheels.stone.transform)
	checks.dry_mast_before_contact=m.stone_dust.all(func(p):return not p.visible) and m.stone_chips.all(func(p):return not p.visible)
	h.inventory.settlement.work_seconds.stone=preload("res://field_settlement.gd").CYCLE_SECONDS.stone*.58
	m.tick(.01)
	checks.cuttings_at_full_plunge=m.drill_head.position.y<m.HEAD_HOME.y-.49 and m.stone_dust.all(func(p):return p.visible) and m.stone_chips.all(func(p):return p.visible)
	m.set_running("wood",false)
	m.set_running("stone",false)
	checks.idle_mast_has_no_cuttings=m.drill_head.position.is_equal_approx(m.HEAD_HOME) and m.stone_dust.all(func(p):return not p.visible) and m.stone_chips.all(func(p):return not p.visible)
	checks.restored_stock=m.trays.wood.get_child_count()==4 and m.trays.stone.get_child_count()==2 and m.balances.wood==7
	h.inventory.settlement.processed_wood=0
	h.inventory.settlement.processed_stone=3
	m.tick(.01)
	checks.new_stock=m.trays.stone.get_child_count()==3 and not m.trays.wood.get_child(0).visible
	checks.cooker_approach_separate=m.at_station(preload("res://field_lakeshore.gd").APRON)=="" and m.at_station(preload("res://field_lakeshore.gd").OUTPUT_APRON)==""
	print(JSON.stringify({"suite":"camp_workshops","checks":checks}))
	h.free()
	quit(1 if false in checks.values() else 0)
