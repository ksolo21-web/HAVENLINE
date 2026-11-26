extends Node3D

signal inventory_changed
signal purchase_completed(plot_id: String)
signal unit_landed(kind: String, destination: String)

const Inventory = preload("res://field_inventory.gd")
const FieldArt = preload("res://field_art.gd")
const FRAME_PATH := "res://assets/field_pack/carry_frame.glb"
const RACK_SHADER := preload("res://assets/field_pack/portable_material.gdshader")
const WIDTH := {"wood":.42, "stone":.32, "meat":.23, "coal":.20, "slate":.205, "metal":.20}
# Largest units sit low. Each family occupies a continuous section of its own column.
const COLUMNS := [["wood", "meat", "slate"], ["stone", "metal", "coal"]]
const PACK_BASE := .655
const COLUMN_X := .214
const COLUMN_Z := -.70
const TIMBER_PAIR_X := .212
const TIMBER_PAIR_Z := -.76
const DIVIDER_HEIGHT := .031
const REFLOW_TIME := .14
const DIVIDER_SCENE = preload("res://assets/field_pack/expedition_shelf.glb")
const StockLayout = preload("res://field_stock_layout.gd")
const INTERVAL := 0.16
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
var dividers := {}
var section_origins := {}
var shifting := {}
var presented := {}
var planned_counts := {}
var minimum_headroom := Vector2i.ZERO
var maximum_headroom := Vector2i.ZERO
var paired_columns := false
var screen_slope := 0.0
var pieces := {}
var flights: Array[Dictionary] = []
var cooldown := 0.0
var measured := {}
var station_material := ""
var timber_pairs := false
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
		frame.scale = Vector3(.76, .78, .78)
		# A shallow cross rail under each material transition keeps the families distinct.
		# The divider uses the same authored timber as the base carrying frame.
		var donor := DIVIDER_SCENE.instantiate()
		var base_shelf := donor.get_node("MiddleSupport") as MeshInstance3D
		var donor_mesh := base_shelf.mesh
		base_shelf.owner = null
		donor.remove_child(base_shelf)
		frame.add_child(base_shelf)
		donor.free()
		var source_box := donor_mesh.get_aabb()
		for column: Array in COLUMNS:
			for kind: String in column.slice(1):
				var divider := MeshInstance3D.new()
				divider.name = kind.capitalize() + "Divider"
				divider.mesh = donor_mesh
				divider.scale = Vector3(.32, DIVIDER_HEIGHT, .24) / source_box.size
				frame.add_sibling(divider)
				dividers[kind] = divider
		var palette := ShaderMaterial.new()
		palette.shader = RACK_SHADER
		palette.set_shader_parameter("surface_kind", 4)
		if frame is MeshInstance3D:
			frame.material_override = palette
		for part in frame.find_children("*", "MeshInstance3D", true, false):
			part.material_override = palette
		for divider: MeshInstance3D in dividers.values():
			divider.material_override = palette
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
	var base: Vector3 = section_origins.get(kind, Vector3(0, PACK_BASE, COLUMN_Z))
	if kind == "wood" and timber_pairs:
		base.x = -TIMBER_PAIR_X if index % 2 == 0 else TIMBER_PAIR_X
		base.z = TIMBER_PAIR_Z
		index = floori(index * .5)
	return base + Vector3.UP * (index * float(tier_height[kind]))

func _headroom_bucket(x: float) -> int:
	var height := PACK_TOP - PACK_BASE
	var camera := get_viewport().get_camera_3d()
	if camera:
		# Measure at the actual column, including simultaneous turning and pinching.
		var base := rack.to_global(Vector3(x, PACK_BASE, TIMBER_PAIR_Z if timber_pairs else COLUMN_Z))
		var screen_y := camera.unproject_position(base).y
		var pixels_per_metre := screen_y - camera.unproject_position(base + Vector3.UP).y
		if pixels_per_metre > .001:
			var margin := get_viewport().get_visible_rect().size.y * TOP_MARGIN
			height = minf(height, (screen_y - margin) / pixels_per_metre)
	return maxi(1, floori(height * 100.0))

func _view_limits() -> Vector2i:
	var x := COLUMN_X if paired_columns else 0.0
	return Vector2i(_headroom_bucket(-x), _headroom_bucket(x))

func _required_height(column: Array, counts: Dictionary, cap: int) -> float:
	var height := 0.0
	var highest_corner := 0.0
	for kind: String in column:
		var n := mini(counts[kind], cap)
		if n <= 0:
			continue
		if height > 0.0:
			height += DIVIDER_HEIGHT
		var unit: Vector3 = measured[kind]
		height += (n - 1) * float(tier_height[kind]) + unit.y
		var radius := Vector2(unit.x, unit.z).length() * .5
		if kind == "wood" and timber_pairs:
			radius += TIMBER_PAIR_X
		highest_corner = maxf(highest_corner, height + radius * screen_slope)
	return highest_corner

func _layout_pack(counts: Dictionary, animate: bool) -> void:
	timber_pairs = counts.wood >= 2 and Inventory.KINDS.all(func(k): return k == "wood" or counts[k] == 0)
	var layers := counts.duplicate()
	if timber_pairs:
		layers.wood = ceili(counts.wood * .5)
	var occupied := []
	for column: Array in COLUMNS:
		occupied.append(column.any(func(k): return counts[k] > 0))
	paired_columns = occupied[0] and occupied[1]
	var ceiling_buckets := _view_limits()
	var camera := get_viewport().get_camera_3d()
	if camera:
		var view_up := camera.get_camera_transform().basis.y
		screen_slope = Vector2(view_up.x, view_up.z).length() / maxf(.001, view_up.y)
	for c in COLUMNS.size():
		var column: Array = COLUMNS[c]
		var headroom := ceiling_buckets[c] / 100.0
		var left := 1
		# A full-height material stack sets a finite bound, even with a million in the ledger.
		var right := 1
		for kind: String in column:
			right = maxi(right, mini(layers[kind], ceili(headroom / float(tier_height[kind])) + 1))
		while left < right:
			var middle := ceili((left + right) * .5)
			if _required_height(column, layers, middle) <= headroom:
				left = middle
			else:
				right = middle - 1
		minimum_headroom[c] = ceili(_required_height(column, layers, left) * 100.0) if left > 1 else 0
		maximum_headroom[c] = 2147483647
		if column.any(func(k): return layers[k] > left):
			maximum_headroom[c] = ceili(_required_height(column, layers, left + 1) * 100.0) - 1
		var height := PACK_BASE
		var x := (-COLUMN_X if c == 0 else COLUMN_X) if paired_columns else 0.0
		for kind: String in column:
			var units := mini(left, layers[kind])
			presented[kind] = mini(left * 2, counts[kind]) if kind == "wood" and timber_pairs else units
			var divider: MeshInstance3D = dividers.get(kind)
			if divider:
				var occupied_section := units > 0 and height > PACK_BASE
				var previously_visible := divider.visible
				divider.visible = occupied_section and _available(kind, HAND) > 0
				if occupied_section:
					# Align the authored shelf's top plane to the packet underside.
					var bounds := divider.mesh.get_aabb()
					var offset := Vector3(bounds.get_center().x, bounds.end.y, bounds.get_center().z) * divider.scale
					height += DIVIDER_HEIGHT
					_move_on_rack(divider, Vector3(x, height, COLUMN_Z) - offset, 0.0, animate and previously_visible and divider.visible)
			section_origins[kind] = Vector3(x, height, COLUMN_Z)
			if units > 0:
				height += float(tier_height[kind]) * (units - 1) + measured[kind].y

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

func _pack_yaw(kind: String, index: int) -> float:
	if kind == "wood" and timber_pairs:
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

func _move_on_rack(node: Node3D, point: Vector3, yaw: float, animate: bool) -> void:
	# Adjacent pickups reserve their final places immediately. Only the existing
	# packets and dividers slide when a section rises, empties or changes columns.
	if animate and shifting.has(node) and shifting[node].target.is_equal_approx(point) and is_equal_approx(shifting[node].yaw, yaw):
		return
	if animate and (not node.position.is_equal_approx(point) or not is_zero_approx(angle_difference(node.rotation.y, yaw))):
		shifting[node] = {"start":node.position, "start_yaw":node.rotation.y, "target":point, "yaw":yaw, "t":0.0}
	else:
		shifting.erase(node)
		node.position = point
		node.rotation.y = yaw

func _advance_reflow(delta: float) -> void:
	for node: Node3D in shifting.keys():
		var move: Dictionary = shifting[node]
		move.t = minf(1.0, float(move.t) + delta / REFLOW_TIME)
		var weight := smoothstep(0.0, 1.0, float(move.t))
		node.position = (move.start as Vector3).lerp(move.target, weight)
		node.rotation.y = lerp_angle(move.start_yaw, move.yaw, weight)
		if move.t >= 1.0:
			shifting.erase(node)

func sync(animate := false) -> void:
	if not inventory or not rack:
		return
	var loaded := false
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
	_layout_pack(counts, animate)
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
				var previously_visible := unit.visible
				unit.visible = i < n
				if i < n:
					if location == HAND:
						loaded = true
						_move_on_rack(unit, _pack_position(kind, i), _pack_yaw(kind, i), animate and previously_visible)
					else:
						unit.global_position = _floor_position(kind, i)
						unit.global_rotation.y = _heading(STOCK, kind, i)
						unit.scale = Vector3.ONE * (storage_unit_scale * StockLayout.width(kind, i) / float(WIDTH[kind]))
			pieces[key] = pool
	if frame:
		frame.visible = loaded

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
	cooldown = INTERVAL
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
	shifting.clear()
	cooldown = 0
	sync()

func _physics_process(delta: float) -> void:
	advance(delta)

func advance(delta: float) -> void:
	# The rack follows the actor without touching its nodes. Only a projection
	# that changes a lane's visible count needs to reposition/show its pool.
	if frame and frame.visible:
		var limits := _view_limits()
		if limits.x < minimum_headroom.x or limits.y < minimum_headroom.y or limits.x > maximum_headroom.x or limits.y > maximum_headroom.y:
			sync()
	_advance_reflow(delta)
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
