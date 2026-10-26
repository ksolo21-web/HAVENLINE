extends SceneTree
## Global asset import proof. NOT full Havenline shipping-scene or owner approval.
## Launch inside a disposable Godot 4.x project after importing the candidate GLB:
## godot --path <staging> --rendering-method mobile --script res://capture.gd -- \
##     --glb=res://assets/<asset>.glb --out=<absolute output dir> --asset-id=<name>
var output_dir: String = ""
var model_path: String = ""
var asset_id: String = ""
var shots: Array = []

func _initialize() -> void:
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--out="):
            output_dir = arg.trim_prefix("--out=")
        elif arg.begins_with("--glb="):
            model_path = arg.trim_prefix("--glb=")
        elif arg.begins_with("--asset-id="):
            asset_id = arg.trim_prefix("--asset-id=")
    assert(not output_dir.is_empty())
    assert(model_path.begins_with("res://assets/"))
    assert(not asset_id.is_empty())
    call_deferred("_run_capture")

func _run_capture() -> void:
    assert(DirAccess.make_dir_recursive_absolute(output_dir) == OK)
    var packed: PackedScene = load(model_path)
    assert(packed != null, "GLB must import before inspection")
    var viewport := SubViewport.new()
    viewport.size = Vector2i(1280, 720)
    viewport.own_world_3d = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    root.add_child(viewport)
    var world := Node3D.new()
    viewport.add_child(world)
    var subject: Node3D = packed.instantiate()
    subject.name = "UnmodifiedArtistCandidate"
    world.add_child(subject)
    var env := WorldEnvironment.new()
    env.environment = Environment.new()
    env.environment.background_mode = Environment.BG_COLOR
    env.environment.background_color = Color("344b5f")
    env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.environment.ambient_light_color = Color("c3d4e5")
    env.environment.ambient_light_energy = 0.65
    world.add_child(env)
    var sunlight := DirectionalLight3D.new()
    sunlight.rotation_degrees = Vector3(-52, 28, 0)
    sunlight.light_energy = 1.35
    world.add_child(sunlight)
    var ground := MeshInstance3D.new()
    ground.mesh = PlaneMesh.new()
    ground.mesh.size = Vector2(8,8)
    var ground_material := StandardMaterial3D.new()
    ground_material.albedo_color = Color("a3bacb")
    ground_material.roughness = 0.96
    ground.material_override = ground_material
    ground.position.y = -0.08
    world.add_child(ground)
    var camera := Camera3D.new()
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.keep_aspect = Camera3D.KEEP_HEIGHT
    camera.size = 3.8
    world.add_child(camera)
    camera.current = true
    var count := _count_meshes(subject)
    assert(count > 0, "Imported GLB has no geometry")
    var viewpoints := {
        "front": Vector3(0,2.8,-5),
        "rear": Vector3(0,2.8,5),
        "left": Vector3(-5,2.8,0),
        "right": Vector3(5,2.8,0),
        "three-quarter": Vector3(4,3.5,-4.8),
        "overhead": Vector3(0.01,7,-0.05),
        "gameplay_oblique": Vector3(5,7,-6)
    }
    for name in viewpoints.keys():
        camera.position = viewpoints[name]
        camera.look_at(Vector3(0,1.0,0), Vector3.UP)
        for tick in range(5):
            await process_frame
        await RenderingServer.frame_post_draw
        var image := viewport.get_texture().get_image()
        var file_name: String = asset_id + "_isolated_" + str(name) + ".png"
        assert(image.save_png(output_dir.path_join(file_name)) == OK)
        shots.append({"view": name, "file": file_name, "width": image.get_width(),
            "height": image.get_height()})
    var report := {
        "asset_id": asset_id,
        "status": "ISOLATED_TECHNICAL_ENGINE_PROOF_ONLY",
        "source_path": model_path,
        "candidate_glb_sha256": FileAccess.get_sha256(model_path),
        "engine": "Godot",
        "renderer": RenderingServer.get_current_rendering_method(),
        "gpu": RenderingServer.get_video_adapter_name(),
        "mesh_count": count,
        "shipping_scene_loaded": false,
        "actual_physical_android_tested": false,
        "owner_reference_fidelity_approved": false,
        "renders": shots
    }
    var file := FileAccess.open(output_dir.path_join("isolated-import.json"), FileAccess.WRITE)
    assert(file != null)
    file.store_string(JSON.stringify(report, "  "))
    file.close()
    print("GLOBAL_ASSET_IMPORT_PROOF ", JSON.stringify(report))
    quit(0)

func _count_meshes(node: Node) -> int:
    var total: int = 0
    if node is MeshInstance3D:
        var mesh_node := node as MeshInstance3D
        if mesh_node.mesh != null:
            total = 1
    for child in node.get_children():
        total += _count_meshes(child)
    return total
