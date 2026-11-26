extends Node3D

signal inventory_changed
signal purchase_completed(plot_id: String)
signal unit_landed(kind: String, destination: String)

const Inventory = preload("res://field_inventory.gd")
const FieldArt = preload("res://field_art.gd")
const FRAME_PATH := "res://assets/field_pack/carry_frame.glb"
const WORN_RESOURCE := preload("res://assets/field_pack/worn_resource.gdshader")
const RACK_SHADER := preload("res://assets/field_pack/portable_material.gdshader")
const WIDTH := {"wood":.42, "stone":.32, "meat":.23, "coal":.20, "slate":.205, "metal":.20}
# Permanent bays keep unlike resources off one another even when a neighboring
# bay empties. The wide timber bay has two side-by-side, bark-outward packets
# per course; the other five bays each hold one vertical stack.
const BAY_X := {"wood":0.0, "slate":-.565, "coal":-.455, "metal":-.165, "meat":.135, "stone":.48}
const OUTER_ROW := ["coal", "metal", "meat", "stone"]
const INNER_Z := -.635
const OUTER_Z := -.965
const PACK_BASE := .91
const INNER_RISE := .10
const TIMBER_PAIR_X := .212
const MAX_LAYERS := 24
const SHELF_SCENE := preload("res://assets/field_pack/expedition_shelf.glb")
const StockLayout = preload("res://field_stock_layout.gd")
const INTERVAL := 0.16
const PAYMENT_INTERVAL := 4.0 / 60.0
const PICKUP_TIME := 0.29
const SEND_TIME := 0.28
# The full reference pack reaches at most 5.6 standing hero heights (1.75 m).
const PACK_TOP := 9.8
const TOP_MARGIN := .08
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
var worn_materials := {}
var shelves: Array[MeshInstance3D] = []
var presented := {}
var planned_counts := {}
var minimum_headroom := 0
var maximum_headroom := 2147483647
var pieces := {}
var flights: Array[Dictionary] = []
var cooldown := 0.0
var measured := {}
var station_material := ""
var tier_height := {"wood":.13, "stone":.11, "meat":.145, "coal":.15, "slate":.12, "metal":.16}

func setup(ledger: Inventory, character: Node3D, item_factory: Callable) -> void:
	inventory = ledger
	actor = character
	factory = item_factory
	rack = Node3D.new()
	rack.name = "FieldPack"
	actor.add_child(rack)
	rack.child_entered_tree.connect(_dress_carried_resource)
	var scene := load(FRAME_PATH) as PackedScene
	if scene:
		frame = scene.instantiate() as Node3D
		rack.add_child(frame)
		frame.position = Vector3(0, 0.50, -0.36)
		frame.scale = Vector3(.76, .78, .78)
		var donor := SHELF_SCENE.instantiate()
		var palette := ShaderMaterial.new()
		palette.shader = RACK_SHADER
		palette.set_shader_parameter("surface_kind", 4)
		if frame is MeshInstance3D:
			frame.material_override = palette
		for part in frame.find_children("*", "MeshInstance3D", true, false):
			part.material_override = palette
		# The two original timber shelves support the actual packet footprints.
		for row in 2:
			var board := donor.get_node("MiddleSupport" if row == 0 else "RearSupport") as MeshInstance3D
			board.owner = null
			donor.remove_child(board)
			rack.add_child(board)
			board.material_override = palette
			shelves.append(board)
		donor.free()
	sync()

# Only the fixed packets on the actor receive a small head sightline.
# Loose drops, stock, processors, transfers and the frame use their own paint.
func _dress_carried_resource(unit: Node) -> void:
	if not unit.has_meta("field_material"):
		return
	for part: MeshInstance3D in unit.find_children("*", "MeshInstance3D", true, false):
		for i in part.mesh.get_surface_count():
			var source := part.get_active_material(i) as StandardMaterial3D
			if not source:
				continue
			if not worn_materials.has(source):
				var material := ShaderMaterial.new()
				material.shader = WORN_RESOURCE
				material.set_shader_parameter("paint",source.albedo_texture)
				material.set_shader_parameter("tint",source.albedo_color)
				material.set_shader_parameter("roughness",source.roughness)
				material.set_shader_parameter("metalness",source.metallic)
				material.set_shader_parameter("specular",source.metallic_specular)
				if source.emission_enabled:
					material.set_shader_parameter("glow",source.emission)
					material.set_shader_parameter("glow_map",source.emission_texture)
					material.set_shader_parameter("glow_power",source.emission_energy_multiplier)
				worn_materials[source] = material
			part.set_surface_override_material(i, worn_materials[source])

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
	var outer := kind in OUTER_ROW
	var x := float(BAY_X[kind])
	if kind == "wood":
		x = -TIMBER_PAIR_X if index % 2 == 0 else TIMBER_PAIR_X
		index = floori(index * .5)
	return Vector3(x, PACK_BASE + (0.0 if outer else INNER_RISE) + index * float(tier_height[kind]), OUTER_Z if outer else INNER_Z)

func _fit_shelves(counts: Dictionary) -> void:
	for row in shelves.size():
		var left := INF
		var right := -INF
		var depth := 0.0
		for kind: String in Inventory.KINDS:
			if counts[kind] <= 0 or (kind in OUTER_ROW) != (row == 1):
				continue
			var unit: Vector3 = measured[kind]
			var first := _pack_position(kind, 0).x
			var last := _pack_position(kind, 1).x if kind == "wood" and counts[kind] > 1 else first
			left = minf(left, first - unit.x * .5)
			right = maxf(right, last + unit.x * .5)
			depth = maxf(depth, unit.z)
		var board := shelves[row]
		board.visible = left <= right
		if not board.visible:
			continue
		var bounds := board.mesh.get_aabb()
		board.scale = Vector3(right - left + .016, .035, depth + .026) / bounds.size
		var top := Vector3((left + right) * .5, PACK_BASE + (INNER_RISE if row == 0 else 0.), INNER_Z if row == 0 else OUTER_Z)
		board.position = top - Vector3(bounds.get_center().x, bounds.end.y, bounds.get_center().z) * board.scale

func _headroom_bucket() -> int:
	var room := PACK_TOP - PACK_BASE
	var camera := get_viewport().get_camera_3d()
	if camera:
		var base := rack.global_position + Vector3.UP * PACK_BASE
		var y := camera.unproject_position(base).y
		var pixels_per_metre := y - camera.unproject_position(base + Vector3.UP).y
		if pixels_per_metre > .001:
			var view_up := camera.global_basis.y
			var slope := Vector2(view_up.x, view_up.z).length() / maxf(.001, view_up.y)
			# The farthest occupied shelf corner stays within 1.4 m of the
			# character in plan, including both packet edges during a turn.
			var safe_y := get_viewport().get_visible_rect().size.y * TOP_MARGIN
			room = minf(room, (y - safe_y) / pixels_per_metre - 1.4 * slope)
	return maxi(1, floori(room * 100.0))

func _layout_pack(counts: Dictionary) -> void:
	var room := _headroom_bucket() / 100.0
	minimum_headroom = 0
	maximum_headroom = 2147483647
	for kind: String in Inventory.KINDS:
		if counts[kind] <= 0:
			presented[kind] = 0
			continue
		var units_per_layer := 2 if kind == "wood" else 1
		var layers := ceili(float(counts[kind]) / units_per_layer)
		var first_top := float(measured[kind].y) + (0.0 if kind in OUTER_ROW else INNER_RISE)
		var step := float(tier_height[kind])
		var visible_layers := clampi(1 + floori((room - first_top) / step), 1, mini(layers, MAX_LAYERS))
		presented[kind] = mini(counts[kind], visible_layers * units_per_layer)
		if visible_layers > 1:
			minimum_headroom = maxi(minimum_headroom, ceili((first_top + (visible_layers - 1) * step) * 100.0))
		if visible_layers < mini(layers, MAX_LAYERS):
			maximum_headroom = mini(maximum_headroom, ceili((first_top + visible_layers * step) * 100.0) - 1)

func _hand_slot(kind: String, logical_index: int) -> int:
	return clampi(logical_index, 0, maxi(0, int(presented.get(kind, 0)) - 1))

func _visible_units(kind: String, count: int, location: String) -> int:
	if location == STOCK:
		return mini(count, StockLayout.CENTERS[kind].size())
	return mini(count, int(presented.get(kind, 0)))

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
				tier_height[kind] = maxf(.02, bounds.size.y)
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

func _pack_yaw(kind: String, index: int) -> float:
	if kind == "wood":
		return PI if posmod(floori(index * .5), 2) == 1 else 0.0
	return _tier_yaw(kind, index)

func _heading(endpoint: String, kind: String, index: int) -> float:
	if endpoint == HAND:
		return actor.global_rotation.y + _pack_yaw(kind, _hand_slot(kind,index))
	return _tier_yaw(kind, StockLayout.slot(kind, index)) if endpoint == STOCK else 0.0

func _place(position_id: String, kind: String, n: int) -> Vector3:
	if position_id == HAND:
		return rack.to_global(_pack_position(kind, _hand_slot(kind,n)))
	if position_id == STOCK:
		return _floor_position(kind, maxi(0,n))
	return (receivers[position_id] as Node3D).global_position + Vector3.UP * .10

func sync(_animate := false) -> void:
	if not inventory or not rack:
		return
	var loaded := false
	var seated := {}
	var counts := {}
	for kind: String in Inventory.KINDS:
		counts[kind] = _available(kind, HAND) + _outstanding(kind, HAND, false)
		if station_material == kind: counts[kind] = maxi(0,counts[kind]-1)
		if counts[kind] > 0 and not measured.has(kind):
			var unit := _piece(kind)
			if unit:
				unit.visible = false
				rack.add_child(unit)
				pieces[HAND + "/" + kind] = [unit]
	_layout_pack(counts)
	planned_counts = counts
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
			if location == HAND and station_material == kind: n = maxi(0,n-1)
			n = _visible_units(kind, n, location)
			if location == HAND:
				seated[kind] = n
			while pool.size() < n:
				var unit := _piece(kind)
				if not unit:
					break
				var parent: Node3D = rack if location == HAND else storage_anchors[kind]
				unit.visible = false
				parent.add_child(unit)
				pool.append(unit)
			for i in pool.size():
				var unit: Node3D = pool[i]
				unit.visible = i < n
				if i < n:
					if location == HAND:
						loaded = true
						unit.position = _pack_position(kind, i)
						unit.rotation.y = _pack_yaw(kind, i)
					else:
						unit.global_position = _floor_position(kind, i)
						unit.global_rotation.y = _heading(STOCK, kind, i)
						unit.scale = Vector3.ONE * (storage_unit_scale * StockLayout.width(kind, i) / float(WIDTH[kind]))
			pieces[key] = pool
	if frame:
		frame.visible = loaded
		_fit_shelves(seated)

func pickup(token: String, kind: String, start: Vector3, start_yaw := 0.0) -> bool:
	if kind not in Inventory.KINDS or token.is_empty() or inventory.collected.has(token):
		return false
	var unit := _piece(kind)
	if not unit:
		return false
	if not inventory.collect(token, kind):
		unit.free()
		return false
	var idx := int(inventory.carried[kind]) - 1 - _outstanding(kind, HAND, true)
	_start(unit, kind, "", HAND, start, idx, PICKUP_TIME, float(FieldArt.WIDTHS[kind]) / float(WIDTH[kind]), 1.0, start_yaw)
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
	# Gameplay or an older save may credit the ledger before a visual sync.
	# Bring that stock into the rack before taking the departing physical packet.
	if source == HAND and int(planned_counts.get(kind, 0)) != _available(kind, HAND) + _outstanding(kind, HAND, false):
		sync(true)
	var source_index := _available(kind, source) - 1
	var start := _place(source, kind, source_index)
	var start_yaw := _heading(source, kind, source_index)
	if source == HAND:
		var pool: Array = pieces[HAND + "/" + kind]
		var carried_unit: Node3D = pool[_hand_slot(kind, source_index)]
		start = carried_unit.global_position
		start_yaw = carried_unit.global_rotation.y
	var start_scale := storage_unit_scale * StockLayout.width(kind, source_index) / float(WIDTH[kind]) if source == STOCK else 1.0
	var end_scale := storage_unit_scale * StockLayout.width(kind, dest_index) / float(WIDTH[kind]) if dest == STOCK else 1.0
	cooldown = INTERVAL if dest == STOCK else PAYMENT_INTERVAL
	_start(unit, kind, source, dest, start, dest_index, SEND_TIME, start_scale, end_scale, start_yaw)
	return true

func _start(unit: Node3D, kind: String, source: String, dest: String, start: Vector3, index: int, duration: float, scale_start: float, scale_end: float, start_yaw: float) -> void:
	add_child(unit)
	unit.global_position = start
	unit.global_rotation.y = start_yaw
	unit.scale = Vector3.ONE * scale_start
	flights.append({"mesh":unit, "kind":kind, "from":source, "to":dest, "start":start, "index":index, "t":0.0, "duration":duration, "scale_start":scale_start, "scale_end":scale_end, "start_yaw":start_yaw})
	sync(true)

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
	if frame and frame.visible:
		var limit := _headroom_bucket()
		if limit < minimum_headroom or limit > maximum_headroom:
			sync()
	cooldown = maxf(0.0, cooldown - delta)
	for flight in flights.duplicate():
		if not flights.has(flight):
			continue
		flight.t = minf(1.0, float(flight.t) + delta / float(flight.duration))
		var t := float(flight.t)
		var index: int = flight.index
		if flight.to == HAND:
			# A deposit can leave while this pickup is airborne. Reserve its
			# current logical slot after settled stock and earlier incoming units.
			index = _available(flight.kind, HAND)
			for earlier in flights:
				if earlier.mesh == flight.mesh:
					break
				if earlier.to == HAND and earlier.kind == flight.kind:
					index += 1
		var dest := _place(flight.to, flight.kind, index)
		var arc := .20 if flight.to == HAND else .40
		var unit: Node3D = flight.mesh
		unit.global_position = (flight.start as Vector3).lerp(dest, t) + Vector3.UP * (4.0*t*(1.0-t)*arc)
		unit.scale = Vector3.ONE * lerpf(flight.scale_start, flight.scale_end, t)
		unit.global_rotation.y = lerp_angle(flight.start_yaw, _heading(flight.to, flight.kind, index), t)
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
	sync(true)
	if accepted:
		inventory_changed.emit()
		unit_landed.emit(kind, dest)
		if dest not in [HAND, STOCK] and inventory.complete(dest):
			purchase_completed.emit(dest)

func available_to_station(kind: String) -> int:
	return _available(kind, HAND)

func available_on_shelf(kind: String) -> int:
	return _available(kind, STOCK)

func show_station_transfer(kind: String) -> Vector3:
	var origin := rack.global_position
	if not kind.is_empty():
		origin = _place(HAND,kind,maxi(0,_available(kind,HAND)-1))
	if kind != station_material:
		station_material = kind
		sync(true)
	return origin
