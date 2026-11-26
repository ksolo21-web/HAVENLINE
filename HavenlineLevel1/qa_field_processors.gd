extends SceneTree
const Workshops=preload("res://field_processors.gd")
class Fixture:
	extends Node3D
	var inventory:Dictionary={"settlement":{"processed_wood":7,"processed_stone":2}}
var checks:={}
func _initialize():run.call_deferred()
func run():
	var h:=Fixture.new()
	root.add_child(h)
	var m:=Workshops.new()
	h.add_child(m)
	m.setup(h)
	checks.unpaid_interior=m.at_station(m.APRONS.wood)=="" and m.at_station(m.APRONS.stone)=="" and m.guards.wood.collision_layer==0 and m.guards.stone.collision_layer==0
	m.set_available(true)
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
	m.set_running("wood",false)
	m.set_running("stone",false)
	checks.restored_stock=m.trays.wood.get_child_count()==4 and m.trays.stone.get_child_count()==2 and m.balances.wood==7
	h.inventory.settlement.processed_wood=0
	h.inventory.settlement.processed_stone=3
	m.tick(.01)
	checks.new_stock=m.trays.stone.get_child_count()==3 and not m.trays.wood.get_child(0).visible
	checks.cooker_approach_separate=m.at_station(preload("res://field_lakeshore.gd").APRON)=="" and m.at_station(preload("res://field_lakeshore.gd").OUTPUT_APRON)==""
	print(JSON.stringify({"suite":"camp_workshops","checks":checks}))
	h.free()
	quit(1 if false in checks.values() else 0)
