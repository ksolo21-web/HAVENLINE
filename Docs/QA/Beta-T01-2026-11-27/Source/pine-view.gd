extends SceneTree
var target := OS.get_environment("T01_MESHY_OUT")
func _initialize() -> void:
	run.call_deferred()
func aligned(model: Node3D, x: float) -> void:
	root.add_child(model)
	var bounds := AABB()
	for child: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		var transformed := child.global_transform * child.get_aabb()
		if bounds.has_volume(): bounds = bounds.merge(transformed)
		else: bounds = transformed
	var ratio := 2.8 / bounds.size.y
	model.scale = Vector3.ONE * ratio
	var center := bounds.get_center()*ratio
	model.position = Vector3(x-center.x,-bounds.position.y*ratio,-center.z)
func shoot(camera: Camera3D, at: Vector3,destination: String) -> void:
	camera.position = at
	camera.look_at(Vector3(0,1.18,0))
	await process_frame
	await process_frame
	RenderingServer.force_draw(false,1.0/60.0)
	root.get_texture().get_image().save_jpg(target.path_join(destination),.94)
func run() -> void:
	var state := GLTFState.new()
	var importer := GLTFDocument.new()
	if importer.append_from_file(target.path_join("Forest-pine.glb"),state) != OK:
		quit(2)
		return
	var candidate := importer.generate_scene(state) as Node3D
	var existing := preload("res://assets/reference_forest/pine_2.glb").instantiate() as Node3D
	aligned(existing,-1.7)
	aligned(candidate,1.7)
	var backdrop := WorldEnvironment.new()
	backdrop.environment = Environment.new()
	var environment := backdrop.environment
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("#d9e3e8")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("#e7f2ff")
	environment.ambient_light_energy = .73
	root.add_child(backdrop)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-43,-31,0)
	sun.light_energy = 1.05
	root.add_child(sun)
	var ground := MeshInstance3D.new()
	ground.mesh = PlaneMesh.new()
	ground.mesh.size = Vector2(100,100)
	ground.material_override = StandardMaterial3D.new()
	ground.material_override.albedo_color = Color("#e5ecf0")
	root.add_child(ground)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 4.0
	root.add_child(camera)
	camera.make_current()
	await shoot(camera,Vector3(0,4.5,8),"Pine-comparison-front.jpg")
	await shoot(camera,Vector3(3.5,5.5,8),"Pine-comparison-quarter.jpg")
	quit()
