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
		var turns:=0.
		for i in path.size():
			height=minf(height,path[i].y)
			if i>0:
				var step:=path[i]-path[i-1]
				length+=step.length()
				var plan:=Vector2(step.x,step.z)
				if plan.length()>.002:
					var heading:=plan.normalized()
					if not direction.is_zero_approx():
						worst_turn=minf(worst_turn,direction.dot(heading))
						turns+=absf(direction.angle_to(heading))
					direction=heading
		result[lane]={"minimum_roller_height":height,"length":length,"minimum_heading_dot":worst_turn,"bend_degrees":rad_to_deg(turns)}
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

func check_fitted_width(network) -> void:
	var kit=network.art.fitted
	var broadest:=0.
	var widened:=0
	for family:String in ["straight","corner","left_corner","incline"]:
		for data:Color in kit.values[family]:
			var widths:=roundi(data.a*255.)%128
			var start:=floori(widths/8.)
			var finish:=widths%8
			var width:float=kit.WIDTH+maxi(start,finish)*kit.Gauge.WIDTH_STEP
			broadest=maxf(broadest,width)
			if width>=.78:widened+=1
	check("open runs fit broad visible Meshy rollers",broadest>=1. and widened>=8)
	var throat:Vector3=network.storage_port("meat",false)
	check("cold room keeps its matching narrow socket",is_equal_approx(network.gauge.fitted_width(throat),kit.WIDTH))
	# Probe the newly occupied floor on the outside of an actual straight.
	# Exclude every location that the original 0.484 m belt already blocked.
	var paid_edge:=false
	for family:String in ["straight","incline"]:
		for i in kit.values[family].size():
			var data:Color=kit.values[family][i]
			var flags:=roundi(data.a*255.)%128
			if mini(floori(flags/8.),flags%8)<3:continue
			var node:Transform3D=kit.transforms[family][i]
			var mid:Vector3=node.origin+node.basis.z*data.b*2.
			for sign_x:float in [-1.,1.]:
				var edge:=mid+node.basis.x*.43*sign_x
				var p:=Vector2(edge.x,edge.z)
				var old_clear:=true
				for segment:Array in network.aisles.rail_cells.get(network.aisles._bucket(p),[]):
					if p.distance_to(network.aisles._closest(p,segment[0],segment[1]))<=kit.WIDTH*.5+.085:
						old_clear=false
						break
				if old_clear and not network.aisles.disc_clear(p,.085):
					paid_edge=true
					break
			if paid_edge:break
		if paid_edge:break
	check("new outer rail blocks pedestrian movement beyond the old footprint",paid_edge)
	readings["rendered gauge"]={"max_width_m":broadest,"sections_at_least_0_78_m":widened}

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
	check_fitted_width(network)
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
	var player_approach:Vector3=world.counter.service_point.global_position
	var pickup:Vector3=network.counter_buffer_position(0)
	check("both food lines end at the separate self-service pickup",network.routes.meal[-1].is_equal_approx(pickup) and network.routes.stored_meal[-1].is_equal_approx(pickup) and pickup.distance_to(player_approach)>.6)
	var apparatus=network.receiver
	check("normal paid counter mounts the industrial receiver",apparatus!=null)
	if apparatus:
		var has_heads:bool=network.art.fitted.counts.get("receiver_straight",0)==2 and network.art.fitted.counts.get("receiver_incline",0)==3
		check("two individually driven D01 heads lead to one descending D01 bed",has_heads and apparatus.inlet("meal").distance_to(apparatus.inlet("stored_meal"))>1.)
		for lane:String in ["meal","stored_meal"]:
			var path:PackedVector3Array=network.routes[lane]
			var high=apparatus.travel(lane)[2]
			check(lane+" travels through its own high mouth then the common stock platform",apparatus.inlet(lane) in path and high in path and high.y-pickup.y>.62 and path[-1].is_equal_approx(pickup))
		var occupied:={}
		var sold:int=world.inventory.settlement.market.sold.meal
		for rank in belts.buffer_capacity():
			var slot:Vector3=world.counter.stock_position("meal",rank)
			occupied[slot]=true
			check("stock "+str(rank)+" is grounded in its own actual queue cell",slot.is_equal_approx(apparatus.slot(apparatus.position_in_queue(rank,sold))) and is_equal_approx(slot.y,apparatus.STOCK_Y) and apparatus.inset(slot))
		check("eight unique places in four real rows and two columns",occupied.size()==8 and absf(apparatus.slot(0).z-apparatus.slot(1).z)>apparatus.ROAST and apparatus.slot(0).distance_to(apparatus.slot(6))>1.80)
		check("stock guard is wider than two metres and reserves its true floor",network.gauge.fitted_width(pickup)>2.4 and not network.aisles.disc_clear(apparatus.shell.get_center(),.31))
		var edge:Vector3=apparatus.point(3.,0.,apparatus.WIDTH*.5)
		var approach:Vector3=edge+Vector3.BACK*.50
		var attempted:Vector3=edge+Vector3.FORWARD*2.8
		var contact:Vector3=network.constrain_motion(approach,attempted,.31)
		check("a real player step cannot tunnel through the raised cabinet",contact.z>edge.z+.30 and contact.z<approach.z and network.aisles.disc_clear(Vector2(contact.x,contact.z),.31))
		readings["industrial receiver"]={"outer_m":apparatus.WIDTH,"length_m":apparatus.LENGTH,"intake_span_m":apparatus.inlet("meal").distance_to(apparatus.inlet("stored_meal")),"intake_high_m":1.33,"stock_y_m":apparatus.STOCK_Y,"portion_m":apparatus.ROAST,"slots":occupied.size()}
	var art=preload("res://field_art.gd")
	for raw:String in ["wood","stone","meat"]:
		var size: Vector3 = art.unit_extents(raw)
		var cross_width := size.z
		var socket_width:float=network.gauge.SOCKET
		check(raw+" cargo clears the standard warehouse throat",cross_width<socket_width)
		readings[raw+" cargo"]={"width_across_deck_m":cross_width,"port_m":socket_width}
	var live_unit: Node3D = belts.goods.meal
	var shelf_unit: Node3D = belts.shelf_items.meal.get_child(0)
	var size: Vector3 = art.unit_extents("meal")
	var invariant := true
	for progress: float in [.01, .15, .38, .58, .83, .99]:
		belts._place_cargo("meal", live_unit, progress)
		var scale_factor: float = live_unit.get_node("GroundedModel").scale.x
		invariant = invariant and live_unit.global_basis.get_scale().is_equal_approx(Vector3.ONE)
		invariant = invariant and is_equal_approx(scale_factor, shelf_unit.get_node("GroundedModel").scale.x)
	check("the same roast size clears the full conveyor and appears on the warehouse shelf", invariant and is_equal_approx(size.x, .46))
	readings["fixed meal extent"] = str(size)
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
	var counter_before:Vector2=layout.center("north_counter")
	var counter_shift:=Vector2(4.,counter_before.y)
	check("owned counter can move along its north fence",layout.relocate("north_counter",counter_shift))
	belts.refresh_paths()
	var unloaded:Vector3=network.counter_buffer_position(0)
	check("actual saved bay carries its stock deck, both food paths and six usable stations",layout.snapshot().get("north_counter")==[counter_shift.x,counter_shift.y] and network.routes.size()==8 and network.aisles.services.size()==6 and network.routes.meal[-1].is_equal_approx(unloaded) and network.routes.stored_meal[-1].is_equal_approx(unloaded))
	world.set_physics_process(false)
	await Session.drain_field_audio(self,world)
	world.queue_free()
	for i in 4:await process_frame
	print("SURFACE_CONVEYOR_QA ",JSON.stringify({"checks":checks,"readings":readings}))
	quit(1 if false in checks.values() else 0)
