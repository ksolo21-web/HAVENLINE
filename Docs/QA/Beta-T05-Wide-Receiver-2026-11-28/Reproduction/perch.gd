extends "res://tests/field_route.gd"
const Session = preload("res://tests/lifecycle_test_profile.gd")
var output := OS.get_environment("HAVENLINE_WIDE_EVIDENCE")
var images := []
var movie := []

func _initialize() -> void:
	run.call_deferred()

func pause(ticks: int) -> void:
	for _i in ticks:
		await physics_frame

func photograph(gate_name: String, number: int, zoom: float) -> void:
	field.set_zoom_ratio(zoom)
	await process_frame
	RenderingServer.force_draw(false,1./60.)
	var frame := root.get_texture().get_image()
	var label := "%s-%d-%dx.jpg" % [gate_name,number,int(zoom)]
	frame.save_jpg(output.path_join(label),.92)
	var bird = field.owl
	images.append({"file":label,"state":bird.state,"yaw":bird.rotation.y,"lookout":bird.get("lookout_yaw"),"position":pt(bird.global_position),"foot_pad":pt(bird._perch()),"size":[frame.get_width(),frame.get_height()],"zoom":field.get_zoom_ratio()})

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene = field
	await pause(4)
	camera = field.camera
	for existing in field.enemies.duplicate(): field.encounters._remove(existing)
	field.encounters.remaining = 90.
	for i in field.inventory.costs.center_hearth.wood:
		field.inventory.collect("perch-hearth-"+str(i),"wood")
		field.inventory.payment("center_hearth","wood",false)
	field._finish_purchase("center_hearth")
	field._apply_hearth(true,false)
	field.actor.global_position = field.owl.Crew.ROOST_AT
	field.previous_dry_position = field.actor.global_position
	for i in field.owl.Crew.OWL_MEAT:
		field.inventory.collect("perch-payment-"+str(i),"meat")
	field.carry.sync(true)
	await pause(155)
	for i in [1,0]:
		var gate = field.gates[i]
		field.actor.global_position = gate.global_position - gate.global_basis.z*2.05
		field.previous_dry_position = field.actor.global_position
		for _tick in 360:
			await physics_frame
			if field.owl.state=="perched" and field.owl.post_index==i and field.owl.age>.48:
				break
		for sample in 3:
			await photograph("East" if i==1 else "South",sample,1.)
			await photograph("East" if i==1 else "South",sample,2.)
			await pause(52)
		field.set_zoom_ratio(1.)
	if OS.get_environment("HAVENLINE_WIDE_PERCH_MOVIE")=="1":
		for i in 36:
			await pause(4)
			await process_frame
			RenderingServer.force_draw(false,1./60.)
			root.get_texture().get_image().save_jpg(output.path_join("Scan-%03d.jpg"%i),.86)
			movie.append({"frame":i,"position":pt(field.owl.global_position),"state":field.owl.state,"head_yaw":field.owl.get("lookout_yaw")})
	var ok: bool = field.owl.Crew.owns_owl(field.inventory.settlement) and images.all(func(row): return row.state=="perched" and row.position==row.foot_pad)
	var record := FileAccess.open(output.path_join("Perch.json"),FileAccess.WRITE)
	record.store_string(JSON.stringify({"passed":ok,"renderer":RenderingServer.get_video_adapter_name(),"captures":images,"scan":movie},"  "))
	record.close()
	await Session.drain_field_audio(self,field)
	field.queue_free()
	await process_frame
	quit(int(not ok))
