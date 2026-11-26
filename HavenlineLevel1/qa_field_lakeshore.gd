extends SceneTree
const Shore=preload("res://field_lakeshore.gd")
var checks:={}
func _initialize():run.call_deferred()
func valid(label:String,value:bool)->void:
	checks[label]=value
func run()->void:
	var stage:=Node3D.new()
	root.add_child(stage)
	var bank:=Shore.new()
	stage.add_child(bank)
	bank.setup(stage)
	await physics_frame
	valid("west of both camp gates",bank.COOKER_AT.x < -18.)
	valid("natural waterline matches both endpoints",bank.shore.size()==108 and bank.get_node("SolidWaterline").get_child(0).shape.get_faces().size()==108*6)
	var origin:=Vector3(bank.LAKE_XZ.x,0,bank.LAKE_XZ.y)
	var dry:=bank.constrain_motion(origin,origin,.31)
	valid("restored lake position depenetrates",dry.distance_to(origin)>4. and not Geometry2D.is_point_in_polygon(Vector2(dry.x,dry.z),bank.shore))
	var stopped:=bank.constrain_motion(bank.APRON,Vector3(-51,0,16.65),.31)
	valid("swept path cannot tunnel",stopped.x>-30. and not Geometry2D.is_point_in_polygon(Vector2(stopped.x,stopped.z),bank.shore))
	var route_start:=Vector3(-14,0,12.6)
	valid("dry final approach",bank.constrain_motion(route_start,bank.APRON,.31).distance_to(bank.APRON)<.03)
	valid("requires working apron",bank.at_cooker(bank.APRON) and not bank.at_cooker(bank.COOKER_AT) and not bank.at_cooker(Vector3.ZERO))
	valid("lake and station reserved",bank.reserves(origin) and bank.reserves(bank.APRON) and not bank.reserves(Vector3(-6,0,3)))
	valid("distinct real work sockets",bank.cooker_input.global_position.distance_to(bank.cooker_output.global_position)>1.75)
	var shaft_before:Basis=bank.saw.basis
	bank.tick(.3)
	valid("idle saw and smoke",shaft_before.is_equal_approx(bank.saw.basis) and not bank.smoke.emitting)
	bank.update_activity(true)
	bank.tick(.2)
	valid("working saw and smoke",not shaft_before.is_equal_approx(bank.saw.basis) and bank.smoke.emitting)
	bank.update_activity(false)
	var finished:Basis=bank.saw.basis
	bank.tick(.3)
	valid("paused work retains physical pose",finished.is_equal_approx(bank.saw.basis) and not bank.smoke.emitting)
	valid("water animation",is_equal_approx(bank.water_material.get_shader_parameter("sim_time"),.8))
	print(JSON.stringify({"suite":"lakeshore","checks":checks,"cooker":str(bank.COOKER_AT),"apron":str(bank.APRON),"input":str(bank.cooker_input.global_position),"output":str(bank.cooker_output.global_position)}))
	stage.free()
	quit(0 if not false in checks.values() else 1)
