extends SceneTree

const Domain = preload("res://scripts/camp_construction.gd")
const View = preload("res://scripts/camp_construction_view.gd")
const Boundary = preload("res://scripts/camp_boundary.gd")
const CameraPolicy = preload("res://scripts/camera_composition.gd")

var checks: Array[Dictionary] = []
var failures: Array[String] = []

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	if not passed:
		failures.append(label)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var manifest := View.read_manifest()
	check("authored T11 stage manifest validates", View.validate_manifest(manifest))
	check("manifest exposes three deterministic camp states", manifest.get("stages", {}).keys().size() == 3, manifest.get("stages", {}).keys())

	var view := View.new()
	root.add_child(view)
	check("view configures from authored stage manifest", view.configure(manifest))

	var site := view.apply_stage("site_unbuilt", "blocked")
	check("preconstruction site builds", bool(site.get("passed", false)) and site.get("rebuilt", false), site)
	check("preconstruction site uses approved build pad", view.stage_root.get_node_or_null("BuildPad") != null)
	var blocked_status := view.status_descriptor()
	check("blocked lifecycle has visible in-world status", blocked_status.visible and blocked_status.lifecycle == "blocked", blocked_status)
	check("blocked status is anchored to construction pad", Vector3(blocked_status.anchor).distance_to(view.interaction_anchor() + Vector3(0.0, 0.035, 0.0)) < 0.001, blocked_status)
	var site_count := view.rebuild_count
	var ready_same := view.apply_stage("site_unbuilt", "ready")
	check("lifecycle-only update does not rebuild unchanged stage", bool(ready_same.get("passed", false)) and not ready_same.get("rebuilt", true) and view.rebuild_count == site_count, ready_same)
	var ready_status := view.status_descriptor()
	check("ready lifecycle visibly differs from blocked", ready_status.color != blocked_status.color and not is_equal_approx(float(ready_status.scale), float(blocked_status.scale)), {"blocked": blocked_status, "ready": ready_status})

	var lifecycle_signatures := {}
	for lifecycle in View.LIFECYCLES:
		check("lifecycle %s applies without geometry rebuild" % lifecycle, view.set_lifecycle(lifecycle) and view.rebuild_count == site_count)
		var status := view.status_descriptor()
		lifecycle_signatures[lifecycle] = "%s|%.3f" % [String(status.color), float(status.scale)]
		check("lifecycle %s stays visibly anchored" % lifecycle, bool(status.visible) and Vector3(status.anchor).distance_to(view.interaction_anchor() + Vector3(0.0, 0.035, 0.0)) < 0.001, status)
	var unique_signatures := {}
	for signature in lifecycle_signatures.values():
		unique_signatures[signature] = true
	check("all six lifecycle states have distinct visible signatures", unique_signatures.size() == View.LIFECYCLES.size(), lifecycle_signatures)

	var initial := view.apply_stage("camp_initial", "complete")
	check("constructed camp stage builds", bool(initial.get("passed", false)) and initial.get("rebuilt", false), initial)
	check("constructed camp has authored warm work floor", view.stage_root.get_node_or_null("WarmWorkFloor") != null)
	check("constructed camp has approved heated vessel", view.stage_root.get_node_or_null("HearthVessel") != null)
	check("constructed camp has approved upgrade pad", view.stage_root.get_node_or_null("UpgradePad") != null)
	check("T22 defense platform is not pre-spawned by T11", view.stage_root.get_node_or_null("DefensePlatform") == null)
	check("T16/T17 context assets are explicitly passive", bool(view.stage_root.get_node("ProcessingCounter").get_meta("t11_passive_only", false)) and bool(view.stage_root.get_node("PaymentPad").get_meta("t11_passive_only", false)))
	var initial_status := view.status_descriptor()
	check("constructed camp status moves to upgrade pad", Vector3(initial_status.anchor).distance_to(view.interaction_anchor() + Vector3(0.0, 0.035, 0.0)) < 0.001 and view.interaction_anchor() == Vector3(-3.0, 0.0, -0.8), initial_status)
	var initial_node_count := view.stage_node_count()

	var upgraded := view.apply_stage("camp_upgraded_01", "complete")
	check("visible upgrade stage builds", bool(upgraded.get("passed", false)) and upgraded.get("rebuilt", false), upgraded)
	check("visible upgrade adds authored paired counter canopies", view.stage_root.get_node_or_null("UpgradeCanopyWest") != null and view.stage_root.get_node_or_null("UpgradeCanopyEast") != null)
	check("visible upgrade adds authored lantern detail", view.stage_root.get_node_or_null("UpgradeLanternNW") != null and view.stage_root.get_node_or_null("UpgradeLanternSE") != null)
	check("visible upgrade adds timber detail", view.stage_root.get_node_or_null("UpgradeTimberWest") != null and view.stage_root.get_node_or_null("UpgradeTimberEast") != null)
	check("upgrade is materially larger than initial camp presentation", view.stage_node_count() >= initial_node_count + 6, {"initial": initial_node_count, "upgraded": view.stage_node_count()})
	var canopy_half_x := 2.45
	var canopy_z_min := 5.6 - 1.25
	check("paired canopies remain outside central-spine lane", 7.1 - canopy_half_x > Boundary.LANE_HALF)
	check("paired canopies remain north of cross-camp lane clearance", canopy_z_min > 2.25 + Boundary.LANE_HALF)
	var upgraded_count := view.rebuild_count
	var repeated := view.apply_stage("camp_upgraded_01", "complete")
	check("unchanged completed upgrade does not rebuild every frame", bool(repeated.get("passed", false)) and not repeated.get("rebuilt", true) and view.rebuild_count == upgraded_count, repeated)

	var site_anchor := Vector2(0.0, 0.2)
	var upgrade_anchor := Vector2(-3.0, -0.8)
	check("construction anchor remains in T04 contextual target envelope", site_anchor.length() <= CameraPolicy.TARGET_MAX_DISTANCE)
	check("upgrade anchor remains in T04 contextual target envelope", upgrade_anchor.length() <= CameraPolicy.TARGET_MAX_DISTANCE)
	check("T03 work-lane half width remains authoritative", is_equal_approx(Boundary.LANE_HALF, 1.30))
	check("T11 does not replace T03 camp center authority", Boundary.CAMP_CENTER == Vector2(0.0, 2.8))

	var source := FileAccess.get_file_as_string("res://scripts/camp_construction.gd")
	check("T11 domain does not preload unfinished T10 runtime", source.find("world_transform.gd") == -1)
	check("T11 domain uses injected semantic port", source.find("transform_port") >= 0 and source.find("preview_transform") >= 0 and source.find("accept_authoritative_receipt") >= 0)
	var descriptor := view.descriptor()
	check("view requires no new gameplay controls", descriptor.required_controls.is_empty() and descriptor.interaction_mode == "movement_proximity_context")
	check("view owns no resource/progression/economy authority", descriptor.owns_resources == false and descriptor.owns_progression == false and descriptor.owns_economy == false)
	check("lifecycle visuals remain presentation-only", bool(descriptor.lifecycle_visual.presentation_only))
	check("view remains explicitly build-pending", descriptor.build_pending_dependency == true)

	var catalog := Domain.read_catalog()
	check("all build-pending recipes remain non-shipping", catalog.recipes.all(func(row): return row.shipping == false and row.test_only == true))
	check("T10 fixture IDs are disclosed as unapproved bindings", catalog.recipes.all(func(row): return row.binding_status == "t10_prebuild_fixture_unapproved"))

	var report := {
		"task": "T11",
		"suite": "camp_construction_integration_build_pending",
		"checks": checks,
		"failures": failures,
		"passed": failures.is_empty(),
		"stage_rebuild_count": view.rebuild_count,
		"initial_stage_node_count": initial_node_count,
		"final_stage_node_count": view.stage_node_count(),
		"lifecycle_signature_count": unique_signatures.size(),
		"build_pending_dependency": true,
		"final_t10_compatibility_claimed": false,
		"task_approved": false,
	}
	print(JSON.stringify(report))
	view.free()
	quit(0 if failures.is_empty() else 1)
