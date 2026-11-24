extends SceneTree

const BuyPad = preload("res://buy_pad.gd")
const Scene = preload("res://buy_pad.tscn")
var _passed := 0
var _failed := 0

func _initialize() -> void:
	call_deferred("_run")

func _check(ok: bool, what: String) -> void:
	if ok:
		_passed += 1
		print("PASS: ", what)
	else:
		_failed += 1
		push_error(what)

func _run() -> void:
	var marker = Scene.instantiate()
	root.add_child(marker)
	var marker_deck: MeshInstance3D = marker.get_node("SlateSurface")
	var brackets: Node3D = marker.get_node("SeparatedBrackets")
	var arm: MeshInstance3D = brackets.get_child(0).get_node("Across")
	var action: Label3D = marker.get_node("Action")
	var cost: Label3D = marker.get_node("Cost")
	var deck_mat: StandardMaterial3D = marker_deck.material_override
	var corner_mat: StandardMaterial3D = arm.material_override
	_check(not marker.visible, "no unearned offer shown before enrollment")
	_check(brackets.get_child_count() == 4 and brackets.get_children().all(func(c: Node): return c.get_child_count() == 2), "four disconnected L brackets, two arms each")
	_check(deck_mat != corner_mat and marker_deck.mesh.size.y < 0.04, "matte low deck independently colored")
	marker.show_offer(BuyPad.OfferPhase.AVAILABLE, false, false, "Build", "Supplied")
	_check(marker.visible and deck_mat.albedo_color == BuyPad.SLATE and corner_mat.albedo_color == BuyPad.IDLE_CORNER, "visible neutral purchase offer")
	_check(action.text == "Build" and cost.text == "Supplied", "labels driven by caller rather than hardcoded costs")
	marker.show_offer(BuyPad.OfferPhase.PAYING, false, false, "Build", "Partial")
	_check(marker.visible and deck_mat.albedo_color == BuyPad.SLATE and corner_mat.albedo_color == BuyPad.ACTIVE_CORNER, "partial payment colors only corners")
	_check(cost.text == "Partial", "partial payment keeps updated cost presentation")
	marker.show_offer(BuyPad.OfferPhase.PENDING, false, false, "Build", "Pending")
	_check(marker.visible and deck_mat.albedo_color == BuyPad.CONFIRM_TINT and corner_mat.albedo_color == BuyPad.ACTIVE_CORNER, "pending confirmation colors the local center without hiding")
	_check(action.text == "Build" and cost.text == "Pending", "pending holds visible offer context")
	marker.show_offer(BuyPad.OfferPhase.AVAILABLE, false, false, "Build", "Retry")
	_check(marker.visible and deck_mat.albedo_color == BuyPad.SLATE and cost.text == "Retry", "rejected or cancelled offer can return to neutral")
	marker.show_offer(BuyPad.OfferPhase.PENDING, false, false, "Build", "Pending")
	marker.show_offer(BuyPad.OfferPhase.ACCEPTED, false, true, "", "")
	_check(not marker.visible and cost.text.is_empty(), "accepted one-time offer hides even with erroneous next-offer flag")
	marker.show_offer(BuyPad.OfferPhase.PAYING, true, false, "Upgrade", "Partial")
	_check(marker.visible and corner_mat.albedo_color == BuyPad.ACTIVE_CORNER, "repeatable remains visible while paying")
	marker.show_offer(BuyPad.OfferPhase.ACCEPTED, true, false, "Upgrade", "")
	_check(not marker.visible, "repeatable accepted without next offer stays hidden")
	marker.show_offer(BuyPad.OfferPhase.ACCEPTED, true, true, "Upgrade", "Next tier")
	_check(marker.visible and cost.text == "Next tier" and deck_mat.albedo_color == BuyPad.SLATE and corner_mat.albedo_color == BuyPad.IDLE_CORNER, "repeatable re-arms only with next offer and clears green")
	var second = Scene.instantiate()
	root.add_child(second)
	second.show_offer(BuyPad.OfferPhase.PAYING, false, false, "Other", "Other")
	_check(corner_mat.albedo_color == BuyPad.IDLE_CORNER and second.visible, "neighbor cue remains independent; no shared changing material")
	marker.queue_free()
	second.queue_free()
	print("RESULT: %d passed; %d failed" % [_passed, _failed])
	quit(int(_failed != 0))
