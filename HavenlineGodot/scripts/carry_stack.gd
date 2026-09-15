class_name HavenlineCarryStack
extends Node3D

## T08 presentation-only physical inventory. Logical counts remain owned by the
## simulation; this node derives a bounded authored-mesh layout from those counts.

const KINDS := ["wood", "stone", "metal", "fuel"]
const VISIBLE_BUDGET := 48
const MAX_SAFE_COUNT := 9223372036854775806
const AUTHORITY_ID := "T08-physical-inventory-v1"
const ASSETS := {
	"wood": "res://assets/stations_v2/wood_stack.glb",
	"stone": "res://assets/stations_v2/stone_stack.glb",
	"metal": "res://assets/stations_v2/metal_stack.glb",
	"fuel": "res://assets/stations_v2/fuel_canister.glb",
}
const PIECE_SCALE := {"wood": 0.22, "stone": 0.22, "metal": 0.22, "fuel": 0.24}
const CARRY_BASE_HEIGHT := 0.28
const CARRY_COLUMN_SPACING := 0.18
const CARRY_COLUMNS := 3
const CARRY_TIER_HEIGHT := 0.2

var loader: Callable # Compatibility fallback only; authored T05 assets are preferred.
var grounded := false
var slots: Array[Node3D] = []
var signature: Array = []
var pools: Dictionary = {"wood": [], "stone": [], "metal": [], "fuel": []}
var last_layout: Array[Dictionary] = []
var rebuild_count := 0

static func contract() -> Dictionary:
	return {
		"authority_id": AUTHORITY_ID,
		"kinds": KINDS.duplicate(),
		"authored_assets": ASSETS.duplicate(),
		"visible_budget": VISIBLE_BUDGET,
		"unlimited_logical_inventory": true,
		"mutates_inventory": false,
		"adds_save_fields": false,
		"manual_inventory_controls": 0,
		"future_resource_fallback": "fail_visible_not_generic",
	}

static func valid_inventory(inventory: Dictionary) -> bool:
	for key in inventory:
		if not (key is String or key is StringName) or String(key) not in KINDS:
			return false
	for kind in KINDS:
		var value: Variant = inventory.get(kind, 0)
		if not (value is int or value is float):
			return false
		var number := float(value)
		if not is_finite(number) or number < 0.0 or number > float(MAX_SAFE_COUNT):
			return false
		if fmod(number, 1.0) != 0.0:
			return false
	return true

static func normalized_counts(inventory: Dictionary) -> Dictionary:
	var result := {}
	for kind in KINDS:
		result[kind] = int(inventory.get(kind, 0))
	return result

static func allocate_visible(counts: Dictionary, budget := VISIBLE_BUDGET) -> Dictionary:
	var result := {"wood": 0, "stone": 0, "metal": 0, "fuel": 0}
	var positive: Array[String] = []
	var total := 0
	for kind in KINDS:
		var count := int(counts[kind])
		total += count
		if count > 0:
			positive.append(kind)
	if total <= budget:
		return counts.duplicate()
	for kind in positive:
		result[kind] = 1
	var remaining := maxi(0, budget - positive.size())
	for slot in remaining:
		var best_kind := positive[0]
		var best_need := -INF
		for kind in positive:
			var ideal := float(counts[kind]) * float(budget) / float(total)
			var need := ideal - float(result[kind])
			if need > best_need:
				best_need = need
				best_kind = kind
		result[best_kind] += 1
	return result

static func layout_for(inventory: Dictionary, is_grounded := false, budget := VISIBLE_BUDGET) -> Array[Dictionary]:
	if not valid_inventory(inventory) or budget <= 0:
		return []
	var counts := normalized_counts(inventory)
	var visible := allocate_visible(counts, budget)
	var layout: Array[Dictionary] = []
	var nonzero: Array[String] = []
	for kind in KINDS:
		if int(counts[kind]) > 0:
			nonzero.append(kind)
	for kind_index in nonzero.size():
		var kind := nonzero[kind_index]
		var shown := int(visible[kind])
		var count := int(counts[kind])
		for index in shown:
			var represented := count / shown + (1 if index < count % shown else 0)
			var row := index / 4
			var column := index % 4
			var position: Vector3
			if is_grounded:
				position = Vector3((kind_index - (nonzero.size() - 1) * 0.5) * 0.82 + (column - 1.5) * 0.13,
					row * 0.12, (column % 2) * 0.12)
			else:
				# Build one compact carrier-bound tower across resource kinds. Global
				# slot tiers remain visibly vertical even for a small mixed load, while
				# the authored pieces and exact represented counts remain unchanged.
				var carrier_slot := layout.size()
				var carrier_column := carrier_slot % CARRY_COLUMNS
				var carrier_tier := carrier_slot / CARRY_COLUMNS
				position = Vector3((carrier_column - (CARRY_COLUMNS - 1) * 0.5) * CARRY_COLUMN_SPACING,
					CARRY_BASE_HEIGHT + carrier_tier * CARRY_TIER_HEIGHT, (carrier_column % 2) * 0.07)
			layout.append({
				"kind": kind,
				"logical_count": count,
				"represented_count": represented,
				"asset": ASSETS[kind],
				"position": position,
				"rotation_y": float((index * 37 + kind_index * 19) % 360) * PI / 180.0,
				"scale": float(PIECE_SCALE[kind]) * (1.55 if is_grounded else 1.0),
			})
	return layout

func configure_grounded(value: bool) -> void:
	if grounded == value:
		return
	grounded = value
	signature = []

func _instantiate_piece(kind: String) -> Node3D:
	var path := String(ASSETS.get(kind, ""))
	if not path.is_empty() and ResourceLoader.exists(path):
		var packed: Variant = load(path)
		if packed is PackedScene:
			var node: Variant = packed.instantiate()
			if node is Node3D:
				node.set_meta("t08_authored_asset", path)
				add_child(node)
				return node
	if loader.is_valid():
		var fallback: Variant = loader.call(kind, self)
		if fallback is Node3D:
			fallback.set_meta("t08_authored_asset", "compatibility_loader")
			return fallback
	return null

func _piece_for(index: int, kind: String) -> Node3D:
	var piece: Node3D = slots[index] if index < slots.size() else null
	if is_instance_valid(piece) and String(piece.get_meta("resource_kind", "")) != kind:
		piece.visible = false
		pools[String(piece.get_meta("resource_kind"))].append(piece)
		piece = null
	if not is_instance_valid(piece):
		piece = pools[kind].pop_back() if not pools[kind].is_empty() else _instantiate_piece(kind)
		if piece == null:
			return null
		piece.set_meta("resource_kind", kind)
		if index < slots.size():
			slots[index] = piece
		else:
			slots.append(piece)
	return piece

func update_inventory(inventory: Dictionary) -> bool:
	if not valid_inventory(inventory):
		return false
	var counts := normalized_counts(inventory)
	var next_signature: Array = KINDS.map(func(kind): return counts[kind])
	next_signature.append(grounded)
	if next_signature == signature:
		return true
	signature = next_signature
	last_layout = layout_for(counts, grounded)
	rebuild_count += 1
	for index in maxi(slots.size(), last_layout.size()):
		if index >= last_layout.size():
			if index < slots.size() and is_instance_valid(slots[index]):
				slots[index].visible = false
			continue
		var row: Dictionary = last_layout[index]
		var piece := _piece_for(index, String(row.kind))
		if piece == null:
			continue
		piece.visible = true
		piece.position = row.position
		piece.rotation = Vector3(0.0, float(row.rotation_y), 0.0)
		piece.scale = Vector3.ONE * float(row.scale)
		piece.set_meta("t08_represented_count", int(row.represented_count))
		piece.set_meta("t08_logical_count", int(row.logical_count))
	return true

func descriptor() -> Dictionary:
	var logical := {}
	for index in KINDS.size():
		logical[KINDS[index]] = int(signature[index]) if signature.size() > index else 0
	var represented_total := 0
	for row in last_layout:
		represented_total += int(row.represented_count)
	var logical_total := 0
	for value in logical.values():
		logical_total += int(value)
	return {
		"authority_id": AUTHORITY_ID,
		"logical_counts": logical,
		"logical_total": logical_total,
		"represented_total": represented_total,
		"visible_instances": last_layout.size(),
		"visible_budget": VISIBLE_BUDGET,
		"grounded": grounded,
		"rebuild_count": rebuild_count,
		"layout": last_layout.duplicate(true),
		"mutates_inventory": false,
	}
