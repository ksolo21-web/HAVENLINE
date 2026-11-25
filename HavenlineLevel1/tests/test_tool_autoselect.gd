extends SceneTree
const Opening = preload("res://opening.tscn")
const Select = preload("res://tool_select.gd")
var checks := 0
var failures := 0

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, desc: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(desc)

func face(actor: Node3D, direction: Vector3) -> void:
	actor.rotation.y = atan2(direction.x, direction.z)

func run() -> void:
	check(Select.for_target("tree") == "axe", "tree resolves to the two-handed axe")
	check(Select.for_target("rock") == "pickaxe", "rock resolves to the two-handed pickaxe")
	check(Select.for_target("gate") == "", "unrelated targets do not invent a tool")
	var game = Opening.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	check(game.character_kit.ready, "character kit bound sockets and action clips")
	check(is_instance_valid(game.resource_rock), "stone node is in the level")
	var chop := StringName("l1_actions/chop")
	var mine := StringName("l1_actions/mine")
	check(game.character_kit._player.has_animation(chop) and game.character_kit._player.has_animation(mine), "chop and mine clips are on the rig")
	check(game.character_kit._palm_l != null and game.character_kit._palm_r != null, "both palm sockets exist")
	check(game.character_kit._palm_l.bone_name == "L_Hand" and game.character_kit._palm_r.bone_name == "R_Hand", "sockets are on the existing hand bones")

	game.actor.position = Vector3(-0.52, 0, 6)
	face(game.actor, Vector3.LEFT)
	check(game.resource_tree.can_address(game.actor.global_position, game.tree_facing()), "actor is in chop range")
	check(not game._rock_is_target(), "the stone is not the tree target")
	check(game.active_tool() == "axe", "auto-select equips the axe at the tree")
	game.request_tree_contact()
	check(game.resource_tree.strikes == 1, "chop contact reaches the tree")
	check(game.active_tool() == "axe" and game.character_kit.action == "chop", "chop state is the two-handed axe")

	game.actor.position = game.resource_rock.global_position + Vector3(1.1, 0, 0)
	face(game.actor, Vector3.LEFT)
	check(game.resource_rock.can_address(game.actor.global_position, game.tree_facing()), "actor is in mine range")
	check(not game._tree_is_target(), "the tree is not the stone target")
	# The chop timer is still running; a new target must retarget once that swing is not forced.
	game.character_kit.action = ""
	game.character_kit.action_left = 0.0
	check(game.active_tool() == "pickaxe", "auto-select equips the pickaxe at the rock")
	game.request_rock_contact()
	check(game.resource_rock.strikes == 1 and game.resource_rock.phase == "seated", "first mine strike counts and leaves the rock")
	check(game.character_kit.action == "mine" and game.active_tool() == "pickaxe", "mine state is the two-handed pickaxe")
	check(game.ledger.stock.wood == 0, "mining does not grant wood")
	print("Tool autoselect checks: ", checks, ", failures: ", failures)
	quit(0 if failures == 0 else 1)
