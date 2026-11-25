extends SceneTree
## Detached source/camera projection only. No saved profile reads outside runner sandbox.

func _initialize() -> void:
	call_deferred("_probe")

func _probe() -> void:
	var v := SubViewport.new()
	v.size = Vector2i(1280, 720)
	root.add_child(v)
	var scene: Node3D = load("res://previews/integrated_opening.tscn").instantiate()
	v.add_child(scene)
	await process_frame
	scene.set_physics_process(false)
	if not scene.bound:
		push_error("V5 price witness could not bind exact preview")
		quit(1)
		return
	var camera: Camera3D = scene.camera
	var pad: Node3D = scene.get_node("ExactStudioV5_PresentationOnly")
	var rows := {}
	for key in ["Action", "Cost"]:
		var label: Label3D = pad.scene_view.get_node(key)
		var midpoint := camera.unproject_position(label.global_position)
		var axis_x := camera.unproject_position(label.to_global(Vector3(label.pixel_size*30,0,0))) - midpoint
		var axis_y := camera.unproject_position(label.to_global(Vector3(0,label.pixel_size*30,0))) - midpoint
		var font := label.font
		if not is_instance_valid(font):
			font = ThemeDB.fallback_font
		if not is_instance_valid(font):
			push_error("Engine font cannot be bound")
			quit(2)
			return
		var box := font.get_string_size(label.text, HORIZONTAL_ALIGNMENT_LEFT, -1, label.font_size)
		var glyph_boxes := []
		var ts := TextServerManager.get_primary_interface()
		for c in label.text:
			if c == " ":
				continue
			for rid in font.get_rids():
				var g := ts.font_get_glyph_index(rid,label.font_size,c.unicode_at(0),0)
				if g == 0:
					continue
				var m := Vector2i(label.font_size,0)
				ts.font_render_glyph(rid,m,g)
				var shape := ts.font_get_glyph_size(rid,m,g)
				glyph_boxes.append({"character":c,"size":[shape.x,shape.y]})
				break
		var mgeo := label.generate_triangle_mesh()
		var points: Array = []
		if mgeo:
			for vertex in mgeo.get_faces():
				var rel: Vector3 = label.to_global(vertex) - pad.global_position
				points.append([rel.x, rel.y, rel.z])
		var aa := label.get_aabb()
		var native_aabb: Array = []
		for i in 8:
			var rel: Vector3 = label.to_global(aa.get_endpoint(i)) - pad.global_position
			native_aabb.append([rel.x, rel.y, rel.z])
		rows[key] = {"triangles":points,"runtime_aabb":native_aabb,"outline":label.outline_size,"texture_filter":label.texture_filter,"text":label.text, "font_size": label.font_size, "fallback_font":font.get_font_name(), "string_metrics":[box.x,box.y],"glyph_texture_metrics":glyph_boxes, "point_projected":[midpoint.x,midpoint.y], "px_axis_x_for_30":[axis_x.x,axis_x.y], "px_axis_y_for_30":[axis_y.x,axis_y.y], "bounds_m_height":pad.fitted_bounds.size.y,"label_m_above_anchor":label.global_position.y - pad.global_position.y,"screen_line_axis_len_for_30":axis_y.length()}
	print("V5_PRICE ", JSON.stringify({"viewport":[v.size.x,v.size.y],"proj":camera.projection,"keep":camera.keep_aspect,"cam_size":camera.size,"label":rows}))
	quit(0)
