extends SceneTree

const Harvest = preload("res://scripts/harvest_presentation.gd")
const Director = preload("res://scripts/context_director.gd")
const Motion = preload("res://scripts/character1_motion.gd")
const Transfer = preload("res://scripts/transfer_feedback.gd")

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
	var presented := harvest.update_action(action,Transform3D.IDENTITY,Vector3(0,0.8,1.0))
	check("T09 contact is synchronized to T06 chop progress", presented.contact_ready and presented.tool == "axe" and presented.contact_marker == "C1TwoHandContact")

	var committed := {
		"committed":true, "resource":"wood", "source_id":String(selected.id),
		"action_token":int(selected.action_token), "receipt_id":"simulation:gather:1",
		"target_position":Vector3(0,0.8,1.0), "actor_id":1,
	}
	check("authoritative committed impact activates T09 feedback", harvest.accept_committed_impact(committed))
	check("the same committed receipt starts one T08 source-to-actor transfer", transfer.transfer("wood",Vector3(0,0.8,1.0),Vector3(0,1.2,0),String(committed.receipt_id),"source_to_actor",1,"actor:1"))
	check("replayed commit fails in both T09 and T08", not harvest.accept_committed_impact(committed) and not transfer.transfer("wood",Vector3(0,0.8,1.0),Vector3(0,1.2,0),String(committed.receipt_id),"source_to_actor",1,"actor:1"))
	check("presentation modules cannot mutate logical inventory", inventory == inventory_before and not harvest.descriptor().mutates_inventory and not transfer.descriptor().mutates_inventory)

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

	print(JSON.stringify({
		"suite":"T09_harvesting_integration", "checks":checks,
		"failures":failures, "passed":failures.is_empty(),
		"t08_active_transfers":transfer.descriptor().active_flights,
		"independent_critic":false, "physical_4k60_verified":false,
	}))
	quit(0 if failures.is_empty() else 1)
