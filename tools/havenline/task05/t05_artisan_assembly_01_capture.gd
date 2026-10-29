extends SceneTree
# T05 assembly-01: real Godot 4.7.2 screenshot review, NOT release or art pass.
var vp: SubViewport
func _initialize():
    call_deferred("_capture")
func _capture():
    var out=OS.get_cmdline_user_args()
    if out.is_empty() or not out[0].begins_with("--out="):
        push_error("Requires explicit --out=absolute_path")
        quit(3)
        return
    var directory=out[0].trim_prefix("--out=")
    DirAccess.make_dir_recursive_absolute(directory)
    var scene=load("res://assets/T05_ASSEMBLY_01_SAW_BLUE_WOOD_UNAPPROVED.glb") as PackedScene
    if scene == null:
        push_error("Original-source Blender assembly GLB import failed")
        quit(4)
        return
    vp=SubViewport.new()
    vp.size=Vector2i(1280,960)
    vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS
    vp.own_world_3d=true
    root.add_child(vp)
    var stage=Node3D.new()
    vp.add_child(stage)
    var model=scene.instantiate()
    stage.add_child(model)
    model.position.y=1.72
    var env=WorldEnvironment.new()
    env.environment=Environment.new()
    env.environment.background_mode=Environment.BG_COLOR
    env.environment.background_color=Color(0.021,0.031,0.045)
    env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
    env.environment.ambient_light_color=Color(0.72,0.83,0.93)
    env.environment.ambient_light_energy=0.72
    stage.add_child(env)
    var sun=DirectionalLight3D.new()
    sun.rotation_degrees=Vector3(-48,28,-12)
    sun.light_energy=1.3
    stage.add_child(sun)
    var rim=DirectionalLight3D.new()
    rim.rotation_degrees=Vector3(-30,-110,15)
    rim.light_energy=0.43
    stage.add_child(rim)
    var camera=Camera3D.new()
    camera.projection=Camera3D.PROJECTION_ORTHOGONAL
    camera.size=6.8
    camera.keep_aspect=Camera3D.KEEP_HEIGHT
    camera.current=true
    stage.add_child(camera)
    var views={
      "source_three_quarter":Vector3(5.5,5.3,8.5),
      "saw_front":Vector3(.2,3.7,9.5),
      "right_side":Vector3(9.5,4.1,0),
      "rear":Vector3(0,4.1,-9.5),
      "underframe":Vector3(-4.5,2.6,8.0)
    }
    var images=[]
    for label in views:
        camera.position=views[label]
        camera.look_at(Vector3(-1.0,2.16,0.0),Vector3.UP)
        for f in range(10):
            await process_frame
        await RenderingServer.frame_post_draw
        var img=vp.get_texture().get_image()
        if img==null or img.get_size()!=Vector2i(1280,960):
            push_error("Bad native screenshot for "+label)
            quit(6)
            return
        var output=directory.path_join("godot_"+label+".png")
        if img.save_png(output)!=OK:
            push_error("Couldn't save screenshot")
            quit(7)
            return
        images.append({"view":label,"size":[1280,960]})
        print("T05_ASSEMBLY01_GODOT_FRAME_OK ",label)
    var proof={
      "status":"NATIVE_GODOT_REAL_ASSEMBLY_01_WIP__NO_ART_APPROVAL",
      "actual_engine":Engine.get_version_info().get("string","unknown"),
      "renderer":RenderingServer.get_current_rendering_method(),
      "gpu":RenderingServer.get_video_adapter_name(),
      "reference_owner_approval":false,
      "shipping_asset_modified":false,
      "physical_phone_benchmarked":false,
      "screenshots":images
    }
    var receipt=FileAccess.open(directory.path_join("godot_receipt.json"),FileAccess.WRITE)
    receipt.store_string(JSON.stringify(proof,"  "))
    receipt.close()
    print("T05_ASSEMBLY01_NATIVE_PASS ",JSON.stringify(proof))
    quit(0)
