extends SceneTree

const Harvest = preload("res://scripts/harvest_presentation.gd")
const Director = preload("res://scripts/context_director.gd")
const Motion = preload("res://scripts/character1_motion.gd")
const Transfer = preload("res://scripts/transfer_feedback.gd")
const Main = preload("res://scripts/main.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name":label, "passed":passed, "detail":detail})
	if not passed:
		failures.append(label)

func option(resource: String, progress: float) -> Dictionary:
	return {
		"kind":"gather", "id":resource + ":source:0", "position":Vector2(0,1),
		"eligible":true, "priority":0.0, "capability":"gather_with_tools",
		"radius":2.0, "target_relevance":1.0, "progress":progress,
	}

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	check("T06 maps wood to chop", Motion.motion_for_action({"kind":"gather","id":"wood:source:0"}) == "chop")
	check("T06 maps stone and metal to mine", Motion.motion_for_action({"kind":"gather","id":"stone:source:0"}) == "mine" and Motion.motion_for_action({"kind":"gather","id":"metal:source:0"}) == "mine")
	check("T06 maps fuel to dismantle", Motion.motion_for_action({"kind":"gather","id":"fuel:source:0"}) == "dismantle")

	var harvest := Harvest.new()
	var transfer := Transfer.new()
	root.add_child(harvest)
	root.add_child(transfer)
	var actor := Node3D.new()
	root.add_child(actor)
	var right_hand := Marker3D.new()
	right_hand.name = "C1RightHandContact"
	actor.add_child(right_hand)
	var left_hand := Marker3D.new()
	left_hand.name = "C1LeftHandContact"
	actor.add_child(left_hand)
	var wood_profile := Harvest.profile_for_resource("wood")
	var wood_anchor := (Vector3(wood_profile.grip_socket)+Vector3(wood_profile.second_hand_socket))*0.5
	right_hand.position = Vector3(wood_profile.grip_socket)-wood_anchor
	left_hand.position = Vector3(wood_profile.second_hand_socket)-wood_anchor
	harvest.bind_actor(actor)
	var source_visual := Node3D.new()
	root.add_child(source_visual)
	check("T09 binds the simulation-owned source visual", harvest.bind_source("wood:source:0","wood",source_visual,2))
	var director := Director.new()
	var inventory := {"wood":0,"stone":0,"metal":0,"fuel":0}
	var inventory_before := inventory.duplicate(true)

	var acquiring := director.advance(0.05,Vector2.ZERO,Vector2.DOWN,Vector2.ZERO,Vector2.ZERO,"player_lead",[option("wood",0.56)])
	var premature := {"kind":"gather","resource":"wood","source_id":String(acquiring.id),"action_token":int(acquiring.action_token),"progress":float(acquiring.progress),"role":"player_lead","actionable":bool(acquiring.actionable)}
	check("T09 rejects non-actionable T07 acquisition dwell", not harvest.begin_action(premature,1))
	var selected := director.advance(0.08,Vector2.ZERO,Vector2.DOWN,Vector2.ZERO,Vector2.ZERO,"player_lead",[option("wood",0.56)])
	check("T07 automatically activates nearby gather context", selected.state == "active" and selected.actionable and selected.identity == "gather:wood:source:0",selected)
	check("T07 still emits no gameplay impact", selected.simulation_authoritative and not selected.emits_gameplay_event)
	var action := {
		"kind":"gather", "resource":"wood", "source_id":String(selected.id),
		"action_token":int(selected.action_token), "progress":float(selected.progress),
		"role":"player_lead", "actionable":bool(selected.actionable),
	}
	check("T09 accepts canonical T07 identity plus authoritative resource", harvest.begin_action(action,1))
	var synthetic_target := Vector3(wood_profile.impact_socket)-wood_anchor
	var presented := harvest.update_action(action,Transform3D.IDENTITY,synthetic_target)
	check("T09 equips the T06 chop contact without pre-commit impact", not presented.contact_ready and presented.tool == "axe" and presented.contact_marker == "C1TwoHandContact")
	var motion_action := harvest.motion_action(action)
	check("T09 remaps presentation progress without changing the T07 action", float(motion_action.progress) < float(action.progress) and float(action.progress) == float(selected.progress))

	var committed := {
		"committed":true, "resource":"wood", "source_id":String(selected.id),
		"action_token":int(selected.action_token), "receipt_id":"simulation:gather:1",
		"target_position":synthetic_target, "actor_id":1,
	}
	presented = harvest.synchronize_committed_contact(action,Transform3D.IDENTITY,synthetic_target,1)
	check("authoritative commit arms exact T06 contact", presented.contact_ready and presented.commit_contact_armed and is_equal_approx(presented.progress,0.56))
	check("authoritative committed impact activates T09 feedback", harvest.accept_committed_impact(committed))
	check("the same committed receipt starts one T08 source-to-actor transfer", transfer.transfer("wood",Vector3(0,0.8,1.0),Vector3(0,1.2,0),String(committed.receipt_id),"source_to_actor",1,"actor:1"))
	check("replayed commit fails in both T09 and T08", not harvest.accept_committed_impact(committed) and not transfer.transfer("wood",Vector3(0,0.8,1.0),Vector3(0,1.2,0),String(committed.receipt_id),"source_to_actor",1,"actor:1"))
	check("presentation modules cannot mutate logical inventory", inventory == inventory_before and not harvest.descriptor().mutates_inventory and not transfer.descriptor().mutates_inventory)
	check("depletion visibility follows authoritative units", harvest.sync_source("wood:source:0",0,0.0) and not source_visual.visible)
	check("respawn visibility follows authoritative units", harvest.sync_source("wood:source:0",2,0.0) and source_visual.visible)

	var moving := director.advance(0.01,Vector2.ZERO,Vector2.DOWN,Vector2(0,0.2),Vector2.ZERO,"player_lead",[option("wood",0.56)])
	if bool(moving.get("cancelled",false)):
		harvest.cancel(String(moving.reason))
	check("T07 movement cancellation removes T09 tool", moving.state == "blocked_movement" and not harvest.descriptor().active and harvest.descriptor().last_cancel_reason == "movement_owns_locomotion")

	director.reset()
	harvest.reset()
	director.advance(0.05,Vector2.ZERO,Vector2.DOWN,Vector2.ZERO,Vector2.ZERO,"player_lead",[option("fuel",0.61)])
	selected = director.advance(0.08,Vector2.ZERO,Vector2.DOWN,Vector2.ZERO,Vector2.ZERO,"player_lead",[option("fuel",0.61)])
	action = {"kind":"gather","resource":"fuel","source_id":String(selected.id),"action_token":int(selected.action_token),"progress":float(selected.progress),"role":"player_lead","actionable":bool(selected.actionable)}
	check("fuel reacquires automatically after cancellation", selected.actionable and harvest.begin_action(action,1))
	harvest.update_action(action,Transform3D.IDENTITY,Vector3(0,0.8,1.0),false)
	check("hidden actor immediately clears equipped tool", not harvest.descriptor().active and harvest.descriptor().last_cancel_reason == "actor_not_presented")
	check("T09 preserves one-joystick zero-action-button language", Director.contract().one_primary_movement_joystick and Harvest.contract().permanent_action_buttons == 0)
	check("T09 adds no persistence field", not Harvest.contract().adds_save_fields)

	var game := Main.new()
	game.size = Vector2(1280,720)
	root.add_child(game)
	for frame in 4:
		await process_frame
	game.set_process(false)
	game.set_physics_process(false)
	for pine_variant in range(1,4):
		var pine_mesh: ArrayMesh = game.merged_cache["world/pine_%d" % pine_variant]
		var crown_cutaway_flags: Array[bool] = []
		for surface_index in pine_mesh.get_surface_count():
			var pine_material: ShaderMaterial = pine_mesh.surface_get_material(surface_index)
			crown_cutaway_flags.append(bool(pine_material.get_shader_parameter("crown_cutaway")))
		check("wood variant %d sightline cutaway affects only its authored crown surface" % pine_variant,crown_cutaway_flags == [false,true,false],crown_cutaway_flags)
	var shipping_source: Dictionary = game.sim.resources[0]
	shipping_source.units = 2
	game.sim.position = shipping_source.position + Vector2(0.0,1.0)
	game.sim.velocity = Vector2.ZERO
	var shipping_impacts_before := int(game.harvest_presentation.descriptor().accepted_impacts)
	var shipping_receipts_before := int(game.transfer_feedback.descriptor().accepted_receipts)
	var shipping_inventory_before := int(game.sim.inventory.wood)
	for commit_index in 2:
		game.sim.action = {
			"kind":"gather", "id":String(shipping_source.id), "position":shipping_source.position,
			"action_token":commit_index+1, "progress":0.99, "role":"player_lead", "actionable":true,
		}
		game._process(1.0 / 60.0)
		game.sim.events.clear()
		game.sim.perform_action(0.60)
		game.sim.elapsed += 0.60
		game.present_events()
		game._process(1.0 / 60.0)
	var shipping_harvest: Dictionary = game.harvest_presentation.descriptor()
	var shipping_transfer: Dictionary = game.transfer_feedback.descriptor()
	check("shipping simulation commits two consecutive wood units", int(shipping_source.units) == 0 and int(game.sim.inventory.wood) == shipping_inventory_before + 2)
	check("back-to-back shipping commits each drive one T09 impact and T08 transfer", shipping_harvest.accepted_impacts == shipping_impacts_before+2 and shipping_transfer.accepted_receipts == shipping_receipts_before+2,[shipping_harvest,shipping_transfer])
	check("shipping depletion hides the bound source", not game.resource_visuals[shipping_source.id].visible)
	game.present_events()
	check("shipping event epoch cannot replay either presentation", game.harvest_presentation.descriptor().accepted_impacts == shipping_impacts_before+2 and game.transfer_feedback.descriptor().accepted_receipts == shipping_receipts_before+2)
	shipping_source.units = int(game.sim.tuning.woodUnitsPerNode)
	shipping_source.respawn = 0.0
	game._process(1.0 / 60.0)
	check("shipping respawn restores the same bound source", game.resource_visuals[shipping_source.id].visible)
	var snapshot: Dictionary = game.sim.snapshot()
	var restored_sim = game.sim.get_script().new()
	check("save snapshot restores through the unchanged simulation schema", restored_sim.restore(snapshot))
	var restored_source: Dictionary = restored_sim.resources.filter(func(item): return String(item.id) == String(shipping_source.id))[0]
	check("save/reload preserves simulation quantities without T09 fields", int(restored_source.units) == int(shipping_source.units) and int(restored_sim.inventory.wood) == int(game.sim.inventory.wood) and not snapshot.has("harvest_presentation") and not snapshot.has("equipped_tool"))
	var original_lead := int(game.sim.lead)
	var switched := game.sim.select_lead(2)
	game._process(1.0 / 60.0)
	check("lead switch clears the previous actor tool immediately", switched and game.harvest_actor_id == 2 and not game.harvest_presentation.descriptor().active)
	check("lead switch does not duplicate inventory", int(game.sim.inventory.wood) == int(restored_sim.inventory.wood))
	game.sim.select_lead(original_lead)
	game._process(1.0 / 60.0)
	var recovered := Harvest.new()
	root.add_child(recovered)
	recovered.bind_source(String(shipping_source.id),String(shipping_source.kind),game.resource_visuals[shipping_source.id],int(shipping_source.units))
	check("fresh presentation reconstructs safely from current simulation state", not recovered.descriptor().active and recovered.sync_source(String(shipping_source.id),int(shipping_source.units),float(shipping_source.respawn)) and game.resource_visuals[shipping_source.id].visible == (int(shipping_source.units) > 0))
	recovered.free()
	if is_instance_valid(game.outpost_audio):
		game.outpost_audio.stop_all()
	game.harvest_presentation.reset()
	# Godot's audio mixer retires active WAV playbacks asynchronously. Give it
	# the same bounded drain window used by the established shipping tests before
	# freeing Main, otherwise a just-played gather clip survives process exit.
	await create_timer(0.35).timeout
	game.free()
	await process_frame
	await process_frame
	var standalone_transfer_count: int = int(transfer.descriptor().active_flights)
	harvest.reset()
	harvest.free()
	transfer.free()
	actor.free()
	source_visual.free()
	await process_frame

	print(JSON.stringify({
		"suite":"T09_harvesting_integration", "checks":checks,
		"failures":failures, "passed":failures.is_empty(),
		"t08_active_transfers":standalone_transfer_count,
		"independent_critic":false, "physical_4k60_verified":false,
	}))
	quit(0 if failures.is_empty() else 1)
