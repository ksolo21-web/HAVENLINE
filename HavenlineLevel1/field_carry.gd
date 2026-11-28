extends Node3D

signal inventory_changed
signal purchase_completed(plot_id: String)
signal unit_landed(kind: String, destination: String)

const Inventory = preload("res://field_inventory.gd")
const FieldArt = preload("res://field_art.gd")
const FRAME_PATH := "res://assets/field_pack/carry_frame.glb"
const WORN_RESOURCE := preload("res://assets/field_pack/worn_resource.gdshader")
const RACK_SHADER := preload("res://assets/field_pack/portable_material.gdshader")
const WIDTH := {"wood":.49, "stone":.36, "meat":.29, "coal":.255, "slate":.25, "metal":.255}
# Permanent bays keep unlike resources off one another even when a neighboring
# bay empties. The wide timber bay has two side-by-side, bark-outward packets
# per course; the other five bays each hold one vertical stack.
const BAY_X := {"wood":0.0, "slate":-.642, "coal":-.48, "metal":-.181, "meat":.135, "stone":.521}
const OUTER_ROW := ["coal", "metal", "meat", "stone"]
const INNER_Z := -.585
const OUTER_Z := -.938
const PACK_BASE := .91
const INNER_RISE := .10
const TIMBER_PAIR_X := .249
const MAX_LAYERS := 24
const BEARER := preload("res://assets/field_pack/pack_bearer.tres")
const SHELF_SCENE := preload("res://assets/field_pack/expedition_shelf.glb")
const StockLayout = preload("res://field_stock_layout.gd")
const INTERVAL := 0.16
const PAYMENT_INTERVAL := 4.0 / 60.0
const PICKUP_TIME := 0.29
const SEND_TIME := 0.28
# A full player rack ends at the keeper's crown. Further bundles keep their
# exact ledger quantities and use the last modeled packet in their own bay.
const PACK_TOP := 1.86
const TOP_MARGIN := .20
const HAND := "carry"
const STOCK := "storage"

var visual_top := PACK_TOP
var fit_to_viewport := true
var objective_card: Control
var top_status: Control
var inventory: Inventory
var actor: Node3D
var factory: Callable
var storage_unit_scale := 1.0
var storage_layout: Callable
var storage_anchors := {}
var receivers := {}
var rack: Node3D
var frame: Node3D
var finished_goods = preload("res://field_goods_pack.gd").new()
var worn_materials := {}
var braces: Array[MeshInstance3D] = []
var shelves: Array[MeshInstance3D] = []
var presented := {}
var planned_counts := {}
var display_clearance := {}
var pieces := {}
var flights: Array[Dictionary] = []
var cooldown := 0.0
var measured := {}
# A visit plans logical receipts separately from its bounded visual flights.
# The reference first lands at 0.234–0.301 s; its last landing is at 0.835–0.903 s.
const RELEASE_WINDOW := .59
const PLOT_RELEASE := .36
const HOPPER_FLIGHT := .15
const HOPPER_SPACING := 2.0 / 60.0
const MAX_BATCH_PIECES := 64
const LARGE_LOAD_PIECES := 12
const BULK_SHELF_WAVE := 3
const PICKUP_PIECES_PER_KIND := 3
# Raw stock withdrawn by hand remains packed until the runner leaves the house.
var storage_protected := {}
var clock := 0.0
var visit_target := ""
var visit_started := 0.0
var scheduled: Array[Dictionary] = []
var next_piece := 0
var release_group := 1
var worksite_demand: Callable
var worksite_land: Callable
var _landing_at_worksite := {}
var worksite_goal: Callable
var travel_clear: Callable
var tier_height := {"wood":.13, "stone":.11, "meat":.145, "coal":.15, "slate":.12, "metal":.16}

func setup(ledger: Inventory, character: Node3D, item_factory: Callable, objective: Control = null, status: Control = null) -> void:
	objective_card = objective
	top_status = status
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
			for side in 2:
				var brace := MeshInstance3D.new()
				brace.name = "ShelfBrace%d_%d" % [row,side]
				brace.mesh = BEARER
				brace.material_override = palette
				rack.add_child(brace)
				braces.append(brace)
		donor.free()
		rack.add_child(finished_goods)
		finished_goods.configure(inventory,frame,shelves[0])
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
		for side in 2:
			braces[row*2+side].visible = board.visible
		if not board.visible:
			continue
		var bounds := board.mesh.get_aabb()
		board.scale = Vector3(right - left + .016, .035, depth + .026) / bounds.size
		var top := Vector3((left + right) * .5, PACK_BASE + (INNER_RISE if row == 0 else 0.), INNER_Z if row == 0 else OUTER_Z)
		board.position = top - Vector3(bounds.get_center().x, bounds.end.y, bounds.get_center().z) * board.scale
		# Attach both sides to the real transverse belt timber and to the
		# intersections of the longitudinal runners and the shelf crosspiece.
		# The endpoints are embedded within those timbers, never beyond the load.
		var spread := minf(.19,(right-left)*.3)
		var center := clampf(top.x,-.28+spread,.28-spread)
		for side in 2:
			var sign_x := -1.0 if side==0 else 1.0
			var heel := Vector3(center+sign_x*spread,.619,-.505 if row==0 else -.527)
			var seat := board.transform * Vector3(sign_x*.28,.158,-.40 if row==0 else -.82)
			var axis := (seat-heel).normalized()
			var width_axis := axis.cross(Vector3.UP).normalized()
			var normal_axis := width_axis.cross(axis).normalized()
			var size := BEARER.get_aabb().size
			var basis := Basis(axis*heel.distance_to(seat)/size.x, normal_axis*.042/size.y, width_axis*.052/size.z)
			braces[row*2+side].transform = Transform3D(basis,(heel+seat)*.5)


func _headroom_bucket(kind: String) -> int:
	var room := visual_top - PACK_BASE
	if not fit_to_viewport:
		return maxi(1, floori(room * 100.0))
	var camera := get_viewport().get_camera_3d()
	if camera:
		var center := _pack_position(kind,0)
		center.y = PACK_BASE
		var half_size: Vector3 = measured[kind]*.5
		if kind == "wood":
			center.x = 0.
			half_size.x += TIMBER_PAIR_X
		else:
			# Packet headings alternate between ±2 degrees around the bay.
			half_size += Vector3(half_size.z,0,half_size.x)*sin(deg_to_rad(2.))
		var base := rack.to_global(center)
		var projected_base := camera.unproject_position(base)
		var y := projected_base.y
		var pixels_per_metre := y - camera.unproject_position(base + Vector3.UP).y
		if pixels_per_metre > .001:
			var view_up := camera.global_basis.y
			var rack_up := rack.global_basis.transposed()*view_up
			# Each row projects differently at the fixed camera. Use the actual
			# packet footprint so a distant bay cannot hide a neighboring stack.
			var edge := rack_up.abs().dot(Vector3(half_size.x,0,half_size.z))
			var safe_y := get_viewport().get_visible_rect().size.y * TOP_MARGIN
			if objective_card and top_status and objective_card.is_visible_in_tree():
				var ticket := objective_card.get_global_transform_with_canvas() * Rect2(Vector2.ZERO, objective_card.size)
				var right := rack.global_basis.transposed() * camera.global_basis.x
				var pixels_per_horizontal_metre := pixels_per_metre / view_up.y
				var center_x := projected_base.x
				var span_x := right.abs().dot(Vector3(half_size.x,0,half_size.z))*pixels_per_horizontal_metre
				# Outside the objective, only the upper resource rail needs clearance.
				if center_x - span_x > ticket.end.x or center_x + span_x < ticket.position.x:
					var status_rect := top_status.get_global_transform_with_canvas() * Rect2(Vector2.ZERO, top_status.size)
					safe_y = minf(safe_y, status_rect.end.y)
			room = minf(room,(y-safe_y)/pixels_per_metre-edge/maxf(.001,view_up.y))
	return maxi(1, floori(room * 100.0))

func _layout_pack(counts: Dictionary) -> void:
	display_clearance.clear()
	for kind: String in Inventory.KINDS:
		if counts[kind] <= 0:
			presented[kind] = 0
			continue
		var room := _headroom_bucket(kind) / 100.0
		var units_per_layer := 2 if kind == "wood" else 1
		var layers := ceili(float(counts[kind]) / units_per_layer)
		var first_top := float(measured[kind].y) + (0.0 if kind in OUTER_ROW else INNER_RISE)
		var step := float(tier_height[kind])
		var visible_layers := clampi(1 + floori((room - first_top) / step), 1, mini(layers, MAX_LAYERS))
		presented[kind] = mini(counts[kind], visible_layers * units_per_layer)
		var minimum := ceili((first_top + (visible_layers - 1) * step) * 100.0) if visible_layers > 1 else 0
		var maximum := ceili((first_top + visible_layers * step) * 100.0) - 1 if visible_layers < mini(layers, MAX_LAYERS) else 2147483647
		display_clearance[kind] = Vector2i(minimum,maximum)

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
			n += int(flight.units)
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
	if position_id.begins_with("work:"): return worksite_goal.call(position_id.trim_prefix("work:"))
	return (receivers[position_id] as Node3D).global_position + Vector3.UP * .10

func sync(_animate := false) -> void:
	if not inventory or not rack:
		return
	var loaded := false
	var seated := {}
	var counts := {}
	for kind: String in Inventory.KINDS:
		counts[kind] = _available(kind, HAND) + _outstanding(kind, HAND, false)

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
		finished_goods.raw_frame_loaded = loaded
		frame.visible = loaded or finished_goods.visible
		_fit_shelves(seated)

func _clear_segment(start: Vector3, end: Vector3, kind: String) -> bool:
	return not travel_clear.is_valid() or travel_clear.call(start, end, float(WIDTH[kind]) * .38)

func pickup(token: String, kind: String, start: Vector3, start_yaw := 0.0) -> bool:
	var accepted := pickup_nearby([{"token":token,"kind":kind,"at":start,"yaw":start_yaw}])
	if accepted.is_empty(): return false
	inventory_changed.emit()
	return true

func pickup_nearby(candidates: Array) -> Array[String]:
	# Commit every distinct token. A dense heap shares representative flights
	# per material so neither atomics nor moving meshes scale with a crowd.
	var families := {}
	for item: Dictionary in candidates:
		var kind: String = item.kind
		if kind not in Inventory.KINDS or item.token.is_empty() or inventory.collected.has(item.token):
			continue
		var destination := _place(HAND,kind,int(inventory.carried[kind]))
		if not _clear_segment(item.at,destination,kind): continue
		if not families.has(kind): families[kind] = []
		families[kind].append(item)
	var accepted: Array[String] = []
	for kind: String in families:
		var items: Array = families[kind]
		var group_size := ceili(float(items.size())/PICKUP_PIECES_PER_KIND)
		for offset in range(0,items.size(),group_size):
			var visual := _piece(kind)
			if not visual: continue
			var count := 0
			var first: Dictionary = items[offset]
			for i in range(offset,mini(offset+group_size,items.size())):
				var token: String = items[i].token
				if inventory.collect(token,kind):
					accepted.append(token)
					count += 1
			if count == 0:
				visual.free()
				continue
			var idx := int(inventory.carried[kind])-count-_outstanding(kind,HAND,true)
			_start(visual,kind,"",HAND,first.at,idx,PICKUP_TIME,float(FieldArt.GROUND_WIDTHS[kind])/float(WIDTH[kind]),1.,first.yaw,count,false)
	if not accepted.is_empty(): sync(true)
	return accepted

func deposit_storage(kind: String) -> bool:
	if cooldown > 0 or not inventory.storage_open(kind) or not storage_anchors.has(kind) or _available(kind, HAND) <= int(storage_protected.get(kind,0)):
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

func _send(kind: String, source: String, dest: String, dest_index: int, amount := 1) -> bool:
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
	if not _clear_segment(start, _place(dest,kind,dest_index), kind):
		unit.free()
		return false
	var start_scale := storage_unit_scale * StockLayout.width(kind, source_index) / float(WIDTH[kind]) if source == STOCK else 1.0
	var end_scale := storage_unit_scale * StockLayout.width(kind, dest_index) / float(WIDTH[kind]) if dest == STOCK else 1.0
	cooldown = INTERVAL if dest == STOCK else PAYMENT_INTERVAL
	var duration := HOPPER_FLIGHT if dest in ["work:wood", "work:stone", "work:meat"] else SEND_TIME
	_start(unit, kind, source, dest, start, dest_index, duration, start_scale, end_scale, start_yaw,amount)
	return true

func _start(unit: Node3D, kind: String, source: String, dest: String, start: Vector3, index: int, duration: float, scale_start: float, scale_end: float, start_yaw: float, amount := 1, refresh := true) -> void:
	add_child(unit)
	unit.global_position = start
	unit.global_rotation.y = start_yaw
	unit.scale = Vector3.ONE * scale_start
	flights.append({"units":amount,"mesh":unit, "kind":kind, "from":source, "to":dest, "start":start, "index":index, "t":0.0, "duration":duration, "scale_start":scale_start, "scale_end":scale_end, "start_yaw":start_yaw})
	if refresh: sync(true)

func cancel_transfers() -> void:
	stop_visit(visit_target)
	for flight in flights:
		(flight.mesh as Node3D).queue_free()
	flights.clear()
	cooldown = 0
	sync()

func _physics_process(delta: float) -> void:
	advance(delta)

func advance(delta: float) -> void:
	clock += delta
	# The rack follows the actor without touching its nodes. Only a projection
	# that changes a lane's visible count needs to reposition/show its pool.
	if frame and frame.visible and fit_to_viewport:
		for kind: String in display_clearance:
			var room := _headroom_bucket(kind)
			var limits: Vector2i = display_clearance[kind]
			if room < limits.x or room > limits.y:
				sync()
				break
	cooldown = maxf(0.0, cooldown - delta)
	var rack_changed := false
	var shelf_landings := PackedStringArray()
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
					index += int(earlier.units)
		var dest := _place(flight.to, flight.kind, index)
		var arc := .20 if flight.to == HAND else .40
		var unit: Node3D = flight.mesh
		var next := (flight.start as Vector3).lerp(dest, t) + Vector3.UP * (4.0*t*(1.0-t)*arc)
		if not _clear_segment(unit.global_position,next,flight.kind):
			# Outgoing receipts remain at their source until landing. Pickups
			# already belong to the pack and settle into its existing lane.
			flights.erase(flight)
			unit.queue_free()
			sync(true)
			continue
		unit.global_position = next
		unit.scale = Vector3.ONE * lerpf(flight.scale_start, flight.scale_end, t)
		unit.global_rotation.y = lerp_angle(flight.start_yaw, _heading(flight.to, flight.kind, index), t)
		if t >= 1.0:
			if flight.to == HAND or flight.to == STOCK:
				flights.erase(flight)
				unit.queue_free()
				rack_changed = true
				if flight.to == STOCK:
					if not inventory.deposit(flight.kind,flight.units): continue
					shelf_landings.append(flight.kind)
				else:
					unit_landed.emit(flight.kind,HAND)
			else:
				_land(flight)
	if rack_changed: sync(true)
	if not shelf_landings.is_empty():
		inventory_changed.emit()
		for kind in shelf_landings: unit_landed.emit(kind,STOCK)

func _land(flight: Dictionary) -> void:
	var kind: String = flight.kind
	var dest: String = flight.to
	flights.erase(flight)
	(flight.mesh as Node3D).queue_free()
	if dest.begins_with("work:"):
		sync(true)
		_landing_at_worksite = flight
		worksite_land.call(dest.trim_prefix("work:"),kind,int(flight.units))
		_landing_at_worksite = {}
		return
	var accepted := inventory.payment(dest,kind,flight.from == STOCK,flight.units)
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


func stop_visit(dest: String) -> void:
	if dest != visit_target: return
	scheduled.clear()
	next_piece = 0
	visit_target = ""

func cancel_worksite(site: String) -> void:
	var dest := "work:"+site
	stop_visit(dest)
	var changed := false
	for flight in flights.duplicate():
		if flight.to != dest: continue
		flights.erase(flight)
		flight.mesh.queue_free()
		changed = true
	if changed: sync(true)

func take_worksite_receipt(site: String, kind: String, amount: int) -> bool:
	if _landing_at_worksite.is_empty() or _landing_at_worksite.to != "work:"+site or _landing_at_worksite.kind != kind or _landing_at_worksite.units != amount: return false
	_landing_at_worksite = {}
	return true

func incoming(site: String, kind: String) -> int:
	return _outstanding(kind,"work:"+site,false)

func visit(dest: String) -> void:
	if visit_target != dest:
		stop_visit(visit_target)
		visit_target = dest
	if next_piece >= scheduled.size():
		_plan_visit(dest)
	var window := RELEASE_WINDOW if dest == STOCK else PLOT_RELEASE
	var last_wave := ceili(float(scheduled.size()) / release_group) - 1
	var interval := window / maxi(1,last_wave)
	if release_group == 1: interval = minf(.10,interval)
	if dest in ["work:wood", "work:stone", "work:meat"]: interval = HOPPER_SPACING
	while next_piece < scheduled.size():
		var wave := floori(float(next_piece)/release_group)
		if clock-visit_started+.00001 < wave*interval: break
		var row := scheduled[next_piece]
		next_piece += 1
		var qty := mini(int(row.units), _available(row.kind,row.source))
		if dest == STOCK:
			qty = mini(qty,_available(row.kind,HAND)-int(storage_protected.get(row.kind,0)))
		elif dest.begins_with("work:"):
			qty = mini(qty,int(worksite_demand.call(dest.trim_prefix("work:"),row.kind)) - _outstanding(row.kind,dest,false))
		elif dest != STOCK:
			qty = mini(qty,int(inventory.remaining(dest).get(row.kind,0))-_outstanding(row.kind,dest,false)) if inventory.offer_open(dest) else 0
		if qty <= 0: continue
		var index := int(inventory.stored[row.kind])+_outstanding(row.kind,STOCK,false) if dest == STOCK else 0
		_send(row.kind,row.source,dest,index,qty)

func _plan_visit(dest: String) -> void:
	scheduled.clear()
	next_piece = 0
	release_group = 1
	visit_started = clock
	var rows: Array[Dictionary] = []
	var total := 0
	var work := dest.begins_with("work:")
	if not work and dest != STOCK and not inventory.offer_open(dest): return
	var needs := inventory.remaining(dest) if not work and dest!=STOCK else {}
	for kind: String in Inventory.KINDS:
		var available := _available(kind,HAND)
		var due := available
		if work:
			due = maxi(0,int(worksite_demand.call(dest.trim_prefix("work:"),kind))-_outstanding(kind,dest,false))
		elif dest == STOCK:
			if not storage_anchors.has(kind) or not inventory.storage_open(kind): continue
			due = maxi(0,available-int(storage_protected.get(kind,0)))
		else:
			due = maxi(0,int(needs.get(kind,0))-_outstanding(kind,dest,false))
		var from_hand := mini(available,due)
		if from_hand > 0: rows.append({"kind":kind,"source":HAND,"units":from_hand})
		total += from_hand
		if work or dest == STOCK or not storage_anchors.has(kind) or not inventory.storage_open(kind): continue
		var from_shelf := mini(due-from_hand,_available(kind,STOCK))
		if from_shelf > 0: rows.append({"kind":kind,"source":STOCK,"units":from_shelf})
		total += from_shelf
	if total == 0: return
	# The normal 52-piece reference stress load still shows one real mesh
	# per bundle. Large stockpiles group into a bounded number of visible packets.
	# Reserve a remainder slot for each material/source pair in those loads.
	var group := 1
	if total > MAX_BATCH_PIECES:
		var budget := LARGE_LOAD_PIECES if dest == STOCK else MAX_BATCH_PIECES
		group = ceili(float(total) / maxi(1,budget - rows.size() + 1))
		# Packets that land together share a durable shelf commit. Preserve
		# each landing and the complete reference release window on bulk visits.
		if dest == STOCK: release_group = BULK_SHELF_WAVE
	# Round-robin families so meat, stone and timber start on the same visit.
	var remaining := total
	while remaining > 0:
		for row in rows:
			var amount := mini(row.units,group)
			if amount == 0: continue
			scheduled.append({"kind":row.kind,"source":row.source,"units":amount})
			row.units -= amount
			remaining -= amount
