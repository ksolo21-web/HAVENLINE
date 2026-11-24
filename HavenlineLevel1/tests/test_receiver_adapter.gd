extends SceneTree
const Opening = preload("res://opening.tscn")
const Save = preload("res://opening_save.gd")
const Ledger = preload("res://opening_ledger.gd")
var failures := 0
var checks := 0
var primary := ""

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
	print("%s %s" % ["PASS" if ok else "FAIL", label])

func _initialize() -> void:
	call_deferred("run")

func observe(game) -> Dictionary:
	return {
		"ledger": game.ledger.snapshot(),
		"camp": game.camp_built.visible,
		"pad": game.purchase_pad_view.scene_view.visible,
		"wood_units": game.wood_stock_view.presented_units,
		"gate_earned": [game.gates[0].active, game.gates[1].active],
		"save": FileAccess.get_file_as_bytes(primary)
	}

func run() -> void:
	var args := OS.get_cmdline_user_args()
	var safety := Save.new()
	if not safety.configure(args):
		push_error("Required authorized disposable profile not present.")
		quit(2)
		return
	for arg in args:
		if arg.begins_with(Save.FLAG):
			primary = arg.trim_prefix(Save.FLAG).path_join(Save.PRIMARY)
	var reading := "--read-paid" in args
	if primary.is_empty() or FileAccess.file_exists(primary) != reading:
		push_error("Unexpected primary presence for test stage.")
		quit(2)
		return
	var game = Opening.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	if game.persist_blocked or not game.purchase_pad_view.binding_ready:
		push_error("Expected authorized disposable save and bound pad.")
		quit(2)
		return
	var pad: Vector3 = game.point(game.layout.pad_xz)
	var canonical := Ledger.new()
	for id in Ledger.KNOWN_WOOD:
		canonical.collect_wood(id)
	canonical.pay_center_hearth()
	var payload := JSON.stringify(canonical.snapshot())
	var expected := JSON.stringify({"version": 1, "payload": payload, "sha256": payload.sha256_text()}).to_utf8_buffer()
	if reading:
		game.actor.position = pad
		var restored := observe(game)
		check(restored.ledger == canonical.snapshot() and restored.save == expected, "cold restore reproduces legacy paid state and exact bytes")
		check(restored.camp and not restored.pad and restored.wood_units == 0 and restored.gate_earned == [true, true], "cold restore projects exactly one earned camp")
		check(not game.fund_opening_receiver("center-hearth", "wood") and observe(game) == restored, "paid receiver inactive after cold restart")
	else:
		game.actor.position = pad
		var fresh := observe(game)
		check(not game.fund_opening_receiver("center-hearth", "wood") and observe(game) == fresh and not FileAccess.file_exists(primary), "underfunded receiver cannot create save or publish")
		for id in Ledger.KNOWN_WOOD:
			check(game._collect_wood_source(id), "test setup only: commit source " + id)
		var before := observe(game)
		check(before.save.size() > 0 and before.pad and not before.camp and before.wood_units == 3 and before.gate_earned == [false, false], "funded stock does not grant camp")
		var pad_bridge = game.purchase_pad_view
		var pad_model = pad_bridge.scene_view
		pad_bridge.binding_ready = false
		pad_model.hide()
		var unbound := observe(game)
		check(not game.fund_opening_receiver("center-hearth", "wood") and observe(game) == unbound and not FileAccess.file_exists(primary.get_base_dir().path_join(Save.STAGING)), "failed hidden binding cannot charge wood, grant camp, alter save bytes or stage writes")
		pad_model.show()
		var unbound_visible := observe(game)
		check(not game.fund_opening_receiver("center-hearth", "wood") and observe(game) == unbound_visible, "visible but not exact-bound is not sufficient")
		pad_bridge.binding_ready = true
		pad_model.installed = false
		check(not game.fund_opening_receiver("center-hearth", "wood") and observe(game) == before, "stale bound flag without installed model cannot charge")
		pad_model.installed = true
		pad_model.hide()
		var unavailable := observe(game)
		check(not game.fund_opening_receiver("center-hearth", "wood") and observe(game) == unavailable, "installed but not offered cannot charge")
		pad_model.show()
		check(observe(game) == before, "restored exact offer retains wood, camp state and save bytes")
		for pair in [
			["cooker", "wood"], ["center-hearth", "fish"], ["wood", "center-hearth"],
			["CENTER-HEARTH", "wood"], ["center-hearth", " wood"],
			[null, "wood"], ["center-hearth", null], [true, "wood"],
			["center-hearth", 3], [StringName("center-hearth"), "wood"]
		]:
			check(not game.fund_opening_receiver(pair[0], pair[1]) and observe(game) == before, "rejected wrong pair " + str(pair))
		check(not game.fund_opening_receiver() and observe(game) == before, "missing all fields rejected")
		game.actor.position = pad + Vector3(.721, 0, 0)
		check(not game.fund_opening_receiver("center-hearth", "wood") and observe(game) == before, "outside original interaction radius rejected")
		game.actor.position = pad + Vector3(.719, 0, 0)
		check(game.fund_opening_receiver("center-hearth", "wood"), "exact eligible IDs inside original radius accepted")
		var after := observe(game)
		check(after.ledger == canonical.snapshot() and after.save == expected, "legacy receipt schema and serialized bytes unchanged")
		check(after.camp and not after.pad and after.wood_units == 0 and after.gate_earned == [true, true], "paid camp and gates published")
		for index in range(3):
			check(not game.fund_opening_receiver("center-hearth", "wood") and observe(game) == after, "repeat request at pad is inert " + str(index))
		check(not FileAccess.file_exists(primary.get_base_dir().path_join(Save.STAGING)), "no staging file left behind")
	print("RECEIVER SUMMARY mode=%s checks=%d failures=%d" % ["read" if reading else "write", checks, failures])
	quit(0 if failures == 0 else 1)
