extends "res://tests/field_route.gd"
const Session=preload("res://tests/lifecycle_test_profile.gd")
func run()->void:
	var dir:=OS.get_environment("BELT_FILM")
	var dry_run:=dir.is_empty()
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=root.get_visible_rect().size*Vector2(.30,.68)
	for i in 4:await physics_frame
	var belt=field.settlement_loop.conveyors.network
	var receipt:={"framebuffer":str(root.size),"visits":{},"path":[],"renderer":RenderingServer.get_video_adapter_name()}
	var sites:=["wood","counter"]
	var frame:=0
	var step:=0
	var previous:Vector3=field.actor.global_position
	for site:String in sites:
		var target:Vector3=belt.accessible_service(site)
		var reached:=false
		var travel:=0.
		var entered:=false
		var start_tick:=step
		for tick_in_leg in 550:
			var feet:Vector3=field.actor.global_position
			if feet.distance_to(target)<.24:
				steer(Vector2.ZERO)
				entered = field.counter.at_service(feet) if site=="counter" else field.processors.at_station(feet)=="wood"
				reached=entered
				if reached:break
			var next:Vector3=belt.walker_waypoint(feet,target)
			move_to([next.x,next.z],.055)
			await physics_frame
			var at:Vector3=field.actor.global_position
			travel+=at.distance_to(previous);previous=at;step+=1
			if step%10==0:
				receipt.path.append([step,pt(at)])
				if not dry_run:
					await process_frame;RenderingServer.force_draw(false)
					root.get_texture().get_image().save_jpg(dir.path_join("frames/f%04d.jpg"%frame),.87)
					frame+=1
		receipt.visits[site]={"accepted_physical_approach":reached,"position":pt(field.actor.global_position),"travel_m":travel,"ticks":step-start_tick}
		print("PUBLIC_VISIT ",site," ",receipt.visits[site])
		if not reached:break
		if not dry_run:
			steer(Vector2.ZERO)
			field.set_zoom_ratio(2.)
			for pause in 25:await physics_frame
			await process_frame;RenderingServer.force_draw(false)
			root.get_texture().get_image().save_jpg(dir.path_join(site+"-at-work-face.jpg"),.93)
			field.set_zoom_ratio(1.)
	steer(Vector2.ZERO)
	if not dry_run:
		var log:=FileAccess.open(dir.path_join("Public-aisles.json"),FileAccess.WRITE)
		log.store_string(JSON.stringify(receipt," "));log.close()
	field.set_physics_process(false)
	await Session.drain_field_audio(self,field);field.queue_free()
	for i in 4:await process_frame
	var okay:bool=receipt.visits.size()==2 and receipt.visits.wood.accepted_physical_approach and receipt.visits.counter.accepted_physical_approach
	quit(0 if okay else 2)
