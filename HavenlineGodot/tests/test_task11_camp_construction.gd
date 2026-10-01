extends SceneTree

const View = preload("res://scripts/camp_construction_view.gd")
const CATALOG_PATH := "res://data/camp_construction_recipes.json"

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var contract := View.contract()
	check("T11 view authority is exact", contract.authority_id == "T11-camp-construction-view-v1")
	check("T10 remains transaction authority", contract.transaction_authority == "T10-world-transform-v1")
	check("T11 presentation cannot mutate resources or transform state", contract.presentation_only and not contract.mutates_resources and not contract.advances_transform_state)
	check("placement validation is pure and does not change T10 authority", contract.placement_validation_pure and not contract.placement_validation_changes_t10_authority)
	check("simple control philosophy preserved", not contract.manual_action_button_required)
	check("auto-build guidance is explicit without manual controls", contract.auto_build_guidance_visible and contract.delivered_stock_flow_visible and contract.feedback_node_budget == View.FEEDBACK_NODE_BUDGET)

	var origin := Vector3.ZERO
	check("empty placement is clear", View.placement_is_clear(origin, [], 2.8))
	check("overlapping footprint is rejected", not View.placement_is_clear(origin, [{"position": Vector3(3.0, 0, 0), "radius": 1.0}], 2.8))
	check("touching boundary is valid rather than over-rejected", View.placement_is_clear(origin, [{"position": Vector3(3.8, 0, 0), "radius": 1.0}], 2.8))
	check("meaningful near-boundary overlap remains rejected", not View.placement_is_clear(origin, [{"position": Vector3(3.79, 0, 0), "radius": 1.0}], 2.8))
	check("malformed footprint fails closed", not View.placement_is_clear(origin, [{"position": "bad", "radius": 1.0}], 2.8))
	check("invalid clearance fails closed", not View.placement_is_clear(origin, [], 0.0))

	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CATALOG_PATH))
	check("T11 construction catalog parses", parsed is Dictionary)
	var rows: Array = parsed.get("builds", []) if parsed is Dictionary else []
	check("catalog has exact two authored build stages", rows.size() == 2)
	if parsed is Dictionary:
		check("catalog is presentation-only", parsed.presentation_only == true and parsed.shadow_resource_authority == false)
		check("catalog points to T10 transaction authority", parsed.transaction_authority == "T10-world-transform-v1")
	for row: Variant in rows:
		check("T11 does not shadow costs", not row.has("costs"), row)
		check("T11 does not shadow prerequisites", not row.has("prerequisites"), row)
		check("T11 does not shadow progression tags", not row.has("progression_tags"), row)
		check("authored before scene exists", FileAccess.file_exists(String(row.before_scene)))
		check("authored after scene exists", FileAccess.file_exists(String(row.after_scene)))
		check("clearance contains footprint", float(row.clearance_radius) >= float(row.footprint_radius))

	var view := View.new()
	get_root().add_child(view)
	check("foundation view configures", view.configure("camp-A", "camp_shelter_foundation"))
	check("foundation authored mesh budget is bounded", view.descriptor().mesh_count > 0 and view.descriptor().mesh_count <= View.MAX_AUTHORED_MESHES)
	check("feedback node budget is bounded", view.descriptor().feedback_node_count <= View.FEEDBACK_NODE_BUDGET and view.descriptor().flow_marker_count == View.FEEDBACK_MARKER_COUNT)
	check("ready guidance makes automatic trigger explicit", view.descriptor().auto_build_guidance.contains("AUTO-BUILD") and view.descriptor().auto_build_guidance.contains("No build button"))
	check("placement context can block authored build", not view.set_placement_context(Vector3.ZERO, [{"position": Vector3(1.0, 0, 0), "radius": 1.0}]) and view.placement_blocked)
	check("ready reflects blocked placement", view.show_ready() and view.descriptor().lifecycle == "blocked")
	check("placement can recover without state mutation", view.set_placement_context(Vector3.ZERO, []) and not view.placement_blocked)

	var preview := {
		"passed": true,
		"recipe_id": "framework_anchor_seed_to_foundation",
		"target_id": "camp-A",
		"source_state": "seed",
		"target_state": "foundation",
		"presentation_key": "framework_foundation",
	}
	check("exact T10 preview selects authored after form", view.show_preview(preview) and view.descriptor().lifecycle == "preview")
	check("preview shows delivered-stock destination and automatic behavior", view.descriptor().delivered_stock_flow_visible and view.descriptor().auto_build_guidance.contains("delivered stock applies automatically"))
	var preview_footing := view.get_node_or_null("CampShelterFoundation/StoneFooting") as MeshInstance3D
	var preview_deck := view.get_node_or_null("CampShelterFoundation/Deck") as MeshInstance3D
	var preview_post := view.get_node_or_null("CampShelterFoundation/PostNW") as MeshInstance3D
	var preview_beam := view.get_node_or_null("CampShelterFoundation/BeamBack") as MeshInstance3D
	check("foundation preview base stays opaque against the world floor", preview_footing != null and preview_deck != null and is_zero_approx(preview_footing.transparency) and is_zero_approx(preview_deck.transparency))
	check("foundation preview frame remains visibly provisional", preview_post != null and preview_post.transparency > 0.0)
	var post_bottom := preview_post.position.y - preview_post.scale.y * 0.5 if preview_post != null else -999.0
	var beam_top := preview_beam.position.y + preview_beam.scale.y * 0.5 if preview_beam != null else 999.0
	check("foundation posts terminate exactly on perimeter beams", preview_beam != null and is_equal_approx(post_bottom, beam_top), {"post_bottom":post_bottom, "beam_top":beam_top})
	var wrong_preview := preview.duplicate(true)
	wrong_preview.presentation_key = "forged"
	check("wrong T10 presentation identity fails closed", not view.show_preview(wrong_preview))

	var intent := preview.duplicate(true)
	intent.merge({"transaction_id": "t11-unit-1", "submit_debit_transaction": true, "replayed": false}, true)
	check("exact T10 intent enters committing presentation", view.show_commit(intent) and view.descriptor().lifecycle == "committing")
	var marker := view.get_node("T11BuildFeedback/DeliveredStockFlow00") as MeshInstance3D
	var marker_before := marker.position
	view._process(0.5)
	check("committing visibly flows delivered stock toward the structure", marker.visible and marker.position != marker_before and view.descriptor().auto_build_guidance.contains("no input needed"))
	var unaccepted := intent.duplicate(true)
	unaccepted.merge({"authority_applied": true, "accepted_by_world_transform": false}, true)
	check("unaccepted authority receipt cannot complete", not view.mark_complete(unaccepted) and view.descriptor().lifecycle == "committing")
	var accepted := intent.duplicate(true)
	accepted.merge({"authority_applied": true, "accepted_by_world_transform": true}, true)
	check("accepted T10 receipt reveals completed authored form", view.mark_complete(accepted) and view.descriptor().lifecycle == "complete")
	check("completion stops resource-flow feedback and announces exact completion", not view.descriptor().delivered_stock_flow_visible and view.descriptor().auto_build_guidance.contains("BUILD COMPLETE"))
	check("duplicate completion cannot replay", not view.mark_complete(accepted))
	check("completed presentation remains authority-free", view.descriptor().presentation_only and not view.descriptor().mutates_resources and not view.descriptor().advances_transform_state)

	print(JSON.stringify({
		"suite": "T11_camp_construction",
		"checks": checks,
		"failures": failures,
		"check_count": checks.size(),
		"passed": failures.is_empty(),
		"task_approved": false
	}))
	quit(0 if failures.is_empty() else 1)
