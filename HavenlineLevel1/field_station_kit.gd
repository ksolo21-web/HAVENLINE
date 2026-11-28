extends RefCounted
## Static fixture scenes and attachment points shared by the inlet and kit proofs.
const Art = preload("res://field_art.gd")
const PARTS := {
	"fishing_rack": {
		"scene": "res://assets/station_kit/fishing_rack.glb",
		"width": 2.45,
		"sockets": {"RodGrip":Vector3(0,.55,.98), "DryApproach":Vector3(0,0,1.91), "Cast":Vector3(0,1.72,-1.31)},
	},
	"fishing_winch": {
		"scene": "res://assets/station_kit/fishing_winch.glb",
		"width": 1.55,
		"sockets": {"TackleInput":Vector3(-.26,.66,.24), "CatchOutput":Vector3(.27,.31,.38), "DryApproach":Vector3(0,0,.91)},
	},
	"processing_counter": {
		"scene": "res://assets/station_kit/processing_counter.glb",
		"width": 2.10,
		"sockets": {"Intake":Vector3(-.68,.477,0), "Grate":Vector3(0,.44,0), "Outfeed":Vector3(.68,.477,0), "DryApproach":Vector3(0,0,.89)},
	},
	"fish_crate": {
		"scene": "res://assets/station_kit/fish_crate.glb",
		"width": 1.02,
		"sockets": {"StockTop":Vector3(0,.438,0), "DryApproach":Vector3(0,0,.82)},
	},
	"fish_crate_empty": {
		"scene": "res://assets/station_kit/fish_crate_empty.glb",
		"width": 1.02,
		"sockets": {"CatchPile":Vector3(0,.268,0), "DryApproach":Vector3(0,0,.82)},
	},
	"fish": {
		"scene": "res://assets/station_kit/fish.glb",
		"width": .52,
		"sockets": {"StackTop":Vector3(0,.21,0)},
	},
	"cargo_crate": {
		"scene": "res://assets/station_kit/cargo_crate.glb",
		"width": .88,
		"sockets": {"StackTop":Vector3(0,.45,0)},
	},
	"fuel_canister": {
		"scene": "res://assets/station_kit/fuel_canister.glb",
		"width": .35,
		"sockets": {"Grip":Vector3(-.05,.44,0)},
	},
}
# Fractions of the closed inlet survey. Each position fits the existing
# east-side bank exclusion strip. Local +Z faces the dry approach.
const INLET_LAYOUT := {
	"fishing_rack": Vector2(.026,1.15),
	"fishing_winch": Vector2(.975,.73),
	"processing_counter": Vector2(.948,.81),
	"fish_crate": Vector2(.930,.95),
}
# Ground contact only. The rod tips and line hang above the water.
const INLET_FEET := {
	"fishing_rack": Rect2(-1.23,.24,2.46,1.03),
	"fishing_winch": Rect2(-.78,-.54,1.56,1.08),
	"processing_counter": Rect2(-1.06,-.40,2.12,.80),
	"fish_crate": Rect2(-.52,-.37,1.04,.74),
}
static var scenes := {}
static var bounds := {}

static func marker(parent: Node3D, label: String, point: Vector3) -> Marker3D:
	var socket := Marker3D.new()
	socket.name = label
	socket.position = point
	parent.add_child(socket)
	return socket

static func instantiate(id: String) -> Node3D:
	var definition: Dictionary = PARTS[id]
	if not scenes.has(id):
		scenes[id] = load(definition.scene) as PackedScene
	var result := Node3D.new()
	result.name = "%sFixture" % id.to_pascal_case()
	var model := (scenes[id] as PackedScene).instantiate() as Node3D
	result.add_child(model)
	if not bounds.has(id):
		var boxes: Array[AABB] = []
		Art._bounds(model,Transform3D.IDENTITY,boxes)
		# The bundled supply props carry linear GLTF paint colors. Godot
		# imports the channel but leaves its material flag off.
		for mesh: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
			var material := mesh.get_active_material(0) as BaseMaterial3D
			if material != null and material.resource_name == "Havenline Supply Paint":
				material.vertex_color_use_as_albedo = true
		var combined := boxes[0]
		for box in boxes:
			combined = combined.merge(box)
		bounds[id] = combined
	var authored: AABB = bounds[id]
	var scale_factor := float(definition.width) / authored.size.x
	model.scale = Vector3.ONE * scale_factor
	model.position = -Vector3(authored.get_center().x,authored.position.y,authored.get_center().z)*scale_factor
	for label: String in definition.sockets:
		marker(result,label,definition.sockets[label])
	return result

static func install_inlet(parent: Node3D, shore: PackedVector2Array) -> Node3D:
	var group := Node3D.new()
	group.name = "ShoreStationKit"
	parent.add_child(group)
	for id: String in INLET_LAYOUT:
		var placement: Vector2 = INLET_LAYOUT[id]
		var count := shore.size()
		var index := roundi(placement.x * count) % count
		var tangent := (shore[(index+1)%count]-shore[posmod(index-1,count)]).normalized()
		var away := Vector2(tangent.y,-tangent.x)
		var point := shore[index] + away*placement.y
		var fixture := instantiate(id)
		group.add_child(fixture)
		fixture.position = Vector3(point.x,.025,point.y)
		fixture.rotation.y = atan2(away.x,away.y)
		fixture.set_meta(&"station_footprint",INLET_FEET[id])
	return group
