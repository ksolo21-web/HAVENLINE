extends "res://tests/field_route.gd"

const Session := preload("res://tests/lifecycle_test_profile.gd")
const CameraPolicy := preload("res://field_camera.gd")
const TEST := "res://tests/qa_field_camera_composition.gd"
const DISPLAYS := [Vector2i(360,840),Vector2i(492,546),Vector2i(896,672),Vector2i(960,540),
	Vector2i(1000,450),Vector2i(960,600),Vector2i(840,360),Vector2i(546,492)]
var checks := {}
var samples := []

func _initialize() -> void:
	if not Session.isolated(self,TEST): run.call_deferred()

func pay(id: String) -> void:
	for kind in field.inventory.remaining(id):
		var amount: int = field.inventory.remaining(id)[kind]
		for i in amount: field.inventory.collect("camera-%s-%s-%d" % [id,kind,i],kind)
		field.inventory.payment(id,kind,false,amount)
	field._finish_purchase(id)

func pose(at: Vector3) -> void:
	field.actor.global_position = at
	field.previous_dry_position = at
	field.actor.velocity = Vector3.ZERO
	for i in 68:
		field.follow_camera(1.0/60.0)
	await process_frame

func visible(at: Vector3) -> bool:
	var canvas := root.get_visible_rect()
	var pixel := camera.unproject_position(at)
	if not canvas.grow(-5.0).has_point(pixel): return false
	var hud = field.opening_hud
	for control in [hud.plate,hud.objective,hud.camp_dock.nav,hud.get_node("HomeCompass")]:
		if control.visible and control.get_global_rect().has_point(pixel): return false
	return not hud.counts_area.has_point(pixel) and not CameraPolicy.quality_plate(hud.quality).has_point(pixel)

func record(label: String, zoom: float, basis: Basis, context: PackedVector3Array, minimum: int) -> void:
	var feet: Vector3 = field.actor.global_position
	var head := feet+Vector3.UP*float(field.layout.actor_height)
	var view := root.get_visible_rect()
	var player_span := camera.unproject_position(head).distance_to(camera.unproject_position(feet)) / minf(view.size.x,view.size.y)
	var baseline := float(field.layout.actor_height)*basis.y.y/13.0
	var count := 0
	for point in context:
		if visible(point): count += 1
	checks[label+" uses fixed orthographic angle and body scale"] = camera.projection==Camera3D.PROJECTION_ORTHOGONAL and camera.global_basis.is_equal_approx(basis) and absf(player_span-baseline*zoom)<.002
	checks[label+" keeps the player and nearby action clear of HUD"] = visible(feet) and visible(head) and count>=minimum
	samples.append({"view":label,"screen":str(root.size),"zoom":field.get_zoom_ratio(),"lead_height_short_axis":player_span,"visible_points":count,"context_points":context.size()})

func pinch() -> void:
	var center := root.get_visible_rect().size*.5
	touch(41,center-Vector2(26,0),true)
	touch(42,center+Vector2(26,0),true)
	var event := InputEventScreenDrag.new()
	event.index = 42
	event.position = center+Vector2(112,0)
	root.push_input(event,true)
	touch(41,center-Vector2(26,0),false)
	touch(42,center+Vector2(112,0),false)

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	for i in 6: await physics_frame
	field.set_physics_process(false)
	camera = field.camera
	var basis := camera.global_basis
	for id in ["center_hearth","expansion_1","storage_wood","storage_stone","storage_meat","expansion_2","camp_cooker"]: pay(id)
	field.reveal_countdown = -1.0
	field._apply_hearth(true,false)
	field.settlement_loop.advance(1.0/60.0)
	for i in 385: field.counter.advance(1.0/60.0)
	checks["ordinary camp purchases expose a live three-customer queue"] = field.counter.active and field.counter.queue.size()==3
	var queue := PackedVector3Array([field.counter.food_rest.global_position])
	for visitor in field.counter.queue:
		queue.append(visitor.body.global_position+Vector3.UP*1.52)
	var service: Vector3 = field.counter.service_point.global_position+Vector3(.79,0,.48)
	checks["queue framing is tested from the real service zone"] = field.counter.at_service(service)
	var first_order: Node3D = field.counter.queue[0].request if not field.counter.queue.is_empty() else null
	for screen in DISPLAYS:
		field.set_zoom_ratio(1.)
		var old_screen := root.size
		var at := root.get_visible_rect().size*Vector2(.45,.63)
		touch(15,at,true)
		root.size = screen
		field.graphics.refresh_window()
		await process_frame
		checks["display %s clears old touch coordinates" % str(screen)] = old_screen==root.size or field.touch_id<0
		await pose(service)
		record("queue %s normal" % str(screen),1.,basis,queue,4)
		pinch()
		await pose(service)
		record("queue %s pinch" % str(screen),2.,basis,queue,4)
		checks["display %s keeps the paying order visible at pinch" % str(screen)] = is_instance_valid(first_order) and visible(first_order.global_position)
		var source: Node3D = field.carry.receivers.get(field.next_project)
		if is_instance_valid(source) and source.visible:
			await pose(source.global_position + basis.x*2.72 + Vector3.BACK*.78)
			record("plot %s pinch" % str(screen),2.,basis,PackedVector3Array([source.global_position]),1)
	var from_counter := camera.global_position
	await pose(Vector3(-38.,0.,19.))
	checks["leaving every action clears the last context and follows the new position"] = camera.global_position.distance_to(from_counter)>15. and visible(field.actor.global_position)
	var stable := camera.global_position
	for invalid in [0.0,-1.0,NAN,INF]: field.follow_camera(invalid)
	checks["invalid update intervals leave a finite camera unchanged"] = camera.global_position.is_finite() and camera.global_position.is_equal_approx(stable)
	checks["invalid viewport dimensions return a finite short-axis span"] = CameraPolicy.view_span(13.0,Vector2.ZERO)==Vector2(13.,13.)
	print("FIELD_CAMERA_COMPOSITION ",JSON.stringify({"checks":checks,"samples":samples}))
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 4: await process_frame
	quit(int(checks.values().has(false)))
