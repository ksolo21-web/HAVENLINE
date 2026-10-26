extends SceneTree
## Global asset import proof. NOT full Havenline shipping-scene or owner approval.
## Launch inside a disposable Godot 4.x project after importing the candidate GLB:
## godot --path <staging> --rendering-method mobile --script res://capture.gd -- \
##     --glb=res://assets/<asset>.glb --out=<absolute output dir> --asset-id=<name>
var output_dir: String = ""
var model_path: String = ""
var asset_id: String = ""
var ao_path: String = ""
var frame_width: int = 1280
var frame_height: int = 720
var shots: Array = []

func _initialize() -> void:
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--out="):
            output_dir = arg.trim_prefix("--out=")
        elif arg.begins_with("--glb="):
            model_path = arg.trim_prefix("--glb=")
        elif arg.begins_with("--asset-id="):
            asset_id = arg.trim_prefix("--asset-id=")
        elif arg.begins_with("--ao="):
            ao_path = arg.trim_prefix("--ao=")
        elif arg.begins_with("--width="):
            frame_width = arg.trim_prefix("--width=").to_int()
        elif arg.begins_with("--height="):
            frame_height = arg.trim_prefix("--height=").to_int()
    assert(not output_dir.is_empty())
    assert(model_path.begins_with("res://assets/"))
    assert(not asset_id.is_empty())
    assert(frame_width >= 640 and frame_width <= 4096 and frame_width % 16 == 0, "Unsupported capture width")
    assert(frame_height >= 360 and frame_height <= 4096 and frame_height % 16 == 0, "Unsupported capture height")
    call_deferred("_run_capture")

func _run_capture() -> void:
    assert(DirAccess.make_dir_recursive_absolute(output_dir) == OK)
    var packed: PackedScene = load(model_path)
    assert(packed != null, "GLB must import before inspection")
    var viewport := SubViewport.new()
    viewport.size = Vector2i(frame_width, frame_height)
    viewport.own_world_3d = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    root.add_child(viewport)
    var world := Node3D.new()
    viewport.add_child(world)
    var subject: Node3D = packed.instantiate()
    subject.name = "UnmodifiedArtistCandidate"
    world.add_child(subject)
    var ao_binding_count: int = 0
    if not ao_path.is_empty():
        assert(ao_path.begins_with("res://assets/"), "AO image must come from isolated staging assets")
        var ao_texture: Texture2D = load(ao_path) as Texture2D
        assert(ao_texture != null, "Separately baked AO texture failed to import")
        ao_binding_count = _bind_preview_ao(subject, ao_texture)
        assert(ao_binding_count > 0, "No imported PBR surfaces accepted AO atlas")
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
    world.add_child(ground)
    var corners: Array[Vector3] = []
    _collect_world_corners(subject, corners)
    assert(not corners.is_empty(), "Imported candidate has no measurable mesh bounds")
    var minimum: Vector3 = corners[0]
    var maximum: Vector3 = corners[0]
    for p in corners:
        minimum = minimum.min(p)
        maximum = maximum.max(p)
    var center: Vector3 = (minimum + maximum) * 0.5
    var extents: Vector3 = maximum - minimum
    var largest_extent: float = maxf(extents.x, maxf(extents.y, extents.z))
    assert(largest_extent > 0.0, "Invalid zero-size candidate bounds")
    ground.position = Vector3(center.x, minimum.y - 0.08, center.z)
    var camera := Camera3D.new()
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.keep_aspect = Camera3D.KEEP_HEIGHT
    # Frame each asset from measured geometry, not a fixed cooker-sized view.
    # This prevents small props from appearing tiny and large stations clipping.
    camera.size = maxf(0.75, largest_extent * 1.85)
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
        var direction: Vector3 = (viewpoints[name] as Vector3).normalized()
        camera.position = center + direction * maxf(4.0, largest_extent * 4.0)
        camera.look_at(center, Vector3.UP)
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
        "preview_ao_texture": ao_path,
        "ao_bound_material_surfaces": ao_binding_count,
        "ao_preview_only_not_shipping_scene": not ao_path.is_empty(),
        "ao_source_sha256": FileAccess.get_sha256(ao_path) if not ao_path.is_empty() else "",
        "camera_orthographic_size": camera.size,
        "native_capture_width": frame_width,
        "native_capture_height": frame_height,
        "world_bounds_min": minimum,
        "world_bounds_max": maximum,
        "view_center": center,
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

func _bind_preview_ao(node: Node, texture: Texture2D) -> int:
    # Test an actual Godot material texture binding without altering GLB source
    # resources, master assets, or any shipping Havenline material.
    var updated: int = 0
    if node is MeshInstance3D:
        var mesh_node: MeshInstance3D = node as MeshInstance3D
        if mesh_node.mesh != null:
            for surface_index in range(mesh_node.mesh.get_surface_count()):
                var original: Material = mesh_node.get_active_material(surface_index)
                if original is BaseMaterial3D:
                    var material: BaseMaterial3D = original.duplicate(true) as BaseMaterial3D
                    material.ao_enabled = true
                    material.ao_texture = texture
                    material.ao_on_uv2 = false
                    material.ao_light_affect = 1.0
                    mesh_node.set_surface_override_material(surface_index, material)
                    if material.ao_enabled and material.ao_texture == texture:
                        updated += 1
    for child in node.get_children():
        updated += _bind_preview_ao(child, texture)
    return updated

func _collect_world_corners(node: Node, points: Array[Vector3]) -> void:
    if node is MeshInstance3D:
        var mesh_node: MeshInstance3D = node as MeshInstance3D
        if mesh_node.mesh != null:
            var local_box: AABB = mesh_node.mesh.get_aabb()
            for ix in range(2):
                for iy in range(2):
                    for iz in range(2):
                        var p: Vector3 = local_box.position + Vector3(
                            local_box.size.x * float(ix),
                            local_box.size.y * float(iy),
                            local_box.size.z * float(iz))
                        points.append(mesh_node.global_transform * p)
    for child in node.get_children():
        _collect_world_corners(child, points)

func _count_meshes(node: Node) -> int:
    var total: int = 0
    if node is MeshInstance3D:
        var mesh_node := node as MeshInstance3D
        if mesh_node.mesh != null:
            total = 1
    for child in node.get_children():
        total += _count_meshes(child)
    return total
