extends SceneTree

const Harvest = preload("res://scripts/harvest_presentation.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name":label, "passed":passed, "detail":detail})
	if not passed:
		failures.append(label)

func action(resource: String, token: int, progress: float, source := "source") -> Dictionary:
	return {
		"kind":"gather", "resource":resource, "source_id":source,
		"action_token":token, "progress":progress, "role":"player_lead",
		"actionable":true,
	}

func contact_target(resource: String) -> Vector3:
	var profile := Harvest.profile_for_resource(resource)
	var anchor := (Vector3(profile.grip_socket)+Vector3(profile.second_hand_socket))*0.5 if not String(profile.secondary_grip_marker).is_empty() else Vector3(profile.grip_socket)
	return Vector3(profile.impact_socket)-anchor

func receipt(resource: String, token: int, receipt_id: String, source := "source", actor_id := 7) -> Dictionary:
	return {
		"committed":true, "resource":resource, "source_id":source,
		"action_token":token, "receipt_id":receipt_id,
		"target_position":contact_target(resource), "actor_id":actor_id,
	}

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var contract := Harvest.contract()
	check("T09 presentation authority is exact", contract.authority_id == "T09-harvest-presentation-v1")
	check("opening resource set is exact", contract.resources == ["wood","stone","metal","fuel"])
	check("simulation remains sole authority", contract.simulation_authoritative and not contract.emits_gameplay_events and not contract.mutates_inventory)
	check("presentation adds no save or control surface", not contract.adds_save_fields and contract.permanent_action_buttons == 0)
	check("one equipped tool is the hard limit", contract.maximum_equipped_tools == 1)
	check("effect descriptor pools are bounded", contract.maximum_fragment_descriptors == 32 and contract.maximum_impact_pulses == 8)
	check("committed impact must stay on its presented source", contract.impact_target_tolerance_meters == 0.25)
	check("real hand sockets use centimeter-scale tolerances", contract.socket_contact_tolerance_meters == 0.025 and contract.second_hand_tolerance_meters == 0.045)
	check("bounded palm settle cannot hide an unreachable tool", contract.maximum_grip_settle_meters == 0.12)
	check("only an authoritative integration beat may arm impact", contract.authoritative_commit_arming_required)
	check("source visibility follows simulation state only", contract.source_visibility_authority == "simulation_units_and_respawn_only")
	check("impact effects use bounded visible geometry", contract.effect_geometry == "bounded_visible_mesh_pools")
	check("player is the only final T09 presentation role", contract.accepted_roles == ["player_lead"] and contract.compatible_future_roles == ["core_human_companion","rescued_survivor_helper"])

	var expected := {
		"wood":["chop","axe","human_player_chop","C1TwoHandContact",0.56,"wood_chips"],
		"stone":["mine","pickaxe","human_player_mine","C1TwoHandContact",0.58,"stone_shards"],
		"metal":["mine","pickaxe","human_player_mine","C1TwoHandContact",0.58,"ore_glint"],
		"fuel":["dismantle","salvage_pry_tool","human_player_dismantle","C1RightHandContact",0.61,"salvage_sparks"],
	}
	for resource in expected:
		var profile := Harvest.profile_for_resource(resource)
		var frozen: Array = expected[resource]
		check(resource + " frozen mapping is exact", [profile.method,profile.tool,profile.animation_profile,profile.contact_marker,profile.impact_progress,profile.effect] == frozen, profile)
		check(resource + " authored tool resolves", ResourceLoader.exists(profile.asset), profile.asset)
	check("future resource has no generic fallback", Harvest.profile_for_resource("fish").is_empty())

	var catalog: Variant = JSON.parse_string(FileAccess.get_file_as_string(contract.catalog))
	check("authored catalog is readable", catalog is Dictionary and catalog.authority_id == "T09-harvesting-tools-v1")
	check("catalog contains exactly three finished tools", catalog.entries.size() == 3 and catalog.entries.map(func(row): return row.id) == ["axe","pickaxe","salvage_pry_tool"])
	for row: Dictionary in catalog.entries:
		check(row.id + " uses bounded authored geometry", int(row.triangles) > 300 and int(row.triangles) <= 2500 and row.materials.size() >= 5, row)
		check(row.id + " has explicit grip and impact sockets", row.grip_socket.size() == 3 and row.impact_socket.size() == 3)
		check(row.id + " declares the second-hand boundary", row.has("second_hand_socket") and row.second_hand_socket.size() in [0,3])

	var harvest := Harvest.new()
	root.add_child(harvest)
	var actor := Node3D.new()
	root.add_child(actor)
	var right_hand := Marker3D.new()
	right_hand.name = "C1RightHandContact"
	actor.add_child(right_hand)
	var left_hand := Marker3D.new()
	left_hand.name = "C1LeftHandContact"
	actor.add_child(left_hand)
	check("actual primary and secondary hand contacts bind",harvest.bind_actor(actor))
	var source_visual := Node3D.new()
	root.add_child(source_visual)
	check("source presentation binds without owning units", harvest.bind_source("tree:0","wood",source_visual,3))
	check("empty and unknown actions fail closed", not harvest.begin_action({}) and not harvest.begin_action(action("fish",1,0.5)))
	var wrong_role := action("wood",1,0.5)
	wrong_role.role = "core_human_companion"
	check("helper cannot borrow final player presentation", not harvest.begin_action(wrong_role))
	check("nonfinite progress fails closed", not harvest.begin_action(action("wood",1,NAN)))
	check("valid action requires a bound presented actor", not harvest.begin_action(action("wood",1,0.56)))

	var input := action("wood",10,0.56,"tree:0")
	var wood_profile := Harvest.profile_for_resource("wood")
	var wood_anchor := (Vector3(wood_profile.grip_socket)+Vector3(wood_profile.second_hand_socket))*0.5
	right_hand.position = Vector3(wood_profile.grip_socket)-wood_anchor
	left_hand.position = Vector3(wood_profile.second_hand_socket)-wood_anchor
	var before := input.duplicate(true)
	check("valid wood action equips authored axe", harvest.begin_action(input,7))
	check("begin cannot mutate caller action", input == before)
	var wood_target := contact_target("wood")
	var wood_state := harvest.update_action(input,Transform3D.IDENTITY,wood_target)
	check("axe binds to T06 two-hand contact", wood_state.active and wood_state.tool == "axe" and wood_state.contact_marker == "C1TwoHandContact")
	check("raw simulation progress is remapped as presentation only", is_equal_approx(wood_state.raw_progress,0.56) and wood_state.progress < 0.56 and not wood_state.contact_ready)
	check("first cycle reaches contact exactly at commit", is_equal_approx(Harvest.presentation_progress("wood",1.0,false),0.56))
	check("live tool exposes authored asset identity", String(harvest.tool_nodes.axe.get_meta("t09_authored_asset","")).ends_with("axe.glb"))
	check("unarmed committed receipt cannot bypass the integration beat", not harvest.accept_committed_impact(receipt("wood",10,"unarmed","tree:0")))
	var wood_contact := harvest.synchronize_committed_contact(input,Transform3D.IDENTITY,wood_target,7)
	check("committed axe solves both hands and impact sockets", wood_contact.contact_alignment_valid and wood_contact.grip_error_m < 0.001 and wood_contact.secondary_grip_error_m < 0.001 and wood_contact.impact_error_m < 0.001,wood_contact)
	check("axe socket pixels are bound to both hand and target authorities", (harvest.tool_nodes.axe.global_transform*Vector3(wood_profile.grip_socket)).distance_to(right_hand.global_position) < 0.001 and (harvest.tool_nodes.axe.global_transform*Vector3(wood_profile.second_hand_socket)).distance_to(left_hand.global_position) < 0.001 and (harvest.tool_nodes.axe.global_transform*Vector3(wood_profile.impact_socket)).distance_to(wood_target) < 0.001)
	check("committed wood impact is accepted once", harvest.accept_committed_impact(receipt("wood",10,"gather:wood:10","tree:0")))
	check("same receipt cannot replay", not harvest.accept_committed_impact(receipt("wood",10,"gather:wood:10","tree:0")))
	harvest.synchronize_committed_contact(input,Transform3D.IDENTITY,wood_target,7)
	check("same active context accepts a later committed unit with a new receipt", harvest.accept_committed_impact(receipt("wood",10,"gather:wood:10b","tree:0")))
	check("post-commit cycle recovers then returns to contact", is_equal_approx(Harvest.presentation_progress("wood",0.0,true),0.56) and is_equal_approx(Harvest.presentation_progress("wood",Harvest.RECOVERY_PORTION,true),1.0) and is_equal_approx(Harvest.presentation_progress("wood",1.0,true),0.56))

	var token := 20
	for resource_value in ["stone","metal","fuel"]:
		var resource := String(resource_value)
		var profile := Harvest.profile_for_resource(resource)
		var anchor := (Vector3(profile.grip_socket)+Vector3(profile.second_hand_socket))*0.5 if not String(profile.secondary_grip_marker).is_empty() else Vector3(profile.grip_socket)
		right_hand.position = Vector3(profile.grip_socket)-anchor
		left_hand.position = Vector3(profile.second_hand_socket)-anchor
		var source := resource + ":0"
		var current := action(resource,token,float(profile.impact_progress),source)
		check(resource + " action begins", harvest.begin_action(current,7))
		var target := contact_target(resource)
		var state := harvest.update_action(current,Transform3D.IDENTITY,target)
		check(resource + " uses exact tool and contact contract", state.tool == profile.tool and state.contact_marker == profile.contact_marker and not state.contact_ready)
		var contact := harvest.synchronize_committed_contact(current,Transform3D.IDENTITY,target,7)
		check(resource + " socket solve stays inside strict contact tolerance", contact.contact_alignment_valid and contact.grip_error_m <= Harvest.SOCKET_CONTACT_TOLERANCE_METERS and contact.impact_error_m <= Harvest.SOCKET_CONTACT_TOLERANCE_METERS and contact.secondary_grip_error_m <= Harvest.SECOND_HAND_TOLERANCE_METERS,contact)
		check(resource + " committed impact is accepted", harvest.accept_committed_impact(receipt(resource,token,"gather:%s:%d" % [resource,token],source)))
		token += 1
	var effects := harvest.fragment_descriptors.map(func(row): return row.effect)
	check("all four source-specific responses are represented", ["wood_chips","stone_shards","ore_glint","salvage_sparks"].all(func(effect): return effect in effects),effects)
	var impact_state := harvest.descriptor()
	check("effects remain inside frozen pools", impact_state.active_fragment_descriptors <= Harvest.MAX_FRAGMENT_DESCRIPTORS and impact_state.active_impact_pulses <= Harvest.MAX_IMPACT_PULSES,impact_state)
	check("accepted impacts create visible geometry, not descriptors alone", impact_state.visible_fragment_nodes > 0 and impact_state.visible_pulse_nodes > 0 and harvest.fragment_pool.any(func(node): return node.visible))
	check("accepted impacts never become gameplay events", impact_state.accepted_impacts == 5 and not impact_state.emits_gameplay_events and not impact_state.mutates_inventory)
	check("committed source response is visible and bounded", harvest.source_bindings["tree:0"].response_age == 0.0)
	check("authoritative depletion hides the source", harvest.sync_source("tree:0",0,0.0) and not source_visual.visible)
	check("authoritative respawn restores the source", harvest.sync_source("tree:0",3,0.0) and source_visual.visible and harvest.source_bindings["tree:0"].respawn_age == 0.0)

	var early := action("stone",90,0.20,"stone:early")
	harvest.begin_action(early,7)
	harvest.update_action(early,Transform3D.IDENTITY,Vector3.ONE)
	check("uncommitted anticipation cannot create impact feedback", not harvest.accept_committed_impact(receipt("stone",90,"early","stone:early")))
	var stale := receipt("stone",91,"stale","stone:early")
	stale.committed = true
	check("stale action token fails closed", not harvest.accept_committed_impact(stale))
	check("action token regression fails before changing presentation", not harvest.begin_action(action("fuel",89,0.61,"fuel:regressed"),7))
	harvest.cancel("movement_owns_locomotion")
	check("cancelled context may re-enter with the same T07 identity and token", harvest.begin_action(early,7))
	check("same token cannot be rebound to another source or actor", not harvest.begin_action(action("stone",90,0.58,"stone:rebound"),8))
	var bound := action("metal",100,0.58,"metal:bound")
	check("new higher action token starts", harvest.begin_action(bound,7))
	var bound_profile := Harvest.profile_for_resource("metal")
	var bound_anchor := (Vector3(bound_profile.grip_socket)+Vector3(bound_profile.second_hand_socket))*0.5
	right_hand.position = Vector3(bound_profile.grip_socket)-bound_anchor
	left_hand.position = Vector3(bound_profile.second_hand_socket)-bound_anchor
	var bound_target := contact_target("metal")
	harvest.update_action(bound,Transform3D.IDENTITY,bound_target)
	harvest.synchronize_committed_contact(bound,Transform3D.IDENTITY,bound_target,7)
	check("committed receipt must match the presented actor", not harvest.accept_committed_impact(receipt("metal",100,"actor:mismatch","metal:bound",8)))
	var displaced := receipt("metal",100,"target:mismatch","metal:bound",7)
	displaced.target_position = bound_target + Vector3(20.0,0.0,20.0)
	check("committed receipt must match the presented source position", not harvest.accept_committed_impact(displaced))
	check("matching actor receipt remains accepted", harvest.accept_committed_impact(receipt("metal",100,"actor:match","metal:bound",7)))
	var advances_valid := true
	for advancing_token in range(101,401):
		advances_valid = harvest.begin_action(action("wood",advancing_token,0.56,"tree:bounded"),7) and advances_valid
	check("long-session token advances remain valid", advances_valid)
	var bounded_tokens := harvest.descriptor()
	check("token identity state stays bounded across a long session", bounded_tokens.highest_action_token == 400 and bounded_tokens.tracked_action_tokens == 1, bounded_tokens)

	harvest.cancel("movement_owns_locomotion")
	var cancelled := harvest.descriptor()
	check("movement cancellation hides the tool", not cancelled.active and cancelled.last_cancel_reason == "movement_owns_locomotion")
	harvest._process(Harvest.EFFECT_LIFETIME_SECONDS)
	check("bounded effects expire", harvest.descriptor().active_fragment_descriptors == 0 and harvest.descriptor().active_impact_pulses == 0)
	harvest.reset()
	check("reset clears presentation-only history and token session", harvest.descriptor().remembered_receipts == 0 and harvest.descriptor().accepted_impacts == 0 and harvest.descriptor().highest_action_token == 0)

	print(JSON.stringify({
		"suite":"T09_harvesting_component", "checks":checks,
		"failures":failures, "passed":failures.is_empty(),
		"tool_assets":catalog.entries.size(), "independent_critic":false,
		"physical_4k60_verified":false,
	}))
	quit(0 if failures.is_empty() else 1)
