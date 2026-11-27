extends RefCounted

const FieldArt = preload("res://field_art.gd")
const TRUCK_SCENE = preload("res://assets/snow_truck/snow_truck.glb")
const GARAGE_SCENE = preload("res://assets/snow_truck/snow_garage.glb")
const WHEELS := [&"WheelFrontLeft", &"WheelFrontRight", &"WheelRearLeft", &"WheelRearRight"]
const BLADES := [&"BladeLeft", &"BladeRight"]
const LOAD_WIDTH := 0.42
const LOAD_KINDS := ["wood", "stone", "metal", "planks", "blocks", "coal", "slate", "meat", "meal", "money"]
const LOAD_SLOTS := [
	Vector3(-0.47, 1.15, 0.50), Vector3(0.01, 1.15, 0.50), Vector3(0.48, 1.15, 0.50),
	Vector3(-0.46, 1.15, 0.97), Vector3(0.01, 1.15, 0.97), Vector3(0.48, 1.15, 0.97),
]

static func truck() -> Node3D:
	return TRUCK_SCENE.instantiate() as Node3D

static func garage() -> Node3D:
	return GARAGE_SCENE.instantiate() as Node3D

static func set_motion(model: Node3D, wheel_angle: float, blade_angle: float) -> void:
	for name in WHEELS:
		var wheel := model.find_child(name, true, false) as Node3D
		if wheel:
			wheel.rotation.x = wheel_angle
	for index in BLADES.size():
		var blade := model.find_child(BLADES[index], true, false) as Node3D
		if blade:
			blade.rotation.y = blade_angle if index == 0 else -blade_angle

static func set_door(model: Node3D, openness: float) -> void:
	var panel := model.find_child("RollupDoor", true, false) as Node3D
	if not panel:
		return
	var raised := clampf(openness, 0.0, 1.0) * 2.36
	if raised == float(panel.get_meta(&"raised_height", -1.0)):
		return
	panel.set_meta(&"raised_height", raised)
	for slat: Node3D in panel.get_children():
		if not slat.has_meta(&"closed_height"):
			slat.set_meta(&"closed_height", slat.position.y)
		slat.position.y = float(slat.get_meta(&"closed_height")) + raised
		slat.visible = slat.position.y < 2.41

static func set_roof_visibility(model: Node3D, shown: bool) -> void:
	var roof := model.find_child("Roof", true, false) as Node3D
	if roof:
		roof.visible = shown

static func set_damage(model: Node3D, missing_fraction: float) -> void:
	var damage := model.find_child("Damage", true, false) as Node3D
	if damage:
		damage.visible = missing_fraction >= 0.55

static func set_load(model: Node3D, quantities: Dictionary) -> void:
	var rack := model.get_node_or_null(^"CargoPreview") as Node3D
	if not rack:
		rack = Node3D.new()
		rack.name = "CargoPreview"
		model.add_child(rack)
	var manifest := PackedStringArray()
	var upper_layers := PackedByteArray()
	for kind in LOAD_KINDS:
		var value: Variant = quantities.get(kind, 0)
		var active: bool = (value is int and value > 0) or (value is String and value != "" and value != "0")
		if active:
			manifest.append(kind)
			upper_layers.append(int(str(value) != "1"))
		if manifest.size() >= LOAD_SLOTS.size():
			break
	if rack.get_meta(&"manifest", PackedStringArray()) == manifest and rack.get_meta(&"upper_layers", PackedByteArray()) == upper_layers:
		return
	rack.set_meta(&"manifest", manifest)
	rack.set_meta(&"upper_layers", upper_layers)
	for child in rack.get_children():
		rack.remove_child(child)
		child.queue_free()
	for index in manifest.size():
		var parcel := FieldArt.make(manifest[index], LOAD_WIDTH)
		if not parcel:
			continue
		rack.add_child(parcel)
		parcel.position = LOAD_SLOTS[index]
		parcel.rotate_y(0.15 * sin(float(index)))
		if upper_layers[index] == 0:
			continue
		# The upper layer rests on the first and makes large loads legible above
		# the bed wall. Neither layer creates one mesh for each resource unit.
		var boxes: Array[AABB] = []
		FieldArt._bounds(parcel, Transform3D.IDENTITY, boxes)
		var stack_top := parcel.position.y
		for box in boxes:
			stack_top = maxf(stack_top, box.end.y)
		var top := FieldArt.make(manifest[index], LOAD_WIDTH * 0.82)
		if top:
			rack.add_child(top)
			top.position = Vector3(parcel.position.x, stack_top - 0.025, parcel.position.z)
			top.rotate_y(0.2 * cos(float(index)))
