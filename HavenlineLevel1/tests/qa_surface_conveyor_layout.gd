extends SceneTree
## Full paid camp from a real saved game. Check the load-bearing deck, working
## floor and actual socket locations after moving an owned saw and returning it.
const Session = preload("res://tests/lifecycle_test_profile.gd")
const Guard = preload("res://opening_save.gd")
const Save = preload("res://field_save.gd")
const FIXTURE = "res://tests/fixtures/camp_hud_paid.json"
const SELF = "res://tests/qa_surface_conveyor_layout.gd"

var world
var checks := {}
var readings := {}

func _initialize() -> void:
	if "--check-paid-deck" in OS.get_cmdline_user_args():
		if not Guard.new().configure(OS.get_cmdline_user_args()):
			quit(2)
			return
		call_deferred("run")
		return
	var profile := Session.make_directory()
	if profile.is_empty():
		quit(2)
		return
	var data := FileAccess.get_file_as_bytes(FIXTURE)
	var file := FileAccess.open(profile.path_join(Save.PRIMARY),FileAccess.WRITE)
	if data.is_empty() or not file:
		Session.remove_owned(profile)
		quit(2)
		return
	file.store_buffer(data)
	file.close()
	var status := Session.child(SELF,profile,"--check-paid-deck")
	Session.remove_owned(profile)
	quit(status)

func check(label:String, passed:bool) -> void:
	checks[label]=passed
	if not passed:
		push_error(label)

func lengths(routes:Dictionary) -> Dictionary:
	var result := {}
	for lane:String in routes:
		var path:PackedVector3Array=routes[lane]
		var length:=0.
		var height:=INF
		var direction:=Vector2.ZERO
		var worst_turn:=1.
		for i in path.size():
			height=minf(height,path[i].y)
			if i>0:
				var step:=path[i]-path[i-1]
				length+=step.length()
				var plan:=Vector2(step.x,step.z)
				if plan.length()>.002:
					var heading:=plan.normalized()
					if not direction.is_zero_approx():worst_turn=minf(worst_turn,direction.dot(heading))
					direction=heading
		result[lane]={"minimum_roller_height":height,"length":length,"minimum_heading_dot":worst_turn}
	return result

func check_decks(routes:Dictionary, label:String) -> void:
	var spans:=lengths(routes)
	var supported:=true
	var continuous:=true
	for lane:String in spans:
		# Lowest machine tray is at 0.215 m. The carrier body is up to
		# 0.135 m thick; leave usable clearance under the full exterior run.
		supported=supported and spans[lane].minimum_roller_height>=.17-.001
		continuous=continuous and spans[lane].minimum_heading_dot>=-.001
	check(label+" dock lips have continuous forward travel without folding back",continuous and not spans.is_empty())
	check(label+" exterior cargo decks are all above the working floor",supported and not spans.is_empty())
	readings[label]=spans

func run() -> void:
	world=load("res://field_opening.tscn").instantiate()
	root.add_child(world)
	current_scene=world
	await physics_frame
	var belts=world.settlement_loop.conveyors
	belts.refresh_paths()
	var network=belts.network
	check("both bought networks expose all eight compatible routes",network.routes.size()==8)
	check_decks(network.routes,"default")
	for station in ["store","wood","stone","meat","cooker_output","counter"]:
		check("reachable public floor at "+station,network.accessible_service(station).is_finite())
	var kitchen:Vector3=world.lakeshore.cooker.global_position
	var kitchen_front:=Vector3(kitchen.x+.25,0,kitchen.z+1.3)
	check("two people fit through the front kitchen approach",network.pedestrian_clear(kitchen_front,kitchen_front+Vector3.BACK*2.2,.60))
	var south:=Vector3(0,0,world.camp_layout.bounds().end.y-1.)
	var east:=Vector3(world.camp_layout.bounds().end.x-1.,0,0)
	var middle:=Vector3(3.,0,2.4)
	check("open aisle from south gate across public courtyard",network.pedestrian_clear(south,middle,.65))
	check("open aisle from public courtyard to east gate",network.pedestrian_clear(middle,east,.65))
	var clerk:Vector3=world.counter.service_point.global_position
	var pickup:Vector3=network.counter_buffer_position(0)
	check("both food lines end at the separate staffed pickup",network.routes.meal[-1].is_equal_approx(pickup) and network.routes.stored_meal[-1].is_equal_approx(pickup) and pickup.distance_to(clerk)>.6)
	var mills=world.processors
	check("saw and quarry share the storehouse utility wing",mills.machines.wood.global_position.distance_to(world.depot.house.global_position)<6.5 and mills.machines.stone.global_position.distance_to(world.depot.house.global_position)<6.5)
	var layout=world.camp_layout
	var previous:Vector2=layout.center("saw_bench")
	var moved:=Vector2(-7.75,-7.25)
	check("owned saw can move with a valid service footprint",layout.relocate("saw_bench",moved))
	belts.refresh_paths()
	check_decks(network.routes,"relocated")
	check("moved saw receives its material at its own new socket",network.routes.has("wood") and network.routes.wood[-1].distance_to(mills.input_position("wood"))<.01)
	check("saw can return to its original footprint",layout.relocate("saw_bench",previous))
	belts.refresh_paths()
	check("all eight lines restored at original positions",network.routes.size()==8)
	world.set_physics_process(false)
	await Session.drain_field_audio(self,world)
	world.queue_free()
	for i in 4:await process_frame
	print("SURFACE_CONVEYOR_QA ",JSON.stringify({"checks":checks,"readings":readings}))
	quit(1 if false in checks.values() else 0)
