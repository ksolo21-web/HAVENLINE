extends SceneTree

const Session = preload("res://tests/lifecycle_test_profile.gd")
const CUT := "pine@650,-3550"
const COOLING := "pine@-1360,-2110"

func _initialize() -> void:
	call_deferred("run")

func record_rows(field: Node3D) -> Array[Dictionary]:
	var relocated: Array[Dictionary] = []
	for row: Dictionary in field.forest.records:
		if row.id.begins_with("pine@"):
			relocated.append(row)
	return relocated

func run() -> void:
	var field = load("res://field_opening.tscn").instantiate()
	root.add_child(field)
	for i in 4: await physics_frame
	field.set_physics_process(false)
	var checks := {}
	var mode := OS.get_environment("T01_SAVE_MODE")
	var rows := record_rows(field)
	var keys := {}
	for row in rows: keys[row.id] = row.transform.origin
	checks["all eleven legacy identities registered once"] = keys.size() == 11 and rows.size() == 11
	checks["relocated roots clear other grove trunks"] = rows.all(func(left: Dictionary):
		return field.forest.records.all(func(right: Dictionary):
			return left.id == right.id or (left.transform.origin as Vector3).distance_to(right.transform.origin) > 1.1))
	checks["profile opened"] = not field.persist_blocked
	if mode == "write":
		# This is the original source-key schema, with one cut and one cooling.
		field.lifecycle.partial[CUT] = 2
		field.lifecycle.cooling[COOLING] = 3.2
		field._persist_world()
		checks["native serializer accepted original source keys"] = not field.persist_blocked and FileAccess.file_exists(field.field_save.directory.path_join(field.field_save.PRIMARY))
	elif mode == "read":
		var cut = rows.filter(func(row): return row.id == CUT)[0]
		var cooling = rows.filter(func(row): return row.id == COOLING)[0]
		field.forest._open_pine(cut)
		field.forest._open_pine(cooling)
		checks["two notches rebound on moved root"] = cut.live.strikes == 2 and cut.live.global_position.is_equal_approx(keys[CUT])
		var remaining: float = field.lifecycle.cooling.get(COOLING,-1.0)
		checks["legacy timer rebound on moved root"] = remaining > 3.0 and remaining <= 3.2 and cooling.live.phase == "credited"
		field.lifecycle.advance(remaining-.01)
		checks["reloaded source does not renew early"] = cooling.live.phase == "credited"
		field.lifecycle.advance(.02)
		checks["the same relocated pine renews when due"] = cooling.live.phase == "rooted" and cooling.live.global_position.is_equal_approx(keys[COOLING])
		for i in field.inventory.costs.center_hearth.wood:
			field.inventory.collect("isolated-relocated-wood-%02d"%i,"wood")
			field.inventory.payment("center_hearth","wood",false)
		field._finish_purchase("center_hearth")
		field._apply_hearth(true,false)
		checks["off-site moved roots survive base purchase"] = not cut.get("occupied",false) and not cooling.get("occupied",false) and field.field_env.seasonal_pines.is_empty()
		field._persist_world()
	elif mode == "paid":
		checks["original aliases persist through a paid cold open"] = field.field_env.perimeter_stage == 1 and keys.has(CUT) and keys.has(COOLING)
		var cut = rows.filter(func(row): return row.id == CUT)[0]
		var cooling = rows.filter(func(row): return row.id == COOLING)[0]
		checks["off-site roots retain standing proxies in paid profile"] = not cut.get("occupied",false) and cut.proxy_visible and not cooling.get("occupied",false) and cooling.proxy_visible
		checks["paid profile retains cut progress"] = field.lifecycle.partial.get(CUT, 0) == 2
	else:
		checks["known fixture stage"] = false
	print("FOREST_SOURCE_RESUME ", JSON.stringify({"stage":mode,"checks":checks,"positions":keys}))
	await Session.drain_field_audio(self,field)
	field.queue_free()
	for i in 8: await process_frame
	quit(int(checks.values().has(false)))
