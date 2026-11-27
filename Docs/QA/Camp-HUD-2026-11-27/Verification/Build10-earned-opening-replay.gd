extends SceneTree

const Scene := preload("res://field_opening.tscn")
const Session := preload("res://tests/lifecycle_test_profile.gd")

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	var field = Scene.instantiate()
	root.add_child(field)
	current_scene = field
	var original := JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("ORIGINAL_FIXTURE"))) as Dictionary
	var saved := JSON.parse_string(original.payload) as Dictionary
	var p: Dictionary = saved.world.player
	var pos := Vector2(field.actor.position.x, field.actor.position.z)
	var checks := {
		"normal scene accepted Build 10 journal":field.field_ready and not field.persist_blocked,
		"paid camp is present":field.camp_active and field.inventory.build_order==saved.build_order,
		"first purchase and partial expansion payments retained":JSON.parse_string(JSON.stringify(field.inventory.paid))==saved.paid,
		"all earned material still accounted for":JSON.parse_string(JSON.stringify(field.inventory.carried))==saved.carried and JSON.parse_string(JSON.stringify(field.inventory.stored))==saved.stored and JSON.parse_string(JSON.stringify(field.inventory.collected))==saved.collected,
		"health restored":field.player_hp==int(p.hp),
		"saved safe position restored":pos.distance_to(Vector2(p.x,p.z))<0.001 and field.field_env.is_inside_camp(field.actor.position),
		"new status panel built":field.opening_hud.plate.name=="SurvivorStatus" and field.opening_hud.camp_dock.is_inside_tree()
	}
	print("UPGRADE_PROBE ", JSON.stringify({"checks":checks, "position_xz":[pos.x,pos.y],"health":field.player_hp,"paid":field.inventory.paid,"carried":field.inventory.carried,"collected_count":field.inventory.collected.size(),"build_order":field.inventory.build_order}))
	field.set_physics_process(false)
	field.carry.set_physics_process(false)
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 4: await process_frame
	quit(int(checks.values().has(false)))
