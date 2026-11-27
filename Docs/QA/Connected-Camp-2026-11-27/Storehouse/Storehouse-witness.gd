extends SceneTree
var game
var house
var camera:Camera3D
var folder:=OS.get_environment("STOREHOUSE_FILM_FOLDER")
var serial:=OS.get_environment("STOREHOUSE_SERIAL")=="1"
var receipts:Dictionary={}
var anchors:Dictionary={}
func _initialize():call_deferred("run")
func vec(p:Vector3)->Array:return [p.x,p.y,p.z]
func snap(label:String):
	await process_frame
	RenderingServer.force_sync()
	RenderingServer.force_draw(false,.016)
	RenderingServer.force_sync()
	root.get_texture().get_image().save_jpg(folder.path_join(label+".jpg"),.96)
func aim(label:String,point:Vector3,offset:Vector3,span:float):
	camera.make_current()
	camera.global_position=point+offset
	camera.look_at(point)
	camera.force_update_transform()
	camera.reset_physics_interpolation()
	camera.near=max(.05,offset.length()-3.3)
	camera.far=80.
	camera.size=span
	await process_frame
	camera.make_current()
	var screen:Vector2=camera.unproject_position(point)
	anchors[label]={"camera":str(root.get_camera_3d().name),"world_target":vec(point),"screen":[screen.x,screen.y],"root":[root.size.x,root.size.y]}
	await snap(label)
func run():
	game=load("res://field_opening.tscn").instantiate()
	root.add_child(game)
	current_scene=game
	house=game.depot.house
	camera=Camera3D.new()
	camera.name="DockPhotography"
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.keep_aspect=Camera3D.KEEP_HEIGHT
	root.add_child(camera)
	game.camera.make_current()
	var safe:Vector3=house.global_position+Vector3(1.85,0,3.45)
	game.actor.global_position=safe
	game.previous_dry_position=safe
	game.camera.position=safe+game.camera_follow_offset
	for i in 12:await physics_frame
	var net=game.settlement_loop.conveyors.network
	print("HOUSE ",JSON.stringify({"routes":net.routes.keys(),"paid":house.connections_paid,"visible":house.connection_roof.visible,"position":vec(house.global_position),"actor":vec(game.actor.position),"roof":house.connection_roof.get_children().map(func(n):return String(n.name))}))
	if not serial:
		for z in [1.,2.]:
			game.set_zoom_ratio(z)
			game.camera.position=game.actor.position+game.camera_follow_offset
			for i in 6:await physics_frame
			await snap("Gameplay-"+str(z as int)+"x")
	var target:Vector3=house.global_position+Vector3.UP*1.29
	game.opening_hud.visible=false
	if not serial:
		await aim("Utility-inspection",target+Vector3(-.31,0,0),Vector3(-5.45,2.82,2.65),7.)
		await aim("Food-inspection",target+Vector3(0,.02,-.28),Vector3(-2.26,2.35,-6.00),7.)
		await aim("Utility-loading-mouths",house.global_position+Vector3(-1.52,.64,-.33),Vector3(-.70,.18,.08),2.6)
		await aim("Prepared-loading-mouths",house.global_position+Vector3(0.,1.20,-1.22),Vector3(.16,.28,-1.62),2.8)
	var transport=game.settlement_loop.conveyors
	for i in 2200:
		await physics_frame
		for lane in (["meal_to_store","stored_meal"] if serial else ["wood","stone"]):
			if receipts.has(lane) or not transport.goods[lane].visible:continue
			var utility:bool=lane in ["wood","stone"]
			var pos:Vector3=transport.goods[lane].global_position
			var port:Vector3=net.storage_port("wood" if utility else "meal",lane=="meal_to_store")
			if pos.distance_to(port)>.30:continue
			# Insist on the outdoor side of the opening. The in-wall lift has a
			# different height, and a shelf pickup can sit near the dock in 3D.
			var outside:float=port.x-pos.x if utility else port.z-pos.z
			if outside<.045 or outside>.29 or absf(pos.y-port.y)>.15:continue
			var frame="Cargo-"+lane
			var direction:=Vector3(-.62,.18,.09) if utility else Vector3(-.31,.37,-1.39)
			receipts[lane]={"tick":i,"item":vec(pos),"port":vec(port),"distance_m":pos.distance_to(port),"outside_m":outside,"loaded":game.inventory.settlement.line_load[lane]}
			await aim(frame,port+Vector3.UP*.24,direction,2.50)
		if receipts.size()==2:break
	game.camera.make_current()
	game.opening_hud.visible=true
	if not serial:
		game.camera.position=safe+game.camera_follow_offset
		game.camera.look_at(safe)
		game.set_zoom_ratio(2.)
		game.actor.global_position=house.global_position+Vector3(0,0,2.04)
		game.previous_dry_position=game.actor.global_position
		for i in 60:await physics_frame
		await snap("Stocked-cutaway")
	print("RECEIPT ",JSON.stringify(receipts))
	print("ANCHORS ",JSON.stringify(anchors))
	print("CUT ",house.inside_view," SLIDE ",house.open_amount)
	game.set_physics_process(false)
	game.carry.set_physics_process(false)
	game.sound.stop_playback()
	for i in 12:
		OS.delay_msec(20)
		await process_frame
	game.queue_free()
	camera.queue_free()
	for i in 4:await process_frame
	quit(0 if receipts.size()>0 else 2)
