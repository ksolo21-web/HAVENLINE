extends Node3D

signal inventory_changed
signal purchase_completed(plot_id: String)
signal unit_landed(kind: String, destination: String)

const Inventory = preload("res://field_inventory.gd")
const FRAME_PATH := "res://assets/field_pack/carry_frame.glb"
const RACK_SHADER := preload("res://assets/field_pack/portable_material.gdshader")
const WIDTH := {"wood":.47, "stone":.42, "meat":.31, "coal":.29, "slate":.31, "metal":.30}
const LANES := {
	"wood":Vector2(-.23,-.36), "stone":Vector2(.23,-.36),
	"meat":Vector2(-.23,-.67), "coal":Vector2(.23,-.71),
	"slate":Vector2(-.23,-1.01), "metal":Vector2(.23,-1.06),
}
const StockLayout = preload("res://field_stock_layout.gd")
const INTERVAL := 0.16
const PICKUP_TIME := 0.29
const SEND_TIME := 0.28
# The full reference pack reaches at most 5.6 standing hero heights (1.75 m).
const PACK_TOP := 9.8
const TOP_MARGIN := .10
const HAND := "carry"
const STOCK := "storage"

var inventory: Inventory
var actor: Node3D
var factory: Callable
var storage_unit_scale := 1.0
var storage_layout: Callable
var storage_anchors := {}
var receivers := {}
var rack: Node3D
var frame: Node3D
var pieces := {}
var flights: Array[Dictionary] = []
var cooldown := 0.0
var measured := {}
var hand_visible := {}
var tier_height := {"wood":.13, "stone":.11, "meat":.145, "coal":.15, "slate":.12, "metal":.16}

func setup(ledger: Inventory, character: Node3D, item_factory: Callable) -> void:
	inventory = ledger
	actor = character
	factory = item_factory
	rack = Node3D.new()
	rack.name = "FieldPack"
	actor.add_child(rack)
	var scene := load(FRAME_PATH) as PackedScene
	if scene:
		frame = scene.instantiate() as Node3D
		rack.add_child(frame)
		frame.position = Vector3(0, 0.50, -0.36)
		frame.scale = Vector3(.84, .78, .83)
		var palette := ShaderMaterial.new()
		palette.shader = RACK_SHADER
		palette.set_shader_parameter("surface_kind", 4)
		if frame is MeshInstance3D:
			frame.material_override = palette
		for part in frame.find_children("*", "MeshInstance3D", true, false):
			part.material_override = palette
	sync()

func define_storage(kind: String, anchor: Node3D) -> void:
	if kind in Inventory.KINDS:
		storage_anchors[kind] = anchor
		sync()

func define_receiver(id: String, anchor: Node3D) -> void:
	if inventory.costs.has(id) and id not in [HAND, STOCK]:
		receivers[id] = anchor

func set_storage_layout(layout: Callable, unit_scale := 1.0) -> void:
	storage_unit_scale = unit_scale
	storage_layout = layout
	sync()

func _pack_position(kind: String, index: int) -> Vector3:
	# Fixed left/right lanes keep every type separate at every load.
	var lane: Vector2 = LANES[kind]
	return Vector3(lane.x,.655 + index * float(tier_height[kind]),lane.y)

func _pack_limit(kind: String) -> int:
	var base := _pack_position(kind, 0)
	var step := float(tier_height[kind])
	var extent: Vector3 = measured.get(kind, Vector3(float(WIDTH[kind]),step,float(WIDTH[kind])))
	var rise := PACK_TOP - base.y - extent.y
	var camera := get_viewport().get_camera_3d()
	if camera:
		# The donor is grounded and centered in XZ. Its circumscribed radius
		# covers every alternating tier yaw, including while the actor turns.
		var up_screen := camera.get_camera_transform().basis.y
		var horizontal := Vector3(up_screen.x,0,up_screen.z).normalized()
		var radius := Vector2(extent.x,extent.z).length() * .5
		var top := rack.to_global(base + Vector3.UP*extent.y) + horizontal*radius
		var screen_y := camera.unproject_position(top).y
		var pixels_per_metre := screen_y - camera.unproject_position(top+rack.global_basis.y).y
		if pixels_per_metre > .001:
			var allowed_y := get_viewport().get_visible_rect().size.y * TOP_MARGIN
			rise = minf(rise, (screen_y - allowed_y) / pixels_per_metre)
	return maxi(1, floori(rise / step) + 1)

func _hand_slot(kind: String, logical_index: int) -> int:
	return clampi(logical_index,0,_pack_limit(kind)-1)

func _visible_units(kind: String, count: int, location: String) -> int:
	if location == STOCK:
		return mini(count, StockLayout.CENTERS[kind].size())
	return mini(count,_pack_limit(kind))

func _floor_position(kind: String, index: int) -> Vector3:
	var slot := StockLayout.slot(kind, index)
	if storage_layout.is_valid():
		return storage_layout.call(kind, slot)
	var anchor: Node3D = storage_anchors[kind]
	return anchor.to_global(StockLayout.position(kind, slot))

func _outstanding(kind: String, endpoint: String, outgoing: bool) -> int:
	var n := 0
	var key := "from" if outgoing else "to"
	for flight in flights:
		if flight.kind == kind and flight[key] == endpoint:
			n += 1
	return n

func _available(kind: String, where: String) -> int:
	var counts := inventory.carried if where == HAND else inventory.stored
	var pending_pickups := _outstanding(kind, HAND, false) if where == HAND else 0
	return maxi(0, int(counts[kind]) - _outstanding(kind, where, true) - pending_pickups)

func _piece(kind: String) -> Node3D:
	var node: Node3D = factory.call(kind, float(WIDTH[kind]))
	if node:
		node.set_meta("field_material", kind)
		if not measured.has(kind):
			var boxes: Array[AABB] = []
			_sample_bounds(node, Transform3D.IDENTITY, boxes)
			if not boxes.is_empty():
				var bounds := boxes[0]
				for box in boxes:
					bounds = bounds.merge(box)
				tier_height[kind] = maxf(.02, bounds.size.y * .96)
				measured[kind] = bounds.size
	return node

func _sample_bounds(node: Node, parent_xform: Transform3D, output: Array[AABB]) -> void:
	var xform := parent_xform
	if node is Node3D:
		xform *= (node as Node3D).transform
	if node is MeshInstance3D and node.mesh:
		output.append(xform * node.mesh.get_aabb())
	for child in node.get_children():
		_sample_bounds(child, xform, output)

func _tier_yaw(kind: String, index: int) -> float:
	# Reverse alternating packets so knots, grain and torn faces change sides.
	var turn := PI if posmod(index, 2) == 1 else 0.0
	return turn + deg_to_rad(float(posmod(index*7 + Inventory.KINDS.find(kind)*5, 5)-2))

func _heading(endpoint: String, kind: String, index: int) -> float:
	if endpoint == HAND:
		return actor.global_rotation.y + _tier_yaw(kind, _hand_slot(kind,index))
	return _tier_yaw(kind, StockLayout.slot(kind, index)) if endpoint == STOCK else 0.0

func _place(position_id: String, kind: String, n: int) -> Vector3:
	if position_id == HAND:
		return rack.to_global(_pack_position(kind, _hand_slot(kind,n)))
	if position_id == STOCK:
		return _floor_position(kind, maxi(0,n))
	return (receivers[position_id] as Node3D).global_position + Vector3.UP * .10

func sync() -> void:
	if not inventory or not rack:
		return
	var loaded := false
	for kind: String in Inventory.KINDS:
		for location: String in [HAND, STOCK]:
			if location == STOCK and not storage_anchors.has(kind):
				continue
			var key := location + "/" + kind
			var pool: Array = pieces.get(key, [])
			var n := 0 if location == STOCK and not inventory.storage_open(kind) else _available(kind, location)
			# Measure the first authored packet before computing capacity, even
			# when a large existing balance is first restored into an empty pool.
			if n > 0 and not measured.has(kind):
				var first := _piece(kind)
				if first:
					var parent: Node3D = rack if location == HAND else storage_anchors[kind]
					parent.add_child(first)
					pool.append(first)
			n = _visible_units(kind, n, location)
			if location == HAND: hand_visible[kind] = n
			while pool.size() < n:
				var unit := _piece(kind)
				if not unit:
					break
				var parent: Node3D = rack if location == HAND else storage_anchors[kind]
				parent.add_child(unit)
				pool.append(unit)
			for i in pool.size():
				var unit: Node3D = pool[i]
				unit.visible = i < n
				if i < n:
					if location == HAND:
						loaded = true
						unit.position = _pack_position(kind, i)
						unit.rotation.y = _tier_yaw(kind, i)
					else:
						unit.global_position = _floor_position(kind, i)
						unit.global_rotation.y = _heading(STOCK, kind, i)
						unit.scale = Vector3.ONE * (storage_unit_scale * StockLayout.width(kind, i) / float(WIDTH[kind]))
			pieces[key] = pool
	if frame:
		frame.visible = loaded

func pickup(token: String, kind: String, start: Vector3) -> bool:
	if kind not in Inventory.KINDS or token.is_empty() or inventory.collected.has(token):
		return false
	var unit := _piece(kind)
	if not unit:
		return false
	if not inventory.collect(token, kind):
		unit.free()
		return false
	var idx := int(inventory.carried[kind]) - 1 - _outstanding(kind, HAND, true)
	_start(unit, kind, "", HAND, start, idx, PICKUP_TIME, 1.15, 1.0, 0.0)
	inventory_changed.emit()
	return true

func deposit_storage(kind: String) -> bool:
	if cooldown > 0 or not inventory.storage_open(kind) or not storage_anchors.has(kind) or _available(kind, HAND) <= 0:
		return false
	var idx := int(inventory.stored[kind]) + _outstanding(kind, STOCK, false) - _outstanding(kind, STOCK, true)
	return _send(kind, HAND, STOCK, idx)

func contribute(id: String) -> bool:
	if cooldown > 0 or not receivers.has(id) or not inventory.offer_open(id):
		return false
	var needs := inventory.remaining(id)
	for kind: String in Inventory.KINDS:
		if needs.get(kind, 0) <= _outstanding(kind, id, false):
			continue
		for origin: String in [HAND, STOCK]:
			if origin == STOCK and (not storage_anchors.has(kind) or not inventory.storage_open(kind)):
				continue
			if _available(kind, origin) > 0:
				return _send(kind, origin, id, 0)
	return false

func _send(kind: String, source: String, dest: String, dest_index: int) -> bool:
	var unit := _piece(kind)
	if not unit:
		return false
	var source_index := _available(kind, source) - 1
	var start := _place(source, kind, source_index)
	var start_scale := storage_unit_scale * StockLayout.width(kind, source_index) / float(WIDTH[kind]) if source == STOCK else 1.0
	var end_scale := storage_unit_scale * StockLayout.width(kind, dest_index) / float(WIDTH[kind]) if dest == STOCK else 1.0
	cooldown = INTERVAL
	_start(unit, kind, source, dest, start, dest_index, SEND_TIME, start_scale, end_scale, _heading(source, kind, source_index))
	return true

func _start(unit: Node3D, kind: String, source: String, dest: String, start: Vector3, index: int, duration: float, scale_start: float, scale_end: float, start_yaw: float) -> void:
	add_child(unit)
	unit.global_position = start
	unit.global_rotation.y = start_yaw
	unit.scale = Vector3.ONE * scale_start
	flights.append({"mesh":unit, "kind":kind, "from":source, "to":dest, "start":start, "index":index, "t":0.0, "duration":duration, "scale_start":scale_start, "scale_end":scale_end, "start_yaw":start_yaw})
	sync()

func cancel_transfers() -> void:
	for flight in flights:
		(flight.mesh as Node3D).queue_free()
	flights.clear()
	cooldown = 0
	sync()

func _physics_process(delta: float) -> void:
	advance(delta)

func advance(delta: float) -> void:
	# The rack follows the actor without touching its nodes. Only a projection
	# that changes a lane's visible count needs to reposition/show its pool.
	for kind: String in Inventory.KINDS:
		var count := _available(kind,HAND)
		if count > 0 and _visible_units(kind,count,HAND) != int(hand_visible.get(kind,0)):
			sync()
			break
	cooldown = maxf(0.0, cooldown - delta)
	for flight in flights.duplicate():
		if not flights.has(flight):
			continue
		flight.t = minf(1.0, float(flight.t) + delta / float(flight.duration))
		var t := float(flight.t)
		var dest := _place(flight.to, flight.kind, flight.index)
		var arc := .20 if flight.to == HAND else .40
		var unit: Node3D = flight.mesh
		unit.global_position = (flight.start as Vector3).lerp(dest, t) + Vector3.UP * (4.0*t*(1.0-t)*arc)
		unit.scale = Vector3.ONE * lerpf(flight.scale_start, flight.scale_end, t)
		unit.global_rotation.y = lerp_angle(flight.start_yaw, _heading(flight.to, flight.kind, flight.index), t)
		if t >= 1.0:
			_land(flight)

func _land(flight: Dictionary) -> void:
	var kind: String = flight.kind
	var dest: String = flight.to
	flights.erase(flight)
	var accepted := true
	if dest == STOCK:
		accepted = inventory.deposit(kind)
	elif dest != HAND:
		accepted = inventory.payment(dest, kind, flight.from == STOCK)
	(flight.mesh as Node3D).queue_free()
	sync()
	if accepted:
		inventory_changed.emit()
		unit_landed.emit(kind, dest)
		if dest not in [HAND, STOCK] and inventory.complete(dest):
			purchase_completed.emit(dest)
