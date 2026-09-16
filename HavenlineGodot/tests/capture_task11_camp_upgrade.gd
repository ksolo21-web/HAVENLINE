extends SceneTree

const View = preload("res://scripts/camp_construction_view.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var view := View.new()
	root.add_child(view)
	var configured := view.configure_from_file()
	var captures: Array[Dictionary] = []
	if configured:
		for row in [
			{"state": "site_unbuilt", "lifecycle": "blocked"},
			{"state": "site_unbuilt", "lifecycle": "ready"},
			{"state": "camp_initial", "lifecycle": "complete"},
			{"state": "camp_upgraded_01", "lifecycle": "complete"},
		]:
			var result := view.apply_stage(String(row.state), String(row.lifecycle))
			captures.append({
				"camp_state_id": row.state,
				"lifecycle": row.lifecycle,
				"passed": result.get("passed", false),
				"rebuilt": result.get("rebuilt", false),
				"node_count": view.stage_node_count(),
				"interaction_anchor": view.interaction_anchor(),
			})
	var report := {
		"task": "T11",
		"capture_kind": "build_pending_stage_manifest",
		"configured": configured,
		"captures": captures,
		"build_pending_dependency": true,
		"final_t10_compatibility_claimed": false,
		"final_visual_critic_evidence": false,
		"task_approved": false,
	}
	print(JSON.stringify(report))
	view.free()
	quit(0 if configured and captures.all(func(row): return bool(row.passed)) else 1)
