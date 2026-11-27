extends "/tmp/havenline-beta-t01/independent/route.gd"

func frame_at(key: String) -> Dictionary:
	await _coast(12)
	await _view(key)
	var soles: Vector3 = field.actor.global_position
	var crowns := []
	var render := {"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),"objects":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)}
	for row: Dictionary in field.forest.records:
		var transform: Transform3D = row.transform
		var size: Vector2 = field.field_env.pine_shapes[row.variant]
		var factor := transform.basis.get_scale().abs().x
		var foot := camera.unproject_position(transform.origin)
		var top := camera.unproject_position(transform.origin + Vector3.UP * size.y * factor)
		crowns.append({"id":row.id,"position":pt(transform.origin),"radius":size.x*factor,"root": [foot.x,foot.y],"crown": [top.x,top.y],"occupied":row.get("occupied",false)})
	var boot := camera.unproject_position(soles)
	var hood := camera.unproject_position(soles + Vector3.UP * 1.56)
	return {"capture":key,"position":pt(soles),"camera_basis":str(camera.global_basis),"view":[root.size.x,root.size.y],"camera_size":camera.size,"zoom":field.get_zoom_ratio(),"camp_stage":field.field_env.perimeter_stage,"boot":[boot.x,boot.y],"hood":[hood.x,hood.y],"crowns":crowns,"render":render,"remaining_hearth_bundles":field.inventory.remaining("center_hearth").get("wood",0),"active_camera":camera==root.get_camera_3d()}

func run() -> void:
	capture=true
	forest_out=OS.get_environment("T01_OUT")
	root.size=Vector2i(460,760)
	field=load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	camera=field.camera
	origin=Vector2(root.get_visible_rect().size)*Vector2(.22,.82)
	await _coast(18)
	var frames := []
	if field.field_env.perimeter_stage == 0:
		if OS.get_environment("T01_PROGRESS") == "1":
			var bundles: int = field.inventory.remaining("center_hearth").wood - 1
			for i in bundles:
				field.inventory.collect("isolated-founding-framing-%02d" % i,"wood")
			field.carry.sync()
			_check(await _walk(Vector3(0.,0.,2.4)),"reach hearth pad by touch")
			for i in 300:
				if field.inventory.remaining("center_hearth").wood == 1: break
				await _step()
			_check(field.inventory.remaining("center_hearth").wood == 1 and field.field_env.perimeter_stage == 0,"real proximity transfer leaves a green pad one bundle short")
		frames.append(await frame_at("founding-1x"))
		await _pinch()
		frames.append(await frame_at("founding-2x"))
	else:
		for route_point: Array in CASES.west.slice(0,5):
			var ok := await _walk(Vector3(route_point[0],0,route_point[1]))
			_check(ok,"cannot reach "+str(route_point))
		frames.append(await frame_at("west-1x"))
		await _pinch()
		frames.append(await frame_at("west-2x"))
	var out := FileAccess.open(forest_out.path_join("projections.json"),FileAccess.WRITE)
	out.store_string(JSON.stringify({"frames":frames,"failures":failures},"\t"))
	out.close()
	await SessionProof.drain_field_audio(self,field)
	field.queue_free()
	for i in 8: await process_frame
	quit(0 if failures.is_empty() else 1)
