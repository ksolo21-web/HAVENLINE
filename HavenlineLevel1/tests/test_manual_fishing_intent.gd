extends "res://tests/test_integrated_manual_shore_route.gd"
## Coordinates and tuning here are a temporary test binding, not authored cast data.
const Cast = preload("res://previews/manual_fishing_intent.gd")
const FIXTURE_KEY := KEY_G

func key_event(pressed: bool, echo := false, code: Key = FIXTURE_KEY) -> InputEventKey:
	var e := InputEventKey.new()
	e.physical_keycode = code
	e.pressed = pressed
	e.echo = echo
	return e

func refused(original: Dictionary, field: String, invalid: Variant) -> bool:
	var changed := original.duplicate()
	changed[field] = invalid
	return not Cast.new().bind(changed)

func run() -> void:
	game = GAME.instantiate()
	game.position = Vector3(2, 1.1, -3)
	root.add_child(game)
	if not game.bound:
		check(false, "accepted opening bound")
		quit(1)
		return
	await tick(10)
	var aim := BANK_ANCHOR.lerp(AcceptedRiver.center_at_x(BANK_ANCHOR.x), .66)
	var fixture := {
		"admitted":true,"spot_id":"shore-intent-fixture","bank_xz":BANK_ANCHOR,"aim_xz":aim,
		"bank_side":game.bank_side,"foot_radius":float(game.layout.actor_radius),
		"stand_tolerance":.14,"height_tolerance":SAMPLE_CONTACT_EPS,
		"cast_range":floor_point(BANK_ANCHOR).distance_to(Vector3(aim.x, AcceptedRiver.WATER_Y, aim.y)) + .2,
		"min_facing_dot":.75,"keycode":int(FIXTURE_KEY)
	}
	var cast := Cast.new()
	check(cast.capture(key_event(true), 1, game, game.actor, game.camera).status == "unadmitted", "no default or unadmitted intent")
	check(refused(fixture,"admitted",false), "caller-unadmitted fixture fails closed")
	check(refused(fixture,"bank_xz",aim), "wet standing point cannot bind")
	check(refused(fixture,"aim_xz",BANK_ANCHOR), "dry aim cannot bind")
	check(refused(fixture,"bank_xz",Vector2(42.0,0.0)), "off-map bank cannot bind")
	check(refused(fixture,"aim_xz",Vector2(42.0,0.0)), "off-map aim cannot bind")
	check(refused(fixture,"aim_xz",AcceptedRiver.center_at_x(10.0)), "reserved channel crossing cannot be bound as aim")
	check(refused(fixture,"bank_side",-game.bank_side), "opposite bank identity cannot bind")
	check(refused(fixture,"cast_range",.01), "aim incompatible with configured reach cannot bind")
	check(refused(fixture,"foot_radius",NAN), "non-finite footprint cannot bind")
	check(refused(fixture,"spot_id",StringName("identifier")), "coerced identity type not admitted")
	check(cast.bind(fixture) and not cast.bind(fixture), "admit explicit geometric source once, no history reset")
	check(not game.persist_requested, "ordinary combined preview remains no-save")
	await earn_camp()
	if failures > 0:
		quit(1)
		return
	var unchanged := var_to_bytes(game.ledger.snapshot())
	check(await travel(game.point([2.0, 1.9])), "normal inside route before casting")
	check(await reach_segment(INSIDE_EAST, "inside-east"), "patient East staging")
	press(KEY_E)
	await tick(70)
	check(game.gates[1].target_open and not game.gates[0].target_open, "ordinary East-only gate control")
	check(await reach_segment(OUTSIDE_EAST, "east-outward"), "normal physical gate crossing")
	check(await reach_segment(BANK_CORRIDOR_TURN, "out-to-turn"), "control route reaches far bank approach")
	check(cast.eligibility(game, game.actor, game.camera) == "away_from_anchor", "actual grounded outside-distance negative")
	check(cast.capture(key_event(true), 1, game, game.actor, game.camera).status == "away_from_anchor", "outside input produces no intent")
	check(cast.capture(key_event(false), 2, game, game.actor, game.camera).status == "released", "valid release clears denied press")
	check(await reach_segment(BANK_ANCHOR, "out-to-provisional-bank"), "normal grounded movement reaches provisional bank")
	await tick(12)
	check(cast.eligibility(game, game.actor, game.camera) == "eligible", "same-frame dry grounded camera-facing eligible")
	var air := CharacterBody3D.new()
	game.add_child(air)
	check(cast.eligibility(game, air, game.camera) == "airborne", "unsettled actor never eligible")
	air.queue_free()
	var actor_yaw: float = game.actor.rotation.y
	game.actor.rotation.y += PI
	check(cast.eligibility(game, game.actor, game.camera) == "wrong_facing", "facing away fails without state effects")
	game.actor.rotation.y = actor_yaw
	var camera_pose: Transform3D = game.camera.global_transform
	game.camera.global_position += Vector3(100, 0, 0)
	check(cast.eligibility(game, game.actor, game.camera) == "outside_view", "otherwise eligible target still needs active camera frustum")
	game.camera.global_transform = camera_pose
	check(cast.capture(key_event(true, false, KEY_H), 3, game, game.actor, game.camera).status == "wrong_input", "arbitrary key not interpreted as cast")
	var exact_mark := Vector3(aim.x, AcceptedRiver.WATER_Y, aim.y)
	var issued := cast.capture(key_event(true), 3, game, game.actor, game.camera)
	check(issued.status == "intent" and issued.spot_id == "shore-intent-fixture" and issued.sequence == 3 and issued.aim_world.is_equal_approx(game.to_global(exact_mark)), "one exact aim intent uses translated water datum")
	check(cast.capture(key_event(true), 3, game, game.actor, game.camera).status == "duplicate_or_stale", "replayed event sequence cannot emit")
	check(cast.capture(key_event(true), 2, game, game.actor, game.camera).status == "duplicate_or_stale", "older event cannot emit")
	check(cast.capture(key_event(true, true), 4, game, game.actor, game.camera).status == "echo", "echo cannot emit")
	check(cast.capture(key_event(true), 5, game, game.actor, game.camera).status == "held", "new sequence is insufficient without a release")
	check(cast.capture(key_event(false), 6, game, game.actor, game.camera).status == "released", "release itself emits no cast")
	check(cast.capture(key_event(true), 7, game, game.actor, game.camera).status == "intent", "new deliberate post-release edge may emit a new pure intent")
	check(var_to_bytes(game.ledger.snapshot()) == unchanged and not game.persist_requested, "no item, recipe, grant, receipt, stock or save effect")
	print("manual fishing intent checks=", checks, " failures=", failures)
	quit(1 if failures else 0)
