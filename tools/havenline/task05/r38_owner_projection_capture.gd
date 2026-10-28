extends SceneTree
# Disposable R38 art-critic capture. Does not integrate into the shipping scene.
var vp:SubViewport
var cam:Camera3D

func _initialize():
    call_deferred("capture")

func apply_to_mesh(node:Node, material:Material):
    if node is MeshInstance3D:
        node.material_override=material
    for child in node.get_children():
        apply_to_mesh(child,material)

func capture():
    vp=SubViewport.new()
    vp.size=Vector2i(960,960)
    vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS
    root.add_child(vp)
    var stage=Node3D.new()
    vp.add_child(stage)
    var scene=load("res://assets/T05_R38_SOURCE_PROJECTED_UNAPPROVED.glb") as PackedScene
    if scene==null:
        push_error("T05_R38_MESH_IMPORT_FAILED")
        quit(3)
        return
    var model=scene.instantiate()
    stage.add_child(model)
    var shader=load("res://owner_projection.gdshader") as Shader
    if shader==null:
        push_error("T05_R38_SOURCE_SHADER_LOAD_FAILED")
        quit(4)
        return
    var mat=ShaderMaterial.new()
    mat.shader=shader
    mat.set_shader_parameter("front_tex",load("res://assets/32451.jpg"))
    mat.set_shader_parameter("right_tex",load("res://assets/32450.jpg"))
    # Original 32441.png contains JPEG bytes; use byte-identical filename alias.
    mat.set_shader_parameter("rear_tex",load("res://assets/32441_exact_jpeg.jpg"))
    if mat.get_shader_parameter("rear_tex")==null:
        push_error("T05_R38_REAR_SOURCE_TEXTURE_LOAD_FAILED")
        quit(5)
        return
    apply_to_mesh(model,mat)
    var environment=WorldEnvironment.new()
    var background=Environment.new()
    background.background_mode=Environment.BG_COLOR
    background.background_color=Color(0.018,0.020,0.030)
    background.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
    background.ambient_light_color=Color(1,1,1)
    background.ambient_light_energy=1.0
    environment.environment=background
    stage.add_child(environment)
    cam=Camera3D.new()
    cam.current=true
    cam.projection=Camera3D.PROJECTION_ORTHOGONAL
    cam.size=4.0
    stage.add_child(cam)
    for item in [["front",30.0,15.0],["side",90.0,7.0],["rear",180.0,7.0],["unobserved_left",-50.0,20.0]]:
        var a=deg_to_rad(item[1])
        var e=deg_to_rad(item[2])
        var center=Vector3(0,1.55,0)
        cam.position=center+Vector3(sin(a)*cos(e),sin(e),cos(a)*cos(e))*7.0
        cam.look_at(center,Vector3.UP)
        for frame in range(12):
            await process_frame
        var image=vp.get_texture().get_image()
        if image==null or image.get_size()!=Vector2i(960,960):
            push_error("T05_R38_CAPTURE_FAILED "+str(item[0]))
            quit(6)
            return
        image.save_png("res://captures/r38_"+str(item[0])+".png")
        print("T05_R38_REAL_GODOT_CAPTURE_OK ",str(item[0]))
    quit(0)
