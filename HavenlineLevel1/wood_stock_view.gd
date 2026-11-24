extends Node3D
## Technical-only readout; consumes published count, without an authority dependency.
const Wood = preload("res://assets/studio/wood_bundle_v3.glb")
const CAP := Vector3(.40, .22, .24)
const CLEARANCE := .025
var presented_units := 0
var payload: Node3D
var counter: Label3D
var fitted_bounds := AABB()
var measured_actor := AABB()

func gather(node: Node, out: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D and node.mesh != null:
		out.append(node)
	for child in node.get_children():
		gather(child, out)

func bounds_of(node: Node3D, relative: Node3D) -> AABB:
	var parts: Array[MeshInstance3D] = []
	gather(node, parts)
	var bounds := AABB()
	for i in parts.size():
		var part := parts[i]
		var box: AABB = (relative.global_transform.affine_inverse() * part.global_transform) * part.get_aabb()
		bounds = box if i == 0 else bounds.merge(box)
	return bounds

func install(known_hero: Node3D) -> void:
	counter = Label3D.new()
	counter.name = "TechnicalWoodCount"
	counter.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	counter.pixel_size = .003
	add_child(counter)
	counter.position = Vector3(0, 1.96, 0)
	measured_actor = bounds_of(known_hero, self)
	if measured_actor.size.y <= .01 or not measured_actor.size.is_finite():
		return # count text remains useful even when exact fit is unavailable
	var candidate := Wood.instantiate() as Node3D
	if candidate == null:
		return
	add_child(candidate)
	var original := bounds_of(candidate, self)
	if minf(original.size.x, minf(original.size.y, original.size.z)) <= .001 or not original.size.is_finite():
		candidate.free()
		return
	var factor := minf(CAP.x / original.size.x, minf(CAP.y / original.size.y, CAP.z / original.size.z))
	candidate.scale *= factor
	var back := measured_actor.position.z - CLEARANCE
	candidate.position = Vector3(-original.get_center().x * factor,
		measured_actor.position.y + measured_actor.size.y * .68 - original.get_center().y * factor,
		back - original.end.z * factor)
	fitted_bounds = bounds_of(candidate, self)
	if not fitted_bounds.size.is_finite() or fitted_bounds.end.z > back + .0001 or fitted_bounds.size.x > CAP.x + .0001 or fitted_bounds.size.y > CAP.y + .0001 or fitted_bounds.size.z > CAP.z + .0001:
		candidate.free()
		return
	payload = candidate
	payload.name = "TechnicalWoodBundleRepresentative"
	reflect_stock(0)

func reflect_stock(published_wood: int) -> void:
	presented_units = maxi(published_wood, 0)
	counter.text = "WOOD x%d [DEV]" % presented_units
	counter.visible = presented_units > 0
	if payload != null:
		payload.visible = presented_units > 0
