extends SceneTree

var world
var save_dir := OS.get_environment("HEAT_CAP")
var prefix := OS.get_environment("HEAT_PREFIX")
var movie := OS.get_environment("HEAT_MOVIE") == "1"
var shot_number := 0
var coords := {}
func _initialize() -> void:
    call_deferred("witness")

func photograph(zoom: float, title: String) -> void:
    world.set_zoom_ratio(zoom)
    await process_frame
    await physics_frame
    RenderingServer.force_draw(false)
    var raw := root.get_texture().get_image()
    var path := save_dir.path_join(prefix+"-"+title+".jpg")
    raw.save_jpg(path,.95)
    coords[title]={"foot":str(world.actor.position),"hp":world.player_hp,"camera_zoom":zoom,"camera_height":world.camera.size,"vent_pixel":str(world.camera.unproject_position(world.field_env.hearth_shell.to_global(Vector3(0,.61,-.02)))),"renderer":RenderingServer.get_video_adapter_name()}
func witness() -> void:
    world = load("res://field_opening.tscn").instantiate()
    root.add_child(world)
    current_scene = world
    for i in 10: await physics_frame
    assert(world.camp_active and not world.persist_blocked)
    world.actor.position=Vector3(1.65,0,-1.30)
    world.previous_dry_position=world.actor.position
    world.camera.position=world.actor.position+world.camera_follow_offset
    world.graphics.set_ultra(true)
    await photograph(1.0,"normal")
    await photograph(2.0,"pinch")
    if movie:
        world.set_zoom_ratio(1.)
        # Start at the south gate, sustain a normal hit outdoors, and run through
        # using the same touchscreen events as the shipped thumbstick.
        var gate:Node3D=world.gates[0]
        var from:Vector3=gate.global_position+Vector3.BACK*1.25
        from.y=0.
        world.actor.position=from
        world.previous_dry_position=from
        world.camera.position=from+world.camera_follow_offset
        world.player_invulnerability=0.
        world._player_hit(7)
        var start:=root.get_visible_rect().size*Vector2(.25,.6)
        for i in 60:
            if i==6:
                var touch:=InputEventScreenTouch.new()
                touch.index=1;touch.position=start;touch.pressed=true
                world._input(touch)
                var right:Vector3=world.camera.global_basis.x
                var drag:=InputEventScreenDrag.new()
                drag.index=1;drag.position=start+Vector2(Vector3.FORWARD.dot(right),Vector3.FORWARD.dot(right.cross(Vector3.UP)))*115.
                world._input(drag)
            if i==18:
                var lift:=InputEventScreenTouch.new()
                lift.index=1;lift.pressed=false;world._input(lift)
            for tick in 5: await physics_frame
            RenderingServer.force_draw(false)
            var frame:=root.get_texture().get_image()
            frame.save_jpg(save_dir.path_join("frames/%03d.jpg"%i),.90)
            if i%4==0:coords["frame"+str(i)]={"player":str(world.actor.position),"hp":world.player_hp,"inside":world.field_env.is_inside_camp(world.actor.position)}
    var f:=FileAccess.open(save_dir.path_join(prefix+"-capture.json"),FileAccess.WRITE)
    f.store_string(JSON.stringify(coords,"  ")+"\n")
    f.close()
    await preload("res://tests/lifecycle_test_profile.gd").drain_field_audio(self,world)
    world.queue_free()
    for i in 4:await process_frame
    quit()
