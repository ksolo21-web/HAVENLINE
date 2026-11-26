extends SceneTree

var world := Node3D.new()
var camera := Camera3D.new()
var output := OS.get_environment("HVN_INDEPENDENT_TOWER")

func _initialize() -> void:
	call_deferred("run")

func shot(file_name: String) -> void:
	RenderingServer.force_draw(false,0)
	var frame := root.get_texture().get_image()
	frame.save_png(output.path_join(file_name+".png"))

func run() -> void:
	root.add_child(world)
	var environment := WorldEnvironment.new()
	environment.environment=Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color("#263848")
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color=Color.WHITE
	environment.environment.ambient_light_energy=1.
	world.add_child(environment)
	var sun:=DirectionalLight3D.new()
	sun.rotation=Vector3(-.82,-.6,0)
	world.add_child(sun)
	var art=load("res://field_tower_art.gd").new()
	art.position=Vector3(8.1,0,-2.4)
	world.add_child(art)
	world.add_child(camera)
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.size=4.05
	var focus:Vector3=art.position+Vector3.UP*1.55
	camera.position=focus+Vector3(7,11,11)
	camera.look_at(focus)
	camera.make_current()
	for i in 2:
		await process_frame
	var old_materials=[]
	for mesh in art.upper_parts:
		old_materials.append(mesh.mesh.surface_get_material(0).get_instance_id())
	var feet=Vector3(6.16776,0,-4.10155)
	var result={}
	for tag in ["opaque","opened","restored"]:
		match tag:
			"opaque": art.update_sightline(feet,null)
			"opened": art.update_sightline(feet,camera)
			"restored": art.update_sightline(Vector3(4.9,0,.2),camera)
		shot(tag)
		var overrides_present=[]
		var authored_unchanged=true
		for i in art.upper_parts.size():
			var mesh=art.upper_parts[i]
			overrides_present.append(mesh.material_override != null)
			authored_unchanged = authored_unchanged and mesh.mesh.surface_get_material(0).get_instance_id()==old_materials[i]
		result[tag]={"active":art.cutaway_active,"upper_overrides":overrides_present,"same_authored_material_id":authored_unchanged}
	var f=FileAccess.open(output.path_join("material-restoration.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(result,"  ")+"\n")
	f.close()
	quit()
