extends SceneTree
# Isolated Godot reference-only review for T05 R34 candidate (not game art).
# To reproduce: place T05_neural_owner_front_UNAPPROVED.glb as
# res://assets/neural_owner_cooker_unapproved.glb in a disposable
# Godot 4.7.2 project using gl_compatibility.
var viewport: SubViewport
var camera: Camera3D
func _initialize():
    call_deferred("capture")

func apply_source_vertex_colors(n: Node):
    if n is MeshInstance3D and n.mesh != null:
        var m := StandardMaterial3D.new()
        m.vertex_color_use_as_albedo = true
        m.roughness = 0.86
        n.material_override = m
    for child in n.get_children():
        apply_source_vertex_colors(child)

func capture():
    viewport = SubViewport.new()
    viewport.size = Vector2i(960, 960)
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    root.add_child(viewport)
    var stage := Node3D.new()
    viewport.add_child(stage)
    var packed := load("res://assets/neural_owner_cooker_unapproved.glb") as PackedScene
    if packed == null:
        push_error("GLB import failed")
        quit(3)
        return
    var model := packed.instantiate()
    stage.add_child(model)
    apply_source_vertex_colors(model)
    var w := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.023, 0.031, 0.052)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.7, 0.79, 0.94)
    env.ambient_light_energy = 0.75
    w.environment = env
    stage.add_child(w)
    var sun := DirectionalLight3D.new()
    sun.light_energy = 1.5
    sun.rotation_degrees = Vector3(-33, -35, 0)
    stage.add_child(sun)
    camera = Camera3D.new()
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.size = 2.0
    camera.current = true
    stage.add_child(camera)
    for pair in [["source_inferred", Vector3(2, 0.8, 2.5)],
                 ["front", Vector3(0, 0.7, 3)],
                 ["side", Vector3(3, 0.7, 0)],
                 ["rear", Vector3(0, 0.7, -3)]]:
        camera.position = pair[1]
        camera.look_at(Vector3.ZERO, Vector3.UP)
        for frame in range(9):
            await process_frame
        var img := viewport.get_texture().get_image()
        if img == null or img.get_size() != Vector2i(960, 960):
            push_error("Native image capture failed")
            quit(4)
            return
        img.save_png("res://captures/godot_neural_" + pair[0] + ".png")
        print("T05_R34_NATIVE_CAPTURE_OK ", pair[0])
    quit(0)
