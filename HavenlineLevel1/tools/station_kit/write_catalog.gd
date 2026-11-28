extends SceneTree
## From the Godot project directory:
## godot --headless --path . --script tools/station_kit/write_catalog.gd -- --write
const Destination := "res://assets/station_kit/catalog.json"
const Art = preload("res://field_art.gd")
const Kit = preload("res://field_station_kit.gd")
const Pads = preload("res://field_station_pad.gd")
const Depot = preload("res://field_depot.gd")
const House = preload("res://field_storage_house.gd")
const Shops = preload("res://field_processors.gd")
const Cook = preload("res://field_lakeshore.gd")
const Guard = preload("res://field_defense_tower.gd")
const Counter = preload("res://field_counter.gd")

var entries: Array[Dictionary] = []
var problems: Array[String] = []

func _initialize() -> void:
	run.call_deferred()

func vec(value: Vector3) -> Array:
	return [snappedf(value.x,.00001),snappedf(value.y,.00001),snappedf(value.z,.00001)]

func attach(sockets: Dictionary) -> Dictionary:
	var as_json := {}
	for label in sockets:
		as_json[label] = vec(sockets[label])
	return as_json

func _inventory(node: Node3D, target: Dictionary) -> void:
	var materials := {}
	var mesh_bounds: Array[AABB] = []
	Art._bounds(node,Transform3D.IDENTITY,mesh_bounds)
	if mesh_bounds.is_empty():
		problems.append("No mesh for " + str(node.name))
		return
	var merged := mesh_bounds[0]
	for bounds in mesh_bounds:
		merged = merged.merge(bounds)
	var triangles := 0
	var surfaces := 0
	var meshes: Array[Node] = node.find_children("*","MeshInstance3D",true,false)
	if node is MeshInstance3D: meshes.append(node)
	for mesh in meshes:
		for surface in mesh.mesh.get_surface_count():
			var arrays: Array = mesh.mesh.surface_get_arrays(surface)
			var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			triangles += (indices.size() if not indices.is_empty() else arrays[Mesh.ARRAY_VERTEX].size())/3
			surfaces += 1
			var paint: Material = mesh.get_active_material(surface)
			if paint == null:
				problems.append("Default paint on " + str(node.name))
				continue
			var paint_id := "%s/%s/%s" % [paint.resource_path,paint.resource_name,paint.get_class()]
			materials[paint_id] = true
	if not merged.position.is_finite() or not merged.size.is_finite() or merged.size.x <= 0. or merged.size.z <= 0.:
		problems.append("Invalid visual bounds for " + str(node.name))
	target.merge({"geometry_bounds":{"minimum":vec(merged.position),"maximum":vec(merged.end)},
		"triangles":triangles,"surfaces":surfaces,"materials":materials.keys()})

func asset(id: String, path: String, purpose: String, footprint: Rect2, sockets: Dictionary, fit: String, view: Node3D = null) -> void:
	if not FileAccess.file_exists(path) or ResourceLoader.exists(path,"PackedScene") == false:
		problems.append("Missing " + path)
		return
	if view == null:
		view = (load(path) as PackedScene).instantiate() as Node3D
	var entry := {"id":id,"asset":path,"sha256":FileAccess.get_sha256(path),"next_use":purpose,
		"fit":fit,"footprint":[footprint.position.x,footprint.position.y,footprint.size.x,footprint.size.y],
		"approach_width":.78 if footprint.has_area() else 0.,"sockets":attach(sockets)}
	_inventory(view,entry)
	if not footprint.has_area():
		var a: Array = entry.geometry_bounds.minimum
		var b: Array = entry.geometry_bounds.maximum
		entry.footprint = [a[0],a[2],snappedf(b[0]-a[0],.00001),snappedf(b[2]-a[2],.00001)]
	entries.append(entry)
	view.free()

func run() -> void:
	asset("hearth","res://assets/field_camp/furnace.glb","hearth warmth and upgrades",Rect2(-.8664,-.8664,1.7328,1.7328),
		{"Firebox":Vector3(.034,-.28,.51),"Draft":Vector3(.02,1.17,-.028),"UpgradeAccess":Vector3(0,0,1.37)},
		"stone shell asset coordinates for FX; fitted camp footprint and ground approach")
	asset("service_counter",Counter.COUNTER.resource_path,"customer pickup and independent cash pile",
		Rect2(-Counter.HALF_BAY,-Counter.HALF_DEPTH,Counter.HALF_BAY*2,Counter.HALF_DEPTH*2),
		{"WorkerInside":Vector3(0,0,1.54),"CustomerOutside":Vector3(0,0,Counter.CUSTOMER_Z),
			"MealOnBoard":Vector3(0,1.08,0),"NotesOnBoard":Vector3(1.16,1.085,-.1)},"north fence socket")
	asset("camp_cooker",Cook.Cooker.resource_path,"cook and accept separate raw and completed goods",Cook.BODY,
		{"RawInput":Vector3(-.94,.49,.06),"CookedOutput":Vector3(.98,.52,.03),"Smoke":Vector3(0,1.67,-.14),
			"Worker":Cook.APRON-Cook.COOKER_AT,"Collection":Cook.OUTPUT_APRON-Cook.COOKER_AT},"camp kitchen local")
	for kind: String in Shops.MACHINES:
		asset("saw_bench" if kind=="wood" else "quarry_drill",Shops.MACHINES[kind].resource_path,
			"wood processing" if kind=="wood" else "stone processing",Shops.FOOTPRINT[kind],
			{"Input":Shops.INPUT[kind],"Output":Shops.OUTPUT[kind],"Worker":Shops.APRONS[kind]-Shops.CENTERS[kind]},"camp workshop local")
	asset("ballista","res://assets/field_world/camp_ballista.glb","defense, aiming and repair",Guard.FOOTPRINT,
		{"SupplyApproach":Vector3(-1.48,0,0),"RepairApproach":Vector3(-1.48,0,.42),"WeaponBearing":Vector3(0,2.82,0)},
		"camp placement local; Turntable and LoadedQuarrel retain the authored weapon transforms")
	var bays := House.BAYS.duplicate()
	bays["LoadingApproach"] = Depot.APRON-Depot.SITE
	asset("storehouse",House.SHELL.resource_path,"camp stock and direct withdrawal",Depot.FOOTPRINT,bays,"grounded house local")
	asset("storehouse_hatches",House.CONNECTIONS.resource_path,"upgradeable storehouse docking and vents",Depot.FOOTPRINT,
		{"UtilityHatch":Vector3(-1.56,.51,0),"FoodHatch":Vector3(1.56,.51,0)},"modular frames; network assigns final paid docks")
	asset("conveyor_modules","res://assets/conveyors/connected_transport_kit.glb","repeatable static rollers, transitions, input and output fittings",
		Rect2(-.23,-.5,.46,1.0),{"Input":Vector3(0,.27,-.5),"Output":Vector3(0,.27,.5)},
		"library nodes Roller, Dock and Socket; unit mating length for straight")
	for id: String in Kit.PARTS:
		var definition: Dictionary = Kit.PARTS[id]
		asset(id,definition.scene,"shore fishing and intake kit" if Kit.INLET_LAYOUT.has(id) else "reusable physical stock module",
			Kit.INLET_FEET.get(id,Rect2()),definition.sockets,"center and ground geometry at the installed width",Kit.instantiate(id))
	for id: String in Art.PATHS:
		if id == "wolf": continue
		var source := Art.make(id)
		var parts: Array[AABB] = []
		Art._bounds(source,Transform3D.IDENTITY,parts)
		var bounds := parts[0]
		for box in parts: bounds = bounds.merge(box)
		asset(id,Art.PATHS[id],"reusable physical stock module",Rect2(),
			{"StackTop":Vector3(0,bounds.end.y,0)},"center and ground geometry at the field carry width",source)
	for role: String in Pads.COLORS:
		var pad := Pads.create(role)
		var source := "res://field_station_pad.gd"
		var entry := {"id":"pad_"+role,"asset":source,"sha256":FileAccess.get_sha256(source),
			"next_use":role+" ground marking","fit":"shallow deck with original interactive face lifted above bevel",
			"footprint":[-1.487,-1.236,2.974,2.472],"approach_width":.78,
			"sockets":attach({"IconSocket":Vector3(0,Pads.FACE_Y+.012,-Pads.SLOT_WIDTH)}),
			"trim":Pads.COLORS[role].to_html(false)}
		_inventory(pad,entry)
		pad.free()
		entries.append(entry)
	var seen := {}
	for entry in entries:
		if seen.has(entry.id): problems.append("Duplicate id " + entry.id)
		seen[entry.id] = true
		if entry.sha256.length()!=64 or entry.sockets.is_empty() or entry.materials.is_empty():
			problems.append("Missing identity, paint or socket for " + entry.id)
	var result := JSON.stringify({"format":1,"units":"metres","items":entries},"  ",true)+"\n"
	if problems.is_empty():
		if "--write" in OS.get_cmdline_user_args():
			var file := FileAccess.open(Destination,FileAccess.WRITE)
			file.store_string(result)
		elif FileAccess.get_file_as_string(Destination)!=result:
			problems.append("Catalog does not match imported assets, attachments and geometry")
	for problem in problems: printerr(problem)
	print("Station kit catalog: %d entries, %d errors" % [entries.size(),problems.size()])
	quit(0 if problems.is_empty() else 1)
