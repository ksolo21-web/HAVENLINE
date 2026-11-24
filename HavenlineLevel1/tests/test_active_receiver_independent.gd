extends SceneTree
const Opening = preload("res://opening.tscn")
const Save = preload("res://opening_save.gd")
var primary := ""
var stage := ""
var checks := 0
var errors := 0
func _initialize() -> void:
	call_deferred("run")
func read(game) -> Array:
	return [game.ledger.snapshot(), game.camp_built.visible, game.wood_stock_view.presented_units,game.gates[0].active,game.gates[1].active,FileAccess.get_file_as_bytes(primary),FileAccess.file_exists(stage)]
func check(result: bool, label: String) -> void:
	checks += 1
	if not result:
		errors += 1
	print(("PASS " if result else "FAIL ") + label)
func rejected(game, baseline: Array, label: String) -> void:
	var answer: bool = game.fund_opening_receiver("center-hearth", "wood")
	check(not answer and read(game) == baseline, label)
func run() -> void:
	var args := OS.get_cmdline_user_args()
	var save := Save.new()
	if not save.configure(args):
		quit(2)
		return
	for argument in args:
		if argument.begins_with(Save.FLAG):
			var folder := argument.trim_prefix(Save.FLAG)
			primary = folder.path_join(Save.PRIMARY)
			stage = folder.path_join(Save.STAGING)
	if primary.is_empty() or FileAccess.file_exists(primary) or FileAccess.file_exists(stage):
		quit(2)
		return
	var game = Opening.instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.actor.position = game.point(game.layout.pad_xz)
	if game.persist_blocked or not game.purchase_pad_view.binding_ready or not game.purchase_pad_view.scene_view.is_visible_in_tree():
		quit(2)
		return
	for id in ["wood-a", "wood-b", "wood-c"]:
		if not game._collect_wood_source(id):
			quit(2)
			return
	var baseline := read(game)
	if baseline[1] or baseline[2] != 3 or baseline[5].is_empty() or baseline[6]:
		quit(2)
		return
	var bridge = game.purchase_pad_view
	var pad = bridge.scene_view
	bridge.binding_ready = false
	pad.hide()
	rejected(game, baseline, "exact V1 reject: hidden unbound cannot debit, grant, write or stage")
	pad.show()
	rejected(game, baseline, "visible unbound is not authorized")
	bridge.binding_ready = true
	pad.hide()
	rejected(game, baseline, "bound but inactive hidden pad")
	pad.show()
	bridge.hide()
	rejected(game, baseline, "model visible locally but ancestor hidden")
	bridge.show()
	pad.installed = false
	rejected(game, baseline, "stale bridge binding flag with model uninstalled")
	pad.installed = true
	bridge.reparent(root)
	rejected(game, baseline, "visibly installed bridge detached from opening")
	bridge.reparent(game)
	pad.reparent(game)
	rejected(game, baseline, "visibly installed model detached from bridge")
	pad.reparent(bridge)
	check(read(game) == baseline and pad.is_visible_in_tree(), "restored state is still exactly payable")
	check(game.fund_opening_receiver("center-hearth", "wood") and game.camp_built.visible and game.ledger.stock.wood == 0 and not pad.is_visible_in_tree(), "ordinary eligible command commits and publishes once")
	var paid := read(game)
	rejected(game, paid, "paid repeat cannot debit, grant, write or stage")
	print("INDEPENDENT ACTIVE RECEIVER CHECKS=", checks, " FAILURES=", errors)
	quit(1 if errors else 0)
