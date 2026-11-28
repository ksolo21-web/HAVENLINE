extends "res://tests/field_route.gd"
const Session = preload("res://tests/lifecycle_test_profile.gd")
const Art = preload("res://field_art.gd")
var output := OS.get_environment("HAVENLINE_WIDE_EVIDENCE")
var bounds := {}
var frames := []
var stride_frames := []

func _initialize() -> void:
	run.call_deferred()

func photograph(tag: String, zoom: float) -> void:
	field.set_zoom_ratio(zoom)
	field.camera.global_position = field.actor.global_position + field.camera_follow_offset
	await process_frame
	RenderingServer.force_draw(false,1./60.)
	var frame := root.get_texture().get_image()
	var filename := "%s-%dx.jpg" % [tag,int(zoom)]
	frame.save_jpg(output.path_join(filename),.92)
	frames.append({"file":filename,"zoom":field.get_zoom_ratio(),"position":pt(field.actor.global_position),"size":[frame.get_width(),frame.get_height()]})

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene = field
	await physics_frame
	field.set_physics_process(false)
	field.world_landscape.set_physics_process(false)
	for wolf in field.enemies.duplicate(): field.encounters._remove(wolf)
	camera = field.camera
	var origin_ := Vector3(2.0,0,6.8)
	var right := camera.global_basis.x
	var near := right.cross(Vector3.UP)
	field.actor.global_position = origin_
	for i in field.inventory.KINDS.size():
		var kind: String = field.inventory.KINDS[i]
		var center := origin_ + near*(2.74 if i<3 else -2.62) + right*(float(i%3)-1.)*1.47
		for j in 3:
			var p := center+Vector3(cos(float(j)*TAU/3.),0,sin(float(j)*TAU/3.))* .48
			var label := "size-%s-%d" % [kind,j]
			field._place_drop(label,kind,p+Vector3.UP*.28,p,.15*j,0.)
			var boxes: Array[AABB] = []
			Art._bounds(field.drops[label].mesh,Transform3D.IDENTITY,boxes)
			var body := boxes[0]
			for b in boxes:
				body = body.merge(b)
			bounds[kind] = {"width_m":maxf(body.size.x,body.size.z),"size":pt(body.size)}
	field.actor.global_position = origin_+near*18.
	field._step_drops(.32)
	field.actor.global_position = origin_
	await photograph("Snow-drops",1.)
	await photograph("Snow-drops",2.)
	for token in field.drops.keys():
		if not field.drops.has(token): continue
		field.actor.global_position = field.drops[token].at + near*.57
		field._step_drops(.33)
		field.carry.advance(.40)
	field.actor.global_position = origin_
	field.actor.rotation.y = atan2(-near.x,-near.z)
	field.carry.sync()
	await photograph("Loaded-pack",1.)
	await photograph("Loaded-pack",2.)
	var quarter := (-near+right*.83).normalized()
	field.actor.rotation.y = atan2(quarter.x,quarter.z)
	field.carry.advance(1./60.)
	await photograph("Quarter-pack",1.)
	await photograph("Quarter-pack",2.)
	if OS.get_environment("HAVENLINE_WIDE_CARRY_MOVIE")=="1":
		field.set_zoom_ratio(1.)
		field.previous_dry_position = field.actor.global_position
		field.encounters.remaining = 90.
		field.set_physics_process(true)
		origin = root.get_visible_rect().size*Vector2(.19,.68)
		steer(Vector2(.80,-.28))
		for i in 18:
			for _tick in 4:
				await physics_frame
			await process_frame
			RenderingServer.force_draw(false,1./60.)
			root.get_texture().get_image().save_jpg(output.path_join("Stride-%03d.jpg"%i),.86)
			stride_frames.append({"frame":i,"actor":pt(field.actor.global_position),"velocity":pt(field.actor.velocity),"zoom":field.get_zoom_ratio()})
		steer(Vector2.ZERO)
	var collected: Dictionary = field.inventory.carried.duplicate()
	var okay: bool = collected.values().all(func(count):return count==3) and field.drops.is_empty()
	var record := FileAccess.open(output.path_join("Resources.json"),FileAccess.WRITE)
	record.store_string(JSON.stringify({"passed":okay,"quantities":collected,"world_bounds":bounds,"pack_widths":field.carry.WIDTH,"renderer":RenderingServer.get_video_adapter_name(),"frames":frames,"stride":stride_frames},"  "))
	record.close()
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(int(not okay))
