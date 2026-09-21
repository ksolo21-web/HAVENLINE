extends SceneTree

const Transform = preload("res://scripts/world_transform.gd")
const View = preload("res://scripts/camp_construction_view.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func simulation_ack(intent: Dictionary) -> Dictionary:
	var receipt := intent.duplicate(true)
	receipt["authority_source"] = "simulation"
	receipt["authority_applied"] = true
	return receipt

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var t10_catalog: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/world_transform_recipes.json"))
	var t11_catalog: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/camp_construction_recipes.json"))
	check("both T10 and T11 catalogs parse", t10_catalog is Dictionary and t11_catalog is Dictionary)
	var t10_by_id := {}
	for row: Variant in t10_catalog.get("recipes", []):
		t10_by_id[String(row.recipe_id)] = row
	for row: Variant in t11_catalog.get("builds", []):
		var recipe: Dictionary = t10_by_id.get(String(row.world_transform_recipe_id), {})
		check("T11 build maps to existing T10 recipe", not recipe.is_empty(), row)
		check("T11 source/target identity matches T10 exactly", String(row.source_state) == String(recipe.source_state) and String(row.target_state) == String(recipe.target_state), row)
		check("T11 presentation identity matches T10 exactly", String(row.presentation_key) == String(recipe.presentation_key), row)
		check("T11 does not duplicate resource/progression authority", not row.has("costs") and not row.has("prerequisites") and not row.has("progression_tags"), row)

	var engine := Transform.new()
	check("approved T10 catalog configures", engine.configure_from_file())
	check("camp target registers on T10 authority", engine.register_target("camp-A", "seed"))
	var inventory := {"wood": 20, "stone": 12, "metal": 2, "fuel": 0}
	var inventory_before := inventory.duplicate(true)
	var view := View.new()
	get_root().add_child(view)
	check("foundation authored presentation configures", view.configure("camp-A", "camp_shelter_foundation"))
	check("foundation placement clear", view.set_placement_context(Vector3.ZERO, []))

	var foundation_preview := engine.preview_transform("framework_anchor_seed_to_foundation", "camp-A", inventory)
	check("T10 exact foundation preview succeeds", foundation_preview.passed and foundation_preview.costs == {"wood": 8, "stone": 4}, foundation_preview)
	check("T11 preview consumes T10 identity without touching caller inventory", view.show_preview(foundation_preview) and inventory == inventory_before)
	var foundation_intent := engine.commit_transform("t11-foundation-1", "framework_anchor_seed_to_foundation", "camp-A", inventory)
	check("T10 exact transaction intent drives T11 committing state", foundation_intent.passed and view.show_commit(foundation_intent))
	var foundation_accepted := engine.accept_authoritative_receipt(simulation_ack(foundation_intent))
	check("T10 accepts authoritative foundation receipt once", foundation_accepted.passed and foundation_accepted.applied and foundation_accepted.accepted_by_world_transform)
	check("T11 completes only from accepted T10 receipt", view.mark_complete(foundation_accepted) and view.descriptor().lifecycle == "complete")
	check("T10 is authoritative foundation state", engine.descriptor().targets["camp-A"].state == "foundation" and engine.descriptor().targets["camp-A"].revision == 1)

	check("reinforced authored presentation configures", view.configure("camp-A", "camp_shelter_reinforced"))
	var blocked := engine.preview_transform("framework_anchor_foundation_to_reinforced", "camp-A", inventory)
	check("T10 prerequisite still blocks reinforcement", not blocked.passed and blocked.errors.has("missing_prerequisite:harvesting_online"), blocked)
	check("T11 renders blocked state without bypass", view.show_blocked(blocked) and view.descriptor().lifecycle == "blocked")
	var reinforced_preview := engine.preview_transform("framework_anchor_foundation_to_reinforced", "camp-A", inventory, ["harvesting_online"])
	check("T10 prerequisite unlocks exact reinforcement", reinforced_preview.passed and reinforced_preview.costs == {"wood": 12, "stone": 8, "metal": 2}, reinforced_preview)
	check("T11 preview follows unlocked T10 offer", view.show_preview(reinforced_preview))
	var reinforced_intent := engine.commit_transform("t11-reinforced-1", "framework_anchor_foundation_to_reinforced", "camp-A", inventory, ["harvesting_online"])
	check("T10 exact reinforcement intent drives committing presentation", reinforced_intent.passed and view.show_commit(reinforced_intent))
	var reinforced_accepted := engine.accept_authoritative_receipt(simulation_ack(reinforced_intent))
	check("T10 accepts reinforcement receipt", reinforced_accepted.passed and reinforced_accepted.applied)
	check("T11 reveals reinforced authored result", view.mark_complete(reinforced_accepted) and view.descriptor().current_scene.ends_with("camp_shelter_reinforced.tscn"))
	check("T10 final state remains sole transform truth", engine.descriptor().targets["camp-A"].state == "reinforced" and engine.descriptor().targets["camp-A"].revision == 2)
	var replay := engine.accept_authoritative_receipt(simulation_ack(reinforced_intent))
	check("T10 replay remains idempotent after T11 presentation", replay.passed and replay.replayed and not replay.applied and engine.descriptor().targets["camp-A"].revision == 2)

	print(JSON.stringify({
		"suite": "T11_T10_integration",
		"checks": checks,
		"failures": failures,
		"check_count": checks.size(),
		"passed": failures.is_empty(),
		"t10_transaction_authority_preserved": true,
		"task_approved": false
	}))
	quit(0 if failures.is_empty() else 1)
