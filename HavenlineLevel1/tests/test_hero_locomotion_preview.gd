extends SceneTree
const GAME = preload("res://previews/integrated_opening.tscn")
const CENTER := Vector2(450, 375)
var game
var checks := 0
var failures := 0
var gesture := 180

func _initialize() -> void:
	call_deferred("run")

func test(ok: bool, name: String) -> void:
	checks += 1
	if not ok:
		failures += 1
	print("%s %s" % ["PASS" if ok else "FAIL", name])

func tick(count: int) -> void:
	for i in range(count):
		await physics_frame

func touch(down: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.device = 1
	event.index = gesture
	event.position = CENTER
	event.pressed = down
	game._input(event)

func drag(direction: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.device = 1
	event.index = gesture
	event.position = CENTER + direction * 82.0
	game._input(event)

func run() -> void:
	game = GAME.instantiate()
	root.add_child(game)
	if not game.bound or not is_instance_valid(game.hero_locomotion.player):
		test(false, "exact imported player and preview bind")
		quit(1)
		return
	await tick(25)
	var controller = game.hero_locomotion
	var player: AnimationPlayer = controller.player
	var visuals := player.get_parent() as Node3D
	var visual_offset := visuals.position
	var start_position := game.actor.position as Vector3
	var skin: Skeleton3D = game.actor.find_children("*", "Skeleton3D", true, false)[0]
	var hand := skin.find_bone("L_Hand")
	test(hand >= 0, "exact left-hand joint exists")
	test(player.current_animation == "l1_hero_preview/idle" and player.is_playing(), "idle is already playing")
	var idle_before: Array[Transform3D] = []
	for joint in range(skin.get_bone_count()):
		idle_before.append(skin.get_bone_global_pose(joint))
	var time0 := player.current_animation_position
	await tick(24)
	var any_idle_deformation := false
	for joint in range(skin.get_bone_count()):
		var pose := skin.get_bone_global_pose(joint)
		var old := idle_before[joint]
		var delta := pose.basis.get_rotation_quaternion().angle_to(old.basis.get_rotation_quaternion())
		if delta > .001 or pose.origin.distance_to(old.origin) > .0005:
			any_idle_deformation = true
	test(any_idle_deformation and not is_equal_approx(time0, player.current_animation_position), "idle advances and deforms the stock skeleton over time")
	test(Vector2(start_position.x, start_position.z).distance_to(Vector2(game.actor.position.x, game.actor.position.z)) < .001, "idle clip cannot drive body position")

	# Regular touch inputs at half and full deflection. Choose a dry, empty
	# screen-horizontal direction with room clear of the original starter tree.
	touch(true)
	drag(Vector2(.43, 0))
	await tick(12)
	test(controller.current == "walk" and player.current_animation == "l1_hero_preview/walk", "partial ordinary drag produces walk")
	drag(Vector2(1, 0))
	await tick(12)
	test(controller.current == "run" and player.current_animation == "l1_hero_preview/run", "full ordinary drag produces run")
	test(Vector2(start_position.x, start_position.z).distance_to(Vector2(game.actor.position.x, game.actor.position.z)) > .25, "actual horizontal travel occurred")
	touch(false)
	await tick(13)
	test(controller.current == "idle", "ordinary release settles to idle")
	test(visuals.position.is_equal_approx(visual_offset), "animation does not change visual root offset")

	# Test fixture only: wall in the same admitted direction, no change to
	# original world, collider, pad, or state. Slides cannot fake forward travel.
	var direction := Vector3(1, 0, 0).rotated(Vector3.UP, atan2(7.0, 11.0))
	var wall := StaticBody3D.new()
	wall.collision_layer = 1
	wall.rotation.y = atan2(direction.x, direction.z)
	var block := CollisionShape3D.new()
	var slab := BoxShape3D.new()
	slab.size = Vector3(5.0, 3.0, .12)
	block.shape = slab
	wall.add_child(block)
	game.add_child(wall)
	wall.position = game.actor.position + direction * .85 + Vector3.UP
	await tick(3)
	gesture += 1
	touch(true)
	drag(Vector2(1, 0))
	await tick(30)
	var stopped := game.actor.position as Vector3
	await tick(18)
	var final := game.actor.position as Vector3
	test(Vector2(stopped.x, stopped.z).distance_to(Vector2(final.x, final.z)) < .02, "physical wall stops actual normal-input movement")
	test(controller.current == "idle" and player.current_animation == "l1_hero_preview/idle", "continued blocked input cannot run in place")
	test(game.bound and not game.persist_requested and game.ledger.receipt.is_empty() and not game.camp_built.visible, "animation never activates save or camp")
	touch(false)
	print("hero locomotion checks=%d failures=%d" % [checks, failures])
	quit(0 if failures == 0 else 1)
