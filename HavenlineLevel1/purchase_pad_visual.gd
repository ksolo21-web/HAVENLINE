extends Node3D
## Presentation bridge only; no trigger, stock mutation, grant, input or save.
const Adapter = preload("res://pad_v5_view.gd")
const Asset = preload("res://assets/studio/purchase_pad_v5.glb")
const FOOTPRINT_CAP := .80
const SEAT_Y := .008
const SEAT_LABEL_GAP := .008
var binding_ready := false
var fitted_bounds := AABB()
var original_bounds := AABB()
var scene_view: Adapter
var _revision := 0

func install_exact() -> bool:
	if scene_view != null:
		return false
	scene_view = Adapter.new()
	add_child(scene_view)
	if not scene_view.install(Asset):
		return false
	var nodes := scene_view.find_children("*", "MeshInstance3D", true, false)
	if nodes.size() != 6:
		return false
	var first := true
	var deck_roof := 0.0
	for node in nodes:
		var piece := node as MeshInstance3D
		var raw: AABB = (scene_view.global_transform.affine_inverse() * piece.global_transform) * piece.get_aabb()
		original_bounds = raw if first else original_bounds.merge(raw)
		first = false
		if piece.name == &"PurchaseDeck_Surface":
			deck_roof = raw.end.y
	if not original_bounds.size.is_finite() or minf(original_bounds.size.x, original_bounds.size.z) <= .01:
		return false
	var factor := FOOTPRINT_CAP / maxf(original_bounds.size.x, original_bounds.size.z)
	scene_view.scale = Vector3.ONE * factor
	var center := original_bounds.get_center()
	scene_view.position = Vector3(-center.x * factor, SEAT_Y - original_bounds.position.y * factor, -center.z * factor)
	fitted_bounds = scene_view.transform * original_bounds
	for child_name in ["Action", "Cost"]:
		var label := scene_view.get_node_or_null(NodePath(child_name)) as Label3D
		if label == null:
			return false
		label.position.y = deck_roof + SEAT_LABEL_GAP / factor
	binding_ready = true
	return true

func reflect_published_state(accepted: bool) -> void:
	if not binding_ready:
		return
	_revision += 1
	var phase := Adapter.Phase.ACCEPTED if accepted else Adapter.Phase.AVAILABLE
	# Rendering receives only an offered or published commit; no faux progress states.
	scene_view.apply_state(_revision, phase, false, false, accepted, "BUILD", "3 WOOD")
