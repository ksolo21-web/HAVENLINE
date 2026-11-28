extends "res://tests/field_route.gd"
const Session = preload("res://tests/lifecycle_test_profile.gd")
var output := OS.get_environment("HAVENLINE_PATCH_EVIDENCE")
var frames := []
var found := {}
var foe: Node3D

func _initialize() -> void:
	run.call_deferred()

func step(count:int) -> void:
	for i in count: await physics_frame

func pinch() -> void:
	var center := root.get_visible_rect().size*Vector2(.57,.44)
	touch(12,center-Vector2(25,0),true)
	touch(13,center+Vector2(25,0),true)
	for i in 8:
		var drag := InputEventScreenDrag.new()
		drag.index = 13
		drag.position = center+Vector2(25+12*i,0)
		root.push_input(drag,true)
		await physics_frame
	touch(12,center-Vector2(25,0),false)
	touch(13,center+Vector2(110,0),false)

func photograph(label: String) -> void:
	await process_frame
	RenderingServer.force_draw(false,1./60.)
	var frame := root.get_texture().get_image()
	frame.save_jpg(output.path_join(label+".jpg"),.90)
	var bird = field.owl
	frames.append({"view":label,"state":bird.state,"zoom":field.get_zoom_ratio(),
		"owl":pt(bird.global_position),"player":pt(field.actor.global_position),
		"wolf":pt(foe.global_position) if is_instance_valid(foe) else [],
		"camera":pt(camera.global_position),"hits":field.inventory.settlement.owl_hits,
		"wolf_hp":foe.hp if is_instance_valid(foe) else -1,
		"pixels":[frame.get_width(),frame.get_height()]})

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	current_scene=field
	await step(6)
	camera = field.camera
	origin = root.get_visible_rect().size*Vector2(.19,.68)
	for existing in field.enemies.duplicate():field.encounters._remove(existing)
	for i in field.inventory.costs.center_hearth.wood:
		field.inventory.collect("proof-hearth-"+str(i),"wood")
		field.inventory.payment("center_hearth","wood",false)
	field._finish_purchase("center_hearth")
	field._apply_hearth(true,false)
	field.actor.global_position=field.owl.Crew.ROOST_AT
	field.previous_dry_position=field.actor.global_position
	for i in field.owl.Crew.OWL_MEAT:field.inventory.collect("proof-owl-"+str(i),"meat")
	field.carry.sync(true)
	await step(145)
	if not field.owl.Crew.owns_owl(field.inventory.settlement):
		push_error("Fixture did not earn the owl");quit(1);return
	for existing in field.enemies.duplicate():field.encounters._remove(existing)
	field.encounters.remaining=90.
	var gate: Vector3 = field.gates[1].global_position
	field.actor.global_position=gate-Vector3(2.,0,0)
	field.previous_dry_position=field.actor.global_position
	for i in 260:
		if move_to([gate.x+6.2,gate.z+1.1],.24):break
		await step(1)
	steer(Vector2.ZERO)
	if field.field_env.is_inside_camp(field.actor.global_position):
		push_error("Touch character could not reach exterior");quit(1);return
	await step(22)
	await pinch()
	await step(12)
	if field.get_zoom_ratio()<1.95:
		push_error("Pinch event did not set the maximum zoom");quit(1);return
	var right := camera.global_basis.x
	var near := right.cross(Vector3.UP)
	var mark: Vector3 = field.actor.global_position+right*3.8-near*.5
	field.encounters.serial+=1
	foe=field.encounters._add(mark,true,field.encounters.serial,mark)
	var starting_hits: int = field.inventory.settlement.owl_hits
	for i in 390:
		await step(1)
		var state: String = field.owl.state
		if state not in ["bank","windup","dive","strike","recover"]:continue
		if not found.has(state):
			found[state]=true
			if state == "strike":
				await photograph("Strike-2x")
				field.set_zoom_ratio(1.)
				field.follow_camera(1./60.)
				await photograph("Strike-1x")
				field.set_zoom_ratio(2.)
			else:
				await photograph(state.capitalize()+"-2x")
		if state=="recover" and field.inventory.settlement.owl_hits>starting_hits and found.has("strike"):break
	var report := {"frames":frames,"confirmed_hit":field.inventory.settlement.owl_hits>starting_hits,
		"outdoor":not field.field_env.is_inside_camp(field.actor.global_position),
		"renderer":RenderingServer.get_video_adapter_name(),"contact_points_from_original_morphed_vertices":true}
	var result := FileAccess.open(output.path_join("Field-attack.json"),FileAccess.WRITE)
	result.store_string(JSON.stringify(report,"  "))
	result.close()
	var okay: bool = report.confirmed_hit and found.has_all(["windup","dive","strike","recover"])
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 4:await process_frame
	quit(int(not okay))
