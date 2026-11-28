extends "res://tests/qa_snow_truck.gd"

const GREEN := Color("#5be72e")
const WHITE := Color("#f8fbff")
var witnesses := []
var output := OS.get_environment("T07_PATCH_REVIEW_OUT")
var native := OS.get_environment("T07_PATCH_REVIEW_STILLS") == "1"
var compass: Control

func _initialize() -> void:
	run.call_deferred()

func witness(name: String, state: Dictionary) -> void:
	state["label"] = name
	state["tick"] = Engine.get_physics_frames()
	witnesses.append(state)
	if native:
		RenderingServer.force_draw(false)
		root.get_texture().get_image().save_jpg(output.path_join(name + ".jpg"), .83)

func _color() -> Color:
	return field.field_env.payment_brackets["buy"].get_shader_parameter("pigment")

func _plot_report() -> Dictionary:
	return {"due": field.inventory.remaining("center_hearth").wood, "color": _color().to_html(),
		"fill": field.field_env.payment_ink["buy"].get_shader_parameter("paid"),
		"action": field.context.descriptor.get("id", ""), "state": field.context.descriptor.get("state", ""),
		"flights": field.carry.flights.size(), "player": pt(field.actor.global_position)}

func gate_markers_hidden() -> bool:
	var markers: Array[Node] = field.camp_built.find_children("*-technical-marker-*", "Node3D", false, false)
	return markers.size() == field.gates.size()*2 and markers.all(func(marker: Node3D) -> bool: return not marker.visible)

func plot_route() -> void:
	_assert("legacy gate markers are explicitly hidden before paying",gate_markers_hidden())
	var pad: Vector3 = field.field_env.buy_anchor.global_position
	var price: int = field.inventory.remaining("center_hearth").wood
	field.actor.global_position = pad + Vector3(0., 0., 2.03)
	field.previous_dry_position = field.actor.global_position
	for index in price:
		field.inventory.collect("review-independent-hearth-%d" % index, "wood")
	field.carry.sync(true)
	steer(_heading(Vector3.FORWARD))
	var approach_checked := false
	for _step in 42:
		await physics_frame
		if not approach_checked and field.context.descriptor.get("id") == "pad:center_hearth" and field.context.descriptor.get("state") == "blocked_movement":
			approach_checked = true
			_assert("moving approach cannot show the authorized highlight or pay", _color().is_equal_approx(WHITE) and field.carry.flights.is_empty())
			witness("plot-approach", _plot_report())
		if field.actor.global_position.z <= pad.z + .34: break
	_assert("approach entered plot reach on actual thumbstick", approach_checked)
	steer(Vector2.ZERO)
	var saw_focus := false
	var saw_launch := false
	for _step in 65:
		await physics_frame
		var cost: int = field.inventory.remaining("center_hearth").wood
		if not saw_focus and _color().is_equal_approx(GREEN) and field.carry.flights.is_empty() and cost == price:
			saw_focus = true
			witness("plot-green-before-transfer", _plot_report())
		if not saw_launch and not field.carry.flights.is_empty():
			saw_launch = true
			witness("plot-first-launch", _plot_report())
		if cost < price:
			witness("plot-first-receipt", _plot_report())
			break
	_assert("green focus precedes first launched parcel and receipt", saw_focus and saw_launch)
	var after_first: int = field.inventory.remaining("center_hearth").wood
	var in_transit := 0
	for flight in field.carry.flights: in_transit += int(flight.units)
	steer(_heading(Vector3.BACK))
	var confirmed_partial := false
	for _step in 12:
		await physics_frame
		if field.context.descriptor.get("state") == "blocked_movement" and field.context.descriptor.get("id") == "pad:center_hearth" and not confirmed_partial:
			confirmed_partial = true
			witness("plot-partial-while-moving", _plot_report())
			_assert("moving clears focus color and preserves paid fill", _color().is_equal_approx(WHITE) and field.field_env.payment_ink["buy"].get_shader_parameter("paid") > 0.)
	_assert("cancel keeps existing credit and permits no new spending", confirmed_partial and field.inventory.remaining("center_hearth").wood >= after_first - in_transit)
	for _step in 45:
		if field.actor.global_position.distance_to(pad) <= .24: break
		var direction: Vector3 = pad - field.actor.global_position
		direction.y = 0.
		steer(_heading(direction))
		await physics_frame
	steer(Vector2.ZERO)
	for _step in 210:
		await physics_frame
		if field.camp_active: break
	_assert("re-entry completes just one legitimate purchase", field.camp_active and field.inventory.build_order.count("center_hearth") == 1)
	_assert("both legacy posts on either side of both openings stay hidden at reveal",gate_markers_hidden())
	witness("plot-reveal", _plot_report())

func _compass_report() -> Dictionary:
	return {"compass": compass.label.text, "accessible": compass.label.accessibility_name,
		"direction": [compass.route.direction_target.x, compass.route.direction_target.y], "gate": compass.route.gate_index,
		"shown": compass.visible, "mounted": truck.mounted, "truck": pt(truck.body.global_position), "parked": truck.parked()}

func vehicle_route() -> void:
	for id in ["center_hearth", "expansion_1", "storage_wood", "storage_stone", "storage_meat", "expansion_2", "snow_garage", "snow_truck"]:
		if field.inventory.complete(id): continue
		_assert("prepared paid " + id, _fund(id))
		if id == "center_hearth":
			for _step in 16: await physics_frame
	for _step in 10: await physics_frame
	field.actor.global_position = truck._exit_position()
	field.previous_dry_position = field.actor.global_position
	for _step in 4: await physics_frame
	await _key()
	_assert("boardable with the regular input action", truck.mounted)
	compass.refresh()
	_assert("parked truck has no redundant return compass", not compass.visible)
	steer(_heading(Vector3.BACK))
	for _step in 125:
		await physics_frame
		if truck.body.global_position.z > 8.6: break
	steer(Vector2.ZERO)
	for _step in 3: await physics_frame
	compass.refresh()
	witness("garage-route-front", _compass_report())
	_assert("outside mounted compass directs to usable garage opening", compass.visible and compass.label.text.begins_with("Snow garage") and compass.route.gate_index == -1 and absf(compass.route.direction_target.x - truck.garage.global_position.x) < .02)
	var bounds: Vector4 = field.field_env.COURTS[field.field_env.perimeter_stage-1]
	truck.body.global_position = Vector3(bounds.z + 3.4, 0., 0.)
	field.actor.global_position = truck.body.global_position
	for _step in 3: await physics_frame
	compass.refresh()
	witness("garage-route-east", _compass_report())
	_assert("mounted compass still routes around fence from east", compass.visible and compass.label.text.begins_with("Snow garage") and compass.route.gate_index == -1 and compass.route.direction_target.x > bounds.z)
	await _key()
	for _step in 5: await physics_frame
	compass.refresh()
	_assert("dismount restores the pedestrian gate compass", not truck.mounted and compass.visible and compass.label.text.begins_with("Camp gate") and compass.route.gate_index >= 0)
	witness("foot-route-east", _compass_report())

func run() -> void:
	field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	camera = field.camera
	truck = field.snow_truck
	origin = root.get_visible_rect().size * Vector2(.28, .71)
	for _step in 8: await physics_frame
	compass = field.opening_hud.get_node("HomeCompass")
	field.encounters.remaining = 900.
	for wolf in field.enemies.duplicate(): field.encounters._remove(wolf)
	await plot_route()
	await vehicle_route()
	print("INDEPENDENT_PATCH ", JSON.stringify({"checks": checks, "events": witnesses, "viewport": [root.size.x, root.size.y],
		"source": {"context": FileAccess.get_sha256("res://field_context.gd"), "navigation": FileAccess.get_sha256("res://field_navigation.gd"),
		"route": FileAccess.get_sha256("res://field_home_route.gd"), "truck": FileAccess.get_sha256("res://field_snow_truck.gd")}}))
	await _close_field()
	quit(0 if not checks.values().has(false) else 1)
