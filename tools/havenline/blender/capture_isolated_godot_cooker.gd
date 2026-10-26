extends SceneTree

## Isolated T05 Blender->Godot import proof.
## The shipping project is NEVER loaded or modified by this stage; therefore
## these pixels are Godot-engine import/material evidence, NOT gameplay QA.
var out_path := ""
var evidence: Array = []
var viewport: SubViewport
var camera: Camera3D

func _initialize() -> void:
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--out="):
            out_path = arg.trim_prefix("--out=")
    assert(not out_path.is_empty(), "Explicit evidence directory required")
    call_deferred("_capture")

func _capture() -> void:
    assert(DirAccess.make_dir_recursive_absolute(out_path) == OK)
    var scene: PackedScene = load("res://assets/T05_cooker_BLENDER_CANDIDATE.glb")
    assert(scene != null, "Blender GLB must import in Godot before inspection")
    viewport = SubViewport.new()
    viewport.size = Vector2i(1280, 720)
    viewport.own_world_3d = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport.msaa_3d = Viewport.MSAA_4X
    root.add_child(viewport)
    var world := Node3D.new()
    viewport.add_child(world)
    var asset: Node3D = scene.instantiate()
    asset.name = "UnalteredBlenderCookerGLB"
    world.add_child(asset)
    var lighting := WorldEnvironment.new()
    lighting.environment = Environment.new()
    lighting.environment.background_mode = Environment.BG_COLOR
    lighting.environment.background_color = Color("344a5d")
    lighting.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    lighting.environment.ambient_light_color = Color("bad5df")
    lighting.environment.ambient_light_energy = 0.56
    world.add_child(lighting)
    var sun := DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-48, 22, 0)
    sun.light_energy = 1.24
    world.add_child(sun)
    var floor := MeshInstance3D.new()
    floor.mesh = PlaneMesh.new()
    floor.mesh.size = Vector2(6, 6)
    var floor_material := StandardMaterial3D.new()
    floor_material.albedo_color = Color("91aec1")
    floor_material.roughness = 0.91
    floor.material_override = floor_material
    floor.position.y = -0.08
    world.add_child(floor)
    camera = Camera3D.new()
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.keep_aspect = Camera3D.KEEP_HEIGHT
    camera.size = 3.35
    world.add_child(camera)
    camera.current = true
    var meshes := _count_meshes(asset)
    assert(meshes > 0, "Candidate has zero imported Godot meshes")
    var shots := {
        "front": Vector3(0, 3.1, -6.0),
        "three-quarter": Vector3(4.0, 3.25, -4.8),
        "right": Vector3(6.0, 3.1, 0.0),
        "rear": Vector3(0, 3.1, 6.0)
    }
    for key in shots:
        camera.position = shots[key]
        camera.look_at(Vector3(0, 1.25, 0), Vector3.UP)
        for step in range(6):
            await process_frame
        await RenderingServer.frame_post_draw
        var img := viewport.get_texture().get_image()
        assert(img.get_width() == 1280 and img.get_height() == 720, "Native Godot screenshot dimensions changed")
        var filename := "isolated-godot-" + key + ".png"
        assert(img.save_png(out_path.path_join(filename)) == OK, "Cannot write Godot evidence")
        evidence.append({"view": key, "file": filename, "resolution": [img.get_width(), img.get_height()]})
    var report := {
        "task": "T05",
        "benchmark": "Blender cookbook importer",
        "status": "ISOLATED_GODOT_IMPORT_ONLY_NOT_SHIPPING_QA",
        "source_file": "T05_cooker_BLENDER_CANDIDATE.glb",
        "renderer": RenderingServer.get_current_rendering_method(),
        "device": RenderingServer.get_video_adapter_name(),
        "godot_mesh_count": meshes,
        "shipping_main_loaded": false,
        "shipping_asset_modified": false,
        "owner_visual_approved": false,
        "captures": evidence
    }
    var file := FileAccess.open(out_path.path_join("isolated-godot-report.json"), FileAccess.WRITE)
    assert(file != null)
    file.store_string(JSON.stringify(report, "  "))
    file.close()
    print("T05_ISOLATED_GODOT_IMPORT_PROOF ", JSON.stringify(report))
    quit(0)

func _count_meshes(node: Node) -> int:
    var count := 1 if node is MeshInstance3D and node.mesh != null else 0
    for child in node.get_children():
        count += _count_meshes(child)
    return count
