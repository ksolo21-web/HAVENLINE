extends "res://tests/field_route.gd"
const Session=preload("res://tests/lifecycle_test_profile.gd")
func run()->void:
	var out:=OS.get_environment("BELT_FILM")
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=root.get_visible_rect().size*Vector2(.30,.68)
	for i in 4:await physics_frame
	var belts=field.settlement_loop.conveyors
	var captured:=false
	var goal:=Vector2(2.,-.8)
	var record:={}
	for tick in 400:
		if move_to([goal.x,goal.y],.13):goal=Vector2(.80,-4.9)
		await physics_frame
		var cargo:Node3D=belts.goods.get("meat")
		if not cargo or not cargo.visible:continue
		var mouth:Vector3=belts.network.storage_port("meat",false)
		var d:=cargo.global_position-mouth
		if d.x<.22 or d.x>.65 or absf(d.z)>.12:continue
		field.set_physics_process(false)
		for ratio in [1,2]:
			field.set_zoom_ratio(ratio)
			await process_frame
			RenderingServer.force_draw(false)
			var photo:=root.get_texture().get_image()
			var scale2:=Vector2(photo.get_size())/root.get_visible_rect().size
			var projected:Vector2=camera.unproject_position(cargo.global_position)*scale2
			if not Rect2(Vector2.ZERO,Vector2(photo.get_size())).has_point(projected):continue
			photo.save_jpg(out.path_join("Cold-dock-%dx.jpg"%ratio),.96)
			record[str(ratio)+"x"]={"ratio":field.trial_camera.zoom_ratio,"renderer_span":camera.size,"player":pt(field.actor.global_position),"cargo":pt(cargo.global_position),"socket":pt(mouth),"source_px":[projected.x,projected.y],"framebuffer":[photo.get_width(),photo.get_height()],"tick":tick}
		captured=record.size()==2
		break
	var file:=FileAccess.open(out.path_join("Cold-dock-zooms.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(record," "));file.close()
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 4:await process_frame
	quit(0 if captured else 2)
