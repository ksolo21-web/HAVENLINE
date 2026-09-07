class_name HavenlineCarryStack
extends Node3D

const KINDS = ["wood", "stone", "metal", "fuel"]
const VISIBLE_BUDGET := 32
var loader: Callable
var slots: Array[Node3D] = []
var signature: Array = []
var pools: Dictionary = {"wood":[],"stone":[],"metal":[],"fuel":[]}

func update_inventory(inventory: Dictionary):
	var next: Array = KINDS.map(func(kind): return inventory.get(kind,0))
	if next == signature: return
	signature = next
	var total := 0
	for value in next: total += int(value)
	var shown := mini(total, VISIBLE_BUDGET)
	for i in range(maxi(slots.size(),shown)):
		if i >= shown:
			slots[i].visible = false
			continue
		var sample := int(float(i) * total / maxf(1,shown))
		var cumulative := 0
		var kind := "wood"
		for index in KINDS.size():
			cumulative += next[index]
			if sample < cumulative:
				kind = KINDS[index]
				break
		var piece: Node3D = slots[i] if i < slots.size() else null
		if piece and piece.get_meta("resource_kind") != kind:
			piece.visible = false
			pools[piece.get_meta("resource_kind")].append(piece)
			piece = null
		if not piece:
			piece = pools[kind].pop_back() if not pools[kind].is_empty() else loader.call(kind,self)
			piece.set_meta("resource_kind",kind)
			if i < slots.size(): slots[i] = piece
			else: slots.append(piece)
		piece.visible = true
		piece.position = Vector3((i % 3 - 1) * .19, (i / 3) * .10,0)
		piece.rotation_degrees.x = 90
		piece.scale = Vector3.ONE * (.63 if kind == "wood" else .18)
	# Physical draw budget never caps, discards or changes logical inventory.
	scale = Vector3.ONE * (1.0 + log(1.0 + maxf(0,total - VISIBLE_BUDGET) / VISIBLE_BUDGET) * .08)
