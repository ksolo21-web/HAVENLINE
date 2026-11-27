extends "res://tests/field_route.gd"
const Session=preload("res://tests/lifecycle_test_profile.gd")
const WAYPOINTS:=[Vector2(2.,-.8),Vector2(.80,-4.9),Vector2(.73,-2.35),Vector2(-2.2,-1.05),Vector2(-4.18,.52),Vector2(-6.77,.42)]
func run()->void:
	var dir:=OS.get_environment("BELT_FILM")
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field);current_scene=field
	camera=field.camera
	origin=root.get_visible_rect().size*Vector2(.30,.68)
	var belts=field.settlement_loop.conveyors
	for i in 4:await physics_frame
	var record:={"began_root_xz":pt(field.actor.position),"source_size":[root.size.x,root.size.y],"route":[],"camera":"normal user gameplay","stock":[],"build_order":field.inventory.build_order.duplicate(),"renderer":RenderingServer.get_video_adapter_name()}
	var target:=0
	var frame:=0
	var witnessed:=false
	for step in 309:
		if step==118:field.set_zoom_ratio(1.78)
		if step==190:field.set_zoom_ratio(1.)
		if target<WAYPOINTS.size() and step<232:
			var goal:Vector2=WAYPOINTS[target]
			if move_to([goal.x,goal.y],.13):target+=1
		else:steer(Vector2.ZERO)
		await physics_frame
		if step in [57,102,150,270]:
			await process_frame
			RenderingServer.force_draw(false)
			root.get_texture().get_image().save_jpg(dir.path_join(["Approach","Cooker","Pinch","Utility"][[57,102,150,270].find(step)]+".jpg"),.93)
		if step%5!=0:continue
		await process_frame
		RenderingServer.force_draw(false)
		root.get_texture().get_image().save_jpg(dir.path_join("frames/f%03d.jpg"%frame),.89)
		frame+=1
		record.route.append([step,pt(field.actor.global_position),field.actor.velocity.length()])
		var j:Dictionary=field.inventory.settlement
		var located:={}
		for key in belts.goods:
			var node:Node3D=belts.goods[key]
			if node.visible:located[key]=pt(node.global_position)
		record.stock.append([step,j.line_load.duplicate(),located,j.counter_stock,j.served])
		if not witnessed and located.has("meat"):
			var mouth:Vector3=belts.network.storage_port("meat",false)
			var cargo:Node3D=belts.goods.meat
			var displacement:=cargo.global_position-mouth
			var px:=camera.unproject_position(cargo.global_position)
			if displacement.x>.15 and displacement.x<.90 and absf(displacement.z)<.5 and root.get_visible_rect().has_point(px):
				witnessed=true
				var photo:=root.get_texture().get_image()
				photo.save_jpg(dir.path_join("Cold-dock-transit.jpg"),.96)
				var scale2:=Vector2(photo.get_size())/root.get_visible_rect().size
				record["cold_dock_witness"]={"tick":step,"cargo":pt(cargo.global_position),"socket":pt(mouth),"screen_px":str(px*scale2)}

	record["waypoints_reached"]=target
	record["mesh_modules"]=belts.network.art.fitted.counts
	var log:=FileAccess.open(dir.path_join("Journey.json"),FileAccess.WRITE)
	log.store_string(JSON.stringify(record," "));log.close()
	field.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 4:await process_frame
	quit()
