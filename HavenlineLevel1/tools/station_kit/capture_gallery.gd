extends SceneTree
## Native renderer proof for the actual imports and their normalized placement.
const Kit = preload("res://field_station_kit.gd")
const Pads = preload("res://field_station_pad.gd")
const Art = preload("res://field_art.gd")
const ENV = preload("res://field_environment.gd")
const IDs := {
	"Shore":["fishing_rack","fishing_winch","processing_counter","fish_crate"],
	"Stock":["wood","stone","metal","fuel_canister","fish","meal","money","cargo_crate","fish_crate_empty"],
	"Pads":["build","upgrade","input","output","stock","payment"],
}
const VIEWS := {
	"front":Vector3(0.,.58,1.),"rear":Vector3(0.,.58,-1.),
	"left":Vector3(-1.,.60,0.),"right":Vector3(1.,.60,0.),
	"three-quarter":Vector3(.75,1.,1.10),"overhead":Vector3(.01,1.,.05),
}
var stage := Node3D.new()
var camera := Camera3D.new()
var outdoor: Environment
var lamps := []
var output := ""
var captures := []

func _initialize() -> void:
	run.call_deferred()

func build_view() -> void:
	root.size = Vector2i(1250,720)
	root.borderless = true
	root.add_child(stage)
	outdoor = Environment.new()
	outdoor.background_mode = Environment.BG_COLOR
	outdoor.background_color = Color("#4a6281")
	outdoor.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	outdoor.ambient_light_color = Color("#cbe3fb")
	outdoor.ambient_light_energy = .69
	var weather := WorldEnvironment.new()
	weather.environment = outdoor
	root.add_child(weather)
	for i in 2:
		var sun := DirectionalLight3D.new()
		sun.rotation_degrees = Vector3(-54. if i==0 else -26.,-28. if i==0 else 143.,0)
		sun.light_color = Color("#fff4e5") if i==0 else Color("#b2cfff")
		sun.light_energy = 0.86 if i==0 else .17
		sun.shadow_enabled = i==0
		sun.directional_shadow_max_distance = 32.
		root.add_child(sun)
		lamps.append(sun)
	var floor := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(200,200)
	var snow := StandardMaterial3D.new()
	snow.albedo_color = Color("#829cb8")
	snow.roughness = .89
	plane.material = snow
	floor.mesh = plane
	root.add_child(floor)
	root.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.current = true

func run() -> void:
	output = OS.get_environment("T05_GALLERY")
	build_view()
	for group: String in IDs:
		var spread := add_group(group)
		var whole_width := spread*1.65
		for view: String in VIEWS:
			var facing: Vector3 = VIEWS[view]
			camera.position = Vector3.UP*.48 + facing*9.
			camera.look_at(Vector3.UP*.48)
			camera.size = whole_width if view not in ["left","right"] else whole_width*.8
			await take(group+"-"+view,group,view)
		if group == "Shore":
			var sun: DirectionalLight3D = lamps[0]
			sun.light_energy = .21
			sun.light_color = Color("#a2caff")
			outdoor.ambient_light_energy = .37
			camera.position = Vector3.UP*.48 + VIEWS["three-quarter"]*9.
			camera.look_at(Vector3.UP*.48)
			camera.size = whole_width
			await take("Shore-night","Shore","night lighting")
			sun.light_energy = .85
			outdoor.ambient_light_energy = .71
			# Isolated whiteout stress fixture only. Live art and lighting are left intact.
			outdoor.fog_enabled = true
			outdoor.fog_light_color = Color("#d6e7f5")
			outdoor.fog_density = .12
			await take("Shore-low-visibility","Shore","whiteout visibility")
			outdoor.fog_enabled = false
			sun.light_energy = .86
			sun.light_color = Color("#fff4e5")
			outdoor.ambient_light_energy = .69
		for child in stage.get_children():
			stage.remove_child(child)
			child.queue_free()
	var file := FileAccess.open(output.path_join("Gallery.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"captures":captures,"adapter":RenderingServer.get_video_adapter_name()},"  "))
	file.close()
	quit()

func add_group(group: String) -> float:
	var ids: Array = IDs[group]
	var columns := 3 if group in ["Stock","Pads"] else 2
	var lines := ceili(float(ids.size())/columns)
	var x_gap := 3.45 if group=="Pads" else (3.55 if group=="Shore" else 1.8)
	var z_gap := 2.82 if group=="Pads" else (3.8 if group=="Shore" else 1.32)
	for i in ids.size():
		var id: String = ids[i]
		var item: Node3D
		if group=="Pads":
			item = pad(id)
		elif Kit.PARTS.has(id):
			item = Kit.instantiate(id)
		else:
			item = Art.make(id)
		stage.add_child(item)
		item.position = Vector3((i%columns-(columns-1)*.5)*x_gap,.008,(floori(float(i)/columns)-(lines-1)*.5)*z_gap)
		if group == "Stock" and id not in ["cargo_crate","fish_crate_empty"]:
			stack(item,id)
	return maxf((columns-1)*x_gap,(lines-1)*z_gap)+1.2

func pad(role: String) -> Node3D:
	var marker := Node3D.new()
	var native := ENV.new()
	var prototype := Node3D.new()
	native.install_payment(prototype,role=="upgrade")
	marker.add_child(Pads.create(role))
	for id in ["Gray","Brackets"]:
		marker.add_child(prototype.get_node(id).duplicate())
	Pads.glyph_socket(marker)
	for orphan in [native.buy_anchor,native.upgrade_anchor,native.resource_sightline,native.hearth_fire]:
		orphan.free()
	native.free()
	return marker

func stack(base: Node3D, id: String) -> void:
	var boxes: Array[AABB] = []
	Art._bounds(base,Transform3D.IDENTITY,boxes)
	var combined := boxes[0]
	for bounds in boxes:
		combined = combined.merge(bounds)
	# Keep the same support planes as the inspected imported stock modules.
	for i in range(1,3):
		var item: Node3D = Kit.instantiate(id) if Kit.PARTS.has(id) else Art.make(id)
		base.add_child(item)
		item.position.y = combined.size.y*i

func take(label: String, group: String, state: String) -> void:
	await process_frame
	RenderingServer.force_draw(true,1./60.)
	var image := root.get_texture().get_image()
	image.save_jpg(output.path_join(label+".jpg"),.89)
	captures.append({"file":label+".jpg","group":group,"view":state,
		"pixels":[image.get_width(),image.get_height()],"scale":root.scaling_3d_scale})
